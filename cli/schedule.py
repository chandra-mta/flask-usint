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

def _set_order_id():
    """
    Pull all schedule entries and update the order_id column.
    Any schedule entry in the past or present is closed and marked order_id == Null
    All future schedule entries, order by start and stop time intervals, then have their order_id's updates sequentially.

    The order_id and start/stop time columns exist in tandem so that users can edit the time intervals while maintaining an ordered schedule.
    """
    query = select(models.Schedule).order_by(models.Schedule.start.asc())
    entries_by_time = db.session.execute(query).scalars().all()

    order_id = 0
    for sched in entries_by_time:
        #: Iterate over each ORM, edit the attributes by direct python assignment.
        #: The SQLalchemy library will keep track of these objects and translate the changes to SQL transactions at the commit() call.
        if sched.stop <= _NOW:
            #: Old Schedule entry. Maintain null order ID
            if sched.order_id is not None:
                sched.order_id = None
        elif sched.start <= _NOW <= sched.stop:
            #: Current Schedule entry. Closed. Null order ID
            if sched.order_id is not None:
                sched.order_id = None
        elif _NOW <= sched.start:
            #: Future Schedule entry. Increment order_id
            sched.order_id = order_id
            order_id +=1
    
    #: Commit order_id updates to table
    db.session.commit()

@click.command("maintain-schedule")
@with_app_context
def maintain_schedule():
    """
    Run all period schedule database maintenance functions
    """
    _inject_schedule_entries()
    _set_order_id()