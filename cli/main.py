"""
CLI interface groupings
"""

import click
from .user import create_user, set_groups, find_user


@click.group()
def cli():
    """CLI for interacting with the usint database"""
    pass


@click.group()
def user():
    """User management commands"""
    pass


# Attach commands to the subgroup
user.add_command(create_user)
user.add_command(set_groups)
user.add_command(find_user)

# Attach subgroup to root CLI
cli.add_command(user)