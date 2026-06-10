"""
Parameter Check Page
==============

**chkupdata/routes.py**: Render the parameter Check Page

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: May 13, 2025

"""
import os
import json
from flask import render_template, request, redirect, url_for, flash

from . import bp
from .forms import ObsidRevForm
from ..supple import database_interface as dbi
from ..supple import read_ocat_data as rod
from ..supple.helper_functions import reorient_rank , rank_ordr, coerce, OCAT_DATETIME_FORMAT

stat_dir =  os.path.join(os.path.dirname(os.path.abspath(__file__)),'..', 'static')
with open(os.path.join(stat_dir, 'labels.json')) as f:
    _LABELS = json.load(f)
with open(os.path.join(stat_dir, 'parameter_selections.json')) as f:
    _PARAM_SELECTIONS = json.load(f)

_FLAG_RANK_COLUMN_ORDR = (
    ('window_flag', 'time_ranks', 'time_columns', 'time_ordr'),
    ('roll_flag', 'roll_ranks', 'roll_columns', 'roll_ordr'),
    ('spwindow_flag', 'window_ranks', 'window_columns', 'window_ordr')
)

@bp.route('/<obsidrev>', methods=['GET'])
@bp.route('/index/<obsidrev>', methods=['GET'])
def index(obsidrev):
    """
    Display the Target Parameter Status Page
    """
    try:
        obsid, rev = [int(x) for x in obsidrev.split('.')]
    except (ValueError, TypeError):
        flash(f"Ill-formatted Obsid.Rev. {obsidrev}")
        return redirect(url_for('chkupdata.provide_obsidrev'))
    
    revision_list = dbi.pull_revision(order_by={'revision_number': 'asc'}, obsid = obsid)
    #: Pop out the revision we are interested in, then use the rest to construct related links for the webpage.
    revision = None
    for i in range(len(revision_list)):
        if revision_list[i].revision_number == rev:
            revision = revision_list.pop(i)
            break
    if revision is None and revision_list == []:
        flash(f"No revisions found for obsid = {obsid}.")
        return redirect(url_for('chkupdata.provide_obsidrev'))
    elif revision is None and revision_list != []:
        flash(f"Could not find obsid.rev = {obsidrev}. Returning most recent revision instead.")
        revision = revision_list.pop(-1)
    other_rev = {f"{r.obsid}.{r.revision_number:>03}" : url_for('chkupdata.index',obsidrev= f"{r.obsid}.{r.revision_number:>03}") for r in revision_list}
    #
    # --- Fetch state information of this obsid
    #
    ocat_data = coerce(rod.read_ocat_data(obsid), output_time_format=OCAT_DATETIME_FORMAT)
    #: If the obsid has rank-order parameters, then it would be in records orientation.
    ocat_data.update({'time_ordr': rank_ordr(ocat_data.get('time_ranks')),
                      'roll_ordr': rank_ordr(ocat_data.get('roll_ranks')),
                      'window_ordr': rank_ordr(ocat_data.get('window_ranks'))})
    
    originals = revision.original
    if revision.kind == 'norm':
        requests = revision.request
    else:
        requests = [] #: If revision wasn't norm this would be the fetch result regardless, but assigning it on the python side is quicker
    org_dict = {}
    for org in originals:
        org_dict[org.parameter.name] = coerce(json.loads(org.value), output_time_format=OCAT_DATETIME_FORMAT)
    req_dict = {}
    for req in requests:
        req_dict[req.parameter.name] = coerce(json.loads(req.value), output_time_format=OCAT_DATETIME_FORMAT)
    #: Add record-orientation of rank information if present

    for flag, rank_name, columns, order in _FLAG_RANK_COLUMN_ORDR:
        org_records, req_records = generate_ranks_display(flag, rank_name, columns, order, org_dict, req_dict)
        org_dict.update(org_records)
        req_dict.update(req_records)

    #: Add unchanging ocat information from the ocat to the original state record so that the display indicates information without indicating an impossible change
    compare_but_uneditable = {}
    for param in _PARAM_SELECTIONS['compare_but_uneditable']:
        compare_but_uneditable[param] = ocat_data.get(param)
    org_dict.update(compare_but_uneditable)

    return render_template('chkupdata/index.html',
                           revision = revision,
                           ocat_data = ocat_data,
                           org_dict = org_dict,
                           req_dict = req_dict,
                           other_rev = other_rev,
                           _LABELS = _LABELS,
                           _PARAM_SELECTIONS = _PARAM_SELECTIONS
                           )

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def provide_obsidrev():
    """
    If the provided obsid.rev is not present in the Usint revision database, display this page to input the correct obsid.rev
    """
    obsidrev_form = ObsidRevForm(request.form)
    if request.method == "POST" and obsidrev_form.is_submitted():
        return redirect(url_for('chkupdata.index', obsidrev = obsidrev_form.obsidrev.data))
    return render_template('chkupdata/provide_obsidrev.html',
                           obsidrev_form = obsidrev_form
                           )

def generate_ranks_display(flag, rank_name, columns, order, org_dict, req_dict):
    """
    Generate the rank-order displays based on the state of original or requested information.
    Note that this algorithm is based on the axiom that the originals table records the non-null rank information as individual columns,
    and that the request table records the desired create, changed, or nullified variables.

    Output is a formatted copy of the rank-ordered parameters in records orientation.
    Then in the chkupdata page, we iterate over these formatted copies with the records orientation of ocat_data in order to display the full change.
    """
    if flag in req_dict.keys():
        #: Change case
        if org_dict.get(flag) in ('Y', 'P') and req_dict.get(flag) in ('N', None):
            #: Nullification of originally present data.
            org_collection = reorient_rank({k: org_dict.get(k) for k in _PARAM_SELECTIONS[columns]}, 'records')
            req_collection = None
        elif org_dict.get(flag) in ('N', None) and req_dict.get(flag) in ('Y', 'P'):
            #: Creation of rank-ordered values
            org_collection = None
            req_collection = reorient_rank({k: req_dict.get(k) for k in _PARAM_SELECTIONS[columns]}, 'records')
    else:
        #: No flag change, so either nothing or a change to existing data.
        if org_dict.get(flag) in ('N', None):
            #: Still Null
            org_collection = None
            req_collection = None
        else:
            #: Original state contains data, and request might contain data.
            org_collection = {}
            req_collection = {}
            for col in _PARAM_SELECTIONS[columns]:
                original_column = org_dict.get(col)
                request_column = req_dict.get(col)
                #: If not present in the request, then retain the original column
                if request_column is None:
                    request_column = original_column
                org_collection[col] = original_column
                req_collection[col] = request_column
            org_collection = reorient_rank(org_collection, 'records')
            req_collection = reorient_rank(req_collection, 'records')
    
    return {order: rank_ordr(org_collection), rank_name: org_collection}, {order: rank_ordr(req_collection), rank_name: req_collection}