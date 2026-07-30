"""
**check_values.py**: Read ocat, original, and request values to perform operational checks

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Jul 28, 2026
"""
from flask import flash
import os
import json
from ..supple.helper_functions import is_large_coord_shift, grab_latest

stat_dir =  os.path.join(os.path.dirname(os.path.abspath(__file__)),'..', 'static')
with open(os.path.join(stat_dir, 'labels.json')) as f:
    _LABELS = json.load(f)

def run_flash_checks(ocat_data, org_dict, req_dict):
    """
    Run all flash checks on the ocat_data, org_dict, and req_dict.

    :param ocat_data: The OCAT data to check.
    :param org_dict: The original dictionary of values.
    :param req_dict: The requested dictionary of values.
    """
    targname_flash(req_dict)
    instrument_flash(req_dict)
    grating_flash(req_dict)
    ra_dec_flash(org_dict, req_dict)
    frame_time_flash(org_dict, req_dict)

def targname_flash(req_dict):
    if req_dict.get('targname') is not None:
        flash('The target name was updated. MP will be notified this change.')
def instrument_flash(req_dict):
    if req_dict.get('instrument') is not None:
        flash('The instrument was updated. MP will be notified this change. <a href="https://cxc.cfa.harvard.edu/cus/InstrumentChanges.html" target="_blank">Instrument Changes Explanation.</a>')
def grating_flash(req_dict):
    if req_dict.get('grating') is not None:
        flash('The grating was updated. MP will be notified this change. <a href="https://cxc.cfa.harvard.edu/cus/InstrumentChanges.html" target="_blank">Instrument Changes Explanation.</a>')

def ra_dec_flash(org_dict, req_dict):
    if req_dict.get('ra') is not None or req_dict.get('dec') is not None:
        #: Change in the RA, DEC. Check to see if the change is too significant.
        original_ra = org_dict.get('ra')
        original_dec = org_dict.get('dec')
        #: If no requested change, use the original value for determining total change magnitude.
        latest_ra = grab_latest('ra', org_dict, req_dict)
        latest_dec = grab_latest('dec', org_dict, req_dict)
        #: Note that the originals could possible be None in a revision of a TOO to define pointing coordinates.
        #: Thus the latest ra, dec must both be defined by this point. If only one is, then flash a warning to return and fill both.
        if (latest_ra is None) ^ (latest_dec is None):
            flash("Only one of RA, DEC is defined. Must be both or neither.")
        else:
            if latest_ra < 0 or latest_ra > 360:
                flash("Value of RA is out of range. Please check the value.")
            if latest_dec < -90 or latest_dec > 90:
                flash("Value of DEC is out of range. Please check the value.")
            if is_large_coord_shift(latest_ra, latest_dec, original_ra, original_dec):
                flash("The coordinates were shifted by more than 8 arcmin.  You need CDO approval.")

def exclusivity_flash(exclusive_group, org_dict, req_dict):
    """
    If exclusive groupings of parameters are used, then flash caution.
    """
    original_exclusives = {}
    latest_exclusives = {}
    for param in exclusive_group:
        original_exclusives[param] = org_dict.get(param)
        latest_exclusives[param] = grab_latest(param, org_dict, req_dict)
    
    #: Should only be one non-null parameter in the latest set of exclusives.
    non_null_count = sum(v is not None for v in latest_exclusives.values())
    if non_null_count > 1:
        #: More that one null value.
        flash(f"Only one of the following parameters can be non-null: {[_LABELS.get(_) for _ in exclusive_group]}")
    elif non_null_count == 0:
        #: All null values
        flash(f"One of the following parameters must be non-null: {[_LABELS.get(_) for _ in exclusive_group]}")

def frame_time_flash(org_dict, req_dict):
    lastest_instrument = grab_latest('instrument', org_dict, req_dict)
    if lastest_instrument.startswith('ACIS'):
        exclusivity_flash(['frame_time', 'most_efficient'], org_dict, req_dict)
    

def hrc_si_flash(org_dict, req_dict):
    lastest_instrument = grab_latest('instrument', org_dict, req_dict)
    if lastest_instrument.startswith('HRC'):
        latest_hrc_si_mode = grab_latest('hrc_si_mode', org_dict, req_dict)
        if latest_hrc_si_mode is None:
            flash("HRC SI Mode is not provided.")

def flag_change_flash(req_dict):
    for flag in ('dither_flag', 'window_flag', 'roll_flag', 'spwindow_flag'):
        flash(f"{_LABELS.get(flag)} was updated, impacting constraints. CDO must approve this change. If approved already, indicate in the comment section.")