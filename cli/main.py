"""
CLI interface groupings
"""

import click
from .user import create_user, set_groups, find_user
from .schedule import maintain_schedule
from .info import print_config, app_root_path
from .database import create_tables

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

# Attach commands to the subgroup
user.add_command(create_user)
user.add_command(set_groups)
user.add_command(find_user)

schedule.add_command(maintain_schedule)
info.add_command(print_config)
info.add_command(app_root_path)

database.add_command(create_tables)

# Attach subgroup to root CLI
cli.add_command(user)
cli.add_command(schedule)
cli.add_command(info)
cli.add_command(database)