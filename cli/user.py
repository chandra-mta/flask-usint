"""
Database user table interface commands
"""
import click
from .core import with_app_context, db, User

@click.command("create")
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

@click.command("groups")
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

@click.command("search")
@click.option("--id", "user_id", type=int, help="User ID")
@click.option("--username", help="Username")
@click.option("--email", help="Email address")
@click.option("--full-name", help="Full name (partial match allowed)")
@with_app_context
def find_user(user_id, username, email, full_name):
    """
    Query the database for a specific user.
    """

    if (user_id is None) and\
        (username is None) and\
        (email is None) and\
        (full_name is None):
        click.secho(
            "Must provide at least one search option (--id, --username, --email, --full-name).",
            fg="red"
        )
        return

    query = User.query

    if user_id is not None:
        query = query.filter(User.id == user_id)

    if username is not None:
        query = query.filter(User.username == username)

    if email is not None:
        query = query.filter(User.email == email)

    if full_name is not None:
        # partial match (case-insensitive)
        query = query.filter(User.full_name.ilike(f"%{full_name}%"))

    results = query.all()

    # --- Output results ---
    if not results:
        click.secho("No users found.", fg="yellow")
        return

    click.echo(f"\nFound {len(results)} user(s):\n")

    for user in results:
        click.echo(user)