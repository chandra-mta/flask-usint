#!/usr/bin/env python

"""

**legacy_usint_files.py:** Automatically generate the legacy USINT files

:Author: W. Aaron (william.aaron@sao.si.edu)
:Last Updated: Sep 30, 2026

"""

import os
from pathlib import Path
import argparse
import subprocess
import json
from datetime import datetime
from legacy_file_writers import FileWriter, StdoutWriter

OCAT_DIR = Path("/data/mta4/CUS/www/Usint/ocat")
#: To use the CLI tools of a given application installation, these must be determined by the OS environment.
#: Thus, conda environments, shells, or cron tabs can determine which app installation we are using.
_root = os.getenv("USINT_APPLICATION_ROOT")
try:
    USINT_APPLICATION_ROOT = Path(_root)
except TypeError as e:
    e.add_note("Script must be invoked with the USINT_APPLICATION_ROOT environment variable set. Try USINT_APPLICATION_ROOT = /proj/web-cxc/wsgi-scripts/cus.")
    raise e

def _make_approved(writer):
    """
    Write the legacy approved file

    Note: Symlink /data/mta4/CUS/www/Usint/APPROVED -> /data/mta4/CUS/www/Usint/ocat/approved

    fetch by Revision ORM. need columns obsid, sequence_number, user, time(in mm/dd/yy format)

    fetching by time frame / other query args but time frame first.
    """
    result = subprocess.run(
        ["python", f"{USINT_APPLICATION_ROOT}/cli.py", "database", "fetch-approved-obsid", "--json-format"],
        capture_output = True,
        text=True,
        check=True
    )
    formatted_approvals = json.loads(result.stdout)
    
    content = ''
    for obsid, data in formatted_approvals.items():
        seq = data.get('revision').get('sequence_number')
        user = data.get('user').get('username')
        time_epoch = data.get('revision').get('time')
        time = datetime.fromtimestamp(time_epoch).strftime("%m/%d/%y")
        content += f"{obsid}\t{seq}\t{user}\t{time}\n"
    
    writer.write('approved.list', content)

def _make_updates_list(writer):
    result = subprocess.run(
        ["python", f"{USINT_APPLICATION_ROOT}/cli.py", "signoffs", "fetch-all-signoffs", "--list-format"],
        capture_output = True,
        text=True,
        check=True
    )
    content = result.stdout
    writer.write('updates_table.list', content)

def legacy_usint_files(writer):
    """
    Batch function for all USINT legacy files
    """
    #_make_approved(writer)
    _make_updates_list(writer)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help = "Determine data output file path. Write stdout for standard out.")
    args = parser.parse_args()
    
    if args.path == "stdout":
        #: Write legacy file content to stdout
        writer = StdoutWriter()
    else:
        #: Write legacy file content to files
        writer = FileWriter(args.path or OCAT_DIR)
    
    legacy_usint_files(writer)