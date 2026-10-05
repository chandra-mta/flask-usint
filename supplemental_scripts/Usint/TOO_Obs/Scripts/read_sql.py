#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#############################################################################################
#                                                                                           #
#       read_sql.py: read data from sql database.                                           #
#                                                                                           #
#               author: t. isobe (tisobe@cfa.harvard.edu)                                   #
#                                                                                           #
#               last update: Jul 23, 2020                                                   #
#                                                                                           #
#############################################################################################

import sys
import os
import string
import re
#
#--- reading directory list
#
path = '/data/mta4/CUS/www/Usint/ocat/Info_save/too_dir_list_py3'

with  open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec("%s = %s" %(var, line))
#
#--- append path to a privte folder
#
sys.path.append(bin_dir)
sys.path.append(cusdir)

import cus_common_functions         as ccf
#
#--- sybase module
#
sys.path.append('/data/mta/Script/Python3.6/Sybase')
import set_sybase_env_and_run       as sser

database = 'axafocat'

#----------------------------------------------------------------------------------------------------
#--- get_target_info: extract a basic target information for a given obsid                        ---
#----------------------------------------------------------------------------------------------------

def get_target_info(obsid):

    """
    extract a basic target information for a given obsid. mintor and group obsids are in list form.
    input:  obsid   --- obsid
    output: target  --- a list of target information:
                            group_id, pre_id, pre_min_lead, pre_max_lead, grating
                            type, instrument, obs_ao_str, status, seq_nbr
                            ocat_propid, soe_st_sched_date, lts_lt_plan,targname, object
            group   --- a list of group obsids
            monitor --- a list of monitor obsids
    """
#
#--- extract target informaton
#
    cmd = 'select group_id,pre_id,pre_min_lead,pre_max_lead,grating,type,instrument,'
    cmd = cmd + 'obs_ao_str,status,seq_nbr,ocat_propid,soe_st_sched_date,lts_lt_plan,'
    cmd = cmd + 'targname,object from target where obsid=' + str(obsid)

    out   = sser.set_sybase_env_and_run(cmd, database)

    group_id          = out[0][0]
    pre_id            = out[0][1]
    pre_min_lead      = out[0][2]
    pre_max_lead      = out[0][3]
    grating           = out[0][4]
    dtype             = out[0][5]
    instrument        = out[0][6]
    obs_ao_str        = out[0][7]
    status            = out[0][8]
    seq_nbr           = out[0][9]
    ocat_propid       = out[0][10]
    soe_st_sched_date = out[0][11]
    lts_lt_plan       = out[0][12]
    targname          = out[0][13]
    dobject           = out[0][14]

    monitor_flag = 'N'
    if pre_id:
        monitor_flag = 'Y'
    
    group   = []
    monitor = []

    cmd = 'select distinct pre_id from target where pre_id=' + str(obsid)
    out = sser.set_sybase_env_and_run(cmd, database)
    try:
    	pre_id_match = out[0][0]
    	if pre_id_match is not None:
        	monitor_flag = 'Y'
    except:
	    pass
#
#--- check group entries
#
    if group_id is not None:
        monitor_flag = 'N'
        pre_min_lead = 'None'
        pre_max_lead = 'None'
        pre_id       = 'None'

        cmd = 'select obsid from target where ocat_propid=' + str(ocat_propid)

        out = sser.set_sybase_env_and_run(cmd, database)
        for ent in out:
            val = ent[0]
            group.append(val)
#
#--- if monitor flag is Y, find which obsids blong to this monitor list
#
    if monitor_flag == 'Y':
        monitor_add  = find_monitor_obs(obsid)

        for ent in monitor_add:
            monitor.append(ent)
#
#--- update ao #
#
    cmd        = 'select ao_str from prop_info where ocat_propid=' + str(ocat_propid)
    out        = sser.set_sybase_env_and_run(cmd, database)
    obs_ao_str = out[0][0]

    target = (group_id, pre_id, pre_min_lead, pre_max_lead, grating, dtype, instrument, obs_ao_str,\
              status, seq_nbr, ocat_propid, soe_st_sched_date, lts_lt_plan,targname, dobject)

    return [target, monitor, group]
            
#----------------------------------------------------------------------------------------------------
#--- find_monitor_obs: find obsid on a monitor list                                               ---
#----------------------------------------------------------------------------------------------------

def find_monitor_obs(obsid):

    """
    for a given obsid, check all other obsid on the same monitor list. return monitor_list.
    input:  obsid   --- obisd
    output: monitor --- a list of monitor obsids
    """
    monitor = [obsid]
    series_rev(obsid, monitor)
    series_fwd(obsid, monitor)

    monitor = sorted(list(set(monitor)))

    return monitor
    
#----------------------------------------------------------------------------------------------------
#---  series_rev: extract a series of pre-id for a given obsid                                    ---
#----------------------------------------------------------------------------------------------------

def series_rev(obsid, monitor):

    """
    for given obsid, database, and monitor list, exract series of pre-id realated to obsid. 
    return monitor_list this one checks obsid in decreasing manner.
    input:  obsid   --- obsid
            monitor --- a list of monitor obsids
    output: monitor --- a list of monitor obsids updated

    """
    cmd =  'select obsid from target where pre_id=' + str(obsid)
    out = sser.set_sybase_env_and_run(cmd, database)

    if len(out) == 0:
        pass
    else:
        for ent in out:
            if len(ent) == 0:
                break
            else:
                obsid = ent[0]
                if str(obsid).isdigit():
                    monitor.append(obsid)
                    series_rev(obsid, monitor)

#----------------------------------------------------------------------------------------------------
#--- series_fwd: extract a series of pre-id for a given obsid. this one look forward.             ---
#----------------------------------------------------------------------------------------------------

def series_fwd(obsid, monitor):

    """
    for given obsid, database, and monitor list, exract series of pre-id realated to obsid. 
    return monitor_list this one checks obsid in increase manner.
    input:  obsid   --- obsid
            monitor --- a list of monitor obsids
    output: monitor --- a list of monitor obsids updated
    
    """
    cmd =  'select pre_id from target where obsid=' + str(obsid)
    out = sser.set_sybase_env_and_run(cmd, database)

    if len(out) == 0:
        pass
    else:
        for ent in out:
            if len(ent) == 0:
                break
            else:
                obsid = ent[0]
                if str(obsid).isdigit():
                    monitor.append(obsid)
                    series_fwd(obsid, monitor)

#---------------------------------------------------------------------------------------------

if __name__ == '__main__':

    if len(sys.argv) > 1:
        obsid = int(float(sys.argv[1].strip()))
    else:
        obsid = 14225

    [target, monitor, group] = get_target_info(obsid)

    for ent in target:
        print(str(ent))

    if len(group) > 0:
        print("group id")
        for ent in group:
            print(ent)

    if len(monitor) > 0:
        print("monitor")
        for ent in monitor:
            print(ent)


