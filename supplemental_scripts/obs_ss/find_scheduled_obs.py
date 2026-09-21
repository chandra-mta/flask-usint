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
def _is_numeric(chk):
    try:
        float(chk)
        return True
    except ValueError:
        return False

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

def find_obsids(ifile, o_dict, m_list, mp_person):
    """
    find obsids and their related information
    input:  ifile       --- a file name
            o_dict      --- a dictionary to keep the information about the obsids
            m_list      --- a list of obsids
            mp_person   --- mp person responsible for the data period
    output: o_dict      --- updated data dictionary
            m_list      --- updated list of obsids
    """
    with open(ifile, encoding='latin-1') as f:
        data = [line.strip() for line in f.readlines()]

    cstep  = 0                  #--- indicator to show which area of the file
    ochk   = 0                  #--- how many times passed "OBS," marker
    ichk   = 0                  #--- how many times passed "ID" marker
    for ent in data:
#
#--- after 'SeqNbr' marker, there is a summary table
#
        if cstep == 0:
            mc1 = re.search('SeqNbr', ent)
#
#--- the summary table finishes with the following marker
#
        if cstep == 1:
            mc2 = re.search('OR QUICK LOOK END', ent)

        if cstep == 2:
            mc3 = re.search(r'OBS\,', ent)
            mc4 = re.search('ID',    ent)
            mc5 = re.search('CAL',   ent)
            mc6 = re.search('HETG',  ent)
            mc7 = re.search('LETG',  ent)
            mc8 = re.search('ACIS',  ent)
            mc9 = re.search('HRC',   ent)

        if cstep == 0 and mc1 is not None:
            cstep = 1
#
#--- here we are reading the summary table
#
        elif cstep == 1:
            atemp = re.split(r'\s+', ent)
            if _is_numeric(atemp[0]):
                try:
                    pid = int(float(atemp[1]))
                except:
                    continue
                m_list.append(pid)
#
#--- name of the target is column somewhere between 18 and 40
#
                name = ent[18:40]
                name.strip()
                o_dict[pid] = [atemp[0], name, 'None', 'CAL', mp_person]

            if mc1 is not None:
                cstep = 1
#
#--- now read more information about the obsidi
#
        elif cstep == 2:
            if mc3 is not None:
                ochk += 1
            if mc4 is not None:
                ent.strip()
#
#--- find which obsid information are presented next
#
                atemp = re.split(r'\,', ent)
                btemp = re.split('ID=', atemp[0]) 
                pid   = int(float(btemp[1]))

                ichk += 1
#
#--- only when ochk and ichk are equal, collect needed info
#
            if ochk == ichk:
                if mc5 is not None:
                    o_dict = update_dict(o_dict, pid, 1, 'CAL')
                if mc6 is not None:
                    o_dict = update_dict(o_dict, pid, 2, 'HETG')
                if mc7 is not None:
                    o_dict = update_dict(o_dict, pid, 2, 'LETG')
                if mc8 is not None:
                    o_dict = update_dict(o_dict, pid, 3, 'ACIS')
                if mc9 is not None:
                    o_dict = update_dict(o_dict, pid, 3, 'HRC')
        
    return [o_dict, m_list]

#--------------------------------------------------------------------------------------
#-- update_dict: update a dictionary element                                         --
#--------------------------------------------------------------------------------------

def update_dict(o_dict, pid,  pos, val):
    """
    update a dictionary element
    input:  o_dict  --- a dictionary
            pid     --- key
            pos     --- position of data update
            val     --- value to be updated
    output: o_dict  --- updated dictionary
    """
    alist       = o_dict[pid]
    alist[pos]  = val
    o_dict[pid] = alist

    return o_dict

def find_scheduled_obs(mp_logs_dir, out_file):
    """
    Write out the scheduled observations by the MP logs OR list files and file owners
    """
    input_or, scheduled_or, pre_scheduled_or = _find_or_files(mp_logs_dir)

    #: get all observations under schedules
    m_list = []                 #--- a list of obsids
    o_dict = {}                 #--- a dictionary to keep info related obsids

    for file in input_or + scheduled_or + pre_scheduled_or:
        mp_person = Path(file).owner()
        [o_dict, m_list] = find_obsids(file, o_dict, m_list, mp_person)
    
    #: remove duplicates
    m_list = sorted(list(set(m_list)))
    output = ''
    for obsid in m_list:
        output += f"{obsid}\t{o_dict[obsid][-1]}\n"

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