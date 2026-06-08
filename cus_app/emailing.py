"""
**emailing.py**: Module for notification functions

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: May 22, 2025

"""

import json
import os
from datetime import datetime
from flask          import current_app, flash, url_for
from flask_login    import current_user
from email.message import EmailMessage
from subprocess import Popen, PIPE
from cus_app.supple.database_interface import pull_revision

CUS  = 'cus@cfa.harvard.edu'
ARCOPS = 'arcops@cfa.harvard.edu'
MP = 'mp@cfa.harvard.edu'
HRC = 'hrcdude@cfa.harvard.edu'
ACIS = 'acisdude@cfa.harvard.edu'

stat_dir =  os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
with open(os.path.join(stat_dir, 'labels.json')) as f:
    _LABELS = json.load(f)

def construct_msg(content, subject, to, sender = None, cc = None):
    """
    Construct Email Instance
    """
    msg = EmailMessage()
    msg.set_content(content)
    msg['Subject'] = subject
    msg['To'] = to
    if sender is not None:
        msg['From'] = sender
    if cc is not None:
        if isinstance(cc,list):
            msg['CC'] = [CUS] + cc
        elif isinstance(cc, set):
            msg['CC'] = [CUS] + list(cc)
        else:
            msg['CC'] = [CUS] + [cc]
    else:
        msg['CC'] = CUS
    return msg

def send_msg(msg):
    """
    Send Email Instance
    """
    if isinstance(msg, (list,tuple)):
        for entry in msg:
            send_msg(entry)
    else:
        #: Print message instead of sending it if configured to test notifications
        if current_app.config['TEST_NOTIFICATIONS']:
            print(msg.as_string())
        else:
            p = Popen(["/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
            (out, error) = p.communicate(msg.as_bytes())
            if error is not None:
                current_app.logger.error(error)
                flash("Error sending notification email. Check Inbox.")
                send_error_email()

def send_email(content, subject, to, sender = None, cc = []):
    """
    Combined send email function.

    :NOTE: This functionality is split only to allow cases in which we'd like to prepare sending emails in bulk before actually sending them.
    In typical usage, the send_email() function will be used across the board.
    """
    msg = construct_msg(content, subject, to, sender = None, cc = [])
    send_msg(msg)

def send_error_email(e=None,logline=None):
    #: TODO. remake error handling such that more logging infromation is properly gathered from disparate sources,
    #: rather than relying on just one log file for everything.
    if not current_app.debug:
        handler_list = current_app.logger.handlers
        for item in handler_list:
            if item.name == "error":
                error_handler = item
                break
        file_path = error_handler.baseFilename
        #Once the log path is found, must search the file to send email contents
        with open(file_path,'r') as f:
            content = f.read()
        content = f"User: {current_user}\n\nocat.log:\n{content}"
        msg = EmailMessage()
        msg.set_content(content)
        msg['Subject'] = f"Usint Error-[{datetime.now().strftime('%c')}]"
        msg['To'] = current_app.config['ADMINS']
        msg['From'] = "UsintErrorHandler"
        p = Popen(["/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
        (out, error) = p.communicate(msg.as_bytes())
        
    else:
        if e is not None:
            #
            #--- File logger has not been initialized for the UsintErrorHandler as we are using the Werkzeug Browser Debugger instead.
            #--- If error passed, then raise in the Werkzeug Browser Debugger.
            #
            raise e
        if logline is not None:
            print(logline)
#
# --- Special case email formatting functions
#
def quick_approval_state_email(ocat_data, rev):
    """
    Convenient function for approval state emails.
    """
    content = ""
    for param in ('obsid', 'seq_nbr', 'targname'):
        content += f"{_LABELS.get(param)} = {ocat_data.get(param)}\n"
    content += f"User = {current_user.username}\n"
    to = [current_user.email]
    if rev.kind == 'asis':
        subject = f"Parameter Change Log: {rev.obsidrev()} (Approved)"
        content += "VERIFIED OK AS IS\n"
    elif rev.kind == 'remove':
        subject = f"Parameter Change Log: {rev.obsidrev()} (Removed)"
        content += "VERIFIED REMOVED\n"
        approved_revisions = pull_revision(order_by = {'revision_number': 'desc'}, obsid=ocat_data.get('obsid'), kind='asis')
        if len(approved_revisions) > 0:
            #: If undoing a previous approval, also notify the previous approver
            print(approved_revisions[0])
            to.append(approved_revisions[0].user.email)

    content += f"PAST COMMENTS = \n{ocat_data.get('comments') or ''}\n\n"
    content += f"PAST REMARKS = \n{ocat_data.get('remarks') or ''}\n\n"
    content += f"Parameter Status Page: {current_app.config['HTTP_ADDRESS']}{url_for('orupdate.index')}\n"
    content += f"Parameter Check Page: {current_app.config['HTTP_ADDRESS']}{url_for('chkupdata.index',obsidrev = rev.obsidrev())}\n"
    print(to)
    return construct_msg(content, subject, to)

def signoff_notify(ocat_data, rev, sign):
    """
    Check the performed signoff for special notification requirements and send those messages.
    """
    if ocat_data.get('obs_type') in ('TOO', 'DDT'):
        #: Notify personnel quickly about updates to a TOO/DDT.
        finished = {
            'arcops' : (sign.general_status != 'Pending') and (sign.acis_status != 'Pending'),
            'instrument' :(sign.acis_si_status != 'Pending') and (sign.hrc_si_status != 'Pending'),
            'usint' : (sign.usint_status != 'Pending')
        }
        if finished['arcops'] and not finished['instrument']:
            subject = f"{ocat_data.get('obs_type')} SI Mode Sign Off Request: (Obsid: {ocat_data.get('obsid')})"

            content = f"Editing of General/ACIS entries of {rev.obsidrev()} were finished and signed off.\n"
            content += "Please update SI Mode entries, then sign off.\n"
            content += f"Parameter Status Page: {current_app.config['HTTP_ADDRESS']}{url_for('orupdate.index')}\n"
            content += f"Parameter Check Page: {current_app.config['HTTP_ADDRESS']}{url_for('chkupdata.index',obsidrev = rev.obsidrev())}\n"

            if ocat_data.get('instrument') in ('HRC-I', 'HRC-S'):
                to = HRC
            else:
                to = ACIS
        elif not finished['arcops'] and finished['instrument']:
            subject = f"{ocat_data.get('obs_type')} General/ACIS Sign Off Request: (Obsid: {ocat_data.get('obsid')})"

            content = f"Editing of SI Mode entries of {rev.obsidrev()} were finished and signed off.\n"
            content += "Please update General/ACIS entries, then sign off.\n"
            content += f"Parameter Status Page: {current_app.config['HTTP_ADDRESS']}{url_for('orupdate.index')}\n"
            content += f"Parameter Check Page: {current_app.config['HTTP_ADDRESS']}{url_for('chkupdata.index',obsidrev = rev.obsidrev())}\n"

            to = ARCOPS
        elif finished['arcops'] and finished['instrument'] and not finished['usint']:
            subject = f"{ocat_data.get('obs_type')} Usint Sign Off Request: (Obsid: {ocat_data.get('obsid')})"

            content = f"Editing of all entries of {rev.obsidrev()} were finished and signed off.\n"
            content += "Please verify and signoff.\n"
            content += f"Parameter Status Page: {current_app.config['HTTP_ADDRESS']}{url_for('orupdate.index')}\n"
            content += f"Parameter Check Page: {current_app.config['HTTP_ADDRESS']}{url_for('chkupdata.index',obsidrev = rev.obsidrev())}\n"

            to = [rev.user.email, current_user.email]
        else:
            return None #: No email
        
        send_email(content, subject, to)