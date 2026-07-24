"""
Database CLI commands

:NOTE: Since the flask-usint application is built to only connect to one database at a time,
    we cannot instantiate the app to directly use its database connections.
    Instead, we manually create these connections and import database ORMs.
"""

import click
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from urllib.parse import urlparse
from .core import db, with_app_context, models

def _file_to_sqlite_uri(filepath: str) -> str:
    """
    Convert a given file path to a sqlite URI
    """
    if not os.path.exists(filepath):
        raise OSError(f"Filepath does not exist: {filepath}")
    
    _absolute = os.path.isabs(filepath)
    
    if _absolute:
        uri = f"sqlite:///{filepath}"
    else:
        uri = f"sqlite:///{os.path.join(os.getcwd(), filepath)}"
    
    return uri

def _sqlite_uri_to_fullpath(uri: str) -> str:
    """
    Parse a given sqlite URI into a file path
    """
    if uri.startswith("sqlite:////"):
        #: Four slashes. Absolute Path
        _absolute = True
    elif uri.startswith("sqlite:///"):
        #: Three slashes/ Relative Path
        _absolute = False
    else:
        #: Incorrect format
        raise OSError(f"SQLite URI invalid (must be absolute or relative) \n URI: {uri}")
    
    _raw_path = urlparse(uri).path.lstrip("/")
    
    if _absolute:
        _full_path = os.path.join(os.getcwd(), _raw_path)
    else:
        _full_path = os.path.join("/", _raw_path)
    return _full_path

def _provide_sessions(
        prod_uri = "sqlite:///instance/usint.db",
        test_uri = "sqlite:///instance/test_usint.db"
):
    """
    Provide production and test database session connections
    """
    _prod = _sqlite_uri_to_fullpath(prod_uri)
    _test = _sqlite_uri_to_fullpath(test_uri)
    _prod_bool = os.path.exists(_prod)
    _test_bool = os.path.exists(_test)
    if _prod_bool and _test_bool:
        prod_engine = create_engine(prod_uri)
        test_engine = create_engine(test_uri)
        ProdSession = sessionmaker(bind=prod_engine)
        TestSession = sessionmaker(bind=test_engine)
        return ProdSession(), TestSession()
    
    else:
        raise OSError("Missing database file.\n prod: {prod_uri} exists: {_prod_bool}\n test: {test_uri} exists: {_test_bool}")

@click.command("create-tables")
@with_app_context
def create_tables():
    """
    All database tables must exists before the server starts.
    Otherwise, the error log will pollute with failed table creation statements as every worker tries to create any missing tables

    If the database tables have been manipulated in some way, or the server-side session table dropped,
    then run this script which creates a single application context to generate the tables for this installation.
    """
    db.create_all()

def _runpragcheck(engine):
    """Run pragma check."""
    with engine.connect() as conn:
        integrity = conn.execute(text("PRAGMA integrity_check")).scalar()
        foreign_key = conn.execute(text("PRAGMA foreign_key_check")).scalar()
        user_version = conn.execute(text("PRAGMA user_version")).scalar()
    if foreign_key is None:
        foreign_key = 'ok'
    return {
        'uri': engine.url,
        'integrity': integrity,
        'foreign_key': foreign_key,
        'user_version': user_version
    }

@with_app_context
def _pragcheck_default_config():
    """Pull app default config uri"""
    uri = db.engine.url
    engine = create_engine(uri, echo=False)
    return _runpragcheck(engine)

def _pragcheck_uri(uri):
    """Format argument uri"""
    if not uri.startswith("sqlite:///"):
        uri = _file_to_sqlite_uri(uri)
    engine = create_engine(uri, echo=False)
    return _runpragcheck(engine)

def _echo_pragcheck(pragcheck):
    """
    Click echo the pragma check
    """
    click.echo(f"Database URI: {pragcheck['uri']}")
    click.echo(f"Integrity Check: {pragcheck['integrity']}")
    click.echo(f"Foreign Key Check: {pragcheck['foreign_key']}")
    click.echo(f"User Version: {pragcheck['user_version']}")

@click.command("pragma-check")
@click.option("--uri", default=None, help="SQLite URI (or filepath) to database for check. Defaults to App Default.")
def pragma_check(uri):
    """
    \b
    Runs SQL pragma statements to check database validity.
    - integrity_check: checks for low-level database file corruption.
    - foreign_key_check: checks for logic. missing parent keys, broken references.
    - user_version: checks usint database version. Defined by admin.
    """

    if uri is None:
        pragcheck = _pragcheck_default_config()
    else:
        pragcheck = _pragcheck_uri(uri)

    _echo_pragcheck(pragcheck)

def _can_sync(prod_pragcheck, test_pragcheck):
    reason = None
    can_sync = False

    if prod_pragcheck.get('uri') == test_pragcheck.get('uri'):
        reason = "Production and test database URIs are the same."
    elif prod_pragcheck.get('integrity') != 'ok':
        reason = "Production database integrity check failed."
    elif test_pragcheck.get('integrity') != 'ok':
        reason = "Test database integrity check failed."
    elif prod_pragcheck.get('foreign_key') != 'ok':
        reason = "Production database foreign key check failed."
    elif test_pragcheck.get('foreign_key') != 'ok':
        reason = "Test database foreign key check failed."
    elif prod_pragcheck.get('user_version') != test_pragcheck.get('user_version'):
        reason = "Production and test database user versions do not match."
    else:
        can_sync = True
    return can_sync, reason

@click.command("sync-test-database")
@click.option("--prod-uri", default="sqlite:///instance/usint.db", help="Production database URI")
@click.option("--test-uri", default="sqlite:///instance/test_usint.db", help="Test database URI")
@click.option("-f", "--force", is_flag=True, help="Force sync without confirmation prompt")
def sync_test_database(prod_uri, test_uri, force):
    """
    \b
    Clear the test database tables to sync with the production database tables.
    This is a destructive operation and will overwrite the test database.
    Note that the tables are not dropped, but all entries are deleted and replaced with the production database entries.
    This preserves schema.
    """
    test_engine = create_engine(test_uri)
    prod_engine = create_engine(prod_uri)

    prod_pragcheck = _runpragcheck(prod_engine)
    test_pragcheck = _runpragcheck(test_engine)

    can_sync, reason = _can_sync(prod_pragcheck, test_pragcheck)

    if not can_sync:
        click.echo(f"Cannot sync databases: {reason}")
        _echo_pragcheck(prod_pragcheck)
        _echo_pragcheck(test_pragcheck)
        prod_engine.dispose()
        test_engine.dispose()
        return

    #: Pragma check has been passed. Proceed with sync.
    prod_engine.dispose()
    tables = db.Model.metadata.sorted_tables #: Auto sorted by foreign key dependence

    if force or click.confirm("Are you sure you want to sync the test database with the production database? This will overwrite the test database."):
        return

    with test_engine.begin() as conn:
        #: Attach the production database to the test database connection
        conn.execute(text(f"ATTACH DATABASE '{_sqlite_uri_to_fullpath(prod_uri)}' AS prod"))

        #: Iterate over the tables in reverse order to drop them (to respect foreign key constraints)
        #: Since we haven't set PRAGMA foreign_keys=ON explicitly, this will transact regardless, but keep reverse order for safety.
        for table in reversed(tables):
            table_name = table.name
            click.echo(f"Deleting all entries from test table: {table_name}")
            #conn.execute(text(f"DELETE FROM {table_name}"))

    #: TODO  include warning if the names for the prod-uri include test and/or the names for the test uri are missing them simple echo before confirmation.