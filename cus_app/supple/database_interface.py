"""
Database Interface
==============

**database_interface.py**: Set of functions interfacing with the Usint database

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: May 01, 2025


:NOTE: Some of the ORM construction functions operate on the SQLalchemy.orm.relationship() mapping to instantiate parameters,
while others reference foreign and primary keys directly. This is because the relationship() mapping requires related ORM's to be added to the database session
before instantiation if the relationship mapped key has the NON NULL constraint.

Therefore, it's more reliable to instantiate with the primary key id's directly for web interface transactions wherever possible.
Such instances would be using the current_user.id rather than the current_user ORM.
In other cases, this is not possible, for example when adding a Revision and Signoff table entires in a web request. This is not possible because it is not known
what Primary Key is available in those tables until database transaction time.
"""
import os
from datetime import datetime, timedelta
import json
from sqlalchemy import select, desc, case, text, or_, delete
from sqlalchemy.orm.exc import NoResultFound
from cus_app.extensions import db
import cus_app.emailing as mail
from cus_app.models import User, Revision, Signoff, Parameter, Request, Original, Schedule
from flask import flash
from flask_login import current_user
from cus_app.supple.helper_functions import coerce_to_json, DATETIME_FORMATS, is_open, get_next_weekday, coerce
from cus_app.supple.read_ocat_data import read_basic_ocat_data
from calendar import MONDAY, SUNDAY

stat_dir =  os.path.join(os.path.dirname(os.path.abspath(__file__)),'..', 'static')
with open(os.path.join(stat_dir, 'parameter_selections.json')) as f:
    _PARAM_SELECTIONS = json.load(f)

def construct_revision(obsid,ocat_data,kind,notes = None):
    """
    Generate a Revision ORM object based on the provided obsid information
    """
    rev_no = find_next_rev_no(obsid)
    curr_epoch = int(datetime.now().timestamp())
    revision = Revision(obsid = int(obsid),
                    revision_number = rev_no,
                    kind = kind,
                    sequence_number = ocat_data.get('seq_nbr'),
                    time = curr_epoch,
                    user_id = current_user.id,
                    notes = notes
                    )
    return revision

def construct_signoff(rev_obj, req_dict={}):
    """
    Determine the Signoffs entry based on the revision object based in kind:(norm, asis, remove, clone).
    The signoff status options are : ('Signed', 'Not Required', 'Pending', 'Discard').
    signoff time is the epoch time of when the signoff was made.
    The signoff itself lists the user id.
    """
    
    if rev_obj.kind in ('asis', 'remove'):
        #:Adding or removing from the approved list. Auto signoff with Usint revision performing user.
        signoff = construct_auto_signoff(rev_obj)
    elif rev_obj.kind == 'clone':
        #: Needs ArcOps and Usint Signoff
        signoff = Signoff(revision = rev_obj,
                            general_status = 'Pending',
                            acis_status = 'Not Required',
                            acis_si_status = 'Not Required',
                            hrc_si_status = 'Not Required',
                            usint_status = 'Pending',
                    )
    elif rev_obj.kind == 'norm':
        #: Determine based on change requests linked to the revision object
        gen, acis, acis_si, hrc_si =  determine_signoff(req_dict)
        signoff = Signoff(revision=rev_obj,
                          general_status = gen,
                          acis_status = acis,
                          acis_si_status = acis_si,
                          hrc_si_status = hrc_si,
                          usint_status = 'Pending'
        )
    return signoff

def construct_auto_signoff(rev_obj):
    """
    Automatically fill a usint signoff ORM without other signoffs.
    """
    curr_epoch = int(datetime.now().timestamp())
    signoff = Signoff(revision = rev_obj,
                            general_status = 'Not Required',
                            acis_status = 'Not Required',
                            acis_si_status = 'Not Required',
                            hrc_si_status = 'Not Required',
                            usint_status = 'Signed',
                            usint_signoff_id = rev_obj.user_id,
                            usint_time = curr_epoch
                    )
    return signoff

def perform_signoff(signoff_id, signoff_kind):
    """
    Update the signoff entry matching to the provided id

    :param signoff_kind: String determining the kind of signoff to provide (gen, acis, acis_si, hrc_si, usint, approve)
    """
    signoff_id = int(signoff_id)
    curr_epoch = int(datetime.now().timestamp())
    signoff_obj = db.session.execute(select(Signoff).where(Signoff.id == signoff_id)).scalar_one()
    matching_rev = signoff_obj.revision
    ocat_data = read_basic_ocat_data(matching_rev.obsid)
    if signoff_kind == 'gen':
        signoff_obj.general_status = 'Signed'
        signoff_obj.general_signoff_id = current_user.id
        signoff_obj.general_time = curr_epoch
    elif signoff_kind == 'acis':
        signoff_obj.acis_status = 'Signed'
        signoff_obj.acis_signoff_id = current_user.id
        signoff_obj.acis_time = curr_epoch
    elif signoff_kind == 'acis_si':
        signoff_obj.acis_si_status = 'Signed'
        signoff_obj.acis_si_signoff_id = current_user.id
        signoff_obj.acis_si_time = curr_epoch
    elif signoff_kind == 'hrc_si':
        signoff_obj.hrc_si_status = 'Signed'
        signoff_obj.hrc_si_signoff_id = current_user.id
        signoff_obj.hrc_si_time = curr_epoch
    elif signoff_kind in ('usint', 'approve'):
        signoff_obj.usint_status = 'Signed'
        signoff_obj.usint_signoff_id = current_user.id
        signoff_obj.usint_time = curr_epoch
        if signoff_kind == 'approve':
            if not is_approved(matching_rev.obsid):
                #: Additionally create an approval revision and signoff.
                new_revision = Revision(obsid = matching_rev.obsid,
                                        revision_number = find_next_rev_no(matching_rev.obsid),
                                        kind = 'asis',
                                        sequence_number = matching_rev.sequence_number,
                                        time = curr_epoch,
                                        user_id = current_user.id
                )
                new_signoff = construct_auto_signoff(new_revision)
                db.session.add(new_revision)
                db.session.add(new_signoff)
                #: Also send notification email if performing this special approval signoff
                msg = mail.quick_approval_state_email(ocat_data, new_revision)
                mail.send_msg(msg)
            else:
                flash(f"Obsid {signoff_obj.revision.obsid} already approved. Performing only Usint Signoff.")
    mail.signoff_notify(ocat_data, matching_rev, signoff_obj)
    db.session.commit()

def construct_requests(rev_obj, req_dict):
    """
    Construct a list of Request ORM's for insertion.
    """
    all_requests = []
    for key, value in req_dict.items():
        if key in _PARAM_SELECTIONS["general_signoff_params"] + _PARAM_SELECTIONS["acis_signoff_params"] + _PARAM_SELECTIONS["acis_si_signoff_params"] + _PARAM_SELECTIONS["hrc_si_signoff_params"]:
            param = pull_param(key)
            req = Request(revision_id= rev_obj.id,
                        parameter_id = param.id,
                        value = coerce_to_json(value)
            )
            all_requests.append(req)
    return all_requests

def construct_originals(rev_obj, org_dict):
    """
    Construct a list of Original ORM's for insertion. Only adding non-null values as null is inferred.
    """
    all_originals = []
    for key, value in org_dict.items():
        if value is not None:
            if key in _PARAM_SELECTIONS["general_signoff_params"] + _PARAM_SELECTIONS["acis_signoff_params"] + _PARAM_SELECTIONS["acis_si_signoff_params"] + _PARAM_SELECTIONS["hrc_si_signoff_params"]:
                param = pull_param(key)
                req = Original(revision_id= rev_obj.id,
                            parameter_id = param.id,
                            value = coerce_to_json(value)
                )
                all_originals.append(req)
    return all_originals

def determine_signoff(req_dict):
    """
    Read the requested changes and determine what kind of signoff is necessary.
    """
    gen = 'Not Required'
    acis = 'Not Required'
    acis_si = 'Not Required'
    hrc_si = 'Not Required'
    #: Iterate through the requested parameter changes and define their signoff.
    for key in req_dict.keys():
        if key in _PARAM_SELECTIONS['general_signoff_params']:
            gen = 'Pending'
        if key in _PARAM_SELECTIONS['acis_signoff_params']:
            acis = 'Pending'
        if key in _PARAM_SELECTIONS['acis_si_signoff_params']:
            acis_si = 'Pending'
        if key in _PARAM_SELECTIONS['hrc_si_signoff_params']:
            hrc_si = 'Pending'
    return gen, acis, acis_si, hrc_si

def user_by_name(username):
    """
    Return User ORM matching provide username. Returns None if no user matches that name.
    """
    return db.session.execute(select(User).where(User.username == username)).scalars().first()

def pull_param(param):
    """
    Fetch the Parameter ORM by name.
    Will return an SQLAlchemy.orm.exc.NoResultFound if the parameter is not in the table
    """
    try:
        result = db.session.execute(select(Parameter).where(Parameter.name == param)).scalar_one()
    except NoResultFound:
        #: Return same error with more specifics
        raise NoResultFound(f"No result for '{param}' parameter search in table.")

    return result

def pull_revision(order_by = {'id': 'asc'}, **kwargs):
    """
    Fetch list of recent revisions based on kwarg criteria
    """
    #
    # --- Starting query object
    #
    query = select(Revision)
    
    #
    # --- Kwarg processing is ordered by order of execution (WHERE, ORDER_BY, LIMIT)
    #
    before = to_epoch(kwargs.pop('before', None))
    if before is not None:
        query = query.where(Revision.time <= before)
        
    after = to_epoch(kwargs.pop('after', None))
    if after is not None:
        query = query.where(Revision.time >= after)
    
    limit = kwargs.pop('limit', None)
    if limit is not None:
        query = query.limit(limit)
    #
    # --- Assumed the remaining unidentified kwargs are WHERE column equality searches
    # --- which will still execute before the ORDER_BY and LIMIT statements in the SQL query,
    # --- but the SQLAlchemy query builder will list these ones after the 'before', 'after' wheres
    #
    query = query.filter_by(**kwargs)
    
    #: By default, order the query by descending Revision ID number so that the end result order
    #: contains a suborder of returning the most recently made revisions first.
    ordering = ",".join([f"{k} {v}" for k,v in order_by.items()])
    query = query.order_by(text(ordering))
    return db.session.execute(query).scalars().all()

def pull_status(limit = 200, **kwargs):
    """
    Pull Revisions and Signoffs in specific ordering.

    :param limit: _description_, defaults to 200
    :type limit: int, optional
    :return: Recent (Revision, Signoff) in descending order.
    """
    if 'order_user' in kwargs.keys():
        #: Order by listing the target user id first, then the rest in descending order
        order_user = int(kwargs['order_user'])
        query = select(Revision, Signoff).join(Revision.signoff).order_by(case((Revision.user_id == order_user, 0),else_=1)).order_by(desc(Revision.id)).limit(limit)

    elif kwargs.get('order_obsid'):
        #: Special case in which we must first subquery the most recent LIMIT number of revisions, then sort by obsid
        subquery = select(Revision.id).order_by(desc(Revision.id)).limit(limit).subquery()
        query = select(Revision, Signoff).join(Revision.signoff).select_from(Revision, subquery).where(Revision.id == subquery.c.id).order_by(Revision.obsid).order_by(desc(Revision.revision_number))
    elif 'user' in kwargs.keys():
        #Pull only the signoffs and revisions involving this user
        user_id = int(kwargs.get('user'))
        user_wheres = or_(Revision.user_id == user_id,
                  Signoff.general_signoff_id == user_id,
                  Signoff.acis_signoff_id == user_id,
                  Signoff.acis_si_signoff_id == user_id,
                  Signoff.hrc_si_signoff_id == user_id,
                  Signoff.usint_signoff_id == user_id
                 )
        query = select(Revision, Signoff).join(Revision.signoff).filter(user_wheres).order_by(desc(Revision.id)).limit(limit)
    else:
        #: Default descending order
        query = select(Revision, Signoff).join(Revision.signoff).order_by(desc(Revision.id)).limit(limit)
    return db.session.execute(query).all()

def find_next_rev_no(obsid):
    """
    Find the revisions for the provided obsid in the listed revision table, and identify the next revision number.

    :return: Next revision number
    :rtype: int
    """
    revision_numbers = db.session.execute(select(Revision.revision_number).where(Revision.obsid == obsid)).scalars().all()
    if len(revision_numbers) == 0:
        return 1
    else:
        return max(revision_numbers) + 1

def is_approved(obsid):
    """
    Check whether an obsid is listed as approved in the usint database

    :rtype: bool
    """
    obsid = int(obsid)
    revision_result = db.session.execute(db.select(Revision).where(Revision.obsid==obsid).order_by(Revision.revision_number)).scalars().all()
    is_approved = False
    for rev in revision_result:
        if rev.kind == 'asis':
            is_approved = True
        elif rev.kind == 'remove':
            is_approved = False
    return is_approved

def has_open_revision(obsid):
    """
    Check database for whether there is an open revision for the approval process.

    :rtype: bool
    """
    result = db.session.execute(select(Revision, Signoff).join(Revision.signoff).where(Revision.obsid == obsid)).all()
    has_open_revision = False
    for revs, signs in result:
        if is_open(signs):
            has_open_revision = True
            break
    return has_open_revision

def remove(revision_id, signoff_id, column):
    """
    Remove signoff entries with the remove submission page
    """
    if column == 'revision':
        db.session.execute(delete(Revision).where(Revision.id == revision_id))
    else:
        signoff = db.session.execute(select(Signoff).where(Signoff.id == signoff_id)).scalar_one()
        setattr(signoff, f"{column}_status", 'Pending')
        setattr(signoff, f"{column}_signoff_id", None)
        setattr(signoff, f"{column}_time", None)
        db.session.add(signoff)
    db.session.commit()

def to_epoch(time):
    """
    Convert variety of time input to epoch time
    """
    if time is None:
        return None
    elif isinstance(time,(int, float)):
        return time
    elif isinstance(time, datetime):
        return time.timestamp()
    elif isinstance(time,str):
        x = time.replace('::', ':')
        x = x.split('.')[0]
        for format in DATETIME_FORMATS:
            try:
                return datetime.strptime(x,format).timestamp()
            except ValueError:
                pass

#
# --- Scheduler Specific Convenience Functions
#
def pull_schedule(begin = datetime.now() - timedelta(days=30)):
    """
    Pull TOO schedule information from the schedules table
    """
    query = select(Schedule).where(Schedule.start > begin).order_by(Schedule.start)
    return db.session.execute(query).scalars().all()

def unlock_schedule_entry(schedule_id):
    """
    Undo signup for a TOO scheduled time duration entry
    """
    sched = db.session.execute(select(Schedule).where(Schedule.id == schedule_id)).scalar_one()
    sched.user_id = None
    sched.assigner_id = None
    db.session.commit()

def split_schedule_entry(schedule_id):
    """
    Add a new time period entry to the table and adjusting the order and start / stop time as necessary.
    """
    sched = db.session.execute(select(Schedule).where(Schedule.id == schedule_id)).scalar_one()
    old_start = sched.start
    old_stop = sched.stop
    diff = (old_stop - old_start).total_seconds()
    if diff <=  172800:
        flash("Sorry there is not enough time to split the row you specified.")
        return None
    #
    # --- Find the start and stop times for both the second split entry
    #
    day_diff = (0.5 * diff) // 86400
    new_stop = sched.start + timedelta(days = day_diff)
    second_start = new_stop + timedelta(days = 1)
    #
    # --- adjust existing orms to make room for new entry.
    #
    sched.stop = new_stop
    result = db.session.execute(select(Schedule).where(Schedule.order_id > sched.order_id)).scalars().all()
    for entry in result:
        entry.order_id += 1
    #
    # --- Insert the new split entry
    #
    new_entry = Schedule(user_id=None,
                         order_id = sched.order_id + 1,
                         start = second_start,
                         stop = old_stop
                         )
    db.session.add(new_entry)
    db.session.commit()

def delete_schedule_entry(schedule_id):
    """
    Remove the time period entry from the table, editing the unlocked adjacent entires to fill in the gaps.
    """
    sched = db.session.execute(select(Schedule).where(Schedule.id == schedule_id)).scalar_one()
    duration = (sched.stop - sched.start).total_seconds()

    prev_sched = db.session.execute(select(Schedule).where(Schedule.order_id == sched.order_id - 1)).scalar_one()
    next_sched = db.session.execute(select(Schedule).where(Schedule.order_id == sched.order_id + 1)).scalar_one()

    #: First check the adjacent periods for determining how we can edit them
    can_edit_prev = prev_sched.user is None
    can_edit_next = next_sched.user is None
    if not can_edit_prev and not can_edit_next:
        flash("Cannot remove specified row. Both adjacent rows locked and uneditable.")
    prev_duration = (prev_sched.stop - prev_sched.start).total_seconds()
    next_duration = (next_sched.stop - next_sched.start).total_seconds()
    #: Try editing only previous entry first
    if can_edit_prev:
        if prev_duration + duration <= 518400:
            #: Able to only edit previous entry
            prev_sched.stop = sched.stop
            result = db.session.execute(select(Schedule).where(Schedule.order_id > sched.order_id)).scalars().all()
            for entry in result:
                entry.order_id -= 1
            db.session.execute(delete(Schedule).where(Schedule.id == sched.id))
            db.session.commit()
            flash("Row Removed. Fit duration into previous entry")
            return None

    if can_edit_next:
        if next_duration + duration <= 518400:
            #: Able to only edit next entry
            next_sched.start = sched.start
            result = db.session.execute(select(Schedule).where(Schedule.order_id > sched.order_id)).scalars().all()
            for entry in result:
                entry.order_id -= 1
            db.session.execute(delete(Schedule).where(Schedule.id == sched.id))
            db.session.commit()
            flash("Row Removed. Fit duration into next entry")
            return None
    
    if can_edit_prev and can_edit_next:
        if prev_duration + duration + next_duration <= 2 * 518400:
            #: Rare edge case in which are removing an entry that is spread between the monday to sunday cycle.
            prev_sched.stop = get_next_weekday(SUNDAY,sched.start)
            next_sched.start = get_next_weekday(MONDAY,prev_sched.stop)
            result = db.session.execute(select(Schedule).where(Schedule.order_id > sched.order_id)).scalars().all()
            for entry in result:
                entry.order_id -= 1
            db.session.execute(delete(Schedule).where(Schedule.id == sched.id))
            db.session.commit()
            flash("Row Removed. Fit duration between previous and next entry with changeover at start of workweek.")
            return None

    #: Reaching this point means we cannot fit time period into the schedule
    flash("Cannot remove specified row. Cannot fit deleted time duration into adjacent entry.")


def update_schedule_entry(schedule_id, user_id, start_string, stop_string):
    """
    Perform signup for a TOO scheduled time duration entry

    Ensures that the time duration entry does not exceed a seven day period
    but calculates difference as less than or equal to six days since the default datetime value puts the stop as
    the start of the day, whereas we reference the end of the day.
    """
    sched = db.session.execute(select(Schedule).where(Schedule.id == schedule_id)).scalar_one()
    user_id = coerce(user_id)
    #: Cannot record the start and stop strings in the url as back slashes since the browser interprets that as a different page.
    start = datetime.strptime(start_string, "%B-%d-%Y")
    stop = datetime.strptime(stop_string, "%B-%d-%Y")
    duration = (stop - start).total_seconds()
    if duration > 518400:
        flash("Updated entry exceeds typical week duration. Please Correct.")
        return None
    elif duration < 518400:
        #: Update to schedule with a partial split. Verify adjacently split values.
        prev_sched = db.session.execute(select(Schedule).where(Schedule.order_id == sched.order_id - 1)).scalar_one()
        next_sched = db.session.execute(select(Schedule).where(Schedule.order_id == sched.order_id + 1)).scalar_one()

        prev_duration = (prev_sched.stop - prev_sched.start).total_seconds()
        next_duration = (next_sched.stop - next_sched.start).total_seconds()

        can_edit_prev = prev_sched.user is None and prev_duration < 518400
        can_edit_next = next_sched.user is None and next_duration < 518400

        #: Check if we need to edit the adjacent split values. If so, then runs checks for how to do so.
        if not ((start - prev_sched.stop).total_seconds() <= 86400 and (next_sched.start - stop).total_seconds() <= 86400 ):
            if not can_edit_prev and not can_edit_next:
                flash("Updated entry less that typical week duration and cannot fit into adjacent entries. Please Correct.")
                return None
            
            if prev_duration < next_duration:
                if can_edit_prev:
                    prev_sched.stop = start - timedelta(days=1)
                elif can_edit_next:
                    next_sched.start = stop + timedelta(days=1)
            else:
                if can_edit_next:
                    next_sched.start = stop + timedelta(days=1)
                elif can_edit_prev:
                    prev_sched.stop = start - timedelta(days=1)
    
    #: Ensure the time period entry matches those listed on the form
    sched.start = start
    sched.stop = stop
    #: Editing the entry possible. Change the listed user
    if user_id is not None:
        sched = db.session.execute(select(Schedule).where(Schedule.id == schedule_id)).scalar_one()
        sched.user_id = user_id
        sched.assigner_id = current_user.id
        subject = 'Update in TOO POC Duty Signup'
        if sched.user_id == sched.assigner_id:
            content = f"{sched.user.full_name} ({sched.user.username}) has signed up for POC duty on the following period(s):\n\n"
        else:
            content = f"{sched.user.full_name} ({sched.user.username}) has been assigned POC duty by {current_user.full_name} ({current_user.username}) on the following period(s):\nIf this is unexpected. Please contact the assigner.\n\n"
        content += f"Start: {start.strftime("%B %d %Y")}\nStop:  {stop.strftime("%B %d %Y")}\n"
        to = [sched.user.email, current_user.email]
        mail.send_email(content, subject, to)
    else:
        flash("No user selected. Only time period(s) adjusted.")

    db.session.commit()