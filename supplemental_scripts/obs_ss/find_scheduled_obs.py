#/usr/bin/env python
"""

**find_scheduled_obs.py:** find MP scheduled observations

:Author: W. Aaron (william.aaron@sao.si.edu)
:Last Updated: Sep 15, 2026

"""
import glob
import os
from datetime import datetime
import sys
import re
from pathlib import Path
import argparse

OBS_SS = Path("/data/mta4/obs_ss")
MP_LOGS_DIR = Path("/data/mpcrit1/mplogs")
SCHEDULED_OBS_LIST = OBS_SS / "scheduled_obs_list"

_NOW = datetime.now()

def _match_to_datetime(filepath):
    schedule_string = os.path.basename(filepath)
    _string = schedule_string.lower().capitalize()
    try:
        return datetime.strptime(_string, "%b%d%y")
    except ValueError:
        #: Doesn't match schedule string format. Ignore
        return None

def _find_or_files(mp_logs_dir):
    """
    Find all MP OR lists scheduled to start after today
    """
    _year = _NOW.year
    weekly_directories = glob.glob(f"{mp_logs_dir}/{_year}/*")
    weekly_directories += glob.glob(f"{mp_logs_dir}/{_year+1}/*")
    input_or = []
    scheduled_or = []
    pre_scheduled_or = []

    for week_dir in weekly_directories:
        _datetime = _match_to_datetime(week_dir)
        if _datetime is not None:
            if _datetime > _NOW:
                #: Perform deeper search.
                input_or += glob.glob(f"{week_dir}/input/*.or")
                scheduled_or += glob.glob(f"{week_dir}/scheduled/*.or")
                pre_scheduled_or += glob.glob(f"{week_dir}/pre_scheduled/*.or")
    
    return input_or, scheduled_or, pre_scheduled_or

def find_scheduled_obs(mp_logs_dir, out_file):
    """
    Write out the scheduled observations by the MP logs OR list files and file owners
    """
    input_or, scheduled_or, pre_scheduled_or = _find_or_files(mp_logs_dir)

    
    if hasattr(out_file, "write"):
        out_file.write(output)
    else:
        with open(out_file, "w") as f:
            f.write(output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help = "Determine data output file path. Write stdout for standard out.")
    args = parser.parse_args()

    if args.path is None:
        find_scheduled_obs(MP_LOGS_DIR, SCHEDULED_OBS_LIST)
    elif args.path == "stdout":
        find_scheduled_obs(MP_LOGS_DIR, sys.stdout)
    else:
        out_file = Path(args.path)
        find_scheduled_obs(MP_LOGS_DIR, out_file)