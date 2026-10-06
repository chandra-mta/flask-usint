#!/usr/bin/env python

"""

**legacy_too_files.py:** Automatically generate the legacy TOO files

:Author: W. Aaron (william.aaron@sao.si.edu)
:Last Updated: Sep 30, 2026

"""

import os
from pathlib import Path
import argparse
import json
from datetime import datetime
from legacy_file_lib import FileWriter, StdoutWriter, subproccess_wrapper, grab_now
from jinja2 import Environment, FileSystemLoader

_JINJA_ENV = Environment(loader=FileSystemLoader("template", followlinks=True))
_JINJA_ENV.globals.update({'enumerate':enumerate, 'zip':zip})

TOO_CONTACT_DIR = Path("/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info")
USINT_DIR = Path("/data/mta4/CUS/www/Usint")
with open(TOO_CONTACT_DIR / 'too_contact_information.json') as f:
    TOO_CONTACT_INFO = json.load(f)
#: To use the CLI tools of a given application installation, these must be determined by the OS environment.
#: Thus, conda environments, shells, or cron tabs can determine which app installation we are using.
_root = os.getenv("USINT_APPLICATION_ROOT")
_env = os.getenv("ENV_CUS")

try:
    USINT_APPLICATION_ROOT = Path(_root)
except TypeError as e:
    e.add_note("Script must be invoked with the USINT_APPLICATION_ROOT environment variable set. Try USINT_APPLICATION_ROOT=/proj/web-cxc/wsgi-scripts/cus.")
    raise e

try:
    ENV_CUS = Path(_env)
except TypeError as e:
    e.add_note("Script must be invoked with the ENV_CUS environment variable set. Try ENV_CUS=/proj/sot/mta/envs/python_web_apps.")
    raise e

def _fetch_schedule():
    result = subproccess_wrapper([f"{ENV_CUS}/bin/python", f"{USINT_APPLICATION_ROOT}/cli.py", "schedule", "fetch-schedule", "--begin", "30", "--json-format"])
    full_sched = json.loads(result.stdout)
    now = grab_now().isoformat()
    curr_sched = None
    idx = None
    for i, entry in enumerate(full_sched):
        if entry['schedule'].get('start') < now < entry['schedule'].get('stop'):
            curr_sched = entry
            idx = i
    return full_sched, curr_sched, idx

def _make_TOO_POC(writer, curr_sched):
    """
    Write the legacy TOO-POC file.

    Note: Symlink /home/mta/TOO-POC -> /data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/TOO-POC
    """
    email = curr_sched['user'].get('email')
    writer.write('TOO-POC', f"{email}\n")

def _make_this_week_person_in_charge(writer, curr_sched):
    """
    Write the legacy this_week_person_in_charge file.

    Format is to have all other personnel commented out from the file except for this week's person in charge.
    """

    content = ''
    for id, user_info in TOO_CONTACT_INFO.items():
        line = f"{user_info.get('full_name')},"
        line += f"{user_info.get('office_phone') or 'NA'},"
        line += f"{user_info.get('cell_phone') or 'NA'},"
        line += f"{user_info.get('home_phone') or 'NA'},"
        line += f"{user_info.get('email')}\n"
        if int(id) != int(curr_sched['schedule'].get('user_id')):
            line = '#' + line
        content += line
    writer.write("this_week_person_in_charge", content)

def _format_period(sched):
    start = datetime.fromisoformat(sched['start'])
    stop = datetime.fromisoformat(sched['stop'])
    return f"{start.strftime("%B")} {start.day} - {stop.strftime("%B")} {stop.day}"

def _make_schedule_html(writer, full_sched, idx):

    period_list=[]
    full_name_list=[]
    office_phone_list=[]
    cell_phone_list=[]
    home_phone_list=[]
    email_list=[]
    for entry in full_sched:
        #: Iterate over schedule entires and paired user.
        user = entry['user'] #: user information or None
        sched = entry['schedule']

        if user is None:
            full_name = 'TBD'
            office_phone = '---'
            cell_phone = '---'
            home_phone = '---'
            email = '---'
        else:
            full_name = user.get('full_name')
            info = TOO_CONTACT_INFO.get(str(user.get('id')))
            office_phone = info.get('office_phone') or 'NA'
            cell_phone = info.get('cell_phone') or 'NA'
            home_phone = info.get('home_phone') or 'NA'
            email = info.get('email') or 'NA'

        period_list.append(_format_period(sched))
        full_name_list.append(full_name)
        office_phone_list.append(office_phone)
        cell_phone_list.append(cell_phone)
        home_phone_list.append(home_phone)
        email_list.append(email)
    
    template = _JINJA_ENV.get_template("too_contact_schedule.html")
    render = template.render(
        period_list=period_list,
        full_name_list=full_name_list,
        office_phone_list=office_phone_list,
        cell_phone_list=cell_phone_list,
        home_phone_list=home_phone_list,
        email_list=email_list,
        idx=idx,
        now = grab_now().strftime('%m/%d/%Y')
    )
    writer.write("too_contact_schedule.html", render)


def legacy_too_files(too_writer, usint_writer):
    """
    Batch function for all TOO legacy files
    """
    full_sched, curr_sched, idx = _fetch_schedule() #: Fetch the full schedule begining 30 days ago
    _make_TOO_POC(too_writer, curr_sched)
    _make_this_week_person_in_charge(too_writer, curr_sched)
    _make_schedule_html(usint_writer, full_sched, idx)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help = "Determine data output file path. Write stdout for standard out.")
    args = parser.parse_args()
    
    if args.path == "stdout":
        #: Write legacy file content to stdout
        too_writer = StdoutWriter()
        usint_writer = StdoutWriter()
        
    else:
        #: Write legacy file content to files
        too_writer = FileWriter(args.path or TOO_CONTACT_DIR)
        usint_writer = FileWriter(args.path or USINT_DIR)
    legacy_too_files(too_writer, usint_writer)