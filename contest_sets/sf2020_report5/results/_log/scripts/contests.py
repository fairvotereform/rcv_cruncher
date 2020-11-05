# cruncher imports
from functools import partial
from .definitions import verifyDir
from rcv_parsers.parsers import *
from .rcv_variants import *

# read functions in parsers and rcv_variants
rcv_dict = get_rcv_dict()
parser_dict = get_parser_dict()

# ensure name uniqueness and merge
if [key for key in rcv_dict.keys() if key in parser_dict.keys()]:
    print("an rcv variant class and a parser function share the same name. Make them unique.")
    raise RuntimeError

def dummy(*args):
    pass

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
    try:
        return eval(s)
    except:
        return dummy

# other helpers
def dop(ctx):
    return '_'.join([ctx['year'], ctx['place'], ctx['office']])

def unique_id(ctx):
    filled_date = "/".join([piece if len(piece) > 1 else "0" + piece for piece in ctx['date'].split("/")])
    pieces = [ctx['place'], filled_date, ctx['office']]
    cleaned_pieces = [re.sub('[^0-9a-zA-Z_]+', '', x) for x in pieces]
    return "_".join(cleaned_pieces)

# primary function
def load_contest_set(contest_set_path, path_prefix=""):

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
    cols_in_order = contest_set_df.columns

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
        d['contest_set_line_df'] = pd.DataFrame([[d[col] for col in cols_in_order]], columns=cols_in_order)
        if path_prefix is not "":
            d['path'] = path_prefix + "/" + d['path']

    return competitions


def read_output_config(contest_set_path):
    """
    Read the output config and return it as a dictionary
    """
    config_path = contest_set_path + '/output_config.csv'
    if os.path.isfile(config_path) is False:
        print("output_config.csv does not exist. Use new_contest_set.py to make example config file.")

    df = pd.read_csv(config_path)
    return {tabulation: to_run for tabulation, to_run in zip(df['tabulation'], df['run'])}


def new_contest_set():
    """
    Creates a new contest set directory and blank contest set csv file
    """
    # create new directory
    set_name = "contest_sets/new_contest_set"
    verifyDir(set_name)

    # create new contest set csv
    colnames = ['contest', 'place', 'state', 'date', 'year',
                'office', 'rcv_type', 'num_winners', 'break_on_overvote',
                'break_on_repeated_skipvotes', 'multi_winner_rounds', 'parser',
                'path', 'idparser', 'master_lookup', 'chp', 'candidate_map', 'state_code', 'county']
    df = pd.DataFrame(columns=colnames)
    df.to_csv(set_name + '/contest_set.csv', index=False)

    # create new output config
    tabulations = ['per_rcv_group_stats', 'per_rcv_type_stats', 'condorcet',
                   'crossover_support', 'cumulative_rankings', 'first_choice_to_finalist',
                   'first_second_choices', 'rank_usage', 'candidate_details', 'round_by_round']
    df = pd.DataFrame()
    df['tabulation'] = tabulations
    df['run'] = True
    df.to_csv(set_name + '/output_config.csv', index=False)
