"""
Database Signoff table interface commands.

Internal functions without app context help define functions for use with only one app context at a time.
Prevents unnecessarily nexting app contexts inside eachother.

class SIGNOFF_COLUMNS(Enum):
    GEN = 'general_status'
    ACIS = 'acis_status'
    ACIS_SI = 'acis_si_status'
    HRC_SI = 'hrc_si_status'
    USINT = 'usint_status'
"""
import click
from .core import with_app_context, db, models
from sqlalchemy import select

SIGNOFF_COLUMNS = {
    'general_status': models.Signoff.general_status,
    'acis_status': models.Signoff.acis_status,
    'acis_si_status': models.Signoff.acis_si_status,
    'hrc_si_status': models.Signoff.hrc_si_status,
    'usint_status': models.Signoff.usint_status
}

def _fetch_by_column_and_status(column_model, status_value):
    """
    Using one of the five SIGNOFF_COLUMN dictionary values, we query and select all values for that column matching the given status.
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


@with_app_context
def fetch_all_pending():
    """
    Fetch all pending signoffs across all columns.
    """
    pass
