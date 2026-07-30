"""
**helper_functions.py**: Common functions used throughout the Usint application

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Apr 28, 2025


:NOTE: Rank-ordered parameters are oriented in the usint Flask Application in one of two ways, depending on the desired purpose.

- records orientation: a list of ordered dictionaries in which each dictionary has a column-key and value matching the rank parameters
    [{'window_constraint': 'Y',
    'tstart': 'Jan 01 2024 12:00AM',
    'tstop': 'Dec 31 2024 12:00AM'},
    {'window_constraint': 'Y',
    'tstart': 'Jan 01 2025 12:00AM',
    'tstop': 'Dec 31 2025 12:00AM'}]

- columns orientation: a dictionary of ordered lists where each key-column in the dictionary matches the rank parameters
    {'window_constraint': ['Y', 'Y'],
    'tstart': ['Jan 01 2024 12:00AM', 'Jan 01 2025 12:00AM'],
    'tstop': ['Dec 31 2024 12:00AM', 'Dec 31 2025 12:00AM']}

"""
import os
import re
import json
import itertools
from math import sqrt
from datetime import datetime, timedelta
import astropy.table
from astropy.coordinates import Angle
from flask import current_app
#
# --- Classes
#
class IterateRecords:
    """Iterating through a set of records-oriented objects"""
    def __init__(self,*args):
        self.list_set = []
        self.num_lists = len(args)
        for arg in args:
            if not isinstance(arg,list):
                self.list_set.append([])
            else:
                self.list_set.append(arg)
        self.top_level_iterator = enumerate(itertools.zip_longest(*self.list_set,fillvalue={}))
        _ = next(self.top_level_iterator)
        self.order = _[0]
        self.keys = set()
        for i in _[1]:
            self.keys = self.keys.union(set(i.keys()))
        #: Iterate over the keys in the record
        self.inner_iterator = iter(self.keys)
        self.inner_level = _[1]
    
    def __iter__(self):
        return self

    
    def __next__(self):
        try:
            curr_param = next(self.inner_iterator)
            curr_values = [x.get(curr_param) for x in self.inner_level]
            return self.order, curr_param, tuple(curr_values)
        except StopIteration:
            _ = next(self.top_level_iterator)
            self.order = _[0]
            self.keys = set()
            for i in _[1]:
                self.keys = self.keys.union(set(i.keys()))
            #: Iterate over the keys in the record
            self.inner_iterator = iter(self.keys)
            self.inner_level = _[1]
            
        return self.__next__()

class IterateColumns:
    """Iterating through a columns-oriented objects"""
    
    @staticmethod
    def get_col(obj,key):
        if obj is None:
            return []
        else:
            return obj.get(key) or []
    
    def __init__(self,*args):
        self.dict_set = []
        self.num_dict = len(args)
        for arg in args:
            if not isinstance(arg,dict):
                self.dict_set.append({})
            else:
                self.dict_set.append(arg)
        self.keys = set()
        for i in self.dict_set:
            self.keys = self.keys.union(set(i.keys()))

        self.top_level_iterator = iter(self.keys)
        _ = next(self.top_level_iterator)
        self.parameter = _
        self.inner_level = [self.get_col(x,_) for x in self.dict_set]
        self.inner_iterator = enumerate(itertools.zip_longest(*self.inner_level,fillvalue=None))
        
    def __iter__(self):
        return self
    
    def __next__(self):
        try:
            ordr, curr_values = next(self.inner_iterator)
            return ordr, self.parameter, tuple(curr_values)
        except StopIteration:
            _ = next(self.top_level_iterator)
        self.parameter = _
        self.inner_level = [self.get_col(x,_) for x in self.dict_set]
        self.inner_iterator = enumerate(itertools.zip_longest(*self.inner_level,fillvalue=None))
        return self.__next__()

#
# --- Globals
#
NULL_LIST = [None,'',' ','<Blank>','N/A','NA','NONE','NULL','Na','None','Null','none','null']
OCAT_DATETIME_FORMAT = "%b %d %Y %I:%M%p" #: Warning Ocat Datetimes are stored without a leading zero in the day. This can cause python comparisons to fail
USINT_DATETIME_FORMAT = "%b %d %Y %H:%M"
STORAGE_FORMAT = '%Y-%m-%dT%H:%M:%SZ' #: ISO 8601 format. Used in storage for Usint SQL Database
DATETIME_FORMATS = [USINT_DATETIME_FORMAT, OCAT_DATETIME_FORMAT, STORAGE_FORMAT, '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M','%m:%d:%Y:%H:%M:%S', '%m:%d:%Y:%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M',]

#
# --- Parameter selection for time, roll, and window ranks
#
TIME_RANK_PARAMS = {'window_constraint', 'tstart', 'tstop'}
ROLL_RANK_PARAMS = {'roll_constraint', 'roll_180', 'roll', 'roll_tolerance'}
WINDOW_RANK_PARAMS = {'chip', 'start_row', 'start_column', 'width', 'height', 'lower_threshold', 'pha_range', 'sample'}
ALL_RANK_PARAMS = TIME_RANK_PARAMS.union(ROLL_RANK_PARAMS).union(WINDOW_RANK_PARAMS)
_SIGNOFF_COLUMNS = ('general', 'acis', 'acis_si', 'hrc_si', 'usint') #: Prefix names for the columns of Signoff

#
# --- Coercion section. Converting values to the correct data types.
#
def coerce_none(val):
    """
    Recursive function to convert containers of NULL_LIST values into the Python native None.
    """
    if isinstance(val, (list, tuple)):
        return [coerce_none(x) for x in val]
    elif isinstance(val, dict):
        return {k:coerce_none(v) for k,v in val.items()}
    elif val in NULL_LIST:
        return None
    return val

def coerce_number(val):
    """
    Perform conversion of a numerical data object to a python native integer or float.
    """
    if not isinstance(val,(int,float)):
        try:
            val = int(val)
        except (ValueError, TypeError):
            try:
                val = float(val)
            except (ValueError, TypeError):
                pass
    return val

def coerce_time(val, output_time_format = STORAGE_FORMAT):
    """
    Parse a variety of different time formats across CXC tools and data sources into the output time format
    """
    if isinstance(val, str):
        x = val.replace('::', ':')
        x = x.split('.')[0]
        for format in DATETIME_FORMATS:
            try:
                return datetime.strptime(x,format).strftime(output_time_format)
            except ValueError:
                pass
    return val

def coerce_to_json(val):
    """
    Coercion of python data type to a json-formatted string for data storage
    """
    if val in NULL_LIST:
        return None
    elif isinstance(val, datetime):
        #: Convert to ISO 8601 string then store
        return json.dumps(val.strftime(STORAGE_FORMAT))
    elif isinstance(val, list):
        if len(val) > 0 and isinstance(val[0], datetime):
            return json.dumps([x.strftime(STORAGE_FORMAT) for x in val])
        else:
            return json.dumps(val)
    else:
        return json.dumps(val)

def coerce_from_json(val):
    """
    Coercion of a JSON-formatting string to a python data type.
    """
    if isinstance(val,str):
        return json.loads(val)
    else:
        return val

def coerce(val, output_time_format = STORAGE_FORMAT):
    """
    Recursive function for converting to python native data types
    """
    if isinstance(val, (list, tuple)):
        return [coerce(x, output_time_format) for x in val]
    elif isinstance(val, dict):
        return {k:coerce(v, output_time_format) for k,v in val.items()}
    #: Null section
    elif val in NULL_LIST:
        return None
    #: Number section
    val = coerce_number(val)
    if isinstance(val,(int,float)):
        return val
    #: Time section if applicable
    val = coerce_time(val, output_time_format)
    #: Regular string
    return val

#
# --- Fetching Functions
#
def get_more(obj,key):
    """
    Formatting function to add None handling to .get()
    """
    if obj is None:
        return None
    else:
        if isinstance(obj,dict):
            return obj.get(key)
        else:
            return obj[key]

def check_obsid_in_or_list(obsids_list):
    """
    check whether obsids in obsids_list are in active OR list

    :param obsid_list: a list of obsids
    :type obsid_list: list
    :return or_dict: map of obsid to boolean if in the OR list
    :rtype: dict(bool)
    """
    or_dict = {}
    with open(os.path.join(current_app.config["OBS_SS"], 'scheduled_obs_list')) as f:
        or_list = [int(line.strip().split()[0]) for line in f.readlines()]
    for obsid in obsids_list:
        if obsid in or_list:
            or_dict[obsid] = True
        else:
            or_dict[obsid] = False
    return or_dict

#
# --- Comparison Functions
#
def approx_equals(first,second):
    """
    Compare values within reason for a revision. Return True if they are close enough to equal
    """
    if first is None and second is not None:
        return False
    elif first is not None and second is None:
        return False
    elif first is None and second is None:
        return True
    elif isinstance(first, (float,int)) and isinstance(second, (float,int)):
        if abs(first - second) < 0.000001:
            return True
        else:
            return False
    elif isinstance(first,datetime) and isinstance(second,datetime):
        diff = (second - first).total_seconds()
        return diff > 60
    elif isinstance(first, list) and isinstance(second, list):
        if len(first) != len(second):
            return False
        _result = True
        for i,j in zip(first,second):
            if not approx_equals(i,j):
                _result = False
                break
        return _result
    elif isinstance(first, dict) and isinstance(second, dict):
        first_keys = set(first.keys())
        second_keys = set(second.keys())
        if first_keys != second_keys:
            return False
        _result = True
        for key in first_keys:
            if not approx_equals(first[key], second[key]):
                _result = False
                break
        return _result
    else:
        return first == second

def grab_latest(param, org_dict, req_dict):
    if param in req_dict.keys():
        #: New value deliberately requested. Possible requested to None value.
        return req_dict.get(param)
    else:
        #: No new request. Check original. If no original value, will still return None.
        return org_dict.get(param)

def construct_notes(ocat_data, org_dict, req_dict):
    """
    Construct Revision notes and format into a JSON string
    """
    notes = {}
    #
    # -- Ocat Data Specific Warnings
    #
    scheduled_obs_time = ocat_data.get('soe_st_sched_date') or ocat_data.get('lts_lt_plan')
    if scheduled_obs_time is not None:
        if (datetime.strptime(coerce_time(scheduled_obs_time), STORAGE_FORMAT) - datetime.now()).total_seconds() < 10 * 86400:
            notes.update({'obsdate_under10': True})
    or_check = check_obsid_in_or_list([ocat_data.get('obsid')])
    if or_check[ocat_data.get('obsid')]:
        notes.update({'on_or_list': True})
    #
    # --- Change Request Specific Warnings
    #
    ra = None
    dec = None
    ora = None
    odec = None
    for param, val in req_dict.items():
        if param == 'targname':
            notes.update({'target_name_change':True})
        elif param == 'comments':
            notes.update({'comment_change': True})
        elif param == 'instrument':
            notes.update({'instrument_change': True})
        elif param == 'grating':
            notes.update({'grating_change': True})
        elif param in ('dither_flag', 'window_flag', 'roll_flag', 'spwindow_flag'):
            notes.update({'flag_change': True})
        elif param == 'ra':
            ra = val
        elif param == 'dec':
            dec = val
    if ra is not None or dec is not None:
        ora = org_dict.get('ra')
        if ra is None:
            ra = ora
        odec = org_dict.get('dec')
        if dec is None:
            dec = odec
        if ora != 0 and odec != 0 and is_large_coord_shift(ra,dec, ora, odec):
                notes.update({'large_coordinate_change': True})
    
    if len(notes) > 0:
        return json.dumps(notes)
    else:
        return None

def is_large_coord_shift(ra,dec, ora, odec):
    """
    Boolean check for whether a coordinate change exceeds 8 arcminutes.
    """
    if ora is None or odec is None:
        return False #: Instance of defining a TOO coordinates location. No need to check.
    diff = sqrt((ora -ra)**2 + (odec - dec)**2)
    return diff > 0.1333
#
#--- Conversion Functions
#
def reorient_rank(ranks, orient):
    """
    Reorient a set of ranks, similar to how convert_astropy_to_native() operates.
    But this alters a set of python natives rather than an astropy table.
    
    'records' is an ordered list of ranks, each entry being a dictionary of parameter name to value for that numbered rank
    'columns' is a dictionary of parameter columns, each entry matching an ordered list of values
    """
    if ranks in (None, [], {}):
        return None
    if orient not in ('records', 'columns'):
        raise ValueError(f"Provide object orient [records, columns]. Provided orient: {orient}.")
    
    if isinstance(ranks,list) and ranks != []:
        #: Is records
        if orient == 'records':
            return ranks
        else:
            columns = {}
            for key, value in ranks[0].items():
                columns[key] = [value]
            for i in range(1,len(ranks)):
                for key, value in ranks[i].items():
                    columns[key].append(value)
        return columns
                    
    elif isinstance(ranks,dict) and ranks != {}:
        #: Is columns
        if orient == 'columns':
            return ranks
        else:
            records = []
            key_list = list(ranks.keys())
            for i in range(len(ranks[key_list[0]])):
                rec = {}
                for key in key_list:
                    rec[key] = ranks[key][i]
                records.append(rec)
        return records
    else:
        raise ValueError(f"Incompatible Rank Object: {ranks}")

def convert_row_to_dict(row):
    """convert an astropy table row into data formats expected by the application

    :param row: Sybase fetched astropy table row.
    :type row: Astropy.table.row.Row
    :returns: Formatted python dictionary
    :rtype: dict
    """
    row_dict = {col: row[col].tolist() for col in row.colnames}
    return row_dict

def convert_astropy_to_native(astropy_object, orient = None):
    """Converts an astropy object into python native objects.

    :param astropy_object: astropy object
    :type astropy_object: Table, Row, Column, ect.
    :param orient: Orientation of data Table conversion(uses pandas convention), defaults to None
    :type orient: str, optional
    """
    
    if isinstance(astropy_object, astropy.table.table.Table):
        #
        # --- Multiple possible orientations.
        # --- Similar argument to pandas dataframe for consistency but does not use pandas
        #
        if (orient == 'records') or (len(astropy_object) == 1 and orient is None):
            result = []
            for row in astropy_object:
                result.append(convert_row_to_dict(row))
            return result
        elif (orient == 'columns') or (len(astropy_object.colnames) == 1 and orient is None):
            result = {}
            for col in astropy_object.colnames:
                result[col] = astropy_object[col].tolist()
            return result
        elif len(astropy_object) == 0:
            raise ValueError("Cannot convert empty astropy table.")
        else:
            raise ValueError(f"Provide object orient [records, columns]. Provided orient: {orient}.")
            
    elif isinstance(astropy_object,astropy.table.row.Row):
        return convert_row_to_dict(astropy_object)
    
    elif isinstance(astropy_object, astropy.table.column.Column):
        return astropy_object.tolist()
    
    elif hasattr(astropy_object, 'tolist'):
        return astropy_object.tolist()
    
def create_obsid_list(list_string, obsid = None):
    """
    Create a list of obsids from form input.
    """
    if list_string is None:
        return []
    list_string = str(list_string)
    if list_string.strip() == '':
        return []
    #: Split the input string into elements
    raw_elements = [x for x in re.split(r'\s+|,|:|;', list_string) if x != '']
    
    #: Combine into string replaceable format for dash parsing
    combined = ','.join(raw_elements)
    combined = combined.replace(',-,','-').replace('-,','-').replace(',-','-')
    
    #: Process Ranges
    obsids_list = []
    for element in combined.split(','):
        if element.isdigit():
            obsids_list.append(int(element))
        else:
            start, end = element.split('-')
            obsids_list.extend(list(range(int(start), int(end) + 1)))
    
    #: Remove duplicates, sort, and exclude the main obsid if applicable
    if obsid is not None:
        obsids_list = sorted(set(obsids_list) - {int(obsid)})
    else:
        obsids_list = sorted(set(obsids_list))
    return obsids_list

#
# --- Calculative Functions
#
def convert_ra_dec_format(dra, ddec, oformat):
    """
    convert ra/dec format
    input:  dra     --- either <hh>:<mm>:<ss> or <dd.ddddd> format
            ddec    --- either <dd>:<mm>:<ss> or <ddd.ddddd> format
            oformat --- specify output format as either 'dd', or 'hmsdms'

    output: tra     --- either <hh>:<mm>:<ss> or <dd.ddddd> format
            tdec    --- either <dd>:<mm>:<ss> or <ddd.ddddd> format
    """
    if dra is None and ddec is None:
        return None, None
    #
    #--- Define input format
    #
    if ":" in str(ddec):
        iformat = 'hmsdms'
    else:
        iformat = 'dd'
    #
    #--- Switch formats
    #
    if iformat == 'dd' and oformat == 'hmsdms':
        angle_ra = Angle(f"{dra} degrees")
        tra = str(angle_ra.to_string(sep=":",pad=True,precision=4,unit='hourangle'))
        angle_dec = Angle(f"{ddec} degrees")
        tdec = str(angle_dec.to_string(sep=":",pad=True,precision=4,alwayssign=True,unit='degree'))
    elif iformat == 'hmsdms' and oformat == 'dd':
        angle_ra = Angle(f"{dra} hours")
        tra = float(angle_ra.to_string(decimal=True,precision=6,unit='degree'))
        angle_dec = Angle(f"{ddec} degrees")
        tdec = float(angle_dec.to_string(decimal=True,precision=6,unit='degree'))
    else:
        return dra, ddec
    
    return tra,tdec

def rank_ordr(ranks):
    """
    Calculate the order of a rank parameter set.
    """
    if ranks is None:
        return 0
    elif isinstance(ranks, list):
        #: records orientation
        return len(ranks)
    elif isinstance(ranks, dict):
        #: Columns orientation
        return max([len(v) for v in ranks.values()])

def is_open(signoff_obj):
    """
    Returns boolean if the signoff entry still needs a signature.
    """
    is_open = False
    for attr in _SIGNOFF_COLUMNS:
        if getattr(signoff_obj, f"{attr}_status") == 'Pending':
            is_open = True
            break
    return is_open

def contains_non_none(obj):
    """
    Function for processing a native python container and determining if non-null information is present for use.
    """
    if isinstance(obj,(list,tuple)):
        result = False
        for i in obj:
            if contains_non_none(i):
                result = True
                break
        return result
    elif isinstance(obj,dict):
        result = False
        for v in obj.values():
            if contains_non_none(v):
                result = True
                break
        return result
    elif obj is not None:
        return True
    else:
        return False
    

def get_next_weekday(weekday_num, dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)):
    """
    Returns the datetime object for the next target weekday.
    """
    days_until_target = (weekday_num - dt.weekday()) % 7
    if days_until_target == 0:
        days_until_target = 7
    target = dt + timedelta(days=days_until_target)
    return target