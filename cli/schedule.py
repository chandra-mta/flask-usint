"""
Database schedule table interface commands
"""
import click
from .core import with_app_context, db, models
from datetime import datetime, timedelta
from sqlalchemy import select

_FUTURE_MONTHS = 8
_PERIOD_DAYS = 6 #: Numerically 13 in as time period end points are inclusive.
#: Example SQLite rows
#: id|order_id|user_id|start|stop|assigner_id
#: 51|31||2027-02-08 00:00:00.000000|2027-02-14 00:00:00.000000|
#: 52|32||2027-02-15 00:00:00.000000|2027-02-21 00:00:00.000000|
#

_NOW = datetime.now()

def _inject_schedule_entries():
    """
    Inject additional schedule time period entries into the schedule table up to a point in the future
    Must run in an app context.
    """

    query = select(models.Schedule).order_by(models.Schedule.order_id.desc())
    latest = db.session.execute(query).scalars().first()

    if latest is None:
        return

    horizon = _NOW + timedelta(days=30 * _FUTURE_MONTHS)

    previous = latest
    order_id = latest.order_id

    while previous.stop < horizon:

        start = previous.stop + timedelta(days=1)
        stop = start + timedelta(days=_PERIOD_DAYS)

        order_id += 1

        new_entry = models.Schedule(
            order_id=order_id,
            start=start,
            stop=stop,
            user_id=None,
            assigner_id=None
        )

        db.session.add(new_entry)
        previous = new_entry

    db.session.commit()

@click.command("maintain-schedule")
@with_app_context
def maintain_schedule():
    """
    Run all period schedule database maintenance functions
    """
    _inject_schedule_entries()