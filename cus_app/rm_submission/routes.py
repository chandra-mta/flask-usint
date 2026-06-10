"""
Remove Submission Page
==============

**rm_submission/routes.py**: Render the remove submission page.

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: May 15, 2025

"""
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for
from flask_login import current_user

from . import bp
from .forms import RemoveRow
from ..supple.helper_functions import _SIGNOFF_COLUMNS
from ..supple import database_interface as dbi

_36_HOURS_AGO = (datetime.now() - timedelta(days=1.5)).timestamp()

@bp.route('/',      methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    """
    Display the Remove Submission Page
    """
    #: Process POST request for Removal requests before displaying the latest status of signoffs.
    if request.method == 'POST':
        for k,v in request.form.to_dict().items():
            if 'Remove' in v:
                revision_id, signoff_id, column = k.split('-')
                #: Removal requested. Following the PRG design pattern, perform redirect then come back.
                return redirect(url_for('rm_submission.remove', revision_id = revision_id, signoff_id = signoff_id, column = column))

    #: Pull the status information relating to the current user
    result = dbi.pull_status(user=current_user.id)

    put_on_page = []
    removal_forms = []
    
    for rev, sign in result:
        reversible = find_reversible_column(rev, sign)
        if reversible != []: #: Can reverse a status so keep in table.
            put_on_page.append((rev,sign,reversible))
    
    #: If we cannot reverse anything, then just fetch the most recent revisions and signoffs and put that data up as non_reversible
    if put_on_page == []:
        can_remove_submission = False
        result = dbi.pull_status(limit=10)
        for rev, sign in result:
            put_on_page.append((rev,sign,[]))
    else:
        can_remove_submission = True
    
    if can_remove_submission:
        #: Populate form with information to allow removal
        for rev,sign,reversible in put_on_page:
            removal_forms.append(RemoveRow(prefix=f"{rev.id}-{sign.id}")) #: Depending on the submitted button time, we will adjust either the signoff or the revision
    return render_template("rm_submission/index.html",
                           put_on_page = put_on_page,
                           removal_forms = removal_forms,
                           can_remove_submission = can_remove_submission,
                           _SIGNOFF_COLUMNS = _SIGNOFF_COLUMNS
                           )    

@bp.route('/<revision_id>/<signoff_id>/<column>', methods=['GET'])
def remove(revision_id, signoff_id, column):
    """
    PRG page for removing a signoff from a column
    """
    dbi.remove(revision_id, signoff_id, column)
    return redirect(url_for('rm_submission.index'))

def find_reversible_column(rev, sign):
    """
    Check if the specific signoff or revision involving the current user is within the last 36 hours.
    If so, record it as reversible based on column in signoff and string marking revision
    """
    reversible = []
    for sign_col in _SIGNOFF_COLUMNS:
        #: Any present signoff can be undone at any time provided it's by the original user
        if getattr(sign, f"{sign_col}_signoff_id") == current_user.id:
            if getattr(sign, f"{sign_col}_time") >= _36_HOURS_AGO:
                reversible.append(sign_col)
    if rev.user_id == current_user.id:
        if rev.time >= _36_HOURS_AGO:
            #: A revision can only be removed if there are no signed statuses remaining
            revision_reverse = True
            for sign_col in _SIGNOFF_COLUMNS:
                if getattr(sign, f"{sign_col}_status") == 'Signed':
                    revision_reverse = False
                    break
            if revision_reverse:
                reversible.append('revision')
    return reversible