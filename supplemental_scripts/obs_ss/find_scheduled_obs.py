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

def find_scheduled_obs(mp_logs_dir, out_file):
    pass

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