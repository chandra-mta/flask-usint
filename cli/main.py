"""
CLI interface groupings
"""

import click
from .user import create_user, set_groups, find_user
from .schedule import maintain_schedule

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

# Attach commands to the subgroup
user.add_command(create_user)
user.add_command(set_groups)
user.add_command(find_user)

schedule.add_command(maintain_schedule)

# Attach subgroup to root CLI
cli.add_command(user)
cli.add_command(schedule)