import copy
import decimal
import os

import rcv_cruncher.parsers as parsers
import rcv_cruncher.util as util

decimal.getcontext().prec = 30


@util.tmpsave
def cvr(ctx):
    """
    If cvr is already stored in ctx use it, else if existing common csv exists, use it. Otherwise run parser.
    """
    converted_path = ctx['contest_set_path'] / f"converted_cvr/{ctx['uid']}.csv"

    if os.path.isfile(converted_path):
        ctx['converted_path'] = converted_path
        return parsers.cruncher_csv(ctx)

    return ctx['parser'](ctx)


def input_ballots(ctx, *, combine_writeins=None):
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

    combine_writeins_flag = ctx['combine_writeins']
    if combine_writeins is not None:
        combine_writeins_flag = combine_writeins

    res = cvr(ctx)

    if isinstance(res, list):
        res = {'ranks': res,
               'weight': [decimal.Decimal('1') for b in res]}

    if 'ranks' not in res or 'weight' not in res:
        print('ballot dict is not properly formatted. debug')
        exit(1)

    if combine_writeins_flag:
        res['ranks'] = [util.merge_writeIns(b) for b in res['ranks']]

    return res


def cleaned_ballots(ctx, *, combine_writeins=None, exclude_writeins=None, treat_combined_writeins_as_duplicates=None):
    """
        For each ballot, return a cleaned version that has pre-skipped
        skipped and overvoted rankings and only includes one ranking
        per candidate (the highest ranking for that candidate).

        Additionally, each ballot may be cut short depending on the
        -exhaust_on_repeated_skipvotes- and -exhaust_on_overvote- settings for
        a contest.

        This function does not exhaust on repeated rankings in the case of combined writeins.
        Writeins are only counted as repeated rankings if they are coded the same way in the CVR,
        NOT if they are combined into the single WRITEIN constant that the combine_writeins option performs.
    """

    combine_writeins_flag = ctx['combine_writeins']
    if combine_writeins is not None:
        combine_writeins_flag = combine_writeins

    exclude_writeins_flag = ctx['skip_writeins']
    if exclude_writeins is not None:
        exclude_writeins_flag = exclude_writeins

    treat_combined_writeins_as_duplicates_flag = ctx['treat_combined_writeins_as_duplicates']
    if treat_combined_writeins_as_duplicates is not None:
        treat_combined_writeins_as_duplicates_flag = treat_combined_writeins_as_duplicates

    # get ballots
    ballot_dict = copy.deepcopy(input_ballots(ctx, combine_writeins=False))

    if combine_writeins_flag and treat_combined_writeins_as_duplicates_flag:
        ballot_dict['ranks'] = [util.merge_writeIns(b) for b in ballot_dict['ranks']]

    new = []
    for b in ballot_dict['ranks']:
        result = []
        # look at successive pairs of rankings - zip list with itself offset by 1
        for elem_a, elem_b in zip(b, b[1:]+[None]):
            if ctx['exhaust_on_repeated_skipped_rankings'] and {elem_a, elem_b} == {util.BallotMarks.SKIPPEDRANK}:
                break
            if ctx['exhaust_on_overvote'] and elem_a == util.BallotMarks.OVERVOTE:
                break
            if ctx['exhaust_on_duplicate_rankings'] and elem_a in result:
                break
            if elem_a not in [*result, util.BallotMarks.OVERVOTE, util.BallotMarks.SKIPPEDRANK]:
                result.append(elem_a)

        new.append(result)

    if combine_writeins_flag:
        new = [util.merge_writeIns(b) for b in new]
        new = [util.remove_dup(b) for b in new]

    if exclude_writeins_flag:
        new = [util.merge_writeIns(b) for b in new]
        new = [util.remove(util.BallotMarks.WRITEIN, b) for b in new]

    ballot_dict['ranks'] = new
    return ballot_dict


def candidates(ctx, *, combine_writeins=None, exclude_writeins=None):

    combine_writeins_flag = ctx['combine_writeins']
    if combine_writeins is not None:
        combine_writeins_flag = combine_writeins

    exclude_writeins_flag = ctx['skip_writeins']
    if exclude_writeins is not None:
        exclude_writeins_flag = exclude_writeins

    cans = set()
    for b in input_ballots(ctx, combine_writeins=combine_writeins_flag)['ranks']:
        cans.update(b)
    cans = cans - {util.BallotMarks.OVERVOTE, util.BallotMarks.SKIPPEDRANK}

    if combine_writeins_flag or exclude_writeins_flag:
        cans = set(util.merge_writeIns(cans))

        # safety check
        uncaught_writeins = [cand for cand in cans
                             if cand != util.BallotMarks.WRITEIN and ('write' in cand.lower() or 'uwi' in cand.lower())]
        if len(uncaught_writeins) > 0:
            raise RuntimeError('more than one writein remaining after merge. debug')

    if exclude_writeins_flag:
        cans = cans - {util.BallotMarks.WRITEIN}

    return cans
