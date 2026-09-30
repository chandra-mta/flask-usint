#!/usr/bin/env python

"""
**create_schedule_table.py**: create a html page from a given schedule

:Author: t. isobe (tisobe@cfa.harvard.edu)
:Last Updated: Mar 17, 2025

"""
import os
import time
from cxotime import CxoTime
import argparse
import getpass
import re
from calendar import month_name
from email.mime.text    import MIMEText
from subprocess     	import Popen, PIPE

#
#--- Define Directory Pathing
#
USINT_DIR = "/data/mta4/CUS/www/Usint"
LIVE_DIR = "/proj/web-cxc/wsgi-scripts/cus"
TOO_CONTACT_DIR = f"{USINT_DIR}/ocat/Info_save/too_contact_info"
HOUSE_KEEPING = f"{LIVE_DIR}/other_scripts/house_keeping"

#
#--- a few emails addresses
#
CUS       = ['cus@cfa.harvard.edu']
ADMIN     = ['bwargelin@cfa.harvard.edu']
#
#--- constant related dates
#
THREE_MON = 86400 * 30 * 3
SEVEN_DAY = 86400 * 7
TESTMAIL = False

#---------------------------------------------------------------------------------------
#--- create_schedule_table: update schedule html page                                 --
#---------------------------------------------------------------------------------------

def create_schedule_table():
    """
    update schedule html page
    input:  none but read from <too_contact_dir>/schedule
    output: <usint_dir>/too_contact_schedule.html
    """
#
#--- find today's date
#
    stime = CxoTime().secs
#
#--- read poc info
#
    poc_dict = read_poc_info()
#
#--- read schedule table
#
    [k_list, d_dict] = read_schedule()
    k_list = sorted(k_list)
    for m in range(0, len(k_list)):
        ctime = dtime_to_ctime(k_list[m])
        if ctime > stime:
            sind = m - 5
            if sind < 0:
                sind = 0
            break

    line = ''
    for key in k_list[sind:]:
        [poc, name, period, start, stop] = d_dict[key]
        if name == 'TBD':
            ophone = ' --- ' 
            cphone = ' --- ' 
            hphone = ' --- ' 
            email  = ' --- '    
        else:
            [ophone, cphone, hphone, email]  = poc_dict[name]

        start = dtime_to_ctime(start)
        stop  = dtime_to_ctime(stop) + 86400 #: Function returns the start of the day, so add one day to make the range inclusive of the final day in schedule

        if (stime >= start) and (stime < stop):
            line = line + '<tr style="color:blue; background-color:lime">'
        else:
            line = line + '<tr>'
        line = line + '<td style="text-align:center;">' + period + '</td>'
        line = line + '<td style="text-align:center;">' + name   + '</td>'
        line = line + '<td style="text-align:center;">' + ophone + '</td>'
        line = line + '<td style="text-align:center;">' + cphone + '</td>'
        line = line + '<td style="text-align:left;">'   + hphone + '</td>'
        line = line + '<td style="text-align:left;">'   
        line = line + '<a href="mailto:' + email + '">'
        line = line + email  + '</a></td>'
        line = line + '</tr>\n'

#
#--- read templates
#
    with open(f"{HOUSE_KEEPING}/Schedule/schedule_main_template") as f:
        head = f.read()

    with open(f"{HOUSE_KEEPING}/Schedule/schedule_tail") as f:
        tail = f.read()

    udate = time.strftime('%m/%d/%Y', time.gmtime())
    tail  = tail.replace('#UPDATE#', udate)

    line  = head + line + tail

    ofile = f"{USINT_DIR}/too_contact_schedule.html"
    with open(ofile, 'w') as fo:
        fo.write(line)
#
#--- send notifications
#
    schedule_notification(k_list, d_dict, poc_dict, stime)
#
#--- update this week's poc list
#
    update_this_week_poc(k_list, d_dict, stime)

#---------------------------------------------------------------------------------------
#-- read_schedule: read the schedule data table                                       --
#---------------------------------------------------------------------------------------

def read_schedule():
    """
    read the schedule data table
    input:  none, but read from <too_contact_dir>/schedule
    output: a dictionary of [poc, name, period, start, stop]. key: start
            key/start/stop is in <yyyy><mm><dd>
    """

    with open(f"{TOO_CONTACT_DIR}/schedule") as f:
        data = [line.strip() for line in f.readlines()]

    d_dict = {}
    k_list = []
    for ent in data:
        atemp = re.split(r'\t+', ent)
        name  = atemp[0]
        smon  = atemp[1]
        sday  = atemp[2]
        syear = atemp[3]
        emon  = atemp[4]
        eday  = atemp[5]
        eyear = atemp[6]
        try:
            poc   = atemp[7]
        except IndexError:
            poc = 'TBD'
        key = f"{syear}{smon:>02}{sday:>02}"
        etime = f"{syear}{emon:>02}{eday:>02}"
        lsmon = month_name[int(smon)]
        start = lsmon + ' ' + sday
        lemon = month_name[int(emon)]
        stop  = lemon + ' '   + eday
        period= start + ' - ' + stop

        k_list.append(key)
        d_dict[key] = [poc, name, period, key, etime]

    return[k_list, d_dict]

#---------------------------------------------------------------------------------------
#-- read_poc_info: read poc information                                               --
#---------------------------------------------------------------------------------------

def read_poc_info():
    """
    read poc information
    input:  none, but read from <too_contact_dir>/this_week_person_in_charge
    output: a dictionary with [ophone, cphone, hphone, email]. key: full name
    """
    with open(f"{TOO_CONTACT_DIR}/active_usint_personnel") as f:
        data = [line.strip() for line in f.readlines()]

    poc_dict = {}
    for ent in data:
        atemp  = ent.split(":")
        key    = atemp[1]
        ophone = atemp[2]
        cphone = atemp[3]
        hphone = atemp[4]
        email  = atemp[5]
        poc_dict[key] = [ophone, cphone, hphone, email]

    return poc_dict

#---------------------------------------------------------------------------------------
#-- schedule_notification: sending out various notifications                          --
#---------------------------------------------------------------------------------------

def schedule_notification(k_list, d_dict, poc_dict, stime):
    """
    sending out various notifications
    input:  k_list      --- a list of poc schedule starting time in <yyyy><mm><dd>
            d_dict      --- a dictionary of schedule information, key: <yyyy><mm>dd>
            poc_dict    --- a dictionary of poc information, key: name
            stime       --- today's time in seconds in 1998.1.1
    output: email sent
    """
#
#--- check whether poc schedule is filled beyond 3 months from today
#
    check_schedule_fill(k_list, stime)
#
#--- check whether the schedule two weeks from now is signed up
#
    check_next_week_filled(k_list, d_dict, stime)
#
#--- send out the first notification to POC: a day before the duty starts
#
    first_notification(k_list, d_dict, poc_dict, stime)
#
#--- send out the second notification to POC: on the day of the duty starts
#
    second_notification(k_list, d_dict, poc_dict, stime)
    
#---------------------------------------------------------------------------------------
#-- check_schedule_fill: check whether the poc schedule is running out in about 3 months 
#---------------------------------------------------------------------------------------

def check_schedule_fill(k_list, stime):
    """
    check whether the poc schedule is running out in about 3 months and if so send out email
    input:  k_list  --- a list of poc schedule starting time in <yyyy><mm><dd>
            stime   --- today's time in seconds in 1998.1.1
            it also read: <house_keeping>/Schedule/add_schedule_log (the last logged time)
                          <house_keeping>/Schedule/add_schedule (template)
    output: email sent
    """
#
#--- find the last entry date of the signed-up list
#
    l_entry = dtime_to_ctime(k_list[-1])
#
#--- check whether the last entry date is less than three months away
#
    tdiff   = l_entry - stime
    if tdiff < THREE_MON:
#
#--- check when the last time this notification was sent
#
        nfile = f"{HOUSE_KEEPING}/Schedule/add_schedule_log"
        if os.path.isfile(nfile):
            with open(nfile, 'r') as f:
                l_time = float(f.read())
        else:
            l_time = 0
#
#--- if the last notification is older than 7 days, send it again
#
        cdiff = stime - l_time
        if cdiff > SEVEN_DAY:
            ifile = f"{HOUSE_KEEPING}/Schedule/add_schedule"
            subj  = 'POC Schedule Needs To Be Filled'

            send_mail(subj, ifile, {'TO': ADMIN, 'CC': CUS})
#
#--- update log time
#
        with open(nfile, 'w') as fo:
            fo.write(str(stime))

#---------------------------------------------------------------------------------------
#-- check_next_week_filled: check the schedule is signed up on the slot two week from current
#---------------------------------------------------------------------------------------

def check_next_week_filled(k_list, d_dict, stime):
    """
    check the schedule is signed up on the slot two week from current
    input:  k_list  --- a list of poc schedule starting time in <yyyy><mm><dd>
            d_dict  --- a dictionary of schedule information, key: <yyyy><mm>dd>
            stime   --- today's time in seconds in 1998.1.1
                          <house_keeping>/Schedule/missing_schedule (template)
    output: email sent
    """
#
#--- find the schedule date two weeks (or two down) from the current one
#
    pos = None
    for k in range(0, len(k_list)):
        c_time = dtime_to_ctime(k_list[k])
        if c_time >= stime:
            pos = k + 1
            break
#
#--- find whether the slot is actually signed up
#
    if pos is None or pos >= len(k_list):
        poc = 'TBD' #Could not find entry two slots after the current time
    else:
        poc = d_dict[k_list[pos]][1]
#
#--- if it is not signed up, send out email on this Friday to notify admin
#
    if poc == 'TBD':
        wday = int(float(time.strftime('%w', time.gmtime())))
        if wday == 5:
            ifile = f"{HOUSE_KEEPING}/Schedule/missing_schedule"
            subj  = 'POC Schedule Needs To Be Filled'

            send_mail(subj, ifile, {'TO': ADMIN, 'CC': CUS})

#---------------------------------------------------------------------------------------
#-- first_notification: send first notification to POC                                --
#---------------------------------------------------------------------------------------

def first_notification(k_list, d_dict, poc_dict, stime):
    """
    send first notification to POC
    input:  k_list      --- a list of poc schedule starting time in <yyyy><mm><dd>
            d_dict      --- a dictionary of schedule information, key: <yyyy><mm>dd>
            poc_dict    --- a dictionary of poc information, key: name
            stime       --- today's time in seconds in 1998.1.1
                  <house_keeping>/Schedule/first_notification (template)
    output: email sent
    """
#
#--- check whether the scheduled poc changes in two days
#
    ncheck = stime + 86400.0
    nstart = stime + 86400.0 * 2
#
#--- find the current period
#
    for k in range(0, len(k_list)-1):
        p1 = dtime_to_ctime(k_list[k])
        p2 = dtime_to_ctime(k_list[k+1])
        if (stime >= p1) and (stime <= p2):
#
#--- if the schedule changes in two days, send a notification
#
            if (ncheck <= p2) and ( p2 <= nstart):
                ifile = f"{HOUSE_KEEPING}/Schedule/first_notification"
                name  = d_dict[k_list[k+1]][1]
                email = poc_dict[name][-1]
                subj  = 'TOO Point of Contact Duty Notification'
                send_mail(subj, ifile, {'TO': [email], 'CC': CUS})

                subj  = 'TOO Point of Contact Duty Notification (sent to: ' + email + ')'
                send_mail(subj, ifile, {'TO': ADMIN, 'CC': CUS})
            break
            
#---------------------------------------------------------------------------------------
#-- second_notification: send second notification to POC                              --
#---------------------------------------------------------------------------------------

def second_notification(k_list, d_dict, poc_dict, stime):
    """
    send second notification to POC
    input:  k_list      --- a list of poc schedule starting time in <yyyy><mm><dd>
            d_dict      --- a dictionary of schedule information, key: <yyyy><mm>dd>
            poc_dict    --- a dictionary of poc information, key: name
            stime       --- today's time in seconds in 1998.1.1
                  <house_keeping>/Schedule/second_notification (template)
    output: email sent
    """
#
#--- check yesterday's time
#
    d_before =  stime - 86400.0
#
#--- check which period yesterday belongs to
#
    for k in range(0, len(k_list)-1):
        p1 = dtime_to_ctime(k_list[k])
        p2 = dtime_to_ctime(k_list[k+1])
        if (p1 <= d_before) and (d_before <= p2):
#
#--- if the schedule just changes today, send a notification
#
            if stime >= p2:
                ifile = f"{HOUSE_KEEPING}/Schedule/second_notification"

                name  = d_dict[k_list[k+1]][1]
                email = poc_dict[name][-1]

                subj  = 'TOO Point of Contact Duty Notification: Second Notification'
                send_mail(subj, ifile, {'TO': [email], 'CC': CUS})

                subj  = 'TOO Point of Contact Duty Notification: Second Notification (sent to: ' + email + ')'
                send_mail(subj, ifile, {'TO': ADMIN, 'CC': CUS})

#---------------------------------------------------------------------------------------
#-- send_mail: sending email                                                          --
#---------------------------------------------------------------------------------------

def send_mail(subject, content, address_dict):
    """Send Emails

    :param subject: Subject line
    :type subject: str
    :param content: Text File of content or string of content
    :type content: str, filepath
    :param address_dict: Dictionary or recipients
    :type address_dict: dict
    """
    if os.path.isfile(content):
            with open(content) as f:
                msg = MIMEText(f.read())
    else:
        msg = MIMEText(content)
    msg['Subject'] = subject
    for k,v in address_dict.items():
        if isinstance(v,list):
            msg[k] = ','.join(v)
        else:
            msg[k] = v
    if TESTMAIL:
        print(msg)
    else:
        p = Popen(["/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
        p.communicate(msg.as_bytes())

#---------------------------------------------------------------------------------------
#-- update_this_week_poc: update this_week_person_in_charge table                      -
#---------------------------------------------------------------------------------------

def update_this_week_poc(k_list, d_dict, stime):
    """
    update this_week_person_in_charge table
    input:  k_list      --- a list of poc schedule starting time in <yyyy><mm><dd>
            d_dict      --- a dictionary of schedule information, key: <yyyy><mm>dd>
            stime       --- today's time in seconds in 1998.1.1
                <too_contact_dir>/this_week_person_in_charge
    output: updated: <too_contact_dir>/this_week_person_in_charge
    """
#
#--- find the current period
#
    for k in range(0, len(k_list)-1):
        p1 = dtime_to_ctime(k_list[k])
        p2 = dtime_to_ctime(k_list[k+1])
        if (stime >= p1) and (stime < p2):
#
#--- find poc
#
            name  = d_dict[k_list[k]][1]
            break
#
#--- read the file
#
    pfile = f"{TOO_CONTACT_DIR}/this_week_person_in_charge"
    with open(pfile) as f:
        data = [line.strip() for line in f.readlines()]
#
#--- mark the poc who are not on duty with '#'
#
    line  = ''
    for ent in data:
        ent   = ent.replace('#', '')
        atemp = ent.split(',')
        poc   = atemp[0]
        contact = atemp[-1]
        if poc == name:
            line = line + ent + '\n'
        else:
            line = line  + '#' + ent + '\n'
#
#--- print out the update
#
    with open(pfile, 'w') as fo:
        fo.write(line)

#---------------------------------------------------------------------------------------
#-- dtime_to_ctime: convert display time to chandra time                              --
#---------------------------------------------------------------------------------------

def dtime_to_ctime(dtime):
    """
    convert display time to chandra time
    input:  dtime   --- display time in <yyyy><mm><dd>
    output: stime   --- time in seconds from 1998.1.1
    """
    ltime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(dtime, '%Y%m%d'))
    stime = int(CxoTime(ltime).secs)
    
    return stime


#---------------------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    args = parser.parse_args()

    if args.mode == 'test':
#
#--- Change pathing to test case. Considering the amount of intermediary files,
#--- copying test version of these files manually is the most direct testing method
#
        USINT_DIR = f"{os.getcwd()}/test/_outTest"
        LIVE_DIR = f"{os.getcwd()}"
        OLD = TOO_CONTACT_DIR
        TOO_CONTACT_DIR = f"{USINT_DIR}/ocat/Info_save/too_contact_info"
        os.makedirs(TOO_CONTACT_DIR, exist_ok = True)
        if not os.path.exists(f"{TOO_CONTACT_DIR}/schedule"):
            os.system(f"cp {OLD}/schedule {TOO_CONTACT_DIR}/schedule")
        if not os.path.exists(f"{TOO_CONTACT_DIR}/active_usint_personnel"):
            os.system(f"cp {OLD}/active_usint_personnel {TOO_CONTACT_DIR}/active_usint_personnel")
        if not os.path.exists(f"{TOO_CONTACT_DIR}/this_week_person_in_charge"):
            os.system(f"cp {OLD}/this_week_person_in_charge {TOO_CONTACT_DIR}/this_week_person_in_charge")
        HOUSE_KEEPING = f"{LIVE_DIR}/house_keeping"

        TESTMAIL = True
        create_schedule_table()

    elif args.mode == 'flight':
        create_schedule_table()




