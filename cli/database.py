"""
Database CLI commands

:NOTE: Since the flask-usint application is built to only connect to one database at a time,
    we cannot instantiate the app to directly use its database connections.
    Instead, we manually create these connections and import database ORMs.
"""

import click
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
import os
from urllib.parse import urlparse
from .core import db, with_app_context, models


def _sqlite_uri_to_fullpath(db_uri: str) -> str:
    """
    Parse a given sqlite URI into a file path
    """
    if db_uri.startswith("sqlite:////"):
        #: Four slashes. Absolute Path
        _absolute = True
    elif db_uri.startswith("sqlite:///"):
        #: Three slashes/ Relative Path
        _absolute = False
    else:
        #: Incorrect format
        raise OSError(f"db_uri invalid. Must be Absolute or Relative \n SQLite URI: {db_uri}")
    
    _raw_path = urlparse(db_uri).path.lstrip("/")
    
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