from collections import Counter, defaultdict
import pandas as pd
import numpy as np
from itertools import combinations
from gmpy2 import mpq as Fraction
from random import choice
from copy import deepcopy

# cruncher imports
from .definitions import SKIPPEDRANK, OVERVOTE, WRITEIN, \
    remove, keep, index_inf, before, replace
from .cache_helpers import save


@save
def ballots(ctx):
    """
    Return parser results for contest.
    Ballots are in form of list of lists.
    """
    res = ctx['parser'](ctx)
    if isinstance(res, dict):
        return res['ranks']
    else:
        return res


@save
def ballots_dict(ctx):
    """
    Return parser results for contest.
    Ballots are in form of list of lists.
    """
    res = ctx['parser'](ctx)
    if isinstance(res, dict):
        return res
    elif isinstance(res, list):
        new_res = {'ranks': res, 'extras': []}
        return new_res


@save
def candidates(ctx):
    cans = set()
    for b in ballots(ctx):
        cans.update(b)
    return cans - {OVERVOTE, SKIPPEDRANK, WRITEIN}


@save
def cleaned(ctx):
    """
        retrieve ballots (list of lists, each containing candidate names in
        rank order, also write-ins marked with WRITEIN constant, and OVERVOTES and
        SKIPVOTES marked with their respective constants)

        For each ballot, return a cleaned version that has pre-skipped
        skipped and overvoted rankings and only includes one ranking
        per candidate (the highest ranking for that candidate).

        Additionally, each ballot may be cut short depending on the
        -break_on_repeated_skipvotes- and -break_on_overvote- settings for
        a contest.

        returns: list of cleaned ballot-lists
    """
    new = []
    for b in ballots(ctx):
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
    return new


@save
def convert_cvr(ctx):
    """
    convert ballots read in with parser into common csv format.
    One ballot per row, columns: ID, extra_info, rank1, rank2 ...
    """
    ballot_dict = deepcopy(ballots_dict(ctx))
    bs = ballot_dict['ranks']
    extras = ballot_dict['extras']

    # how many ranks?
    num_ranks = max(len(i) for i in bs)

    # replace constants with strings
    bs = [replace(SKIPPEDRANK, 'skipped', b) for b in bs]
    bs = [replace(WRITEIN, 'writein', b) for b in bs]
    bs = [replace(OVERVOTE, 'overvote', b) for b in bs]

    # make sure all ballots are lists of equal length, adding trailing 'skipped' if necessary
    bs = [b + (['skipped'] * (num_ranks - len(b))) for b in bs]

    # ballotIDs in extras?
    if 'ballotID' not in extras:
        extras['ballotID'] = range(1, len(bs) + 1)

    # assemble output_table, start with extras
    output_df = pd.DataFrame.from_dict(extras)

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

# @save
# def bottom_up_stv(ctx):
#     ballots = deepcopy(cleaned(ctx))
#     rounds = []
#     while True:
#         rounds.append(list(zip(*Counter(b[0] for b in ballots).most_common())))
#         finalists,_ = rounds[-1]
#         if len(finalists) == ctx['number']:
#             return finalists
#         ballots = remove([], (keep(finalists[:-1], b) for b in ballots))


def round_by_round(ctx):
    """
    Run the rcv contest and return the round-by-round totals.
    'rounds' is a list of lists.
    Each list in 'rounds' contains two tuples (candidate names and round tallies)
    Both tuples are sorted in descending order of round tallies

    [[(round 1 candidates), (round 1 tally)],
     [(round 2 candidates), (round 2 tally)],
     ...,
     [(final round candidates), (final round tally)]]
    """
    rounds, _ = ctx['rcv_type'](ctx)
    return rounds


def candidate_outcomes(ctx):
    """
    Run the rcv contest and return a list of dictionaries (one per candidate).

    Each dict contains:
    candidate_name
    round_elected: None (if loser) or integer
    round_eliminated: None (if winner) or integer
    """
    _, outcomes = ctx['rcv_type'](ctx)
    return outcomes


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

    candidate_set = sorted(candidates(ctx))
    cleaned_ballots = cleaned(ctx)

    # create data frame that will be populated and output
    condorcet_percent_df = pd.DataFrame(np.NaN, index=candidate_set, columns=candidate_set)
    condorcet_count_df = pd.DataFrame(np.NaN, index=candidate_set, columns=candidate_set)

    # turn ballot-lists into ballot-dict with
    # key 'id' containing a unique integer id for the ballot
    # key 'ranks' containing the original ballot-list
    ballot_dicts = [{'id': ind, 'ranks': ballot} for ind, ballot in enumerate(cleaned_ballots)]

    # make dictionary with candidate as key, and value as list of ballot-dicts
    # that contain their name in any rank
    cand_ballot_dict = {cand: [ballot for ballot in ballot_dicts if cand in ballot['ranks']]
                        for cand in candidate_set}

    # all candidate pairs
    cand_pairs = combinations(candidate_set, 2)

    for pair in cand_pairs:

        cand1 = pair[0]
        cand2 = pair[1]

        # get the union of their ballots
        combined_ballot_list = cand_ballot_dict[cand1] + cand_ballot_dict[cand2]
        uniq_pair_ballots = list({v['id']: v['ranks'] for v in combined_ballot_list}.values())
        n_uniq_ballots = len(uniq_pair_ballots)

        # how many ballots rank cand1 above cand2?
        cand1_vs_cand2 = sum([index_inf(b, cand1) < index_inf(b, cand2)
                              for b in uniq_pair_ballots])

        # the remainder then must rank cand2 over cand1
        cand2_vs_cand1 = n_uniq_ballots - cand1_vs_cand2

        # add counts to df
        condorcet_count_df.loc[cand1, cand2] = cand1_vs_cand2
        condorcet_count_df.loc[cand2, cand1] = cand2_vs_cand1

        # calculate percent
        cand1_percent = (cand1_vs_cand2 / n_uniq_ballots) * 100
        cand2_percent = (cand2_vs_cand1 / n_uniq_ballots) * 100

        # add to df
        condorcet_percent_df.loc[cand1, cand2] = cand1_percent
        condorcet_percent_df.loc[cand2, cand1] = cand2_percent

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

    condorcet_percent_df.index.name = "condorcet winner: " + condorcet_winner
    condorcet_count_df.index.name = "condorcet winner: " + condorcet_winner

    return condorcet_count_df, condorcet_percent_df


# def rcv_ballots(clean_ballots):
#     rounds = []
#     ballots = remove([],deepcopy(clean_ballots))
#     while True:
#         rounds.append(list(zip(*Counter(b[0] for b in ballots).most_common())))
#         finalists, tallies = rounds[-1]
#         if tallies[0]*2 > sum(tallies):
#             return rounds
#         ballots = remove([], (keep(finalists[:-1], b) for b in ballots))


# def rcv_stack(ballots):
#     stack = [ballots]
#     results = []
#     while stack:
#         ballots = stack.pop()
#         finalists, tallies = map(list, zip(*Counter(b[0] for b in ballots if b).most_common()))
#         if tallies[0]*2 > sum(tallies):
#             results.append((finalists, tallies))
#         else:
#             losers = finalists[tallies.index(min(tallies)):]
#             for loser in losers:
#                 stack.append([keep(set(finalists)-set([loser]), b) for b in ballots])
#             if len(losers) > 1:
#                 stack.append([keep(set(finalists)-set(losers), b) for b in ballots])
#     return results


# def rcvreg(ballots):
#     rounds = []
#     while True:
#         rounds.append(list(zip(*Counter(b[0] for b in ballots).most_common())))
#         finalists, tallies = rounds[-1]
#         if tallies[0]*2 > sum(tallies):
#             return rounds
#         ballots = remove([], (keep(finalists[:-1], b) for b in ballots))

@save
def first_second_tables(ctx):

    candidate_set = sorted(candidates(ctx))
    cleaned_ballots = cleaned(ctx)

    # create data frame that will be populated and output
    percent_no_exhaust_df = pd.DataFrame(np.NaN, index=['first_choice', *candidate_set], columns=candidate_set)
    percent_df = pd.DataFrame(np.NaN, index=['first_choice', *candidate_set, 'exhaust'], columns=candidate_set)
    count_df = pd.DataFrame(np.NaN, index=['first_choice', *candidate_set, 'exhaust'], columns=candidate_set)

    # group ballots by first choice
    first_choices = {cand: [] for cand in candidate_set}
    for b in cleaned_ballots:
        if len(b) >= 1:
            first_choices[b[0]].append(b)
    # [first_choices[b[0]].append(b) for b in cleaned_ballots if len(b) >= 1]

    total_first_round_votes = float(sum([len(first_choices[i]) for i in first_choices]))

    # add first choices to tables
    # and calculate second choices
    for cand in candidate_set:

        first_choice_count = len(first_choices[cand])
        first_choice_percent = (first_choice_count / total_first_round_votes) * 100

        count_df.loc['first_choice', cand] = first_choice_count
        percent_df.loc['first_choice', cand] = first_choice_percent
        percent_no_exhaust_df.loc['first_choice', cand] = first_choice_percent

        ############################################################
        # calculate second choices, group second choices by candidate
        possible_second_choices = list(set(candidate_set) - {cand})
        second_choices = {backup_cand: [] for backup_cand in possible_second_choices + ['exhaust']}
        second_choices['exhaust'] = []

        for b in first_choices[cand]:
            if len(b) >= 2:
                second_choices[b[1]].append(b)
            else:
                second_choices['exhaust'].append(b)
        # [second_choices[b[1]].append(b) if len(b) >= 2 else second_choices['exhaust'].append(b)
        # for b in first_choices[cand]]

        total_second_choices = float(sum([len(second_choices[i]) for i in second_choices]))
        total_second_choices_no_exhaust = float(sum([len(second_choices[i]) for i in second_choices
                                                     if i != 'exhaust']))

        # count second choices and add to table
        for backup_cand in possible_second_choices + ['exhaust']:

            second_choice_count = len(second_choices[backup_cand])

            # if there are not backup votes fill with zeros
            if total_second_choices == 0:
                second_choice_percent = 0
            else:
                second_choice_percent = (second_choice_count / total_second_choices) * 100

            if total_second_choices_no_exhaust == 0:
                second_choice_percent_no_exhaust = 0
            else:
                second_choice_percent_no_exhaust = (second_choice_count / total_second_choices_no_exhaust) * 100

            count_df.loc[backup_cand, cand] = second_choice_count
            percent_df.loc[backup_cand, cand] = second_choice_percent
            if backup_cand != 'exhaust':
                percent_no_exhaust_df.loc[backup_cand, cand] = second_choice_percent_no_exhaust

    return count_df, percent_df, percent_no_exhaust_df


@save
def sequential_rcv(ctx):
    pass



@save
def stv_fractional_ballot(ctx):
    """
    Static threshold multi-winner elections with fractional surplus transfer
    """

    ctx['use_multiwinner_rounds'] = True

    rounds = []
    outcomes = []

    # select all non-empty ballots and pair each with Fraction(1)
    bs = [(b, Fraction(1)) for b in cleaned(ctx) if b]

    # set win threshold
    threshold = int(len(bs)/(ctx['num_winners']+1)) + 1

    # run rounds until enough winners are found
    round_num = 0
    num_winners = 0
    while ctx['num_winners'] == num_winners:

        round_num += 1

        # is the number of candidates remaining equal
        # to the number of winner left to elect?
        # If so, they win
        # this is necessary step when using a static threshold
        num_winners = len({i for i in outcomes if i['round_elected']})
        num_remaining = 0


        # accumulate fractional values currently held by
        # first-ranked candidate on each ballot
        totals = defaultdict(int)
        for cand_list, ballot_frac in bs:
            totals[cand_list[0]] += ballot_frac

        # sort totals dict into descending order
        ordered = sorted(totals.items(), key=lambda x: -x[1])
        rounds.append(ordered)


        # split ordered totals into two lists
        names, tallies = zip(*ordered)

        # any candidates over the threshold?
        if any([i > threshold for i in tallies]):

            looking_for_winners = True
            round_winners = []

            while looking_for_winners:

                round_winner = names[0]
                round_others = names[1:]

                # then add to contest winners list
                outcomes.append({'name': round_winner, 'round_elected': round_num,
                                'round_eliminated': None})

                # fractional surplus to transfer from each winner ballot
                surplus_percent = (tallies[0] - threshold) / tallies[0]

                # if surplus to transfer is non-zero
                if surplus_percent:

                    # which ballots had the winner on top
                    # and need to be fractionally split
                    winner_in_active_rank = [cand_list[0] == round_winner for cand_list, ballot_frac in bs]

                    # split out tuples
                    split_cand_lists, split_ballot_fracs = zip(*bs)

                    # adjust ballot fracs for winner ballots
                    new_ballot_fracs = [ballot_frac * surplus_percent if winner_active else ballot_frac
                                        for ballot_frac, winner_active in zip(split_ballot_fracs, winner_in_active_rank)]

                    # stitch cand_lists back with new ballot fracs
                    bs = list(zip(split_cand_lists, new_ballot_fracs))

                # remove winner from ballots
                bs = [(keep(round_others, cand_list), ballot_frac) for cand_list, ballot_frac in bs]

                # remove newly-empty ballots
                bs = [b for b in bs if b[0]]

                # update winner list for round
                round_winners.append(round_winner)

                # identify next round-winner ordering
                filtered_ordering = [(cand, cand_tally)
                                    for cand, cand_tally in ordered if cand not in round_winners]

                # any candidates left?
                if filtered_ordering:

                    names, tallies = zip(*filtered_ordering)

                    # if there are no more candidates over the threshold, then move to the next round
                    if any([i > threshold for i in tallies]) is False:
                        looking_for_winners = False
                else:

                    # no candidates left, exit loop
                    looking_for_winners = False

                # if contest setting specifies only one winner per round, then move to next round
                if ctx['use_multiwinner_rounds'] is False:
                    looking_for_winners = False

        else:  # no winner

            # remove candidate from ballots that received the lowest count
            loser_count = min(tallies)

            # in case of tied losers, randomly choose one to eliminate
            round_loser = choice([cand for cand, cand_tally in ordered if cand_tally == loser_count])
            outcomes.append({'name': round_loser, 'round_elected': None,
                             'round_eliminated': round_num})

            # remove loser from
            bs = ((remove(round_loser, cand_list), ballot_frac) for cand_list, ballot_frac in bs)

            # remove newly-empty ballots
            bs = [b for b in bs if b[0]]

    return rounds, outcomes


@save
def stv_whole_ballot(ctx):
    pass


@save
def rcv_multiWinner_thresh15(ctx):

    rounds = deepcopy(until2rcv(ctx))
    rounds_slice = []

    # find round where all candidates are above 15 percent
    done = False
    while not done:

        current_round = rounds.pop(0)
        rounds_slice.append(current_round)

        # check for finish condition
        _, round_tally = current_round
        round_total = sum(round_tally)

        # might need to adjust rounding here
        if all([i > (round_total * 0.15) for i in round_tally]):
            done = True

    return rounds_slice


@save
def rcv_single_winner(ctx):
    """
        Runs a single winner RCV contest.

        Retrieves the cleaned ballots using ctx and
        returns a list of round-by-round vote counts.
        Runs until single winner threshold is reached.

        [[(round 1 candidates), (round 1 tally)],
         [(round 2 candidates), (round 2 tally)],
         ...,
         [(final round candidates), (final round tally)]]
    """

    rounds = deepcopy(until2rcv(ctx))
    rounds_slice = []

    # find round where a candidate has over 50% of active round votes
    done = False
    while not done:

        current_round = rounds.pop(0)
        rounds_slice.append(current_round)

        # check for finish condition
        _, round_tally = current_round

        round_total = sum(round_tally)

        # does round leader have the majority?
        # might need to adjust rounding here
        if round_tally[0]*2 > round_total:
            done = True

    return rounds_slice


@save
def until2rcv(ctx):
    """
    run an rcv election until there are two candidates remaining.
    This is might lead to more rounds than necessary to determine a winner.
    """

    losers = []
    rounds = []
    candidate_set = candidates(ctx)
    bs = [list(i) for i in cleaned(ctx)]

    n_finalists = float('inf')
    while n_finalists > 2:

        # tally ballots and reorder tallies
        # using active rankings for each ballot,
        # skipping empty ballots
        round_tally = list(zip(
            *Counter(b[0] for b in bs if b).most_common()
        ))
        rounds.append(round_tally)

        finalists, tallies = round_tally
        n_finalists = len(finalists)

        # find round loser
        loser_count = min(tallies)
        round_loser = choice([cand for cand, cand_tally in zip(finalists, tallies)
                              if cand_tally == loser_count])
        losers.append(round_loser)

        # calculate transfer from loser
        round_loser_ballots = [b for b in bs if b[0] == round_loser]
        round_transfer = Counter([b[1] if len(b) > 1 else 'exhaust' for b in round_loser_ballots])
        round_transfer[round_loser] = len(round_loser_ballots) * -1

        # remove round loser from ballots, all ranking spots.
        # removing the round loser from all ranking spots now is equivalent
        # to waiting and skipping over an already-eliminated candidate
        # once they become the active ranking in a later round.

        # remove candidate from ballots that received the lowest count
        # in case of tied losers, randomly choose one to eliminate
        bs = [remove(round_loser, b) for b in bs]

    return rounds


########################################################################################
########################################################################################
########################################################################################
########################################################################################
########################################################################################
########################################################################################
# outcome stat functions


@save
def contest_winner(ctx):
    '''
    The winner of the election, or, in multiple winner contests, the
    hypothetical winner if the contest was single winner.
    '''
    # Horrible Hack!
    # no mapping file for the 2006 Burlington Mayoral Race, so hard coded here:
    if ctx['place'] == 'Burlington' and ctx['date'] == '2006':
        return 'Bob Kiss'
    return str(winner(ctx)).title()


@save
def condorcet(ctx):
    '''
    Is the winner the condorcet winner?
    The condorcet winner is the candidate that would win a 1-on-1 election versus
    any other candidate in the election. Note that this calculation depends on
    jurisdiction dependant rule variations.
    '''

    # first round winner is the condorcet winner
    if len(rcv_single_winner(ctx)) == 1:
        return True

    net = Counter()
    for b in cleaned(ctx):
        for loser in losers(ctx):

            # accumulate difference between the number of ballots ranking
            # the winner before the loser
            net.update({loser: before(winner(ctx), loser, b)})

    if not net:  # Uncontested Race -> net == {}
        return True

    # if all differences are positive, then the winner was the condorcet winner
    return min(net.values()) > 0


def come_from_behind(ctx):
    """
    True if rcv winner is not first round leader
    """
    return winner(ctx) != rcv_single_winner(ctx)[0][0][0]


def final_round_active_votes(ctx):
    '''
    The number of votes that were awarded to any candidate in the final round.
    '''
    return sum(rcv_single_winner(ctx)[-1][1])


def first_round_active_votes(ctx):
    '''
    The number of votes that were awarded to any candidate in the first round.
    '''
    return sum(rcv_single_winner(ctx)[0][1])


def final_round_winner_percent(ctx):
    '''
    The percent of votes for the winner in the final round. The final round is
    the first round where the winner receives a majority of the non-exhausted
    votes.
    '''
    return rcv_single_winner(ctx)[-1][1][0] / sum(rcv_single_winner(ctx)[-1][1])


def final_round_winner_vote(ctx):
    '''
    The number of votes for the winner in the final round. The final round is
    the first round where the winner receives a majority of the non-exhausted
    votes.
    '''
    return rcv_single_winner(ctx)[-1][1][0]


def final_round_winner_votes_over_first_round_valid(ctx):
    '''
    The number of votes the winner receives in the final round divided by the
    number of valid votes in the first round.
    '''
    return final_round_winner_vote(ctx) / first_round_active_votes(ctx)


def first_round_winner_place(ctx):
    '''
    In terms of first round votes, what place the eventual winner came in.
    '''
    return rcv_single_winner(ctx)[0][0].index(winner(ctx)) + 1


def first_round_winner_percent(ctx):
    '''
    The percent of votes for the winner in the first round.
    '''
    wind = rcv_single_winner(ctx)[0][0].index(winner(ctx))
    return rcv_single_winner(ctx)[0][1][wind] / sum(rcv_single_winner(ctx)[0][1])


def first_round_winner_vote(ctx):
    '''
    The number of votes for the winner in the first round.
    '''
    wind = rcv_single_winner(ctx)[0][0].index(winner(ctx))
    return rcv_single_winner(ctx)[0][1][wind]


def finalists(ctx):
    return rcv_single_winner(ctx)[-1][0]


def finalist_ind(ctx):
    """
    Returns a list indicating the first rank on each ballot where a finalist is listed.
    List element is Inf if no finalist is present
    """
    final_candidates = finalists(ctx)
    inds = []

    # loop through each ballot and check for each finalist
    for b in ballots(ctx):
        min_ind = float('inf')
        for c in final_candidates:
            if c in b:
                min_ind = min(b.index(c), min_ind)
        inds.append(min_ind)

    return inds


@save
def losers(ctx):
    return set(candidates(ctx)) - {winner(ctx)}


# fixme
def number_of_candidates(ctx):
    '''
    The number of non-candidates on the ballot, not including write-ins.
    '''
    return len(candidates(ctx))


@save
def ranked_winner(ctx):
    """
     Number of ballots with a non-overvote mark for the winner
    """
    return sum(winner(ctx) in b for b in ballots(ctx))


@save
def winner(ctx):
    return rcv_single_winner(ctx)[-1][0][0]


@save
def winners_consensus_value(ctx):
    '''
    The percentage of valid first round votes that rank the winner in the top 3.
    '''
    return winner_in_top_3(ctx) / first_round_active_votes(ctx)



@save
def winner_ranking(ctx):
    """
        Returns a dictionary with ranking-count key-values, with count
        indicating the number of ballots in which the winner received each
        ranking.
    """
    return Counter(
        b.index(winner(ctx)) + 1 if winner(ctx) in b else None for b in cleaned(ctx)
    )


@save
def winner_in_top_3(ctx):
    """
        Sum the counts from the ranking-count entries, where the ranking is < 4
    """
    return sum(v for k, v in winner_ranking(ctx).items() if k is not None and k < 4)
