"""
**scheduler/forms.py**: Flask WTForm of the TOO Scheduler Page.

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: May 19, 2025

"""
from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField

from cus_app.extensions import db
from cus_app.models import User
from sqlalchemy import select
from calendar import month_name
from datetime import datetime

#
# --- Define globals for form
#
_TOO_USERS = db.session.execute(select(User).where(User.groups.like('%too%'))).scalars().all()
_USER_CHOICE = [(None, 'TBD')] + [(user.id, user.full_name) for user in _TOO_USERS]
#: Iterated over to match
_MONTH_CHOICE = [(name, name) for name in list(month_name[1:])]
_DAY_CHOICE = [(f"{i:>02}", f"{i:>02}") for i in range(1,32)]
_YEAR_CHOICE = [(str(i),str(i)) for i in range(datetime.now().year - 1, datetime.now().year + 3)]

class ScheduleRow(FlaskForm):
    """
    To make use of pairing form actions to a schedule entry id,
    we will only use one form per time period entry, and depending on whether a person is 
    signed up for the period or not will impact which form fields are rendered.

    :Note: No field is rendered in the schedule page if the time period has already passed.
    """
    #: Rendered if a user is not assigned for a time period entry
    user = SelectField("Contact", choices=_USER_CHOICE)
    start_month = SelectField("Month", choices=_MONTH_CHOICE)
    start_day = SelectField("Date", choices=_DAY_CHOICE)
    start_year = SelectField("Year", choices=_YEAR_CHOICE)
    stop_month = SelectField("Month", choices=_MONTH_CHOICE)
    stop_day = SelectField("Date", choices=_DAY_CHOICE)
    stop_year = SelectField("Year", choices=_YEAR_CHOICE)
    update = SubmitField("Update")
    split = SubmitField("Split")
    delete = SubmitField("Delete")
    #: Rendered if a user is assigned to the time period entry
    unlock = SubmitField("Unlock")