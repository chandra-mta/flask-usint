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
from calendar import month_abbr
from datetime import datetime
from usint_supplemental_lib import FileWriter, StdoutWriter, subprocess_wrapper
from jinja2 import Environment, FileSystemLoader

_JINJA_ENV = Environment(loader=FileSystemLoader("template", followlinks=True))
_JINJA_ENV.globals.update({'enumerate':enumerate, 'zip':zip})

USINT_DIR = Path("/data/mta4/CUS/www/Usint")
ARCHIVE_SUBDIR_NAME = "Save_month_html"
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

def _grab_now():
    return datetime.now()

def _determine_time_range(year, month):
    """
    Given a year and month, find the epoch time range
    """
    start = int(datetime(year,month,1,0,0).timestamp())
    if month == 12:
        stop = int(datetime(year+1,1,1,0,0).timestamp())
    else:
        stop = int(datetime(year,month+1,1,0,0).timestamp())
    return [start, stop]

def top_level_page(writer):
    """
    Write the updated.html page. With monthly subpages from Jan 2005 to current month and year.
    """
    now = _grab_now()
    template = _JINJA_ENV.get_template('revision_archive_main.jinja')
    render = template.render(
        curr_year=now.year,
        curr_month=now.month,
        month_abbr=month_abbr,
        archive_subdir_name=ARCHIVE_SUBDIR_NAME
    )
    writer.write("updated.html", render)

def _fetch_user_info():
    """
    Fetch full user information dictionary.
    """
    user_result = subprocess_wrapper([f"{ENV_CUS}/bin/python", f"{USINT_APPLICATION_ROOT}/cli.py", "user", "fetch-all-users", "--json-format"])
    user_table = json.loads(user_result.stdout)
    user_info = {}
    for user in user_table:
        user_info[int(user.get('id'))] = user
    return user_info

def _epoch_to_date(epoch):
    return datetime.fromtimestamp(epoch).strftime("%m/%d/%Y")

def _format_signoff_column(signoff, column_key, user_info):
    """Format the HTML table column entries based on signoff status."""
    status = signoff.get(f"{column_key}_status")
    if status == 'Discard':
        return "N/A"
    elif status == "Not Required":
        return "NULL"
    elif status == "Signed":
        _id = int(signoff.get(f"{column_key}_signoff_id"))
        _time = int(signoff.get(f"{column_key}_time"))
        username = user_info[_id].get('username')
        date = _epoch_to_date(_time)
        return f"{username} {date}"

def format_revision_history(revision_history, user_info):
    """
    Given a fetched_revision history, format the signoff information into the archive format list used in the html page.
    """
    #: Fetched in ascending time order, but written to the web page in reverse time order.
    obsidrev_list = []
    sequence_list = []
    revision_date_list = []
    revision_user_list = []

    gen_acis_list = []
    acis_si_list = []
    hrc_si_list = []
    usint_list = []
    for entry in reversed(revision_history):
        revision = entry['revision']
        signoff = entry['signoff']
        if signoff['usint_status'] != 'Signed':
            #: If the revision isn't closed yet (usint verified), then ignore archiving this record.
            continue

        obsidrev_list.append(f"{revision.get('obsid')}.{revision.get('revision_number'):>03}")
        sequence_list.append(revision.get('sequence_number'))
        revision_date_list.append(_epoch_to_date(revision.get('time')))
        revision_user_list.append(
            user_info[int(revision.get('user_id'))].get('username')
        )

        _gen = _format_signoff_column(signoff,'general', user_info)
        _acis = _format_signoff_column(signoff,'acis', user_info)
        if _acis == 'NULL':
            if _gen == 'NULL':
                gen_acis_col = "NULL"
            else:
                gen_acis_col = _gen
        else:
            gen_acis_col = _acis
        gen_acis_list.append(gen_acis_col)
        acis_si_list.append(_format_signoff_column(signoff, 'acis_si', user_info))
        hrc_si_list.append(_format_signoff_column(signoff, 'hrc_si', user_info))
        usint_list.append(_format_signoff_column(signoff,"usint", user_info))
    
    return obsidrev_list, sequence_list, revision_date_list, revision_user_list, gen_acis_list, acis_si_list, hrc_si_list, usint_list


def revision_archive(writer, year, month):
    """
    Write a monthly batch summary webpage to USINT_DIR/Save_month_html.
    """
    #: To match user id's with fewer databse transactions, we pull the full listing.
    user_info = _fetch_user_info()

    start, stop = _determine_time_range(year, month)

    revision_result = subprocess_wrapper([f"{ENV_CUS}/bin/python", f"{USINT_APPLICATION_ROOT}/cli.py", "database", "fetch-revision-history", "--start", str(start), "--stop", str(stop), "--json-format"])
    revision_history = json.loads(revision_result.stdout)

    obsidrev_list, sequence_list, revision_date_list, revision_user_list, gen_acis_list, acis_si_list, hrc_si_list, usint_list = format_revision_history(revision_history, user_info)

    template = _JINJA_ENV.get_template('revision_archive_month.jinja')

    render = template.render(
        obsidrev_list=obsidrev_list,
        sequence_list=sequence_list,
        revision_date_list=revision_date_list,
        revision_user_list=revision_user_list,
        gen_acis_list=gen_acis_list,
        acis_si_list=acis_si_list,
        hrc_si_list=hrc_si_list,
        usint_list=usint_list,
        month=month_abbr[month],
        year=year
    )

    writer.write(f"{month_abbr[month]}_{year}.html", render)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help = "Determine data output file path. Write stdout for standard out.")
    parser.add_argument("-y", "--year", type=int, help = "Year of the archive page to generate. Default is current year.")
    parser.add_argument("-m", "--month", type=int, help = "Month of the archive page to generate. Default is current month.")
    args = parser.parse_args()
    
    if args.path == "stdout":
        #: Write legacy file content to stdout
        usint_writer = StdoutWriter()
        archive_writer = StdoutWriter()
    else:
        #: Write legacy file content to files
        usint_writer = FileWriter(args.path or USINT_DIR)
        if args.path is None:
            archive_writer = FileWriter(USINT_DIR / ARCHIVE_SUBDIR_NAME)
        else:
            archive_writer = FileWriter(f"{args.path}/{ARCHIVE_SUBDIR_NAME}")

    if args.year is None and args.month is None:
        now = _grab_now()
        year = now.year
        month = now.month
    else:
        year = args.year
        month = args.month
    
    top_level_page(usint_writer)
    revision_archive(archive_writer, year, month)