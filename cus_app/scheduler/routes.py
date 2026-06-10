"""
TOO Schedule Page
==============

**scheduler/routes.py**: Render the TOO Duty scheduler page.

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: May 19, 2025

"""
from flask import render_template, request, redirect, url_for

from . import bp
from .forms import ScheduleRow
from ..supple import database_interface as dbi


@bp.route('/',      methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    """
    Display the TOO scheduler page.
    """
    #: Process POST request before displaying schedule data
    if request.method == 'POST':
        #
        # --- Only one submit button will be present per request, so iterate and find it
        #
        form_dict = request.form.to_dict()
        for k,v in form_dict.items():
            if 'Unlock' in v:
                schedule_id = k.split('-')[0]
                #: Unlock requested. Following the PRG design pattern, perform redirect then come back.
                return redirect(url_for('scheduler.unlock', schedule_id = schedule_id))
            if 'Update' in v:
                schedule_id = k.split('-')[0]
                user_id = form_dict[f'{schedule_id}-user']
                #: Cannot record the start and stop strings in the url as back slashes since the browser interprets that as a different page.
                start_string = form_dict[f"{schedule_id}-start_month"] + "-" + form_dict[f"{schedule_id}-start_day"] + "-" + form_dict[f"{schedule_id}-start_year"]
                stop_string = form_dict[f"{schedule_id}-stop_month"] + "-" + form_dict[f"{schedule_id}-stop_day"] + "-" + form_dict[f"{schedule_id}-stop_year"]
                #: Update requested. Following the PRG design pattern, perform redirect then come back.
                return redirect(url_for('scheduler.update', schedule_id = schedule_id, user_id = user_id, start_string = start_string, stop_string = stop_string))
            if 'Split' in v:
                schedule_id = k.split('-')[0]
                return redirect(url_for('scheduler.split', schedule_id = schedule_id))
            if 'Delete' in v:
                schedule_id = k.split('-')[0]
                return redirect(url_for('scheduler.delete', schedule_id = schedule_id))


    schedule_list = dbi.pull_schedule()
    schedule_forms = []
    for entry in schedule_list:
        form = ScheduleRow(formdata=None, **prep_form(entry)) #:Set form data to None so that undesirable selections are ignored.
        schedule_forms.append(form)
    return render_template('scheduler/index.html',
                           schedule_list = schedule_list,
                           schedule_forms = schedule_forms
                           )


@bp.route('/unlock/<schedule_id>', methods=['GET'])
def unlock(schedule_id):
    """
    PRG page for clearing a time period of its assigned user.
    """
    dbi.unlock_schedule_entry(schedule_id = schedule_id)
    return redirect(url_for('scheduler.index'))

@bp.route('/update/<schedule_id>/<user_id>/<start_string>/<stop_string>', methods=['GET'])
def update(schedule_id, user_id, start_string, stop_string):
    """
    PRG page for updating a time period entry
    """
    dbi.update_schedule_entry(schedule_id, user_id, start_string, stop_string)
    return redirect(url_for('scheduler.index'))

@bp.route('/split/<schedule_id>', methods=['GET'])
def split(schedule_id):
    """
    PRG page for creating a new time period entry with a smaller time duration.
    """
    dbi.split_schedule_entry(schedule_id)
    return redirect(url_for('scheduler.index'))

@bp.route('/delete/<schedule_id>', methods=['GET'])
def delete(schedule_id):
    """
    PRG page for deleting a time period entry and offloading its scheduling time onto unlocked time entries.
    """
    dbi.delete_schedule_entry(schedule_id)
    return redirect(url_for('scheduler.index'))

def prep_form(entry):
    """
    Prepare form starting data for the particular entry
    """
    kwarg = {'prefix': str(entry.id)}
    data = {'user': entry.user_id,
            'start_month': entry.start.strftime('%B'),
            'start_day': entry.start.strftime('%d'),
            'start_year': entry.start.strftime('%Y'),
            'stop_month': entry.stop.strftime('%B'),
            'stop_day': entry.stop.strftime('%d'),
            'stop_year': entry.stop.strftime('%Y'),
            }
    kwarg['data'] = data
    return kwarg

