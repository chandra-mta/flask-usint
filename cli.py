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
    """
    Create a new user in the database.
    User ID numbers are automatically assigned by the database upon injection.
    """

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

@click.command("set-groups")
@click.option("--username", prompt=True, help="Username to update")
@click.option(
    "--group",
    multiple=True,
    help="Specify groups (repeat for multiple, replaces existing groups. e.g. --group usint --group too)"
)
@click.option(
    "--add-group",
    multiple=True,
    help="Add group(s) without removing existing ones"
)
@click.option(
    "--remove-group",
    multiple=True,
    help="Remove group(s) from existing groups"
)
@with_app_context
def set_groups(username, group, add_group, remove_group):
    """
    Change the group assignments for a user.
    """
    #: Query for the User ORM
    user = User.query.filter_by(username=username).first()

    if not user:
        click.secho(f"User '{username}' not found.", fg="red")
        return

    # --- parse current groups ---
    current = []
    if user.groups:
        current = [g.strip().lower() for g in user.groups.split(":") if g.strip()]

    new_groups = current.copy()

    # --- replace mode ---
    if group:
        new_groups = [g.strip().lower() for g in group if g.strip()]

    # --- additive changes ---
    if add_group:
        for g in add_group:
            g = g.strip().lower()
            if g and g not in new_groups:
                new_groups.append(g)

    # --- removal ---
    if remove_group:
        new_groups = [g for g in new_groups if g not in remove_group]

    # deduplicate (safe guard)
    new_groups = list(dict.fromkeys(new_groups))

    new_group_string = ":".join(new_groups)

    # --- show diff ---
    click.echo("\nUpdating user groups:")
    click.echo(f"User: {username}")
    click.echo(f"Current groups: {user.groups or '(none)'}")
    click.echo(f"New groups:     {new_group_string or '(none)'}")

    if current == new_groups:
        click.secho("No changes detected.", fg="yellow")
        return

    # --- confirmation ---
    if not click.confirm("\nProceed with group changes?", default=False):
        click.secho("Aborted. No changes made.", fg="yellow")
        return

    # --- commit ---
    user.groups = new_group_string
    db.session.commit()

    click.secho("Groups updated successfully.", fg="green")

@click.group()
def cli():
    """
    Group together multiple functions callable from the CLI
    """
    pass
cli.add_command(create_user)
cli.add_command(set_groups)

if __name__ == "__main__":
    cli()