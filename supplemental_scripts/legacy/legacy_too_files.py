#!/usr/bin/env python

"""

**legacy_too_files.py:** Automatically generate the legacy TOO files

:Author: W. Aaron (william.aaron@sao.si.edu)
:Last Updated: Sep 30, 2026

"""

import os
from datetime import datetime
import sys
import re
from pathlib import Path
import argparse
import subprocess
import json
import io

TOO_CONTACT_DIR = Path("/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info")
#: To use the CLI tools of a given application installation, these must be determined by the OS environment.
#: Thus, conda environments, shells, or cron tabs can determine which app installation we are using.
_root = os.getenv("USINT_APPLICATION_ROOT")
try:
    USINT_APPLICATION_ROOT = Path(_root)
except TypeError as e:
    e.add_note("Script must be invoked with the USINT_APPLICATION_ROOT environment variable set. Try USINT_APPLICATION_ROOT = /proj/web-cxc/wsgi-scripts/cus.")
    raise e

def _write(outfile, output):
    """Handle outputs types, testing/stdout, file path, or file handler"""
    #: Already opened file handler
    if hasattr(outfile, "write"):
        outfile.write(output)
    elif isinstance(outfile,str):
        #: String file path.
        with open(outfile, "w") as f:
            f.write(output)

def _make_TOO_POC(too_poc_output):
    """
    Write the legacy TOO-POC file.

    Note: Symlink /home/mta/TOO-POC -> /data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/TOO-POC
    """
    result = subprocess.run(
        ["python", f"{USINT_APPLICATION_ROOT}/cli.py", "schedule", "fetch-schedule", "--json-format"],
        capture_output = True,
        text=True,
        check=True
    )
    curr_sched = json.loads(result.stdout)
    email = curr_sched['user'].get('email')
    _write(too_poc_output, f"{email}\n")

def legacy_too_files(too_contact_dir):
    """
    If the input file directory is actually sys.stdout, then this batch function inputs the file path
    """
    if isinstance(too_contact_dir, Path):
        _make_TOO_POC(too_contact_dir / "TOO-POC")
    elif isinstance(too_contact_dir, io.TextIOWrapper):
        _make_TOO_POC(too_contact_dir)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help = "Determine data output file path. Write stdout for standard out.")
    args = parser.parse_args()

    if args.path is None:
        legacy_too_files(TOO_CONTACT_DIR)
    elif args.path == "stdout":
        legacy_too_files(sys.stdout)
    else:
        outpath = Path(args.path)
        legacy_too_files(outpath)