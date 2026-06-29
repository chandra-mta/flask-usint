"""
Database schedule table interface commands
"""
import click
from .core import with_app_context, db, User, Schedule

@click.command("maintain-schedule")
@with_app_context
def maintain_schedule():
    pass