"""
CLI interface groupings
"""

import click
from .user import create_user, set_groups, find_user, fetch_all_users
from .schedule import maintain_schedule, fetch_schedule, send_too_reminder_emails
from .info import print_config, app_root_path, url_for_endpoint
from .database import create_tables, pragma_check, sync_test_database, fetch_approved_obsids, fetch_revision_history
from .signoffs import fetch_pending, send_signoff_reminder_emails, fetch_all_signoffs
from .core import with_app_context
from flask import current_app

@click.command()
@with_app_context
def version():
    """
    Print out the current application version
    """
    click.secho(current_app.config.get('APP_VERSION'))

@click.group()
def cli():
    """CLI for interacting with the usint database"""
    pass


@click.group()
def user():
    """User management commands"""
    pass

@click.group()
def schedule():
    """TOO Schedule management commands"""
    pass

@click.group()
def info():
    """App installation information commands"""
    pass

@click.group()
def database():
    """Database CLI commands"""
    pass

@click.group()
def signoffs():
    """Signoff table management commands"""
    pass

# Attach commands to the subgroup
user.add_command(create_user)
user.add_command(set_groups)
user.add_command(find_user)
user.add_command(fetch_all_users)

schedule.add_command(maintain_schedule)
schedule.add_command(fetch_schedule)
schedule.add_command(send_too_reminder_emails)

info.add_command(print_config)
info.add_command(app_root_path)
info.add_command(url_for_endpoint)

database.add_command(create_tables)
database.add_command(pragma_check)
database.add_command(sync_test_database)
database.add_command(fetch_approved_obsids)
database.add_command(fetch_revision_history)

signoffs.add_command(fetch_pending)
signoffs.add_command(send_signoff_reminder_emails)
signoffs.add_command(fetch_all_signoffs)

# Attach subgroup to root CLI
cli.add_command(user)
cli.add_command(schedule)
cli.add_command(info)
cli.add_command(database)
cli.add_command(signoffs)
cli.add_command(version)