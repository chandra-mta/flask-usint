#!/usr/bin/env python

"""

**revision_archive.py:** Generate archive pages of usint revisions (updated.html)

:Author: W. Aaron (william.aaron@sao.si.edu)
:Last Updated: Oct 13, 2026

"""

import os
from pathlib import Path
import argparse
import json
from datetime import datetime
from usint_supplemental_lib import FileWriter, StdoutWriter, subproccess_wrapper
from jinja2 import Environment, FileSystemLoader

_JINJA_ENV = Environment(loader=FileSystemLoader("template", followlinks=True))
_JINJA_ENV.globals.update({'enumerate':enumerate, 'zip':zip})

USINT_DIR = Path("/data/mta4/CUS/www/Usint")
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

def revision_archive(writer):
    """
    Write the update.html page to USINT_DIR and the monthly batch summary webpages to USINT_DIR/Save_month_html
    """
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help = "Determine data output file path. Write stdout for standard out.")
    args = parser.parse_args()
    
    if args.path == "stdout":
        #: Write legacy file content to stdout
        writer = StdoutWriter()
    else:
        #: Write legacy file content to files
        writer = FileWriter(args.path or USINT_DIR)
    
    revision_archive(writer)