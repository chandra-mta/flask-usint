"""
Express Approval Page
==============

**express/routes.py**: Render the Express Approval Page

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: May 12, 2025

"""
import os
import json
from datetime import datetime, timedelta

from flask import current_app, render_template, request, flash, session, redirect, url_for, abort
from flask_login    import current_user
from sqlalchemy.orm.exc import NoResultFound

from cus_app.extensions import db
from cus_app.models import register_user
from cus_app.express import bp
from cus_app.express.forms import ExpressApprovalForm, ConfirmForm
from cus_app.supple.read_ocat_data import read_basic_ocat_data
import cus_app.supple.database_interface as dbi
from cus_app.supple.helper_functions import create_obsid_list

@bp.before_app_request
def before_request():
    if not current_user.is_authenticated:
        register_user()

@bp.route('/',      methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    """
    Display the Express Approval Page
    """
    express_form = ExpressApprovalForm(request.form)
    if request.method == 'POST' and express_form.is_submitted():
        #: Redirect to confirmation page, processing the approval.
        try:
            obsid_list = create_obsid_list(express_form.multiobsid.data)
            if obsid_list != []:
                session['express_approval'] = obsid_list
                return redirect(url_for('express.confirm'))
        except (ValueError, TypeError):
            flash("Error in parsing form input. Please verify formatting.")
    return render_template('express/index.html',
                            express_form = express_form
                            )

@bp.route('/confirm', methods=['GET', 'POST'])
def confirm():
    """
    Process the provided list, recording which obsids will be approved, which are already approved, and which are not in the ocat
    """
    confirm_form = ConfirmForm(request.form)
    if request.method == 'POST' and confirm_form.is_submitted():
        if confirm_form.previous_page.data:
            return redirect(url_for('express.index'))
        elif confirm_form.finalize.data:
            return redirect(url_for('express.finalize'))
    else:
        obsid_list = session.pop('express_approval', [])
        to_approve = {}
        unapprovable = {}
        for obsid in obsid_list:
            try:
                ocat_data = read_basic_ocat_data(obsid)
                is_approved = dbi.is_approved(obsid)
                ocat_data.update({'has_open_revision': dbi.has_open_revision(obsid), 'is_approved': is_approved})
                if dbi.is_approved(obsid) or ocat_data.get('status') in ['observed', 'archived', 'canceled', 'discarded']:
                    unapprovable[obsid] = ocat_data
                else:
                    to_approve[obsid] = ocat_data
            except NoResultFound:
                unapprovable[obsid] ={'not_in_ocat': True}
        session['to_approve'] = to_approve
        return render_template('express/confirm.html',
                            to_approve = to_approve,
                            unapprovable = unapprovable,
                            confirm_form = confirm_form
                                )

@bp.route('/finalize', methods=['GET', 'POST'])
def finalize():
    """
    Perform the approvals and display the completion page.
    """
    to_approve = session.pop('to_approve', {})
    try:
        for obsid, ocat_data in to_approve.items():
            revision = dbi.construct_revision(obsid,ocat_data,'asis')
            signoff = dbi.construct_signoff(revision)
            db.session.add(revision)
            db.session.add(signoff)
        db.session.commit()
    except Exception as e:  # noqa: E722
        #: In the event of an error, roll back the database session to avoid commits instilled by the server-side cookies
        #: TODO. Do we still clear the session cookies if the database injection failed? I'd assume not...
        db.session.rollback()
        raise e #: TODO replace with abort(500)
    return render_template('express/finalize.html',
                           to_approve = to_approve
                           )