from collections import Counter
import pandas as pd
import numpy as np
from itertools import combinations
from gmpy2 import mpq as Fraction
from copy import deepcopy

# cruncher imports
from .definitions import SKIPPEDRANK, OVERVOTE, WRITEIN, \
    index_inf, replace, merge_writeIns
from .cache_helpers import save


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
    res = ctx['parser'](ctx)

    # temporary fix?
    # since I havent attempted to rewrite parsers in any way, just merge together
    # writeIns that may remain at this step

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
    return set(merge_writeIns(candidates(ctx)))


@save
def candidates_no_writeIns(ctx):
    return candidates_merged_writeIns(ctx) - {WRITEIN}


@save
def convert_cvr(ctx):
    """
    convert ballots read in with parser into common csv format.
    One ballot per row, columns: ID, extra_info, rank1, rank2 ...
    """
    ballot_dict = deepcopy(ballots(ctx))
    bs = ballot_dict['ranks']
    weight = ballot_dict['weight']
    del ballot_dict['ranks']
    del ballot_dict['weight']

    # how many ranks?
    num_ranks = max(len(i) for i in bs)

    # replace constants with strings
    bs = [replace(SKIPPEDRANK, 'skipped', b) for b in bs]
    bs = [replace(WRITEIN, 'writein', b) for b in bs]
    bs = [replace(OVERVOTE, 'overvote', b) for b in bs]

    # make sure all ballots are lists of equal length, adding trailing 'skipped' if necessary
    bs = [b + (['skipped'] * (num_ranks - len(b))) for b in bs]

    ballot_dict['ranks'] = bs

    # ballotIDs in extras?
    if 'ballotID' not in ballot_dict:
        ballot_dict['ballotID'] = [i for i in range(1, len(bs) + 1)]

    # assemble output_table, start with extras
    output_df = pd.DataFrame.from_dict(ballot_dict)

    # are weights all one, then dont add to output
    if not all([i == 1 for i in weight]):
        output_df['weight'] = weight

    # add in rank columns
    for i in range(1, num_ranks + 1):
        output_df['rank' + str(i)] = [b[i-1] for b in bs]

    return output_df


########################################################################################
########################################################################################
########################################################################################
########################################################################################
########################################################################################
########################################################################################
# rcv tabulation functions

###################
# INTERFACE

@save
def rcv_obj(ctx):
    return ctx['rcv_type'](ctx)


def round_by_round_trimmed(ctx):
    """
    Run the rcv contest and return the round-by-round totals,
    containing only the candidates that received any votes that round.

    Return a list of lists.
    Each list contains two tuples (candidate names and round tallies)
    Both tuples are sorted in descending order of round tallies

    rounds_trimmed:
    [[(round 1 candidates), (round 1 tally)],
     [(round 2 candidates), (round 2 tally)],
     ...,
     [(final round candidates), (final round tally)]]
    """
    return rcv_obj(ctx).results()['rounds_trimmed']


def round_by_round_full(ctx):
    """
    Run the rcv contest and return the round-by-round totals,
    with zeros added for eliminated candidates and those failing to achieve any votes.

    Return a list of lists.
    Each list contains two tuples (candidate names and round tallies)
    Both tuples are sorted in descending order of round tallies

    rounds_full:
    [[(round 1 candidates), (round 1 tally)],
     [(round 2 candidates), (round 2 tally)],
     ...,
     [(final round candidates), (final round tally)]]
    """
    return rcv_obj(ctx).results()['rounds_full']


def round_by_round_transfers(ctx):
    """
    Run the rcv contest and return the round-by-round transfers.

    Return a list of dicts, one dict per round.
    Each dict contains candidate names as keys and transfer counts as values

    transfers:
    [
    {cand1: transfer_count. cand2: transfer_count, ... exhaust: transfer_count}, # round 1
    {cand1: transfer_count. cand2: transfer_count, ... exhaust: transfer_count}, # round 2
    ...
    {cand1: transfer_count. cand2: transfer_count, ... exhaust: transfer_count}, # final round
    ]
    """
    return rcv_obj(ctx).results()['transfers']


def candidate_outcomes(ctx):
    """
    Run the rcv contest and return a list of dictionaries (one per candidate).

    Each dict contains:
    candidate_name
    round_elected: None (if loser) or integer
    round_eliminated: None (if winner) or integer
    """
    return rcv_obj(ctx).results()['candidate_outcomes']


def final_weights(ctx):
    """
    Run the rcv contest and return a list of final ballot weights. Weights may have started out
    not equal to 1 (weighted poll) or have been reduced to below as a result of fractional vote transfers.
    """
    return rcv_obj(ctx).results()['final_weights']


####################
# OUTCOME STATS

@save
def contest_winner(ctx):
    '''
    The winner(s) of the election.
    '''
    # Horrible Hack!
    # no mapping file for the 2006 Burlington Mayoral Race, so hard coded here:
    if ctx['place'] == 'Burlington' and ctx['date'] == '2006':
        return 'Bob Kiss'
    return ", ".join([str(w).title() for w in winner(ctx)])


@save
def condorcet(ctx):
    '''
    Is the winner the condorcet winner?
    The condorcet winner is the candidate that would win a 1-on-1 election versus
    any other candidate in the election. Note that this calculation depends on
    jurisdiction dependant rule variations.

    In the case of multi-winner elections, this result will only pertain to the first candidate elected.
    '''

    _, _, condorcet_winner = condorcet_tables(ctx)
    if winner(ctx)[0] == condorcet_winner:
        return "Yes"
    else:
        return "No"


def come_from_behind(ctx):
    """
    "yes" if rcv winner is not first round leader, else "no"

    In the case of multi-winner elections, this result will only pertain to the first candidate elected.
    """
    if winner(ctx)[0] != round_by_round_trimmed(ctx)[0][0][0]:
        return "Yes"
    else:
        return "No"


def final_round_active_votes(ctx):
    '''
    The number of votes that were awarded to any candidate in the final round. (weighted)
    '''
    return float(sum(round_by_round_trimmed(ctx)[-1][1]))


def first_round_active_votes(ctx):
    '''
    The number of votes that were awarded to any candidate in the first round. (weighted)
    '''
    return float(sum(round_by_round_trimmed(ctx)[0][1]))


def final_round_winner_percent(ctx):
    '''
    The percent of votes for the winner in the final round.
    If more than one winner, return the final round count for the first winner elected. (weighted)
    '''
    obj = rcv_obj(ctx)
    round_dict = obj.get_round_dict(obj.n_rounds())
    return float(round_dict[winner(ctx)[0]]/sum(round_dict.values()))


def final_round_winner_vote(ctx):
    '''
    The number of votes for the winner in the final round.
    If more than one winner, return the final round count for the first winner elected. (weighted)
    '''
    obj = rcv_obj(ctx)
    round_dict = obj.get_round_dict(obj.n_rounds())
    return float(round_dict[winner(ctx)[0]])


def final_round_winner_votes_over_first_round_valid(ctx):
    '''
    The number of votes the winner receives in the final round divided by the
    number of valid votes in the first round.

    If more than one winner, return the final round count for the first winner elected. (weighted)
    '''
    return float(final_round_winner_vote(ctx) / first_round_active_votes(ctx))


def first_round_winner_place(ctx):
    '''
    In terms of first round votes, what place the eventual winner came in.
    In the case of multi-winner elections, this result will only pertain to the first candidate elected.
    '''
    return round_by_round_trimmed(ctx)[0][0].index(winner(ctx)[0]) + 1


def first_round_winner_percent(ctx):
    '''
    The percent of votes for the winner in the first round.
    In the case of multi-winner elections, this result will only pertain to the first candidate elected. (weighted)
    '''
    wind = round_by_round_trimmed(ctx)[0][0].index(winner(ctx)[0])
    return float(round_by_round_trimmed(ctx)[0][1][wind] / sum(round_by_round_trimmed(ctx)[0][1]))


def first_round_winner_vote(ctx):
    '''
    The number of votes for the winner in the first round.
    In the case of multi-winner elections, this result will only pertain to the first candidate elected. (weighted)
    '''
    wind = round_by_round_trimmed(ctx)[0][0].index(winner(ctx)[0])
    return float(round_by_round_trimmed(ctx)[0][1][wind])


def finalists(ctx):
    """
    Any candidate that was active into the final round.
    """
    return round_by_round_trimmed(ctx)[-1][0]


def finalist_ind(ctx):
    """
    Returns a list indicating the first rank on each ballot where a finalist is listed.
    List element is Inf if no finalist is present
    """
    final_candidates = finalists(ctx)
    inds = []

    # loop through each ballot and check for each finalist
    for b in ballots(ctx)['ranks']:
        min_ind = float('inf')
        for c in final_candidates:
            if c in b:
                min_ind = min(b.index(c), min_ind)
        inds.append(min_ind)

    return inds


def number_of_winners(ctx):
    """
    Count how many winners a contest had.
    """
    return sum(c['round_elected'] is not None for c in candidate_outcomes(ctx))


def number_of_rounds(ctx):
    """
    Count how many rounds a contest had.
    """
    return len(round_by_round_full(ctx))


def number_of_candidates(ctx):
    '''
    The number of candidates on the ballot, not including write-ins.
    '''
    return len(candidates_no_writeIns(ctx))


@save
def ranked_winner(ctx):
    """
    Number of ballots with a non-overvote mark for the winner
    """
    return sum(bool(set(winner(ctx)).intersection(b)) for b in ballots(ctx)['ranks'])


def win_threshold(ctx):
    return float(rcv_obj(ctx).win_threshold())


@save
def winner(ctx):
    """
    Return contest winner names in order of election.
    """
    elected_candidates = [d for d in candidate_outcomes(ctx) if d['round_elected'] is not None]
    return [d['name'] for d in sorted(elected_candidates, key=lambda x: x['round_elected'])]


@save
def winners_consensus_value(ctx):
    '''
    The percentage of valid first round votes that rank any winner in the top 3.
    '''
    return float(winner_in_top_3(ctx) / first_round_active_votes(ctx))


@save
def winner_ranking(ctx):
    """
    Returns a dictionary with ranking-count key-values, with count
    indicating the number of ballots in which the winner received each
    ranking.
    If more than one winner is elected in the contest, the value returned for this function refers to the
    first winner elected.
    """
    return Counter(
        b.index(winner(ctx)) + 1 if winner(ctx) in b else None for b in cleaned(ctx)['ranks']
    )


@save
def winner_in_top_3(ctx):
    """
    Number of ballots that ranked any winner in the top 3 ranks. (weighted)
    """
    top3 = [b[:min(3, len(b))] for b in ballots(ctx)['ranks']]
    top3_check = [set(winner(ctx)).intersection(b) for b in top3]
    return sum([weight * bool(top3) for weight, top3 in zip(ballots(ctx)['weight'], top3_check)])


##########################
# MISC TABULATION

@save
def condorcet_tables(ctx):
    """
    Returns a two condorcet tables as a pandas data frame with candidate names as row and column indices.
    One contains counts and the other contains percents.

    Each cell indicates the count/percentage of ballots that ranked the row-candidate over
    the column-candidate (including ballots that only ranked the row-candidate). When calculating percents,
    the denominator is each cell is the number of ballots that ranked the row-candidate OR the column-candidate.

    Symmetric cells about the diagonal should sum to 100 (for the percent table).
    """
    candidate_set = sorted(candidates_merged_writeIns(ctx))
    cleaned_dict = deepcopy(cleaned_writeIns_merged(ctx))
    cleaned_ballots = [{'ranks': ranks, 'weight': weight}
                       for ranks, weight in zip(cleaned_dict['ranks'], cleaned_dict['weight'])]


    # create data frame that will be populated and output
    condorcet_percent_df = pd.DataFrame(np.NaN, index=candidate_set, columns=candidate_set)
    condorcet_count_df = pd.DataFrame(np.NaN, index=candidate_set, columns=candidate_set)

    # turn ballot-lists into ballot-dict with
    # key 'id' containing a unique integer id for the ballot
    # key 'ranks' containing the original ballot-list
    ballot_dicts = [{'id': ind, 'ballot': ballot} for ind, ballot in enumerate(cleaned_ballots)]

    # make dictionary with candidate as key, and value as list of ballot-dicts
    # that contain their name in any rank
    cand_ballot_dict = {cand: [ballot for ballot in ballot_dicts if cand in ballot['ballot']['ranks']]
                        for cand in candidate_set}

    # all candidate pairs
    cand_pairs = combinations(candidate_set, 2)

    for pair in cand_pairs:
        cand1 = pair[0]
        cand2 = pair[1]

        # get the union of their ballots
        combined_ballot_list = cand_ballot_dict[cand1] + cand_ballot_dict[cand2]
        uniq_pair_ballots = list({v['id']: v['ballot'] for v in combined_ballot_list}.values())

        uniq_pair_ballots_weights = [ballot['weight'] for ballot in uniq_pair_ballots]
        sum_weighted_ballots = sum(uniq_pair_ballots_weights)

        # which ballots rank cand1 above cand2?
        cand1_vs_cand2 = [index_inf(b['ranks'], cand1) < index_inf(b['ranks'], cand2) for b in uniq_pair_ballots]
        cand1_vs_cand2_weightsum = sum(weight * flag for weight, flag
                                       in zip(uniq_pair_ballots_weights, cand1_vs_cand2))

        # the remainder then must rank cand2 over cand1
        cand2_vs_cand1 = [not i for i in cand1_vs_cand2]
        cand2_vs_cand1_weightsum = sum(weight * flag for weight, flag
                                       in zip(uniq_pair_ballots_weights, cand2_vs_cand1))

        # add counts to df
        condorcet_count_df.loc[cand1, cand2] = float(cand1_vs_cand2_weightsum)
        condorcet_count_df.loc[cand2, cand1] = float(cand2_vs_cand1_weightsum)

        # calculate percent
        if sum_weighted_ballots:
            cand1_percent = (cand1_vs_cand2_weightsum / sum_weighted_ballots) * 100
            cand2_percent = (cand2_vs_cand1_weightsum / sum_weighted_ballots) * 100
        else:
            cand1_percent = 0
            cand2_percent = 0

        # add to df
        condorcet_percent_df.loc[cand1, cand2] = float(cand1_percent)
        condorcet_percent_df.loc[cand2, cand1] = float(cand2_percent)

    # find condorcet winner and set index name to include winner
    condorcet_winner = None

    if len(candidate_set) == 1:

        condorcet_winner = candidate_set[0]
    else:

        for cand in candidate_set:

            not_cand = set(candidate_set) - {cand}
            all_winner = all(condorcet_percent_df.loc[cand, not_cand] > 50)

            if all_winner:
                if condorcet_winner is None:
                    condorcet_winner = cand
                else:
                    print("cannottt be more than one condorcet winner!!!!")
                    exit(1)

    return condorcet_count_df, condorcet_percent_df, condorcet_winner


@save
def first_second_tables(ctx):
    """
    Return two pandas tables with candidates as columns and first row showing distribution of first round votes.
    Subsequent rows indicate second choice vote distribution for each column.

    first table is vote counts
    second table is percentages
    """

    candidate_set = sorted(candidates_merged_writeIns(ctx))
    cleaned_dict = deepcopy(cleaned_writeIns_merged(ctx))
    cleaned_ballots = [{'ranks': ranks, 'weight': weight}
                       for ranks, weight in zip(cleaned_dict['ranks'], cleaned_dict['weight'])]


    # create data frame that will be populated and output
    percent_no_exhaust_df = pd.DataFrame(np.NaN, index=['first_choice', *candidate_set], columns=candidate_set)
    percent_df = pd.DataFrame(np.NaN, index=['first_choice', *candidate_set, 'exhaust'], columns=candidate_set)
    count_df = pd.DataFrame(np.NaN, index=['first_choice', *candidate_set, 'exhaust'], columns=candidate_set)

    # group ballots by first choice
    first_choices = {cand: [] for cand in candidate_set}
    for b in cleaned_ballots:
        if len(b['ranks']) >= 1:
            first_choices[b['ranks'][0]].append(b)

    # sum total first round votes
    total_first_round_votes = 0
    for cand in first_choices:
        total_first_round_votes += sum([b['weight'] for b in first_choices[cand]])

    # add first choices to tables
    # and calculate second choices
    for cand in candidate_set:

        ############################################################
        # update first round table values
        first_choice_count = sum([b['weight'] for b in first_choices[cand]])
        first_choice_percent = (first_choice_count / total_first_round_votes) * 100

        count_df.loc['first_choice', cand] = float(first_choice_count)
        percent_df.loc['first_choice', cand] = float(first_choice_percent)
        percent_no_exhaust_df.loc['first_choice', cand] = float(first_choice_percent)

        ############################################################
        # calculate second choices, group second choices by candidate
        possible_second_choices = list(set(candidate_set) - {cand})
        second_choices = {backup_cand: [] for backup_cand in possible_second_choices + ['exhaust']}

        # group ballots by second choices
        for b in first_choices[cand]:
            if len(b['ranks']) >= 2:
                second_choices[b['ranks'][1]].append(b['weight'])
            else:
                second_choices['exhaust'].append(b['weight'])

        # sum total second round votes
        total_second_choices = 0
        total_second_choices_no_exhaust = 0
        for backup_cand in second_choices:
            total_second_choices += sum(second_choices[backup_cand])
            if backup_cand != 'exhaust':
                total_second_choices_no_exhaust += sum(second_choices[backup_cand])

        # count second choices and add to table
        for backup_cand in second_choices:

            # fill in second choice values in table
            second_choice_count = sum(second_choices[backup_cand])

            # if there are not backup votes fill with zeros
            if total_second_choices == 0:
                second_choice_percent = 0
            else:
                second_choice_percent = (second_choice_count / total_second_choices) * 100

            if total_second_choices_no_exhaust == 0:
                second_choice_percent_no_exhaust = 0
            else:
                second_choice_percent_no_exhaust = (second_choice_count / total_second_choices_no_exhaust) * 100

            count_df.loc[backup_cand, cand] = float(second_choice_count)
            percent_df.loc[backup_cand, cand] = float(second_choice_percent)
            if backup_cand != 'exhaust':
                percent_no_exhaust_df.loc[backup_cand, cand] = float(second_choice_percent_no_exhaust)

    return count_df, percent_df, percent_no_exhaust_df

