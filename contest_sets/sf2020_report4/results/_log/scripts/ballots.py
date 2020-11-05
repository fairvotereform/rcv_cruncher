from copy import deepcopy
import os
from gmpy2 import mpq as Fraction

from scripts.cache_helpers import save
from scripts.definitions import merge_writeIns, SKIPPEDRANK, OVERVOTE, WRITEIN
from rcv_parsers.parsers import common_csv

global COMMON_CVR_DIR

def set_cvr_dir(d):
    global COMMON_CVR_DIR
    COMMON_CVR_DIR = d

def cvr(ctx):
    """
    If existing common csv exists, use it. Otherwise run parser.
    """
    global COMMON_CVR_DIR
    if os.path.isfile(COMMON_CVR_DIR + '/' + ctx['dop'] + '.csv'):
        return common_csv(ctx, COMMON_CVR_DIR)
    else:
        return ctx['parser'](ctx)

@save
def ballots(ctx):
    """
    Return parser results for contest.
    Ballots are returned in a dictionary:

    ballot_ranks - can contain candidate name, or OVERVOTE, WRITEIN, or SKIPPEDRANK constants

    {
    'ranks' - list of marks,
    'weight' - (default 1) weight given to ballot,
    ...
    ... any other fields
    }
    """
    res = cvr(ctx)

    if isinstance(res, list):
        return {'ranks': res,
                'weight': [Fraction(1) for b in res]}
    else:
        if 'ranks' not in res or 'weight' not in res:
            print('ballot dict is not properly formatted. debug')
            exit(1)

    return res


@save
def ballots_writeIns_merged(ctx):
    """
    Return ballots dict with all writeIn candidates merged together.
    """
    ballot_dict = deepcopy(ballots(ctx))
    ballot_dict['ranks'] = [merge_writeIns(b) for b in ballot_dict['ranks']]
    return ballot_dict


@save
def cleaned(ctx):
    """
        For each ballot, return a cleaned version that has pre-skipped
        skipped and overvoted rankings and only includes one ranking
        per candidate (the highest ranking for that candidate).

        Additionally, each ballot may be cut short depending on the
        -break_on_repeated_skipvotes- and -break_on_overvote- settings for
        a contest.
    """

    # get ballots
    ballot_dict = deepcopy(ballots(ctx))

    new = []
    for b in ballot_dict['ranks']:
        result = []
        # look at successive pairs of rankings - zip list with itself offset by 1
        for elem_a, elem_b in zip(b, b[1:]+[None]):
            if ctx['break_on_repeated_skipvotes'] and {elem_a, elem_b} == {SKIPPEDRANK}:
                break
            if ctx['break_on_overvote'] and elem_a == OVERVOTE:
                break
            if elem_a not in [*result, OVERVOTE, SKIPPEDRANK]:
                result.append(elem_a)

        # if ctx['ignore_writeins']:
        #     result = [i for i in result if "write" not in i.lower()]

        new.append(result)

    ballot_dict['ranks'] = new
    return ballot_dict


@save
def cleaned_writeIns_merged(ctx):
    """
    Return ballots dict with all writeIn candidates merged together.
    """
    # get ballots
    ballot_dict = deepcopy(ballots_writeIns_merged(ctx))

    new = []
    for b in ballot_dict['ranks']:
        result = []
        # look at successive pairs of rankings - zip list with itself offset by 1
        for elem_a, elem_b in zip(b, b[1:]+[None]):
            if ctx['break_on_repeated_skipvotes'] and {elem_a, elem_b} == {SKIPPEDRANK}:
                break
            if ctx['break_on_overvote'] and elem_a == OVERVOTE:
                break
            if elem_a not in [*result, OVERVOTE, SKIPPEDRANK]:
                result.append(elem_a)

        # if ctx['ignore_writeins']:
        #     result = [i for i in result if "write" not in i.lower()]

        new.append(result)

    ballot_dict['ranks'] = new
    return ballot_dict


@save
def candidates(ctx):
    cans = set()
    for b in ballots(ctx)['ranks']:
        cans.update(b)
    return cans - {OVERVOTE, SKIPPEDRANK}


@save
def candidates_merged_writeIns(ctx):
    cands = set(merge_writeIns(candidates(ctx)))
    writeins = [cand for cand in cands if 'writein' in cand.lower()]
    if len(writeins) > 1:
        print('more than one write remaining after merge. debug')
        exit(1)
    return cands


@save
def candidates_no_writeIns(ctx):
    return candidates_merged_writeIns(ctx) - {WRITEIN}