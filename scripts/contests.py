from functools import partial
import pandas as pd
import os
import re
# cruncher imports
from .parsers import get_parser_dict
from .rcv_variants import get_rcv_dict

# read functions in parsers and rcv_variants
rcv_dict = get_rcv_dict()
parser_dict = get_parser_dict()

# ensure name uniqueness and merge
if [key for key in rcv_dict.keys() if key in parser_dict.keys()]:
    print("an rcv variant class and a parser function share the same name. Make them unique.")
    raise RuntimeError
eval_dict = rcv_dict.update(parser_dict)

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
    if s in eval_dict:
        return eval_dict[s]
    else:
        print(s + " is neither an rcv class or parser function.")
        raise RuntimeError

# other helpers
def dop(ctx):
    return ','.join([ctx['date'], ctx['office'], ctx['place']])

def unique_id(ctx):

    pieces = [ctx['place'], ctx['date'], ctx['office'], ctx['contest']]
    cleaned_pieces = [re.sub('[^0-9a-zA-Z_]+', '', x) for x in pieces]

    return "__".join(cleaned_pieces)

# primary function
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
