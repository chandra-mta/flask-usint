#!/proj/sot/ska3/flight/bin/python

#################################################################################################
#                                                                                               #
#           updated_fill.py: update updated.html  page                                          #
#                                                                                               #
#               author: t. isobe (tisobe@cfa.harvard.edu)                                       #
#                                                                                               #
#               last update: Sep 18, 2024                                                       #
#                                                                                               #
#################################################################################################

import re
import sys
import os
import time
import numpy
from calendar import month_abbr
import argparse
import sqlite3 as sq
from contextlib import closing
from datetime import datetime

#
#--- Define Directory Pathing
#
CUS_DIR = "/data/mta4/CUS/www/Usint"
OCAT_DIR = "/data/mta4/CUS/www/Usint/ocat"
TEMPLATE_DIR = "/data/mta4/CUS/www/Usint/ocat/house_keeping/Updated/Templates"
CHKUPDATA_LINK = "https://cxc.cfa.harvard.edu/wsgi/cus/usint/chkupdata"

#---------------------------------------------------------------------------------------
#-- update_sub_page: update/create sub html pages                                   ----
#---------------------------------------------------------------------------------------

def update_sub_page(tyear, tmon):
    """
    update/create sub html pages
    input:  none, but read from <ocat_dir>/updates_table.list
    output: <cus_dir>/Save_month_html/<mmm>_<yyyy>.html
    """
#
#--- update/create the last one year of the htmls
#
    lyear = tyear - 1

    for year in [lyear, tyear]:
        for  mon in range(1, 13):
            if (year == lyear) and (mon < tmon):
                continue

            if (year == tyear) and (mon > tmon):
                break
#
#--- Extract status information from updates table.db
#
            [rev_start, rev_stop] = find_rev_time_range(year,mon)
            with closing(sq.connect(f"{OCAT_DIR}/updates_table.db")) as conn: #Auto-closes
#
#--- Update the conneciton row factory for values keyed by column names
#
                conn.row_factory = sq.Row
                with conn: #Auto-commits
                    with closing(conn.cursor()) as cur: #Auto-closes
                        fetch_result = cur.execute(f"SELECT * FROM revisions WHERE rev_time >= {rev_start} AND rev_time <= {rev_stop} ORDER BY rev_time DESC").fetchall()

#
#--- create a html page content
#
            lmon = month_abbr[mon]
            iyear    = str(year)
            hline    = create_sub_html_page(fetch_result, lmon, iyear)
#
#--- print out the  page
#
            with open(f"{CUS_DIR}/Save_month_html/{lmon}_{iyear}.html", 'w') as fo:
                fo.write(hline)


#--------------------------------------------------------------------------------------------------------------------
#-- find_rev_time_range: find the start and stopping rev_time for revisions in created in provided month and year  --
#--------------------------------------------------------------------------------------------------------------------

def find_rev_time_range(year, mon):
    """
    Finds the start and stopping rev_time for revisions in created in provided month and year.
    rev_time is the epoch time number for when the revison was ssubmitted and the revision file was created.
    This number is recorded in the updates_table.db database in the rev_time column.
    input:  year ---- numerical year
            mon --- numerical month
    """
    start = int(datetime(year,mon,1,0,0).timestamp())
    if mon == 12:
        stop = int(datetime(year+1,1,1,0,0).timestamp())
    else:
        stop = int(datetime(year,mon+1,1,0,0).timestamp())
    return [start, stop]

#---------------------------------------------------------------------------------------
#-- create_sub_html_page: create a html page content                                  --
#---------------------------------------------------------------------------------------

def create_sub_html_page(fetch_result, lmon, iyear):
    """
    create a html page content
    input:  data_list   --- a list of data
            lmon        --- month of the data file
            iyear       --- year of the data file
    output: out         --- a html code for the page
    """
#
#--- read templates
#
    with open(f"{TEMPLATE_DIR}/header_part", 'r') as f:
        head_part = f.read()

    head_part = head_part.replace('#LMON#',  lmon)
    head_part = head_part.replace('#IYEAR#', iyear)

    with open(f"{TEMPLATE_DIR}/tail_part", 'r') as f:
        tail_part = f.read()
#
#--- start creating each line
#
    line = ''
    
    for entry in fetch_result:
        if entry['rev_time'] != 0:
            ftime = datetime.fromtimestamp(entry['rev_time']).strftime('%m/%d/%Y')
        else:
            ftime = 'missing'
        
        if entry['usint_verification'] == 'NA':
            continue
#
#--- create each html data line
#
        line += f'<tr>\n<td><a href="{CHKUPDATA_LINK}/{entry["obsidrev"]}">{entry["obsidrev"]}</a>'
        line += f'<br/>{entry["sequence"]}<br/>{ftime}<br/>{entry["submitter"]}</td>\n'

        if entry['general_signoff'] == None:
            if entry['acis_signoff'] == None:
                line += f'<td>NULL</td>'
            elif entry['acis_signoff'] == 'N/A':
                line += f'<td>N/A</td>'
            else:
                line += f'<td>{entry["acis_signoff"]} {entry["acis_date"]}</td>'
        elif entry['general_signoff'] == 'N/A':
            line += f'<td>N/A</td>'
        else:
            line += f'<td>{entry["general_signoff"]} {entry["general_date"]}</td>'

        if entry['acis_si_mode_signoff'] == None:
            line += f'<td>NULL</td>'
        elif entry['acis_si_mode_signoff'] == 'N/A':
            line += f'<td>N/A</td>'
        else:
            line += f'<td>{entry["acis_si_mode_signoff"]} {entry["acis_si_mode_date"]}</td>'
        
        if entry['hrc_si_mode_signoff'] == None:
            line += f'<td>NULL</td>'
        elif entry['hrc_si_mode_signoff'] == 'N/A':
            line += f'<td>N/A</td>'
        else:
            line += f'<td>{entry["hrc_si_mode_signoff"]} {entry["hrc_si_mode_date"]}</td>'
        
        line += f'<td>{entry["usint_verification"]} {entry["usint_date"]}</td>\n</tr>\n'
#
#--- combine header body and tail to crate a page
#
    out = head_part + line + tail_part

    return out
 
#---------------------------------------------------------------------------------------
#-- update_main_page: update main page                                                --
#---------------------------------------------------------------------------------------

def update_main_page():
    """
    update main page
    input:  none
    output: <cus_dir>/updated.html
    """
#
#--- find today's date
#
    out = time.strftime('%Y:%m', time.gmtime())
    atemp = re.split(':', out)
    tyear = int(float(atemp[0]))
    tmon  = int(float(atemp[1]))
#
#--- read templates
#
    with open(f"{TEMPLATE_DIR}/main_page", 'r') as f:
        head_part = f.read()

    with open(f"{TEMPLATE_DIR}/main_tail", 'r') as f:
        tail_part = f.read()
#
#--- start a table part
#
    line = '<tr><th>Year</th>\n'
    for year in range(2005, tyear+1):
        line = line + '<th>' + str(year) + '</th>\n'
    line = line + '</tr>\n'

    yspan  = tyear - 2004
    yspans = yspan - 1

    for mon in range(1, 13):
        lmon = month_abbr[mon]
        line = line + '<tr><th>' + lmon + '</th>\n'

        for i in range(0, yspan):
            year = 2005 + i
            fname = lmon + '_' + str(year) + '.html'
            if i < yspans:
                line = line + '<td><a href="./Save_month_html/'
                line = line + fname + '">' + lmon + '</a></td>\n'
            else:
                if mon > tmon:
                    line = line + '<td>&#160;</td>\n'
                else:
                    line = line + '<td><a href="./Save_month_html/'
                    line = line + fname + '">' + lmon + '</a></td>\n'
        line = line + '</tr>'
#
#--- combine them
#
    line = head_part + line + tail_part
#
#--- print out the page
#
    with open(f"{CUS_DIR}/updated.html", 'w') as fo:
        fo.write(line)

#---------------------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-p", "--path", required = False, help = "Directory path to determine output location of web files.")
    parser.add_argument("--main", action=argparse.BooleanOptionalAction, help = "Select whether ot update the main page or not.")
    parser.add_argument("-y", "--year", type=int, required = False, help = "Select year for report generation. Defaults to current year")
    args = parser.parse_args()

#
#--- Select running of main options if running on the first day of the month
#
    if args.main == None:
        if int(time.strftime('%d', time.gmtime())) == 1:
            RUN_MAIN = True
        else:
            RUN_MAIN= False
    else:
        RUN_MAIN = args.main
#
#--- Select year for report generation
#
    atemp  = re.split(':', time.strftime('%Y:%m', time.gmtime()))
    curr_year = int(atemp[0])
    curr_mon = int(atemp[1])
    if args.year == None or args.year == curr_year:
        tyear = curr_year
        tmon = curr_mon
    elif args.year < curr_year:
        tyear = args.year
        tmon = 12
    else:
        parser.error(f"Invalid Year: {args.year}")

#
#--- Determine if running in test mode and change pathing if so
#
    if args.mode == "test":
#
#--- Define Directory Pathing
#
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        CUS_DIR = f"{SCRIPT_DIR}/test/outTest"
        TEMPLATE_DIR = f"{SCRIPT_DIR}/Templates"
        os.makedirs(f"{CUS_DIR}/Save_month_html", exist_ok = True)

        if RUN_MAIN:
            update_main_page()
        update_sub_page(tyear, tmon)

    elif args.mode == "flight":
#
#--- Create a lock file and exit strategy in case of race conditions
#
        import getpass
        name = os.path.basename(__file__).split(".")[0]
        user = getpass.getuser()
        if os.path.isfile(f"/tmp/{user}/{name}.lock"):
            sys.exit(f"Lock file exists as /tmp/{user}/{name}.lock. Process already running/errored out. Check calling scripts/cronjob/cronlog.")
        else:
            os.system(f"mkdir -p /tmp/{user}; touch /tmp/{user}/{name}.lock")

        if RUN_MAIN:
            update_main_page()
        update_sub_page(tyear, tmon)
#
#--- Remove lock file once process is completed
#
        os.system(f"rm /tmp/{user}/{name}.lock")




