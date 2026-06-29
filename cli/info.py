"""
Application information commands
"""
import click
from .core import with_app_context
from pprint import pformat
from flask import current_app

@click.command("print-config")
@with_app_context
def print_config():
    """
    Print the configuration of the application.

    :NOTE: Some config options such as LOGGING_MODE are altered when running the CLI commands for an app.
    """
    click.echo(
        pformat(dict(current_app.config), indent=4, width=80)
    )

@click.command("root")
@with_app_context
def app_root_path():
    """
    Print the absolute path of the configured application root.
    """
    click.echo(current_app.root_path)