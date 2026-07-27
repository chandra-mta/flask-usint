#!/usr/bin/env python
"""
This script parses the old database text file formats to inject the data into the usint database.

This is a convenience script to assist our database model transition and is not necessary for the function of the application.


This script operates by writing to the usint.db file which will be our production database.
But during this transition period, it will merely be a correctly formatted database reflecting the same contents as
the v1.1 production text files which we treat as our database (everything in /data/mta4/CUS/www/Usint/ocat)

Our test run of the v2.1 application will operate on the test_usint.db file, which will periodically be wiped to reflect
the contents onf the "production" usint.db file. This is all meant to compartmentalize our data so that
our real revisions are recorded as they used to be, while these *.db SQLite databases are updated to reflect their contents.

This script is prototyped for migrating our old format and thus is not written with updates in mind.
Do not develop this script. Only use it for the v1.1 to v2.1 database migration.

"""

import os
from datetime import datetime
import json
import sqlite3 as sq
from contextlib import closing
from astropy.table import Table
import numpy as np
import re
import itertools

from sqlalchemy import create_engine, select, desc

from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy import event

#: local imports
from cus_app.models import User, Revision, Signoff, Parameter, Request, Original, Schedule
import __chkupdata_read as cr
from cus_app.supple.helper_functions import is_large_coord_shift


#: Turn on foreign keys anytime there is a connection.
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

OCAT_DATETIME_FORMAT = "%b %d %Y %I:%M%p" #: Warning Ocat Datetimes are stored without a leading zero in the day. This can cause python comparisons to fail
USINT_DATETIME_FORMAT = "%b %d %Y %H:%M"
STORAGE_FORMAT = '%Y-%m-%dT%H:%M:%SZ' #: ISO 8601 format. Used in storage for Usint SQL Database
DATETIME_FORMATS = [USINT_DATETIME_FORMAT, OCAT_DATETIME_FORMAT, STORAGE_FORMAT, '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M','%m:%d:%Y:%H:%M:%S', '%m:%d:%Y:%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M',]
_SIGNOFF_COLUMNS = ('general', 'acis', 'acis_si', 'hrc_si', 'usint') #: Prefix names for the columns of Signoff
UPDATES_DIR = "/data/mta4/CUS/www/Usint/ocat/updates"

ALL_NULL_SET = {'',
' ',
'<Blank>',
'N/A',
'NA',
'NONE',
'NULL',
'Na',
'None',
None,
'Null',
'none',
'null'
}

_OCAT_DATETIME_FORMAT = "%b %d %Y %I:%M%p"
_USINT_DATETIME_FORMAT = "%b %d %Y %H:%M"

_DATETIME_FORMATS = ['%m:%d:%Y:%H:%M:%S', '%m:%d:%Y:%H:%M', _USINT_DATETIME_FORMAT, _OCAT_DATETIME_FORMAT, '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M']

STORAGE_FORMAT = '%Y-%m-%dT%H:%M:%SZ' #: ISO 8601 format

#
# --- parameter selection for time, roll, and window ranks
#
TIME_RANK_PARAMS = {'window_constraint', 'tstart', 'tstop'}
ROLL_RANK_PARAMS = {'roll_constraint', 'roll_180', 'roll', 'roll_tolerance'}
WINDOW_RANK_PARAMS = {'chip', 'start_row', 'start_column', 'width', 'height', 'lower_threshold', 'pha_range', 'sample'}
ALL_RANK_PARAMS = TIME_RANK_PARAMS.union(ROLL_RANK_PARAMS).union(WINDOW_RANK_PARAMS)

engine = create_engine("sqlite:///instance/usint.db", echo=False)
Session = sessionmaker(bind=engine)
session = Session()


all_parameters_by_name ={}
all_parameters_by_id = ['No ID Zero']
for row in session.execute(select(Parameter).order_by(Parameter.id)):
    obj = row[0]
    all_parameters_by_name[obj.name] = obj
    all_parameters_by_id.insert(obj.id, obj)

#: Schedule File Parsing
def pull_schedule_table():
    schedule_file = "/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/schedule"
    def list_to_datetime(section):
        month = section[0]
        day = section[1]
        year = section[2]
        return datetime.strptime(f"{month:>02}/{day:>02}/{year}","%m/%d/%Y")
    with open(schedule_file) as f:
        data = [line.strip().split("\t") for line in f.readlines()]

    rows = []
    count = 0
    for entry in data:
        if entry[0] == 'TBD':
            user = None
        else:
            user = entry[0]
        if len(entry) == 8:
            #: Signed up
            assignee = entry[7]
        elif len(entry) == 7:
            assignee = None
        start = list_to_datetime(entry[1:4])
        stop = list_to_datetime(entry[4:7])
        if start > datetime.now():
            order_id = count
            count += 1
        else:
            order_id = None
        rows.append({'user': user, 'start': start, 'stop': stop, 'order_id': order_id, 'assignee': assignee})
    return Table(rows)

def recreate_schedule_table():
    x = pull_schedule_table()
    Schedule.__table__.drop(engine, checkfirst=True)
    Schedule.__table__.create(engine, checkfirst=True)
    for row in x:
        if row['user'] == None:
            user_id = None
        else:
            #print(row['user'])
            query = select(User.id).where(User.full_name == row['user'])
            user_id = session.execute(query).scalar_one()
            
        if row['assignee'] == None:
            assigner_id = None
        else:
            #print(row['assignee'])
            query = select(User.id).where(User.username == row['assignee'])
            assigner_id = session.execute(query).scalar_one()
            
        entry = Schedule(
            user_id = user_id,
            start = row['start'],
            stop = row['stop'],
            order_id = row['order_id'],
            assigner_id = assigner_id
        )
        session.add(entry)
    session.commit()


#: Pull revisions
def grab_old_signoff():
    """
    identifies signoff state and relevant revision file
    """
    last_rev = session.execute(select(Revision).order_by(desc(Revision.time)).limit(1)).scalar_one()
    last_obsidrev = f"{last_rev.obsid}.{last_rev.revision_number:>03}"
    names= ("obsidrev", 
        "general_signoff",
        "general_date",
        "acis_signoff",
        "acis_date",
        "acis_si_signoff",
        "acis_si_date",
        "hrc_si_signoff",
        "hrc_si_date",
        "usint_verification",
        "usint_date",
        "sequence",
        "submitter",
        "rev_time"
       )
    with closing(sq.connect("/data/mta4/CUS/www/Usint/ocat/updates_table.db")) as conn: #Auto-closes
        with conn: #Auto-commits
            with closing(conn.cursor()) as cur: #Auto-closes
                fetch_result = cur.execute(f"SELECT * FROM revisions where rev_time >= {last_rev.time} and obsidrev!={last_obsidrev}").fetchall()
    return Table(rows=fetch_result,names=names)

def grab_specific_signoff_row(obsidrev):
    """
    Grabs a signoff and revision based on time in case it's missing from the table in the previous creation set
    """
    names= ("obsidrev", 
        "general_signoff",
        "general_date",
        "acis_signoff",
        "acis_date",
        "acis_si_signoff",
        "acis_si_date",
        "hrc_si_signoff",
        "hrc_si_date",
        "usint_verification",
        "usint_date",
        "sequence",
        "submitter",
        "rev_time"
       )
    with closing(sq.connect("/data/mta4/CUS/www/Usint/ocat/updates_table.db")) as conn: #Auto-closes
        with conn: #Auto-commits
            with closing(conn.cursor()) as cur: #Auto-closes
                fetch_result = cur.execute(f"SELECT * FROM revisions where obsidrev={float(obsidrev)}").fetchall()
    return Table(rows=fetch_result,names=names)
    

def read_basic_info(file):
    """
    Read info from file
    """
    rev_info = {}
    with open(file) as f:
        obsline = f.readline()
        seqnum = f.readline()
        target = f.readline()
        submitter = f.readline()
        rev_type = f.readline()
        #: some text files have problem lines when calculating this so
    if "COMMENT" in rev_type.upper() or "NORM" in rev_type.upper():
        #: old format
        rev_info['kind'] = 'norm'

    elif "CLONE" in rev_type.upper():
        rev_info['kind'] = 'clone'

    elif "REMOVE" in rev_type.upper():
        rev_info['kind'] = 'remove'

    elif "AS IS" in rev_type.upper() or "ASIS" in rev_type.upper():
        rev_info['kind'] = 'asis'
    else:
        #: Unidentified type. Skipping automated processing
        return {}
    #rev_info['obsid_rev'] = float(os.path.basename(file)) calculate outside so that we only read files without ~
    rev_info['obsid'] = int(obsline.split("=")[-1].strip())
    rev_info['sequence_number'] = int(seqnum.split("=")[-1].strip())
    #rev_info['target'] = target.split("=")[-1].strip()
    query = select(User.id).where(User.username == submitter.split("=")[-1].strip().lower())
    rev_info['user_id'] = session.execute(query).scalar_one()
    #rev_info['submitter'] = submitter.split("=")[-1].strip().lower()
    rev_info['time'] = min([int(os.path.getmtime(file)), int(os.path.getctime(file))])
    
    rev_info['revision_number'] = int(os.path.basename(file).split('.')[1])
    return rev_info

#: Process current structure
def process_entry(row, key):
    org_signoff = row[f"{key}_signoff"]
    org_time = row[f"{key}_date"]
    
    if org_time in (None, np.ma.masked):
        time = None
    else:
        try:
            time = int(datetime.strptime(org_time, "%m/%d/%y").timestamp())
        except:
            time = None
    
    if org_signoff in (None, np.ma.masked):
        status = "Not Required"
        signoff = None
    elif org_signoff == "N/A":
        status = "Discard"
        signoff = None
    elif org_signoff == "NA":
        status = "Pending"
        signoff = None
    else:
        status = "Signed"
        query = select(User.id).where(User.username == org_signoff)
        signoff = session.execute(query).scalar_one()
    
    return status, signoff, time

def process_usint(row):
    org_signoff = row[f"usint_verification"]
    org_time = row[f"usint_date"]
    
    if org_time in (None, np.ma.masked):
        time = None
    else:
        try:
            time = int(datetime.strptime(org_time, "%m/%d/%y").timestamp())
        except:
            time = None
    
    if org_signoff in (None, np.ma.masked):
        status = "Not Required"
        signoff = None
    elif org_signoff == "N/A":
        status = "Discard"
        signoff = None
    elif org_signoff == "NA":
        status = "Pending"
        signoff = None
    else:
        status = "Signed"
        query = select(User.id).where(User.username == org_signoff)
        signoff = session.execute(query).scalar_one()
    
    return status, signoff, time


#: Coercion section
#
# --- Coercion section. Converting the strings text to the correct data types.
#
def coerce_none(val):
    if val in ALL_NULL_SET:
        return None
    return val

def coerce_number(val):
    if not isinstance(val,(int,float)):
        try:
            val = int(val)
        except ValueError:
            try:
                val = float(val)
            except ValueError:
                pass
    return val

def coerce_time(val):
    if isinstance(val, str):
        x = val.replace('::', ':')
        if x[-1] == "Z":
            x = x[:-1]
        x = x.split('.')[0]
        for format in _DATETIME_FORMATS:
            try:
                return datetime.strptime(x,format)
            except ValueError:
                pass
    return val

def coerce_json(val):
    """Coercion of python data type to a json-formatted string for data storage"""
    if val in ALL_NULL_SET:
        return None
    elif isinstance(val, datetime):
        #: Convert to ISO 8601 string then store
        return json.dumps(val.strftime(STORAGE_FORMAT))
    else:
        return json.dumps(val)

def coerce(val):
    #: Null section
    if val in ALL_NULL_SET:
        return None
    #: Number section
    val = coerce_number(val)
    if isinstance(val,(int,float)):
        return val
    #: Time section.
    val = coerce_time(val)
    if isinstance(val,datetime):
        return val
    #: Regular string
    return val

def coerce_json_column(val):
    """operate very similarly to the coerce_json() function but tailored for columns"""
    #: Ignore None values
    val = [x for x in val if x is not None]
    if val == []:
        return None
    tmp = []
    for i in val:
        if isinstance(i,datetime):
            tmp.append(i.strftime(STORAGE_FORMAT))
        else:
            tmp.append(i)
    return json.dumps(tmp)


def approx_equals(first,second):
    """
    Compare values within reason for a revision. Return True if they are close enough to equal
    """
    if first is None and second is not None:
        return False
    elif first is not None and second is None:
        return False
    elif first is None and second is None:
        return True
    elif isinstance(first, (float,int)) and isinstance(second, (float,int)):
        if abs(first - second) < 0.000001:
            return True
        else:
            return False
    elif isinstance(first,datetime) and isinstance(second,datetime):
        diff = (second - first).total_seconds()
        return abs(diff) < 60
    elif isinstance(first, list) and isinstance(second, list):
        if len(first) != len(second):
            return False
        _result = True
        for i,j in zip(first,second):
            if not approx_equals(i,j):
                _result = False
                break
        return _result
    elif isinstance(first, dict) and isinstance(second, dict):
        first_keys = set(first.keys())
        second_keys = set(second.keys())
        if first_keys != second_keys:
            return False
        _result = True
        for key in first_keys:
            if not approx_equals(first[key], second[key]):
                _result = False
                break
        return _result
    else:
        return first == second

#: File parsing
def find_file(obsid, rev):
    """
    Current record of the revisions table contains separation between the obsid and the revision.
    """
    if isinstance(obsid,str):
        obsid = int(obsid)
    if isinstance(rev,str):
        rev = int(rev)
    result = None
    for i in range(6):
        obsid_rev_str = f"{obsid:0{i}}.{rev:03}"
        file = os.path.join(UPDATES_DIR, obsid_rev_str)
        if os.path.isfile(file):
            result = file
            break
    return result


def is_rank(key):
    if key in ALL_RANK_PARAMS:
        return True
    #: Check based on matching a rank with a followup order
    for rank_param in ALL_RANK_PARAMS:
        match = re.search(fr"{rank_param}\d", key)
        if match is not None:
            return True
    return False

def clean_ordr(key):
    return key[:-1]

def clean_ranks(record_info):
    
    tmp_dict = {}
    all_keys = set(record_info.keys())
    for key in all_keys:
        if is_rank(key):
            tmp_dict[key] = record_info.pop(key)
    column_oriented_ranks = {}
    for param, group in itertools.groupby(sorted(tmp_dict.keys()), clean_ordr):
        tmp_org = []
        tmp_req = []
        for i in group:
            #: Record only useful values inside lists. If there is an order change or brand new ranks, then list the 
            tmp_org.append(tmp_dict.get(i)[0])
            tmp_req.append(tmp_dict.get(i)[1])
        column_oriented_ranks[param] = [tmp_org, tmp_req]
    return record_info, column_oriented_ranks

def clean_record(d_dict):
    record_info = {} #:coerce and clear values
    for parameter, changes in d_dict.items():
        #: if it's non-null, we keep it.
        out = [coerce(x) for x in changes]
        if out !=  [None, None]:
            record_info[parameter.lower()] = out
    #: if's it's a rank parameter, we isolate it.
    record_info, column_oriented_ranks = clean_ranks(record_info)
    return record_info, column_oriented_ranks

def construct_entries(Revision_obj):
    
    obsid = Revision_obj.obsid
    rev = Revision_obj.revision_number
    file = find_file(obsid,rev)
    d_dict, p_list, gc_dict, ac_dict, awc_dict = cr.get_data(file)
    
    record_info, column_oriented_ranks = clean_record(d_dict)
    
    org = []
    req = []
    
    #: TODO: Need to adjust the column oriented ranks so that we only store strings instead of datetimes inside of the lists
    #: Pop out None in the original records? if there is valuable data?
    #: starting to feel like we need to iterate over the None values in ranks differently.
    
    for key, value in record_info.items():
        """Construct the table entry ORM objects"""
        
        #: Record original non-null state information
        if key in all_parameters_by_name.keys():
            if value[0] is not None:
                org.append(Original(
                            revision = Revision_obj,
                            parameter_id = all_parameters_by_name[key].id,
                            value = coerce_json(value[0])
                ))
            if not approx_equals(value[0], value[1]):
                req.append(Request(
                        revision = Revision_obj,
                        parameter_id = all_parameters_by_name[key].id,
                        value = coerce_json(value[1])
            ))
                
                
    for key, value in column_oriented_ranks.items():
        """Construct the table entry ORM objects"""
        #: Record original non-null state information
        #: Additionally checking to ignore null filled columns in org
        if key in all_parameters_by_name.keys():
            tmp_org = coerce_json_column(value[0]) #: json formated version is what's stored, but we run comparisons off python data types
            tmp_req = coerce_json_column(value[1])
            if tmp_org is not None:
                org.append(Original(
                            revision = Revision_obj,
                            parameter_id = all_parameters_by_name[key].id,
                            value = tmp_org
                ))
            if not approx_equals(value[0], value[1]):
                req.append(Request(
                            revision = Revision_obj,
                            parameter_id = all_parameters_by_name[key].id,
                            value = tmp_req
                ))
    
    return org, req


def note_construct(revision):
    """
    Pull revision object data and see if notes need to be marked
    """
    if revision.kind == 'norm':
        #: might have changes we are interested in
        notes = {}
        requests = revision.request
        #: iterate over the set to see if the note's need updating
        pull_org = False
        ra = None
        dec = None
        ora = None
        odec = None
        for req in requests:
            #print(req)
            if req.parameter_id == 1:
                notes.update({'target_name_change':True})
            elif req.parameter_id == 20:
                notes.update({'comment_change': True})
            elif req.parameter_id == 2:
                notes.update({'instrument_change': True})
            elif req.parameter_id == 3:
                notes.update({'grating_change': True})
            elif (req.parameter_id == 21) | (req.parameter_id == 28) | (req.parameter_id == 32) | (req.parameter_id == 83):
                notes.update({'flag_change': True})
            elif (req.parameter_id == 92):
                ra = json.loads(req.value)
                pull_org = True
            elif (req.parameter_id == 93):
                dec = json.loads(req.value)
                pull_org = True
        if pull_org:
            originals = revision.original
            for org in originals:
                if (org.parameter_id == 92):
                    ora = json.loads(org.value)
                elif (org.parameter_id == 93):
                    odec = json.loads(org.value)
            if ra is None:
                ra = ora
            if dec is None:
                dec = odec
            if ora !=0 and odec != 0 and is_large_coord_shift(ra,dec, ora, odec):
                notes.update({'large_coordinate_change': True})
        
        if len(notes) >0:
            return notes
        else:
            return None
        
    else:
        return None


def rev_sign_orms(old_signoff_row):
    rev_info = read_basic_info(f"{UPDATES_DIR}/{old_signoff_row['obsidrev']}")
    new_rev = Revision(obsid=rev_info['obsid'],
                       revision_number = rev_info['revision_number'],
                       kind = rev_info['kind'],
                       sequence_number = rev_info['sequence_number'],
                       time = rev_info['time'],
                       user_id = rev_info['user_id']
    )
    
    org = []
    req = []
    if rev_info['kind'] == 'norm':
        org, req = construct_entries(new_rev)
        setattr(new_rev, 'request', req)
        setattr(new_rev, 'original', org)
        note = note_construct(new_rev)
        setattr(new_rev, 'notes', note)
    
    new_sign = Signoff(revision = new_rev)
    
    for col in ("general", "acis", "acis_si", "hrc_si"):
        status, signoff, time = process_entry(old_signoff_row, col)
        setattr(new_sign, f"{col}_status", status)
        setattr(new_sign, f"{col}_signoff_id", signoff)
        setattr(new_sign, f"{col}_time", time)
    
    status, signoff, time = process_usint(old_signoff_row)
    col = 'usint'
    setattr(new_sign, f"{col}_status", status)
    setattr(new_sign, f"{col}_signoff_id", signoff)
    setattr(new_sign, f"{col}_time", time)
    
    return new_rev, new_sign, org, req

def is_open(row):
    small_set = [row[col] for col in ('general_signoff', 'acis_signoff', 'acis_si_signoff', 'hrc_si_signoff', 'usint_verification')]
    if 'NA' in  small_set:
        return True
    else:
        return False

def add_till_break(old_signoff):
    """
    add to the database until we get to the most recent revision that hasn't been signed-off
    """
    #last_rev = session.execute(select(Revision).order_by(desc(Revision.time)).limit(1)).scalar_one()
    #old_signoff = grab_old_signoff(last_rev.time)
    #old_signoff = grab_old_signoff()
    idx = 0
    while True:
        row = old_signoff[idx]
        if not is_open(row):
            idx += 1
            new_rev, new_sign, org, req = rev_sign_orms(row)
            session.add(new_rev)
            session.add(new_sign)
            for i in org:
                session.add(i)
            for j in req:
                session.add(j)
            session.commit()
        else:
            break
    #print()

if __name__ == "__main__":
    
    #: Recreates the schedule table every time.
    recreate_schedule_table()

    #: Sanity checks for the most recent revisions.
    last_rev = session.execute(select(Revision).order_by(desc(Revision.time)).limit(1)).scalar_one()
    
    old_signoff = grab_old_signoff()

    new_entry_count = len(old_signoff)
    print(f"Datetime: {datetime.now().isoformat()}")
    if new_entry_count > 0:
        print(f"Last revision: {last_rev}")
        print(f"Fetched Signoff. Entries: {new_entry_count}")
        print(old_signoff[0])

        add_till_break(old_signoff)
        print("added all completed signoff entries. ANy remaining are still open.")
    else:
        print("No completed signoff entires to add.")
        