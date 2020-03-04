from functools import partial
import pandas as pd
import os
import re

# cruncher imports
from .cache_helpers import tmpsave
from .parsers import santafe, santafe_id, maine, minneapolis, \
    sf, sfnoid, old, prm, burlington, sf2019, utah, ep, dominion5_10
from .tabulation import rcv_single_winner, stv_fractional_ballot, \
    stv_whole_ballot, sequential_rcv, rcv_multiWinner_thresh15, until2rcv


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

def rcv_type(ctx):
    return ctx['rcv_type'].__name__

def num_winners(ctx):
    return ctx['num_winners']

@tmpsave
def dop(ctx):
    return ','.join(str(f(ctx)) for f in [date, office, place])

@tmpsave
def unique_id(ctx):

    pieces = [ctx['place'], ctx['date'], ctx['office'], ctx['contest']]
    cleaned_pieces = [re.sub('[^0-9a-zA-Z_]+', '', x) for x in pieces]

    return "__".join(cleaned_pieces)

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

def load_contest_set(contest_set_path):

    ##########################
    # verify paths
    contest_set_defaults_fpath = contest_set_path + '/../contest_set_key.csv'
    contest_set_fpath = contest_set_path + '/contest_set.csv'

    if os.path.isfile(contest_set_defaults_fpath) is False:
        print("not a valid file path: " + contest_set_defaults_fpath)
        exit(1)

    if os.path.isfile(contest_set_fpath) is False:
        print("not a valid file path: " + contest_set_fpath)
        exit(1)

    # assemble typecast funcs
    cast_dict = {'str': cast_str, 'int': cast_int,
                 'bool': cast_bool, 'func': cast_func}

    ##########################
    # defaults

    # read in contest set default values
    contest_set_defaults_df = pd.read_csv(contest_set_defaults_fpath, skiprows=1)

    # create default dict
    defaults = {}
    for index, row in contest_set_defaults_df.iterrows():
        defaults[row['field']] = {'type': row['typecast'], 'default': row['default']}

    ##########################
    # contest set

    # read in contest set
    contest_set_df = pd.read_csv(contest_set_fpath, dtype=object)

    # fill in na values with defaults and evaluate column, if indicated
    for col in contest_set_df:
        contest_set_df[col] = contest_set_df[col].fillna(defaults[col]['default'])
        contest_set_df[col] = [cast_dict[defaults[col]['type']](i) for i in contest_set_df[col].tolist()]

    # convert df to listOdicts, one dict per row
    competitions = contest_set_df.to_dict('records')

    # add dop, unique_id
    for d in competitions:
        d['dop'] = dop(d)
        d['unique_id'] = unique_id(d)

    return competitions
