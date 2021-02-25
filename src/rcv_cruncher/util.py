import decimal
import functools
import os
import pathlib

import pandas as pd

###############################################################
# constants

NAN = decimal.Decimal('NaN')


class BallotMarks():
    SKIPPEDRANK = "skipped"
    OVERVOTE = "overvote"
    WRITEIN = "writein"


class InactiveType():
    UNDERVOTE = "undervote"
    PRETALLY_EXHAUST = "pretally_exhaust"
    NOT_EXHAUSTED = "not_exhausted"
    POSTTALLY_EXHAUSTED_BY_RANK_LIMIT = "posttally_exhausted_by_rank_limit"
    POSTTALLY_EXHAUSTED_BY_ABSTENTION = "posttally_exhausted_by_abstention"
    POSTTALLY_EXHAUSTED_BY_OVERVOTE = "posttally_exhausted_by_overvote"
    POSTTALLY_EXHAUSTED_BY_REPEATED_SKIPVOTE = "posttally_exhausted_by_repeated_skipvote"
    POSTTALLY_EXHAUSTED_BY_DUPLICATE_RANKING = "posttally_exhausted_by_duplicate_ranking"

########################
# helper funcs


def before(victor, loser, ballot):
    """
        Used to calculate condorcet stats. Each ballot passed through this
        function gets mapped to either
        1 (winner ranked before loser),
        0 (neither appear on ballot),
        or -1 (loser ranked before winner).
    """
    for rank in ballot:
        if rank == victor:
            return 1
        if rank == loser:
            return -1
    return 0


def remove(x, lst):
    # removes all x from list l
    return [i for i in lst if i != x]


def keep(x, lst):
    # keeps only all x in list l
    return [i for i in lst if i in x]


def isInf(x):
    # checks if x is inf
    return x == float('inf')


def index_inf(lst, el):
    # return element index if in list, inf otherwise
    if el in lst:
        return lst.index(el)
    else:
        return float('inf')


def replace(target, replacement, lst):
    # return a list with all instances of 'target' set to 'replacement'
    return [replacement if i == target else i for i in lst]


def merge_writeIns(b):
    return [BallotMarks.WRITEIN if 'write' in i.lower() or 'uwi' in i.lower() else i for i in b]


def verifyDir(dir_path, make_if_missing=True, error_msg_tail='is not an existing folder'):
    """
    Check that a directory exists and if missing, either error or create it.

    :param dir_path: directory path to verify
    :param make_if_missing: if True, create directory if missing
    :param error_msg_tail: if make_if_missing is False and directory missing,
     print this error message after the dir_path.
    """
    if os.path.isdir(dir_path) is False:
        if make_if_missing:
            os.mkdir(longname(dir_path))
        else:
            print(dir_path + ' ' + error_msg_tail)
            raise RuntimeError


def flatten_list(lst):
    return [i for sublist in lst for i in sublist]


def project_root():
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    if '/' in dname:
        return "/".join(dname.split("/")[:-1])
    if '\\' in dname:
        return "\\".join(dname.split("\\")[:-1])


def remove_dup(lst):
    x = []
    for i in lst:
        if i not in x:
            x.append(i)
    return x


def decimal2float(stat, round_places=3):
    """Convert any decimal objects used internally into float for reporting.

    Args:
        stat (any): Any value.

    Returns:
        any type not Decimal: If the stat passed is type Decimal, it is converted to float.
    """

    if isinstance(stat, decimal.Decimal):
        return round(float(stat), round_places)
    else:
        return stat


def tmpsave(f):
    """
        decorator used to stash function results in the ctx object. Future calls
        retrieve the stashed value instead of recomputing the actual function
    """
    @functools.wraps(f)
    def fun(ctx):
        if f.__name__ in ctx:
            return ctx[f.__name__]
        return ctx.setdefault(f.__name__, f(ctx))

    return fun


def DL2LD(dl):
    return [dict(zip(dl, t)) for t in zip(*dl.values())]
    #return pd.DataFrame(dl).to_dict('records')


def LD2DL(ld):
    # assumes all dicts have same keys, which they should in these use cases
    return {k: [dic[k] for dic in ld] for k in ld[0]}
    #return pd.DataFrame(ld).to_dict('list')


def longname(path):
    return pathlib.Path('\\\\?\\' + os.fspath(path.resolve()))

