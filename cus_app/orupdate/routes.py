"""
Target Parameter Status Page
==============

**orupdate/routes.py**: Render the target parameter Status Page

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: May 06, 2025

"""
import os
import json
from datetime import datetime, timedelta

from flask import render_template, request, redirect, url_for, flash
from flask import session as web_session
from flask_login import current_user

from cus_app.models import register_user
from cus_app.orupdate import bp
from cus_app.orupdate.forms import SignoffRow, OrderForm
from cus_app.supple.helper_functions import is_open
import cus_app.supple.database_interface as dbi

stat_dir =  os.path.join(os.path.dirname(os.path.abspath(__file__)),'..', 'static')
with open(os.path.join(stat_dir, 'color.json')) as f:
    _COLORS = json.load(f)

_36_HOURS_AGO = (datetime.now() - timedelta(days=1.5)).timestamp()

@bp.before_app_request
def before_request():
    if not current_user.is_authenticated:
        register_user()

@bp.route('/',      methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    """
    Display the Target Parameter Status Page
    """
    #: Process POST request for signoff buttons before displaying parameter status page.
    if request.method == 'POST':
        for k,v in request.form.to_dict().items():
            if 'Signoff' in v:
                #: Signoff requested. Following the PRG design pattern, perform redirect then come back.
                signoff_id, signoff_kind = k.split('-')
                return redirect(url_for('orupdate.perform_signoff', id = signoff_id, kind = signoff_kind))

    status_page_order_kwarg = web_session.get('status_page_order_kwarg', {}) #: Pull revision orders by descending submission by default

    #: TODO Suggested future development to convert table sorting to a jQuery data table approach to avoid unnecessary queries.
    order_form = OrderForm(request.form, data={'username': current_user.username}) #: default input username is current user
    #: Process the order_form to determine the order of displayed revisions on the status page
    if order_form.order_submission.data:
        status_page_order_kwarg = {}
    elif order_form.order_obsid.data:
        status_page_order_kwarg = {'order_obsid': True}
    elif order_form.order_username.data:
        #: Provide user id instead to refine query, if the username is misspelled no change
        user = dbi.user_by_name(order_form.username.data)
        if user is not None:
            status_page_order_kwarg = {'order_user': user.id}
        else:
            flash("Unknown username. Please verify spelling.")

    web_session['status_page_order_kwarg'] = status_page_order_kwarg
    result = dbi.pull_status(**status_page_order_kwarg)

    open_revision_signoff = []
    open_forms =[]
    open_is_approved = []
    closed_revision_signoff = []
    multi_revision_info = {}

    count = 0

    for rev, sign in result:
        if rev.obsid not in multi_revision_info.keys():
            multi_revision_info[rev.obsid] = {'opened': [], 'closed': [], 'color': None}
        if is_open(sign):
            open_revision_signoff.append((rev,sign))
            open_forms.append(SignoffRow(prefix=str(sign.id)))
            multi_revision_info[rev.obsid]['opened'].append(rev.revision_number)
            if dbi.is_approved(rev.obsid):
                open_is_approved.append(True)
            else:
                open_is_approved.append(False)
            #: Assign a multi color once two open revisions are found, applied to all
            if len(multi_revision_info[rev.obsid]['opened']) == 2:
                col = list(_COLORS)[count % len(_COLORS)]
                multi_revision_info[rev.obsid]['color'] = _COLORS.get(col)
                count += 1
        else:
            #: Limit the retention of closed revisions to the last 1.5 days
            multi_revision_info[rev.obsid]['closed'].append(rev.revision_number)
            if rev.time >= _36_HOURS_AGO:
                closed_revision_signoff.append((rev,sign))
    return render_template("orupdate/index.html",
                           order_form = order_form,
                           open_revision_signoff = open_revision_signoff,
                           open_forms = open_forms,
                           closed_revision_signoff = closed_revision_signoff,
                           multi_revision_info = multi_revision_info,
                           open_is_approved = open_is_approved
                           )

@bp.route('/<id>/<kind>', methods=['GET', 'POST'])
def perform_signoff(id,kind):
    """
    Redirect page for performing the signoff
    """
    dbi.perform_signoff(id, kind)
    return redirect(url_for('orupdate.index'))