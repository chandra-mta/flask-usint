"""
**check_values.py**: Read ocat, original, and request values to perform operational checks

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Jul 28, 2026
"""
from flask import flash
from ..supple.helper_functions import is_large_coord_shift

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
        latest_ra = req_dict.get('ra') or original_ra
        latest_dec = req_dict.get('dec') or original_dec
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

def exclusivity_flash(org_dict, req_dict):
    