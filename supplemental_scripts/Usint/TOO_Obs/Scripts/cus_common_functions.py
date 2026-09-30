#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

import os
import sys
import re
import string
import random
import time
import math
import numpy
import codecs

#--------------------------------------------------------------------------
#-- add_leading_zero: add leading 0 to digit                             --
#--------------------------------------------------------------------------

def add_leading_zero(val, dlen=2):
    """
    add leading 0 to digit
    input:  val     --- neumeric value or string value of neumeric
            dlen    --- length of digit
    output: val     --- adjusted value in string
    """
    try:
        val = int(val)
    except:
        return val

    val  = str(val)
    vlen = len(val)
    for k in range(vlen, dlen):
        val = '0' + val

    return val
#--------------------------------------------------------------------------
#-- is_leapyear: check whether the year is a leap year                   --
#--------------------------------------------------------------------------

def is_leapyear(year):
    """
    check whether the year is a leap year
    input:  year    --- year
    output: True/False
    """
    year = int(float(year))
    chk  = year % 4             #--- every 4 years:   leap year
    chk2 = year % 100           #--- but every 100 years: not leap year
    chk3 = year % 400           #--- except every 400 year: leap year

    val  = False
    if chk == 0:
        val = True
        if chk2 == 0:
            val = False
    if chk3 == 0:
        val = True

    return val

def isLeapYear(year):
    is_leapyear(year)

#--------------------------------------------------------------------------
#-- read_data_file: read a data file and create a data list              --
#--------------------------------------------------------------------------

def read_data_file(ifile, remove=0, ctype='r'):
    """
    read a data file and create a data list
    input:  ifile   --- input file name
            remove  --- if > 0, remove the file after reading it
            ctype   --- reading type such as 'r' or 'b'
    output: data    --- a list of data
    """
#
#--- if a file specified does not exist, return an empty list
#
    if not os.path.isfile(ifile):
        return []

    try:
        with open(ifile, ctype) as f:
            data = [line.strip() for line in f.readlines()]
    except:
        with codecs.open(ifile, ctype, encoding='utf-8', errors='ignore') as f:
            data = [line.strip() for line in f.readlines()]
#
#--- if asked, remove the file after reading it
#
    if remove > 0:
        rm_files(ifile)

    return data

#--------------------------------------------------------------------------
#-- rm_files: remove a file of named file in a list                      --
#--------------------------------------------------------------------------

def rm_files(ifile):
    """
    remove a file of named file in a list
    input:  ifile   --- a file name or a list of file names to be removed
    output: none
    """
    mc = re.search('\*', ifile)
    if mc  is not None:
        cmd = 'rm -fr ' +  ifile
        os.system(cmd)

    else:
        if isinstance(ifile, (list, tuple)):
            ilist = ifile
        else:
            ilist = [ifile]

        for ent in ilist:
            if os.path.isfile(ent):
                cmd = 'rm -fr ' + ent
                os.system(cmd)

def rm_file(ifile):
    rm_files(ifile)

#--------------------------------------------------------------------------
#-- change_month_format: cnvert month format between digit and three letter month 
#--------------------------------------------------------------------------

def change_month_format(month):
    """
    cnvert month format between digit and three letter month
    input:  month   --- either digit month or letter month
    oupupt: either digit month or letter month
    """
    m_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',\
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
#
#--- check whether the input is digit
#
    try:
        var = int(float(month))
        if (var < 1) or (var > 12):
            return 'NA'
        else:
            return m_list[var-1]
#
#--- if not, return month #
#
    except:
        mon = 'NA'
        var = month.lower()
        for k in range(0, 12):
            if var == m_list[k].lower():
                return k+1

        return mon

#--------------------------------------------------------------------------
#-- is_neumeric: checking the input is neumeric value                    --
#--------------------------------------------------------------------------

def is_neumeric(val):
    """
    checking the input is neumeric value
    input:  val --- input value
    output: True/False
    """

    try:
        var = float(val)
        return True
    except:
        return False

def chkNumeric(val):
    is_neumeric(val)

