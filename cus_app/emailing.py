"""
**emailing.py**: Module for notification functions

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: May 22, 2025

"""

import json
import os
from flask          import current_app, url_for
from flask_login    import current_user
from flask_mail import Message
from .extensions import mail

from cus_app.supple.database_interface import pull_revision

CUS  = 'cus@cfa.harvard.edu'
ARCOPS = 'arcops@cfa.harvard.edu'
MP = 'mp@cfa.harvard.edu'
HRC = 'hrcdude@cfa.harvard.edu'
ACIS = 'acisdude@cfa.harvard.edu'

stat_dir =  os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
with open(os.path.join(stat_dir, 'labels.json')) as f:
    _LABELS = json.load(f)

def _split_addresses(field):
    if not field:
        return []
    if isinstance(field, (list, tuple)):
        return list(field)
    return [addr.strip() for addr in field.split(",")]

def construct_msg(content, subject, to, sender=None, cc=None):
    if sender is None:
        sender = current_app.config.get("MAIL_DEFAULT_SENDER")

    if cc is not None:
        if isinstance(cc, (list, set)):
            _cc = [CUS] + list(cc)
        else:
            _cc = [CUS, cc]
    else:
        _cc = [CUS]

    msg = Message(
        subject=subject,
        recipients=to,
        cc=_cc,
        body=content,
        sender=sender
    )
    
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
        if current_app.config['MAIL_SUPPRESS_SEND']:
            print(msg.as_string())
        else:
            mail.send(msg)

def send_email(content, subject, to, sender = None, cc = []):
    """
    Combined send email function.

    :NOTE: This functionality is split only to allow cases in which we'd like to prepare sending emails in bulk before actually sending them.
    In typical usage, the send_email() function will be used across the board.
    """
    msg = construct_msg(content, subject, to, sender = sender, cc = [])
    send_msg(msg)

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