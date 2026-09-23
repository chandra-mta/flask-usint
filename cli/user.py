"""
Database user table interface commands
"""
import click
from .core import with_app_context, db, models, supple

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
    existing = models.User.query.filter(
        (models.User.username == username)
    ).first()

    if existing:
        click.secho("User with that username already exists.", fg="red")
        return


    # --- Create user ---
    user = models.User(
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
    user = models.User.query.filter_by(username=username).first()

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
@click.option("--groups", help="Groups")
@click.option("--is-active", is_flag=True, help="Return only users marked active.")
@click.option("--json-format/--no-json-format", default=False, help="Format user results as JSON file to stdout.")
@with_app_context
def find_user(user_id, username, email, full_name, groups, is_active, json_format):
    """
    Query the database for a specific user.
    """

    if (user_id is None) and\
        (username is None) and\
        (email is None) and\
        (full_name is None) and \
        (groups is None):
        click.secho(
            "Must provide at least one search option (--id, --username, --email, --full-name, --groups).",
            fg="red"
        )
        return

    query = models.User.query

    if user_id is not None:
        query = query.filter(models.User.id == user_id)

    if username is not None:
        query = query.filter(models.User.username == username)

    if email is not None:
        query = query.filter(models.User.email == email)

    if full_name is not None:
        # partial match (case-insensitive)
        query = query.filter(models.User.full_name.ilike(f"%{full_name}%"))
    
    if groups is not None:
        #: uses partial match due to group string formatting listing multiple groups for an individual
        query = query.filter(models.User.groups.ilike(f"%{groups}%"))

    if is_active:
        query = query.filter(models.User.is_active == True)

    results = query.all()

    #: Output results
    if json_format:
        if not results:
            click.echo(supple.helper_functions.coerce_to_json(None))
        else:
            formatted_result = []
            for user in results:
                formatted_result.append(user.to_dict())
            _json = supple.helper_functions.coerce_to_json(formatted_result, indent=2)
            click.echo(_json)
    else:

        if not results:
            click.secho("No users found.", fg="yellow")
        else:
            click.secho(f"Found {len(results)} user(s):", fg='green')
            for user in results:
                click.echo(user)