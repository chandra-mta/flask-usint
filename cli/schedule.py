"""
Database schedule table interface commands
"""
import click
from .core import with_app_context, db, models, supple
from datetime import datetime, timedelta
from sqlalchemy import select
import json

_FUTURE_MONTHS = 8
_PERIOD_DAYS = 6 #: Numerically 13 in as time period end points are inclusive.
#: Example SQLite rows
#: id|order_id|user_id|start|stop|assigner_id
#: 51|31||2027-02-08 00:00:00.000000|2027-02-14 00:00:00.000000|
#: 52|32||2027-02-15 00:00:00.000000|2027-02-21 00:00:00.000000|
#

def _grab_now():
    return datetime.now()

def _inject_schedule_entries():
    """
    Inject additional schedule time period entries into the schedule table up to a point in the future
    Must be called in app context wrapper function.
    """
    _now = _grab_now()
    query = select(models.Schedule).order_by(models.Schedule.order_id.desc())
    latest = db.session.execute(query).scalars().first()

    if latest is None:
        return

    horizon = _now + timedelta(days=30 * _FUTURE_MONTHS)

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
    db.session.flush() #: Ensure Primary key ID's are assigned in case later maintenance functions need them

def _set_order_id():
    """
    Pull all schedule entries and update the order_id column.
    Any schedule entry in the past or present is closed and marked order_id == Null
    All future schedule entries, order by start and stop time intervals, then have their order_id's updates sequentially.
    Must be called in app context wrapper function.
    The order_id and start/stop time columns exist in tandem so that users can edit the time intervals while maintaining an ordered schedule.
    """
    _now = _grab_now()
    query = select(models.Schedule).order_by(models.Schedule.start.asc())
    entries_by_time = db.session.execute(query).scalars().all()

    order_id = 0
    for sched in entries_by_time:
        #: Iterate over each ORM, edit the attributes by direct python assignment.
        #: The SQLalchemy library will keep track of these objects and translate the changes to SQL transactions at the commit() call.
        if sched.stop <= _now:
            #: Old Schedule entry. Maintain null order ID
            if sched.order_id is not None:
                sched.order_id = None
        elif sched.start <= _now <= sched.stop:
            #: Current Schedule entry. Closed. Null order ID
            if sched.order_id is not None:
                sched.order_id = None
        elif _now <= sched.start:
            #: Future Schedule entry. Increment order_id
            sched.order_id = order_id
            order_id +=1

def _fetch_current_schedule():
    """
    Fetch the current scheduler entry.
    Must be called in app context wrapper function.
    """
    _now = _grab_now()
    query = select(models.Schedule).where(models.Schedule.start <= _now).where(models.Schedule.stop >= _now)
    current_schedule = db.session.execute(query).scalar_one()
    return current_schedule

def _fetch_by_order_id(order_id = 0):
    """
    Fetch an upcoming schedule entry by order id.
    Must be called in app context wrapper function.

    Note that upcoming schedule entries start indexing at 0 as the represent the order of editable entries.
    The current schedule is not editable and therefore order_id = Null.
    The next schedule entry will be editable, therefore it starts indexing at 0.
    """
    query = select(models.Schedule).where(models.Schedule.order_id == order_id)
    schedule = db.session.execute(query).scalar_one()
    return schedule

def _format_schedule_info(sched):
    """
    Format SQLAlchemy ORM into a JSON dict of Schedule and user information
    Must be called in app context wrapper function.
    """
    if sched.user_id is None:
        #: No assigned user, therefore the resultant user is None in the fetched information.
        _dict = {
            'schedule': sched.to_dict(),
            'user': None
        }
    else:
        #: Assigned schedule
        _dict = {
            'schedule': sched.to_dict(),
            'user': sched.user.to_dict()
        }
    _json = supple.helper_functions.coerce_to_json(_dict, indent = 2)
    return _json

@click.command("maintain-schedule")
@with_app_context
def maintain_schedule():
    """
    Run all period schedule database maintenance functions
    """
    try:
        _inject_schedule_entries()
        _set_order_id()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


@click.command("fetch-schedule")
@click.option("--order-id", default = None, help="Specify order_id to fetch upcoming entires. First upcoming entry starts at zero.")
@click.option("--json-format/--no-json-format", default=False, help="Format user results as JSON file to stdout.")
@with_app_context
def fetch_schedule(order_id, json_format):
    """
    Fetch the current or an editable upcoming schedule entry.
    
    Note that upcoming schedule entries start indexing at 0 as the represent the order of editable entries.
    The current schedule is not editable and therefore order_id = Null.
    The next schedule entry will be editable, therefore it starts indexing at 0.
    """
    if order_id is None:
        #: We fetch the current schedule entry.
        _schedule = _fetch_current_schedule()
    elif int(order_id) < 0:
        click.secho("order id must be a non-negative integer.", fg='red')
    else:
        _schedule = _fetch_by_order_id(order_id=int(order_id))

    if json_format:
        _json = _format_schedule_info(_schedule)
        click.echo(_json)
    else:
        click.secho(_schedule)