#!/usr/bin/env python
"""
Python script to act as the command line interface for this flask-usint application installation.
Note that the commands are installation specific, and will affect only what this directory's application can control.
"""
import sys
def _import_fail(error):
    print("Failed to start CLI due to import error.\n")
    print(str(error))
    print("Check that you have conda activated the environment running this application installation.")
    print(f"Python: {sys.executable}")
    sys.exit(1)

try:
    #: If fails, likely not running the correct conda environment.
    from cus_app import create_app
    from cus_app.extensions import db
    from cus_app.models import User
    import click
    from functools import wraps
except ImportError as e:
    _import_fail(e)

#
# --- Command Line Functions
#

def with_app_context(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        app = create_app()
        with app.app_context():
            return f(*args, **kwargs)
    return wrapper


@click.command("create-user")
@click.option("--username", prompt="Username (POGO Username)", help="Username (POGO Username)")
@click.option("--email", prompt=True, help="Email address")
@click.option("--full-name", prompt="Full name (first and last)", help="Full name (first and last)")
@click.option(
    "--group",
    multiple=True,
    default=["usint"],
    help="Repeat this option to assign multiple groups (e.g. --group usint --group too)",
)
@click.option("--inactive", is_flag=True, help="Mark user as inactive (default: active)")
@with_app_context
def create_user(username, email, full_name, group, inactive):
    """Create a new user in the database."""

    # --- Validate uniqueness ---
    existing = User.query.filter(
        (User.username == username)
    ).first()

    if existing:
        click.secho("User with that username already exists.", fg="red")
        return


    # --- Create user ---
    user = User(
        username = username,
        email = email,
        full_name = full_name,
        is_active = not inactive,
        groups = ":".join(group) #: normalize formatting
    )
    
    click.echo("\nuser to be created:")
    click.echo(user)
    
    if not click.confirm("\nProceed with creating this user?", default=False):
        click.secho("Aborted. No changes made.", fg="yellow")
        return
    db.session.add(user)
    db.session.commit()
    click.secho("User created successfully.", fg="green")

@click.group()
def cli():
    pass

cli.add_command(create_user)

if __name__ == "__main__":
    cli()