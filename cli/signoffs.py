"""
Database Signoff table interface commands.

Internal functions without app context help define functions for use with only one app context at a time.
Prevents unnecessarily nexting app contexts inside eachother.

Additionally, reminder email templates are located in the app source code jinja tempaltes folder,
and are used to generate the email content for sending reminder emails for pending signoffs.
This requires operating within the app context.
uses the app.jinja_env

"""
import click
from .core import with_app_context, db, models, emailing, add_additional_cli_error_context
from sqlalchemy import select
from flask import current_app

SIGNOFF_COLUMNS = {
    'general_status': models.Signoff.general_status,
    'acis_status': models.Signoff.acis_status,
    'acis_si_status': models.Signoff.acis_si_status,
    'hrc_si_status': models.Signoff.hrc_si_status,
    'usint_status': models.Signoff.usint_status
}

SIGNOFF_SUBJECTS = {
    'general_status': "Updates needed for obsid.revs (General sign-off)",
    'acis_status': "Updates needed for obsid.revs (ACIS sign-off)",
    'acis_si_status': "Updates needed for obsid.revs (ACIS SI sign-off)",
    'hrc_si_status': "Updates needed for obsid.revs (HRC SI sign-off)",
    'usint_status': "Updates needed for obsid.revs (USINT sign-off)"
}

_OTHER_PENDING_COLUMNS = {
    'usint_status' : ('hrc_si_status', 'acis_si_status', 'acis_status', 'general_status'),
    'hrc_si_status' : ('acis_si_status', 'acis_status', 'general_status'),
    'acis_si_status' : ('acis_status', 'general_status'),
    'acis_status' : ('general_status'),
}

def _fetch_by_column_and_status(column_model, status_value):
    """
    Using one of the five SIGNOFF_COLUMN dictionary values, we query and select all values for that column matching the given status.

    Note that this internal function must be invoked within an app context, as it uses the database session to query the Signoff table.
    """
    query = select(models.Signoff).where(column_model == status_value)
    pending_list = db.session.execute(query).scalars().all()
    return pending_list

@click.command("fetch-pending")
@click.option(
    '--column',
    '-c',
    type=click.Choice([
        'general_status',
        'acis_status',
        'acis_si_status',
        'hrc_si_status',
        'usint_status'
    ]),
    help='Signoff Column to fetch pending Results.',
    required=True
)
@with_app_context
def fetch_pending(column):
    """
    Fetch all pending signoffs for a given column.
    """
    column_model = SIGNOFF_COLUMNS[column]
    pending_list = _fetch_by_column_and_status(column_model, 'Pending')
    click.echo(f"Pending signoffs for {column}:")
    for signoff in pending_list:
        click.secho(signoff, fg='cyan')

def _fetch_all_pending():
    """
    Fetch all pending signoffs across all columns.

    Note that this internal function must be invoked within an app context, as it uses the database session to query the Signoff table.
    """
    pending_results = {}
    for column_name, column_model in SIGNOFF_COLUMNS.items():
        pending_list = _fetch_by_column_and_status(column_model, 'Pending')
        pending_results[column_name] = pending_list
    return pending_results

def _categorize_pending_signoffs(pending_results):
    """
    Some signoffs are pending in multiple columns, but we need them in a specific order.
    This function parses the pending signoffs and drops them from a column's list if they are also pending
    in a previous signoff column.
    """
    categorized_pending = {
        'general_status': pending_results['general_status'],
        'acis_status': [],
        'acis_si_status': [],
        'hrc_si_status': [],
        'usint_status': []
    }

    def _other_pending(signoff, check_list):
        """
        Iterate over the ORM columns provided. If one is pending, return True
        """
        other_pending = False
        for name, value in models.iter_columns(
            signoff, check_list
        ):
            if value=='Pending':
                other_pending = True
        return other_pending

    for column_category, check_list in _OTHER_PENDING_COLUMNS.items():
        #: Check each status column for whether the previous columns are still pending.
        for signoff in pending_results[column_category]:
            other_pending = _other_pending(signoff, check_list)
            if not other_pending:
                #: Then include in the matching column category
                categorized_pending[column_category] += signoff

    return categorized_pending    

def _construct_group_reminder_content(column, pending_list):
    """
    Construct the reminder email content using the pending signoffs list.

    Note that this internal function must be invoked within an app context, as it uses the current_app.jinja_env to render the email template.
    """
    template = current_app.jinja_env.get_template(f'email/{column}_reminder_email.jinja')
    try:
        content = template.render(pending_list=pending_list)
    except RuntimeError as e:
        e = add_additional_cli_error_context(e)
        raise e
    return content

@click.command("send-reminder-emails")
@with_app_context
def send_reminder_emails():
    """
    Send a reminder email for all pending signoffs across all columns.
    """
    pending_results = _fetch_all_pending()
    categorized_pending = _categorize_pending_signoffs(pending_results)
    #print(categorized_pending)
    count = 0
    for column, pending_list in categorized_pending.items():
        count += len(pending_list)

    if count > 0:
        column = 'general_status'
        gen_content =_construct_group_reminder_content(column, categorized_pending[column])
        to = 'william.aaron@sao.si.edu'
        emailing.send_email(gen_content, SIGNOFF_COLUMNS[column], to=to)
        
        click.secho("Reminder emails sent for pending signoffs.", fg='green')
    else:
        click.secho("No Pending Signoffs. No Emails Sent.", fg='green')