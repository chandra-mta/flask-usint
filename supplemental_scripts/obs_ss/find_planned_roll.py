#!/usr/bin/env python
"""
**find_planned_roll.py:** extract obsid and planned roll angle from MP site

:Author: W. Aaron (william.aaron@sao.si.edu)
:Last Updated: Sep 15, 2026

"""
import sys
import re
from pathlib import Path
import argparse

OBS_SS = Path("/data/mta4/obs_ss")
LONG_TERM_SCHEDULE_FILE = Path("/proj/web-icxc/htdocs/mp/lts/lts-current.html")
MP_LONG_TERM = OBS_SS / "mp_long_term"

def parse_schedule_file(data):
    """
    The HTML files does not contain an actual table to display the schedule information, opting instead to use the <pre> tag.
    Thus, we parse by regex searching.
    """
    line = ''
    for ent in data:
        mc = re.search('LTS changes', ent)
        if mc is not None:
            break

        mc = re.search(r'target_param\.cgi', ent)
        if mc is not None:
        #: find obsid
            atemp = re.split(r'target_param\.cgi\?', ent)
            btemp = re.split('\"', atemp[1])
            obsid = int(float(btemp[0]))
        #: find planned role
            atemp = re.split(r'\s+', ent)
            acnt  = 0
            for val in atemp:
                mc1 = re.search('ACIS', val)
                mc2 = re.search('HRC',  val)
                if (mc1 is not None) or (mc2 is not None):
                    break
                else:
                    acnt += 1

            if acnt > 0:
                pl_roll   = atemp[acnt-4]
                pl_range  = atemp[acnt-3]

                line += f"{obsid}:{pl_roll}:{pl_range}\n"
    return line

def read_schedule_file(html_file_path):
    with open(html_file_path, encoding='latin-1') as f:
        data = [line.strip() for line in f.readlines()]
    return data

def find_planned_roll(html_file_path, out_file):

    data = read_schedule_file(html_file_path)
    results = parse_schedule_file(data)

    if hasattr(out_file, "write"):
        out_file.write("\n".join(results))
        out_file.write("\n")
    else:
        with open(out_file, "w") as out:
            out.write("\n".join(results))
            out.write("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help = "Determine data output file path. Write stdout for standard out.")
    args = parser.parse_args()

    if args.path is None:
        find_planned_roll(LONG_TERM_SCHEDULE_FILE, MP_LONG_TERM)
    elif args.path == "stdout":
        find_planned_roll(LONG_TERM_SCHEDULE_FILE, sys.stdout)
    else:
        out_file = Path(args.path)
        find_planned_roll(LONG_TERM_SCHEDULE_FILE, out_file)