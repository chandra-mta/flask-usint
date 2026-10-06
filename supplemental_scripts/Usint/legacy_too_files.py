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
from legacy_file_lib import FileWriter, StdoutWriter, subproccess_wrapper, grab_now

TOO_CONTACT_DIR = Path("/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info")
USINT_DATA = Path("/data/mta4/CUS/Data")
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
    for _sched in full_sched:
        if _sched['schedule'].get('start') < now < _sched['schedule'].get('stop'):
            curr_sched = _sched
    return full_sched, curr_sched

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
    with open(USINT_DATA / 'too_contact_information.json') as f:
        too_contact_info = json.load(f)

    content = ''
    for id, user_info in too_contact_info.items():
        line = f"{user_info.get('full_name')},"
        line += f"{user_info.get('office_phone') or 'NA'},"
        line += f"{user_info.get('cell_phone') or 'NA'},"
        line += f"{user_info.get('home_phone') or 'NA'},"
        line += f"{user_info.get('email')}\n"
        if not (int(id) == int(curr_sched['schedule'].get('user_id'))):
            line = '#' + line
        content += line
    writer.write("this_week_person_in_charge", content)
        
    

def legacy_too_files(writer):
    """
    Batch function for all TOO legacy files
    """
    full_sched, curr_sched = _fetch_schedule() #: Fetch the full schedule begining 30 days ago
    _make_TOO_POC(writer, curr_sched)
    _make_this_week_person_in_charge(writer, curr_sched)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help = "Determine data output file path. Write stdout for standard out.")
    args = parser.parse_args()
    
    if args.path == "stdout":
        #: Write legacy file content to stdout
        writer = StdoutWriter()
    else:
        #: Write legacy file content to files
        writer = FileWriter(args.path or TOO_CONTACT_DIR)
    legacy_too_files(writer)