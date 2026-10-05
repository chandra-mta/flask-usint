#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#################################################################################################
#                                                                                               #
#  update_obs_lists.py: read mta archive email, find triggered ddt/too and update related files #
#                                                                                               #
#               author: t. isobe (tisobe@cfa.harvard.edu)                                       #
#                                                                                               #
#               last update: Sep 21, 2021                                                       #
#                                                                                               #
#################################################################################################

import os
import sys
import re
import string
import math
import numpy
import unittest
import time
from datetime import datetime
from time import gmtime, strftime, localtime
import Chandra.Time
#
#--- reading directory list
#
path = '/data/mta4/CUS/www/Usint/ocat/Info_save/too_dir_list_py'
with  open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var   = atemp[1].strip()
    line  = atemp[0].strip()
    exec("%s = %s" %(var, line))
#
#--- append path to a private folder
#
sys.path.append(cusdir)
sys.path.append(bin_dir)
#
import cus_common_functions             as ccf  #---- cus common functions
#
#--- set a temporary file name
#
import random 
rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)

cmon   = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
dmon1  = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334] 
dmon2  = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335] 
solar  = ['mercury', 'venus','earth', 'moon', 'mars','jupiter','saturn', 'uranus', 'neptune', 'pluto']

cus    = 'cus@cfa.harvard.edu'
admin  = 'bwargelin@cfa.harvard.edu'
tech   = 'lina.pulgarin-duque@cfa.harvard.edu'

#----------------------------------------------------------------------------------------------
#-- update_obs_lists: read mta archive email, find triggered ddt/too and update related files 
#----------------------------------------------------------------------------------------------

def update_obs_lists():
    """
    read mta archive email, find triggered ddt/too and update related files
    input: none 
    output: <too_dir>/ddt_list, <too_dir>/too_list, <too_dir>/new_data_list
    """
    today = time.strftime("%Y:%j:00:00:00", time.gmtime())
    t30   = Chandra.Time.DateTime(today).secs  + 86400 * 30
#
#--- create dictionaries etc
#
    spc_dict  = special_poc()               #--- a dictionary: obsid <---> poc
 
    pobs_dict = find_prop_poc()             #--- a dictionary: obsid <---> poc; pre-defined by prop #
 
    [t_poc, poc_emails] = find_current_poc()#--- today's poc id
#
#--- each list in dectionay form
#
    [ddt_dict, too_dict, new_dict] = read_too_ddt_lists()   
#
#--- a dictioinary: obsid <---> [otype, date, seqnum, prpnum, target, status] 
#--- from sot database; include, observed, scheduled, and unobserved
#
    obs_dict = read_sot_ocat()
#
#
#------------ all information gathered, now go through sot data ----------------------------
#
#
    new_data = []
    ddt_data = []
    too_data = []
    obs_30d  = []

    for obsid in obs_dict.keys():
        [otype, date, seqnum, pnum, target, inst, grating, status, ao] = obs_dict[obsid]
        info_set = [obsid, pnum, pobs_dict, spc_dict, t_poc, otype, grating, seqnum, inst, target]
#
#--- check whether poc is already assigned 
#
        try:
            line  = new_dict[obsid]
            atemp = re.split('\s+', line)
            poc   = atemp[4]
            if otype in ['too', 'ddt']:
                try:
                    poc = pobs_dict[obsid]
                except:
                    pass

            if poc.lower() == 'tbd': 
                if otype in ['too', 'ddt']:
                    try:
                        poc = pobs_dict[obsid]
                        if poc.lower() == 'tbd':
                            poc  = check_poc(info_set)
                    except:
                        poc  = check_poc(info_set)

                elif date.lower() != 'na':
                    poc  = check_poc(info_set)
#
#--- if poc is not assigned yet
#
        except:
            if date.lower() != 'na':
                if otype in ['too', 'ddt']:
                    try:
                        poc = pobs_dict[obsid]
                    except:
                        poc  = check_poc(info_set)

                else:
                    poc  = check_poc(info_set)

            else:
                poc  = 'tbd'
#
#--- check ddt/too observations triggered in email
#
        if obsid in dt_obsids:
            if poc.lower() == 'tbd':
                if otype in ['too', 'ddt']:
                    try:
                        poc = pobs_dict[obsid]
                        if poc.lower() == 'tbd':
                            poc  = check_poc(info_set)
                    except:
                        poc  = check_poc(info_set)
#
#--- even if date is not given, if the too/ddt obs is approved by email, put in the list
#
                    if date.lower() == 'na':
                        date = 'tbd'

                else:
                    poc  = check_poc(info_set)
#
#---notify admin/poc about new ddt/too obs is activated in email
#
            send_notice(obsid, poc, date, poc_emails)
#
#--- if poc is not given, don't list
#
        if (poc == 'tbd') and (date.lower() == 'na'):
            continue
#
#--- create the information line
#
        if len(poc) < 4:
            apoc = poc + '\t\t'
        elif len(poc) < 8:
            apoc = poc + '\t'
        else:
            apoc = poc

        line = otype + '\t'  + str(seqnum) + '\t' + str(obsid) + '\t' 
        line = line + status + '\t' + apoc + '\t' + str(ao)    + '\t' + date
#
#--- save data of new_obs_list
#
        if date.lower() == 'na':
            if status in ['too', 'ddt']:
                new_data.append(line)
        else:
            new_data.append(line)
#
#--- save the observations happens in the next 30 days
#
        if status in ['unobserved', 'scheduled']:
            if date.lower() != 'na':
                try:
                    tdate = convert_date_format(date)
                    if tdate <= t30:
                        obs_30d.append(line)
                except:
                    pass
#
#--- save data of ddt_list and too_list
#
        if date.lower() != 'na':

            if otype == 'ddt':
                ddt_data.append(line)

            elif otype == 'too':
                too_data.append(line)
#
#--- find new entry and send out email
#
    check_new_data(new_data, new_dict)
#
#--- update the data
#
    update_file('new_obs_list',  new_data)
    update_file('obs_in_30days', obs_30d)
    update_file('ddt_list',      ddt_data)
    update_file('too_list',      too_data)
#
#--- new_obs_list with title line
#
    cmd = 'cat ' +  too_dir + 'new_list_header ' + too_dir 
    cmd = cmd    + 'new_obs_list >  ' + too_dir + 'new_obs_list.txt'
    os.system(cmd)

#----------------------------------------------------------------------------------------------
#-- check_poc: determine who is poc for the observation                                      --
#----------------------------------------------------------------------------------------------

def check_poc(info_set):
    """
    determine who is poc for the observation
    input:  info_set        --- a list of the following information:
                obsid       --- obsid
                pnum        --- proposal number
                poc_dict    --- a dictionary of proposal id <---> poc
                spc_dict    --- a dictionary of obsid <---> poc for a pre-assigned case
                t_poc       --- a current poc
                otype        --- a otype of observation
                grating     --- grating
                seqnum      --- sequence number
                instrument  --- an instrument
                target      --- the name of the target
    output: poc             --- poc
    """
    [obsid, pnum, poc_dict, spc_dict, t_poc, otype, grating, seqnum, instrument, target] = info_set

    poc = special_obs(target)
    if poc == 'na':
        try:
            poc = spc_dict(obsid)
        except:
            try:
                poc = poc_dict[pnum]
            except:
                if otype in ['ddt', 'too']:
                    poc = t_poc
                else:
                    poc = match_usint_person(otype, grating, seqnum, instrument)

    if (poc.upper() == 'TBD'):
        if otype in ['ddt', 'too']:
            poc = t_poc
        
    return poc

#---------------------------------------------------------------------------------------------
#--  match_usint_person: find usint person who is in charge for the observation            ---
#---------------------------------------------------------------------------------------------

def match_usint_person(otype, grating, seq, instrument):

    """
    find usint person who is in charge for the observation.
    input:  tpye        --- observsation otype
            grating     --- grating (letg/hetg)
            seq         --- sequence #
            instrument  --- instrument
    output: poc         --- poc id
    """
    if otype.lower() == 'cal':
        poc = 'cal'

    elif grating.lower() == 'letg':
        poc = 'letg'

    elif grating.lower() == 'hetg':
        poc = 'hetg'

    elif instrument.lower()  in ['hrc','hrc-i', 'hrc-s']:
        poc = 'hrc'

    elif seq >= 100000 and seq < 300000:
        poc = 'sjw'

    elif seq >= 300000 and seq <400000:
        poc = 'sjw'

    elif seq >= 400000 and seq <500000:
        poc = 'sjw'

    elif seq >= 500000 and seq < 600000:
        poc = 'jeanconn'

    elif seq >= 600000 and seq < 700000:
        poc = 'lpulgarinduque'

    elif seq >= 700000 and seq < 800000:
        poc = 'malgosia'

    elif seq >= 800000 and seq < 900000:
        poc = 'ping'

    elif seq >= 900000 and seq < 1000000:
        poc = 'das'

    return poc

#----------------------------------------------------------------------------------------------
#-- update_file: update the file                                                             --
#----------------------------------------------------------------------------------------------

def update_file(ofile, odata):
    """
    update the file
    input:  ofile   --- the name of the ouptput file
            odata   --- a list of data
    output: <too_dir>/ofile --- udated data file
    """
    cmd = 'rm -f ' + too_dir + ofile + '~'
    os.system(cmd)

    cmd = 'cp ' + too_dir + ofile + ' ' + too_dir + ofile + '~'
    os.system(cmd)

    line = ''
    for ent in odata:
        line = line + ent + '\n'

    out = too_dir + ofile
    with  open(out, 'w') as fo:
        fo.write(line)

#----------------------------------------------------------------------------------------------
#-- replace_poc: replace a poc id from a given data line                                     --
#----------------------------------------------------------------------------------------------

def replace_poc(line, poc):
    """
    replace a poc id from a given data line
    input:  line    --- data line
            poc     --- poc id
    output: line    --- the updated data line
    """
    atemp = re.split('\t+', line)
    line  = atemp[0] + '\t'
    line  = line + atemp[1] + '\t'
    line  = line + atemp[2] + '\t'
    line  = line + atemp[3] + '\t'
    line  = line + poc      + '\t'
    line  = line + atemp[5] + '\t'
    line  = line + atemp[6] 

    return line

#----------------------------------------------------------------------------------------------
#-- create_obsids_on_the_list: create a list of obsids which are already in too_list and ddt_list 
#----------------------------------------------------------------------------------------------

def create_obsids_on_the_list():
    """
    create a list of obsids which are already in too_list and ddt_list
    input: none but read from <too_dir>/too_list and <too_dir>/ddt_list
    output: obs_list    --- a list of obsids
    """
    obs_list = []
    for otype in ('too_list', 'ddt_list'):
        ifile = too_dir + otype
        data  = ccf.read_data_file(ifile)
        for ent in data:
            atemp = re.split('\s+', ent)
            obsid = int(float(atemp[2]))
            obs_list.append(obsid)

    return obs_list

#----------------------------------------------------------------------------------------------
#-- check_time_limit: check whether the even happend in a given time period                  --
#----------------------------------------------------------------------------------------------

def check_time_limit(kdate, lhr = 2):
    """
    check whether the even happend in a given time period
    input:  kdate   --- date in Date: <dd> <Mmm> <yyyy> <time> -0400
                        Example: "Date: Tue, 20 Mar 2018 11:28:47 -0400"
            lhr     --- how many hours back we should include from the current hour
    ouput:  0 or 1  --- 0 if the time is outside of the period. otherwise 1
    """
    if kdate == '':
        return 0

    today = time.strftime("%Y:%j:%H:%M:%S", time.gmtime())
    tcut  = Chandra.Time.DateTime(today).secs  - 3600.0 * lhr 

    atemp = re.split('\s+', kdate)
#
#---    date format: <Mmm> <dd> <yyyy>
#
    date  = atemp[3] + ' ' + atemp[2] + ' ' + atemp[4]
            
    mc    = re.search(':', atemp[5])
    if mc is not None:
        hpart = atemp[5]
    else:
        hpart = '00:00:00'

    stime = convert_date_format(date, hhmmss = hpart)

    if stime < tcut:
        return  0
    else:
        return  1

#----------------------------------------------------------------------------------------------
#-- find_prop_poc: create a dictionary of proposal # <---> poc                               --
#----------------------------------------------------------------------------------------------

def find_prop_poc():
    """
    create a dictionary of proposal # <---> poc
    input:  none, but read from <too_dir>/propno_poc_list
    output: prop_dict   --- a dictionary of proposal # <---> poc
    """

    ifile = too_dir + 'propno_poc_list'

    data  = ccf.read_data_file(ifile)

    prop_dict = {}
    for ent in data:
        atemp = re.split('<>', ent)
        prop_dict[atemp[0]] = atemp[1]

    tfile = too_dir + 'tooddt_prop_obsid_list'

    data  = ccf.read_data_file(tfile)

    pobs_dict = {}
    for ent in data:
        atemp = re.split('<>', ent)
        pnum  = atemp[0]
        obs_list = re.split(':', atemp[1])
        try:
            poc = prop_dict[pnum]
        except:
            poc = 'tbd'

        for obsid in obs_list:
            pobs_dict[int(float(obsid))] = poc

    return pobs_dict

#----------------------------------------------------------------------------------------------
#-- update_prop_poc: update propno_poc_list                                                  --
#----------------------------------------------------------------------------------------------

def update_prop_poc(prop_dict, propnum, poc):
    """
    update propno_poc_list
    input:  prop_dict   --- a dictionary of proposal # <---> poc 
            propnum     --- a proposal # which a new poc is assigned
            poc         --- poc id
    output: updated <too_dir>/propno_poc_list
    """
    prop_dict[propnum] = poc

    pnum_list = prop_dict.keys()

    line = ''
    for pnum in pnum_list:
        line = line + prop_dict[pnum] + '\n'

    out = too_dir + '/propno_poc_list'
    with open(out, 'w') as fo:
        fo.write(line)

#----------------------------------------------------------------------------------------------
#-- read_sot_ocat: read sot database and create obsid <--> basic info dictionary             --
#----------------------------------------------------------------------------------------------

def read_sot_ocat():
    """
    read sot database and create obsid <--> basic info dictionary
    input:  none but read from <obs_ss>/sot_ocat.out
    output: obs_dict    --- a dictionary of obsid <---> [otype, date,seqnum, prpnum, target, status]
    """
#
#--- set time limit to the 90 days ago
#
    today = time.strftime("%Y:%j:00:00:00", time.gmtime())
    tcut  = Chandra.Time.DateTime(today).secs  - 86400 * 90
#
#--- read <obs_ss>/sot_ocat.out; an ascii version of the sot data
#
    ifile = obs_ss + 'sot_ocat.out'
    data  = ccf.read_data_file(ifile)
#
#--- create a dictionary of data for given condition
#
    obs_dict = {}
    for ent in data:
        atemp = re.split('\^', ent)
        
        try:
            status = atemp[16].strip().lower()
            if status.lower() in ['archived', 'canceled', 'discarded', 'untriggered']:
                continue

            otype   = atemp[14].strip().lower()
            obsid   = int(atemp[1].strip())
            seqnum  = int(atemp[3].strip())
            target  = atemp[4].strip()
            grating = atemp[11].strip().lower()
            inst    = atemp[12].strip().lower()
            date    = atemp[13].strip()
            if date == 'NULL':
                date = atemp[15].strip()

            if (date == 'NULL') or (date == ''):
                date = 'NA'

            prpnum  = int(atemp[19].strip())
            ao      = int(atemp[-2].strip())
#
#--- if it is observed and older than 90 days, don't include in the list
#
            if date.lower() != 'na':
                tdate = convert_date_format(date)
                if status == 'observed':
                    if tdate < tcut:
                        continue

            obs_dict[obsid] = [otype, date, seqnum, prpnum, target,  inst, grating, status, ao]

        except:
            continue

    return obs_dict

#----------------------------------------------------------------------------------------------
#-- convert_date_format: convert date format from <Mmm> <dd> <yyyy> to seconds from 1998.1.1 --
#----------------------------------------------------------------------------------------------

def convert_date_format(date, hhmmss=''):
    """
    convert date format from <Mmm> <dd> <yyyy> to seconds from 1998.1.1
    input:  date    --- date in the fromat of <Mmm> <dd> <yyyy>
            hhmmss  --- <hh>:<mm>:<ss>; default: '' which creates 00:00:00
    output: date    --- date in seconds from 1998.1.1
    """
    if date.lower() == 'na':
        return 'na'

    else:
        atemp = re.split('\s+', date)
        for k in range(0, len(cmon)):
            if (cmon[k] == atemp[0]) or (cmon[k] == atemp[1]):
                pos = k
                break
        try:
            day   = int(float(atemp[1]))
        except:
            val   = atemp[0].strip()
            val   = val.replace(',', '')
            day   = int(float(val))

        year = int(float(atemp[2]))
        if ccf.is_leapyear(year):
            yday = dmon2[k] + day
        else:
            yday = dmon1[k] + day

        cday = str(yday)
        if yday < 10:
            cday = '00' + cday
        elif yday < 100:
            cday = '0'  + cday

        if hhmmss == '':
            tdate = str(year) + ':' + cday + ':00:00:00'
        else:
            mc = re.search(':', hhmmss)
            if mc is not None:
                tdate = str(year) + ':' + cday + ':' + hhmmss
            else:
                tdate = str(year) + ':' + cday + ':00:00:00'

        tdate = Chandra.Time.DateTime(tdate).secs

        return tdate

#----------------------------------------------------------------------------------------------
#-- special_poc: find poc who is pre-assigned for a specific obsid and create a dictionary   --
#----------------------------------------------------------------------------------------------

def special_poc():
    """
    find poc who is pre-assigned for a specific obsid and create a dictionary
    input:  none but read from <too_dir>/special_obsid_poc_list
    output: spc_dict   --- a dictionary of obsid <---> poc
    """
    ifile = too_dir + 'special_obsid_poc_list'

    data  = ccf.read_data_file(ifile)

    spc_dict = {}
    for ent in data:
        atemp = re.split('\s+', ent)
        spc_dict[atemp[0]] = atemp[1]

    return spc_dict

#----------------------------------------------------------------------------------------------
#-- find_current_poc: find the current poc                                                   --
#----------------------------------------------------------------------------------------------

def find_current_poc():
    """
    find the current poc 
    input:  none, but read from <too_dir>/this_week_person_in_charge
    output: poc     --- poc id
    """
    ifile = too_dir + 'this_week_person_in_charge'

    data  = ccf.read_data_file(ifile)

    poc_emails = {}
    for ent in data:
        atemp = re.split('\,', ent)
        btemp = re.split('\@', atemp[-1])
        poc_emails[btemp[0]] = atemp[-1]
        if ent[0] == '#':
            continue

        else:
            atemp = re.split(',', ent)
            btemp = re.split('@', atemp[-1])
            poc   = btemp[0].strip()

    if poc == 'pzhao':
        poc = 'ping'
        poc_emails[poc] = poc_emails['pzhao']
    elif poc == 'swolk':
        poc = 'sjw'
        poc_emails[poc] = poc_emails['swolk']
    elif poc == 'jdrake':
        poc = 'jd'
        poc_emails[poc] = poc_emails['jdrake']
    elif poc == 'msobolewska':
        poc = 'malgosia'
        poc_emails[poc] = poc_emails['msobolewska']

    return [poc, poc_emails]

#----------------------------------------------------------------------------------------------
#-- read_too_ddt_lists: read three ddt/too related files and put in the dictionary form       -
#----------------------------------------------------------------------------------------------

def read_too_ddt_lists():
    """
    read three ddt/too related files and put in the dictionary form
    input:  none but read from <too_dir>/<file name>
    output: a list of <ddt_dict>, <too_dict>, <new_dict>
    """
    ifile    = too_dir + 'ddt_list'
    ddt_dict = read_table_file(ifile)

    ifile    = too_dir + 'too_list'
    too_dict = read_table_file(ifile)

    ifile    = too_dir + 'new_obs_list'
    new_dict = read_table_file(ifile)


    return [ddt_dict, too_dict, new_dict]


#----------------------------------------------------------------------------------------------
#-- read_table_file: create a dictionary of obsid <---> the data line                        --
#----------------------------------------------------------------------------------------------

def read_table_file(ifile):
    """
    create a dictionary of obsid <---> the data line
    input:  ifile   --- data file name
    output: t_dict  --- the dictionary of obsid <---> the data lien
        note: we assume that obsid is located at the third element of the data line
    """
    data   = ccf.read_data_file(ifile)

    t_dict = {}
    for ent in data:
        atemp         = re.split('\s+', ent)
        obsid         = int(float(atemp[2]))
        t_dict[obsid] = ent

    return t_dict

#----------------------------------------------------------------------------------------------
#-- special_obs: find poc for the special target                                             --
#----------------------------------------------------------------------------------------------

def special_obs(target):
    """
    find poc for the special target
    input:  target  --- target name
    ouput:  poc     --- poc id
    """
    mc  = re.search('crab',  target.lower())
    mc2 = re.search('comet', target.lower())

    if mc is not None:
        poc = 'ppp'

    elif mc2 is not None:
        poc = 'sjw'

    elif target.lower() in  solar:
        poc = 'sjw'

    elif target.lower() == 'none':
        poc = 'sjw'

    else:
        poc = 'na'

    return poc

#----------------------------------------------------------------------------------------------
#-- check_new_data: check whether new observations are added to the list and send email to admin
#----------------------------------------------------------------------------------------------

def check_new_data(new_data, new_dict):
    """
    check whether new observations are added to the list and send email to admin
    input:  new_data    --- a list of updated new_obs_list
            new_dict    --- a dictionary of the previous new_obs_list info
    output: email sent to adim
    """
    save = []
    for ent in new_data:
        atemp = re.split('\s+', ent)
        obsid = int(float(atemp[2]))
        try:
            test = new_dict[obsid]
        except:
            save.append(ent)

    if len(save) > 0:
        line = ''
        for ent in save:
            line = line + ent + '\n'

        with  open(zspace, 'w') as fo:
            fo.write(line)
        
        #cmd = 'cat ' + zspace + '| mailx -s "Subject: New Observation(s)" -b ' + tech + ' ' 
        #cmd = cmd + ' -c ' + cus + ' ' + admin
        #os.system(cmd)

        ccf.rm_files(zspace)

#----------------------------------------------------------------------------------------------
#-- send_notice: sending out  email notifying that DDT/TOO observation is activated          --
#----------------------------------------------------------------------------------------------

def send_notice(obsid, poc, date, poc_emails):
    """
    sending out  email notifying that DDT/TOO observation is activated
    input:  obsid       --- obsid
            poc         --- poc
            date        --- planned observation date
            poc_emails  --- a dictionary of poc <---> email address
    output: email sent out
    """
    line = 'An email is sent out to notify the following DDT/TOO obsid is activated:\n\n'
    line = line + 'Obsid: ' + str(obsid) + '\tPOC: ' + str(poc) + '\tPlanned Date: ' + date + '\n'

    with  open(zspace, 'w') as fo:
        fo.write(line)

#    if poc != 'tbd':
#        try:
#            pemail = poc_emails[poc]    
#        except:
#            pemail = ''
#        cmd = 'cat ' + zspace + '| mailx -s "Subject: New TOO/DDT"  -b ' + tech 
#        cmd = cmd + ' -c ' + cus + ' '  + admin + ' ' + pemail
#    else:
#        cmd = 'cat ' + zspace + '| mailx -s "Subject: New TOO/DDT"  -b ' + tech + ' ' 
#        cmd = cmd + ' -c ' + cus + ' '  + admin
#    os.system(cmd)

    ccf.rm_files(zspace)

#----------------------------------------------------------------------------------------------

if __name__ == '__main__':

    update_obs_lists()
