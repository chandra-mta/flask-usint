#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#############################################################################################
#                                                                                           #
#       update_tooddt_prop_list.py: update tooddt_prop_obsid_list/propno_poc_list           #
#                                                                                           #
#       author: t. isobe (tisobe@cfa.harvard.edu)                                           #
#                                                                                           #
#       last update: Jul 30, 2020                                                           #
#                                                                                           #
#############################################################################################

import sys
import os
import string
import re
import getpass
#
#--- reading directory list
#
path = '/data/mta4/CUS/www/Usint/ocat/Info_save/too_dir_list_py3'

with open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec("%s = %s" %(var, line))
#
#--- append path to a private folder
#
sys.path.append(cusdir)
sys.path.append(too_bin_dir)

import cus_common_functions     as ccf
import read_sql                 as tdsql
#
#--- check whose account, and set a path to temp location
#
user = getpass.getuser()
user = user.strip()

if user == 'mta':
    temp_dir = mtemp_dir
elif user == 'cus':
    temp_dir = ctemp_dir
elif user == 'html':
    temp_dir = htemp_dir
else:
    temp_dir = './'
#
#--- set a few directory/file paths
#
uspp_dir        = "/proj/web-icxc/htdocs/uspp/TOO/"
outdir          = too_dir + 'tooddt_prop_obsid_list'
tooddt_poc_list = too_dir + 'propno_poc_list'

#---------------------------------------------------------------------------------------------
#-- update_tooddt_prop_list: update tooddt_prop_obsid_list and propno_poc_list              --
#---------------------------------------------------------------------------------------------

def update_tooddt_prop_list():
    """
    update tooddt_prop_obsid_list and propno_poc_list
    input:  none    
    output: tooddt_prop_obsid_list  --- proposal id <---> a list of obsids
            propno_poc_list         --- proposal id <---> poc correpsondace table
    """
#
#--- create a dict of prop no <---> poc
#
    propid_poc_dict = find_poc()
#
#--- update too part
#
    prop_list1 = make_too_obs_list()
#
#--- update ddt part
#
    prop_list2 = make_ddt_obs_list()
#
#--- combine them
#
    prop_list  = prop_list1 + prop_list2
#
#--- read the current prop no <---> poc list
#
    data = ccf.read_data_file(tooddt_poc_list)
#
#--- update propid_poc_dict base on the current list
#
    poc_dict = {}
    for ent in data:
        atemp = re.split('<>', ent)
        poc = atemp[1]
        if poc == 'TBD':
            if atemp[0] in propid_poc_dict:
                poc = propid_poc_dict[atemp[0]]
            else:
                pass
            
        poc_dict[atemp[0]] = poc
#
#--- backup the current list
#
    cmd  = 'mv ' + tooddt_poc_list + ' ' + tooddt_poc_list + '~'
    os.system(cmd)
#
#--- update the list
#
    line = ''
    for ent in prop_list:
        if ent in poc_dict:
            poc = poc_dict[ent]
            line = line + ent + '<>' + poc + '\n'
        else:   
            line = line + ent + '<>TBD\n'


    with open(tooddt_poc_list, 'w') as fo:
        fo.write(line)
    
#---------------------------------------------------------------------------------------------
#-- make_too_obs_list: create a table of too obsids for corresponding proporsal numbers     --
#---------------------------------------------------------------------------------------------

def make_too_obs_list():
    """
    create a table of too obsids for corresponding proporsal numbers
    input:  none 
    output: <too_dir> + too_prop_obsid_list
            prop_list   --- a list of proposal numbers
    """
#
#--- create a dict of obsid <---> status
#
    obsid_status     = find_obsid_status()
#
#--- go through the proposal cycle between 13 and the current of too lists
#--- and extract proposal id of all too observations
#
    return_prop_list = []
    line             = ''
    for cycle in range(13, 100):
        ifile = uspp_dir + "cycle" + str(cycle) + "_toos.html"
        if os.path.isfile(ifile):
            [prop_list, prop_dict] = find_too_observations(ifile)
        else:
            break

        for prop_num in prop_list:
            obsid_list = []
            for obsid in prop_dict[prop_num]:
#
#--- check status and don't include archived or canceled observations
#
                if obsid in obsid_status:
                    status = obsid_status[obsid]
                else:   
                    status = ''

                if (status == 'archived') or (status == 'canceled'):
                    continue
                else:
                    obsid_list.append(obsid)

            if len(obsid_list) > 0:
                return_prop_list.append(prop_num)
#
#--- output format is <prop_id><><obsid>:<obsid>:..
#
                line = line + prop_num + '<>' + obsid_list[0]
                for k in range(1, len(obsid_list)):
                    line = line + ':' + obsid_list[k]
                line = line + '\n'

            else:
                continue

    with open(outdir, 'w') as fo:
        fo.write(line)

    return return_prop_list

#---------------------------------------------------------------------------------------------
#-- find_too_observations: create lists of too obsids for a corresponding proproal numbers ---
#---------------------------------------------------------------------------------------------

def find_too_observations(ifile):
    """
    create lists of too obsids for a corresponding proproal numbers
    input:  file        --- a file name
    output: prop_list   --- a list of proposal numbers
            prot_dict   --- a dictionay of a list of obsids for a given proposal number
    """
#
#--- open too lists for a given proposal cycle
#
    data = ccf.read_data_file(ifile)

    prop_list = []
    prop_dict = {}
    chk1      = 0
    chk2      = 0
    for ent in data:
#
#--- collect all proposal number from the top part of the page
#
        if chk1 == 0:
            mc1 = re.search('<a href="#',  ent)
            if mc1 is not None:
                atemp   = re.split('<a href="#', ent)
                btemp   = re.split('"', atemp[1])
                prop_no = btemp[0]
                prop_list.append(prop_no)
                continue
#
#--- each proposal detail description finishes "End of..."; so look for a new proposal
# 
        mc2 = re.search('End of proposal number', ent)
        if mc2 is not None:
            chk2 = 0
            continue
#
#--- a new proposal detail starts
#
        mc3 = re.search('PROPOSAL NO.' , ent)
        if (mc3 is not None) and (chk2 == 0):
            if chk1 == 0:
                for pname in prop_list:
                    prop_dict[pname] = []
                chk1 = 1
                continue

            atemp   = re.split('PROPOSAL NO.</b>', ent)
            prop_no = atemp[1].strip()
            chk2    = 1
            continue
#
#--- find obsid 
#
        mc4 = re.search('OBSID:',  ent)
        mc5 = re.search('TARGET:', ent)
        if (mc4 is not None) and (mc5 is not None):
            atemp = re.split('OBSID:</b>', ent)
            btemp = re.split('<b>', atemp[1])
            obsid = btemp[0].strip()
#
#--- put in the dictionary
#
            plist = prop_dict[prop_no]
            plist.append(obsid)
            prop_dict[prop_no] = plist
        

    return [prop_list, prop_dict]


#---------------------------------------------------------------------------------------------
#-- find_obsid_status: create a dictionary of obsid <---> status                           ---
#---------------------------------------------------------------------------------------------

def find_obsid_status():
    """
    create a dictionary of obsid <---> status
    input:  none, but the data is read from /data/mta4/obs_ss/sot_ocat.out
    output: obsid_status[obsid] = status
    """
    ifile = obs_ss + 'sot_ocat.out'
    data  = ccf.read_data_file(ifile)

    obsid_status = {}
    for ent in data:
        atemp               = re.split('\^', ent)
        obsid               = atemp[1].strip()
        status              = atemp[16].strip()
        obsid_status[obsid] = status

    return obsid_status

#---------------------------------------------------------------------------------------------
#-- make_ddt_obs_list: a create a table of proposal numbers and obsids related to them      --
#---------------------------------------------------------------------------------------------

def make_ddt_obs_list():
    """
    a create a table of proposal numbers and obsids related to them
    input:  none
    output: updated table of tooddt_prop_obsid_list
            prop_list   --- a list of propsal numbers
    """
    [obsid_list, prop_list] = find_ddt_obsid_status()

    line = ''
    for prop_no in prop_list:

        olist = obsid_list[prop_no]
        if len(olist) > 0:
            olist2 = []
#
#--- just in a case, check the database to see whether there are more than listed in sot data
#
            for obsid in olist:
                olist2.append(obsid)
                [sqlinfo, monitor, groupid]  = tdsql.get_target_info(obsid)
                olist2 = olist2 + monitor
                olist2 = olist2 + groupid
#
#--- clean out so that we won't have a duplicated information
#
            olist2 = sorted(list(set(olist2)))
            line   = line + str(prop_no) + '<>' + str(olist2[0])
            for k in range(1, len(olist2)):
                line = line + ':' + str(olist2[k])
            line = line + '\n'

    with open(outdir, 'a') as fo:
        fo.write(line)

    return prop_list

#---------------------------------------------------------------------------------------------
#-- find_ddt_obsid_status: find current DDT observaitons and find their proposal numbers    --
#---------------------------------------------------------------------------------------------

def find_ddt_obsid_status():
    """
    find current DDT observaitons and find their proposal numbers
    input: none but read from /data/mta4/obs_ss/sot_ocat.out
    output: obsid_dict  --- a dictionary of a list of obsids for each proposal number
            prop_list   --- a list of proposal numbers
    """
#
#--- find ddt observations from <obs_ss>/sot_ocat.out data table file
#
    ifile = obs_ss + 'sot_ocat.out'
    data  = ccf.read_data_file(ifile)

    prop_list  = []
    obsid_dict = {}
    for ent in data:
        mc = re.search('DDT', ent)
        if mc is not  None:
            atemp   = re.split('\^', ent)
            obsid   = int(atemp[1].strip())
            status  = atemp[16].strip()
            prop_no = atemp[19].strip()

            if (status == 'archived') or (status == 'canceled'):
                continue 
#
#--- create a list of obsids and put in the dictionay form 
#
            try:
                alist = obsid_dict[prop_no]
                alist.append(obsid)
                obsid_dict[prop_no] = alist
            except:
                obsid_dict[prop_no] = [obsid]
                prop_list.append(prop_no)

    return [obsid_dict, prop_list]

#---------------------------------------------------------------------------------------------
#-- find_poc: create prop-id <---> poc dictionary from new_obs_list                        ---
#---------------------------------------------------------------------------------------------

def find_poc():
    """
    create prop-id <---> poc dictionary from new_obs_list
    input:  none, but read from tooddt_prop_obsid_list and new_obs_list
    output: propid_poc_dict ---- propid<--->poc dict
    """
    ifile = ocat_dir + 'approved'
    app   = ccf.read_data_file(ifile)
    spoc  = {}
    for ent in app:
        atemp = re.split('\s+', ent)
        spoc[atemp[1]] = atemp[2]

    ifile = too_dir + 'tooddt_prop_obsid_list'
    prop  = ccf.read_data_file(ifile)
    
    ifile = too_dir + 'new_obs_list'
    data  = ccf.read_data_file(ifile)

    propid_poc_dict = {}
    for ent in data:
        atemp = re.split('\s+', ent)
        if atemp[0] == 'too' or atemp[0] == 'ddt':

            pid = 'NA'
            for comp in prop:
                mc  = re.search(atemp[2], comp)
                if mc is not None:
                    btemp = re.split('<>', comp)
                    pid   = btemp[0]
                    break

            if pid != 'NA':
                poc = atemp[4]
                if poc == 'TBD':
                    if atemp[2] in spoc:
                        poc = spoc[atemp[2]]
                    else:  
                        pass

                propid_poc_dict[pid] = poc

    return propid_poc_dict
            

#---------------------------------------------------------------------------------------------

if __name__ == '__main__':

    update_tooddt_prop_list()

