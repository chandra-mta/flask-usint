#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#################################################################################################
#                                                                                               #
#       new_too_ddt_notifier.py: notify new ddt/too observations to poc                         #
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
import time
import unittest
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
sys.path.append(bin_dir)
#
import cus_common_functions         as ccf  #---- mta common functions
#
#--- set a temporary file name
#
import random
rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)

cus    = 'cus@cfa.harvard.edu'
admin  = 'bwargelin@cfa.harvard.edu'
tech   = 'lina.pulgarin-duque@cfa.harvard.edu'

#------------------------------------------------------------------------------------------------------
#-- new_too_ddt_notifier: notify new ddt/too observations to poc                                     --
#------------------------------------------------------------------------------------------------------

def new_too_ddt_notifier():
    """
    notify new ddt/too observations to poc 
    input: none but read from <too_dir>/too_list, <too_dir>/ddt_list
    output: email sent out to poc
    """
#
#--- create a list of poc and a dictionary of poc <---> email address
#
    [poc_list, email_dict] = get_poc_email_dict() 
#
#--- find new too/ddt observations
#
    [new_too, new_ddt] = find_new_obs()
#
#--- if there are new observations, send email to poc
#
    if len(new_too) > 0:
        too_obs = create_user_obsid_dict(poc_list, new_too)
        send_email('too', too_obs, poc_list, email_dict)

    if len(new_ddt) > 0:
        ddt_obs = create_user_obsid_dict(poc_list, new_ddt)
        send_email('ddt', ddt_obs, poc_list, email_dict)
        
#------------------------------------------------------------------------------------------------------
#-- create_user_obsid_dict: create poc <---> a list of obsids                                        --
#------------------------------------------------------------------------------------------------------

def create_user_obsid_dict(poc_list, dlist):
    """
    create poc <---> a list of obsids
    input:  poc_list    --- a list of poc
            dlist       --- a list observation info
    output: p_obs       --- a dictionary of poc <---> a list of obsids
    """
#
#--- initialize dictionary with empty lists
#
    p_obs = {}
    plen  = len(poc_list)
    for poc in poc_list:
        p_obs[poc] = []

    for ent in dlist:
#
#--- find who is the poc for the obsid
#
        atemp = re.split('\s+', ent)
        obsid = atemp[2]
        poc   = atemp[4]
        for comp in poc_list:
            if poc == comp:
#
#--- update a list and then put back to the dictionary
#
                out = p_obs[poc]
                out.append(obsid)
                p_obs[poc] = out
                break
    return p_obs

#------------------------------------------------------------------------------------------------------
#-- get_poc_email_dict: create a list of poc and a dictonary of poc <---> email address             ---
#------------------------------------------------------------------------------------------------------

def get_poc_email_dict():
    """
    create a list of poc and a dictonary of poc <---> email address
    input:  none but read from <too_dir>/usint_personal
    output: poc_list    --- a list of poc
            email_dict  --- a dictonary of poc <--> email address
    """
    p_list =  too_dir + 'usint_personal'
    data   = ccf.read_data_file(p_list)

    poc_list   = []
    email_dict = {}
    for ent in data:
        atemp = re.split(':', ent)
        poc   = atemp[0]
        email = atemp[5].strip()
        
        poc_list.append(poc)
        email_dict[poc] = email

    return [poc_list, email_dict]

#------------------------------------------------------------------------------------------------------
#-- send_email: send email notice to poc                                                            ---
#------------------------------------------------------------------------------------------------------

def send_email(dtype, p_obs_dict, poc_list, email_dict):

    """
    send email notice to poc 
    input:  dtype       --- too, ddt
            p_obs_dict  --- a dictionary of poc <---> a list of obsids
            poc_list    --- a list of poc
            email_dict  --- a dictionary of poc <---> email address
    output: meail sent to poc
    """
    for poc in poc_list:
        out = p_obs_dict[poc]
        if len(out) == 0:
            continue 

        line = ''
        if len(out) > 1:
            line = line + '\nNew '   + dtype.upper() + ' observations (OBSIDs: ' 

            for pout in out:
                line = line + pout + ' ' 

            line = line + ') are assigned to POC: ' + poc +'. Please check:\n\n'

        elif len(out) == 1:
            line = '\nA new ' + dtype.upper() + ' observation (OBSID: ' + out[0] + ') is assigned to '
            line = line + 'POC: ' + poc + '.  Please check:\n\n'

        else:
            continue

        for obsid in out:
            line = line +  'https://cxc.cfa.harvard.edu/mta/CUS/Usint/ocatdata2html.cgi?' + obsid + '\n'

        line = line + '\nfor more information.\n\n'
        line = line + 'If you are not POC for this observation, \n'
        line = line + 'please reply to tisobe@cfa.harvard.edu cc:cus@cfa.harvard.edu.\n'

        with open(zspace, 'w') as fo:
            fo.write(line)

        email = email_dict[poc] + ' ' + cus

        subject = 'New ' + dtype.upper() + ' Observation'
        #cmd = 'cat ' + zspace + ' | mailx -s"' + subject + '" -b '  + tech 
        #cmd = cmd + ' -c ' + cus + ' '  + admin + ' ' + email
#
        #os.system(cmd)

        ccf.rm_files(zspace)

#------------------------------------------------------------------------------------------------------
#-- find_new_obs: find newly added too and/or ddt observations from the lists                        --
#------------------------------------------------------------------------------------------------------

def find_new_obs():
    """
    find newly added too and/or ddt observations from the lists
    input:  none but read from <too_dir>/too_list, <too_dir>/ddt_list
    output: too/ddt --- a list of the information of the new observations
        e.g.: "too     401991  20264   observed        msobolewska     19      Feb 28 2018  9:36AM"
    """
    ifile = too_dir + 'too_list'
    ofile = too_dir + 'too_list~'

    ndata = ccf.read_data_file(ifile)
    ndata = check_status(ndata)

    odata = ccf.read_data_file(ofile)
    odata = check_status(odata)

    too   = numpy.setdiff1d(ndata, odata)

    ifile = too_dir + 'ddt_list'
    ofile = too_dir + 'ddt_list~'

    ndata = ccf.read_data_file(ifile)
    ndata = check_status(ndata)

    odata = ccf.read_data_file(ofile)
    odata = check_status(odata)

    ddt   = numpy.setdiff1d(ndata, odata)

    return [too, ddt]
    
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------

def check_status(olist):

    nlist = []
    for ent in olist:
        mc1 = re.search('scheduled', ent)
        mc2 = re.search('unobserved', ent)
        if (mc1 is not None) or (mc2 is not None):
            nlist.append(ent)

    return nlist

#------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    new_too_ddt_notifier()


