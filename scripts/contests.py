
from functools import partial
import pandas as pd
import os
import re

# cruncher imports
from .cache_helpers import tmpsave
from .parsers import santafe, santafe_id, maine, minneapolis, \
    sf, sfnoid, old, prm, burlington, sf2019, utah, ep


##########################
# getter function that exist only for the function list in the cruncher
# much simpler to access ctx dictionary directly

def contest_name(ctx):
    return ctx['contest']

def place(ctx):
    return ctx['place']

def state(ctx):
    return ctx['state']

def date(ctx):
    return ctx['date']

def office(ctx):
    return ctx['office']

@tmpsave
def dop(ctx):
    return ','.join(str(f(ctx)) for f in [date, office, place])

@tmpsave
def unique_id(ctx):

    pieces = [ctx['place'],  ctx['date'], ctx['office'], ctx['contest']]
    cleaned_pieces = [re.sub('[^0-9a-zA-Z_]+', '', x) for x in pieces]

    return "__".join(cleaned_pieces)

def contest_func_list():
    return [contest_name, place, state, date, office, unique_id]

#########################

# typecast functions

def cast_str(s):
    """
    If string-in-string '"0006"', evaluate to '0006'
    If 'None', return None (since this string cannot be evaluated)
    else, return str() result
    """
    if (s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'"):
        return eval(s)
    elif s == 'None':
        return None
    else:
        return str(s)

def cast_int(s):
    return int(s)

def cast_bool(s):
    return eval(s.title())

def cast_func(s):
    return eval(s)

def load_manifest(cruncher_path):

    ##########################
    # verify path
    if os.path.isdir(cruncher_path) is False:
        print("not a valid file path: " + cruncher_path)
        exit(1)


    # assemble typecast funcs
    cast_dict = {'str': cast_str, 'int': cast_int,
                 'bool': cast_bool, 'func': cast_func}


    ##########################
    # defaults

    # read in manifest default values
    manifest_defaults_fpath = cruncher_path + '/manifest_key.csv'
    manifest_defaults_df = pd.read_csv(manifest_defaults_fpath, skiprows=1)

    # create default dict
    defaults = {}
    for index, row in manifest_defaults_df.iterrows():
        defaults[row['field']] = {'type': row['typecast'], 'default': row['default']}


    ##########################
    # manifest

    # read in manifest
    manifest_fpath = cruncher_path + '/manifest.csv'
    manifest_df = pd.read_csv(manifest_fpath, dtype=object)

    # fill in na values with defaults and evaluate column, if indicated
    for col in manifest_df:
        manifest_df[col] = manifest_df[col].fillna(defaults[col]['default'])
        manifest_df[col] = [cast_dict[defaults[col]['type']](i) for i in manifest_df[col].tolist()]

    # convert df to listOdicts, one dict per row
    competitions = manifest_df.to_dict('records')

    # add dop, unique_id
    for d in competitions:
        d['dop'] = dop(d)
        d['unique_id'] = unique_id(d)

    return competitions
