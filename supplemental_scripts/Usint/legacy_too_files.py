#!/usr/bin/env python

"""

**legacy_too_files.py:** Automatically generate the legacy TOO files

:Author: W. Aaron (william.aaron@sao.si.edu)
:Last Updated: Sep 30, 2026

"""

import os
from pathlib import Path
import argparse
import subprocess
import json
from legacy_file_lib import FileWriter, StdoutWriter, subproccess_wrapper

TOO_CONTACT_DIR = Path("/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info")
#: To use the CLI tools of a given application installation, these must be determined by the OS environment.
#: Thus, conda environments, shells, or cron tabs can determine which app installation we are using.
_root = os.getenv("USINT_APPLICATION_ROOT")
_env = os.getenv("ENV_CUS")

try:
    USINT_APPLICATION_ROOT = Path(_root)
except TypeError as e:
    e.add_note("Script must be invoked with the USINT_APPLICATION_ROOT environment variable set. Try USINT_APPLICATION_ROOT = /proj/web-cxc/wsgi-scripts/cus.")
    raise e

try:
    ENV_CUS = Path(_env)
except TypeError as e:
    e.add_note("Script must be invoked with the ENV_CUS environment variable set. Try ENV_CUS = /proj/sot/mta/envs/python_web_apps.")
    raise e

def _make_TOO_POC(writer):
    """
    Write the legacy TOO-POC file.

    Note: Symlink /home/mta/TOO-POC -> /data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/TOO-POC
    """
    result = subproccess_wrapper([f"{ENV_CUS}/bin/python", f"{USINT_APPLICATION_ROOT}/cli.py", "schedule", "fetch-schedule", "--json-format"])
    curr_sched = json.loads(result.stdout)
    email = curr_sched['user'].get('email')
    writer.write('TOO-POC', f"{email}\n")

def legacy_too_files(writer):
    """
    Batch function for all TOO legacy files
    """
    _make_TOO_POC(writer)

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