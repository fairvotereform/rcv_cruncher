from copy import deepcopy
from random import choice

import pandas as pd
import numpy as np
from itertools import combinations
from collections import Counter

csv_fpath = 'C:/Users/User/Documents/fairvote/projects/rcv-cruncher/contest_sets/survey_2_27/SurveyUSA_Respondent_Level_Data.csv'
condorcet_count_fpath = 'C:/Users/User/Documents/fairvote/projects/rcv-cruncher/contest_sets/survey_2_27/condorcet_count.csv'
condorcet_percent_fpath = 'C:/Users/User/Documents/fairvote/projects/rcv-cruncher/contest_sets/survey_2_27/condorcet_percent.csv'
first_second_count_fpath = 'C:/Users/User/Documents/fairvote/projects/rcv-cruncher/contest_sets/survey_2_27/first_second_count.csv'
first_second_percent_fpath = 'C:/Users/User/Documents/fairvote/projects/rcv-cruncher/contest_sets/survey_2_27/first_second_percent.csv'
first_second_percent_noExhaust_fpath = 'C:/Users/User/Documents/fairvote/projects/rcv-cruncher/contest_sets/survey_2_27/first_second_percent_noExhaust.csv'
rcv_until2_fpath = 'C:/Users/User/Documents/fairvote/projects/rcv-cruncher/contest_sets/survey_2_27/rcv_until2.csv'
rcv_fpath = 'C:/Users/User/Documents/fairvote/projects/rcv-cruncher/contest_sets/survey_2_27/rcv.csv'
ideology_fpath = 'C:/Users/User/Documents/fairvote/projects/rcv-cruncher/contest_sets/survey_2_27/ideology.csv'

def candidates_noUndecided():
    return {'Joe Biden', 'Michael Bloomberg', 'Pete Buttigieg',
           'Tulsi Gabbard', 'Amy Klobuchar', 'Bernie Sanders',
            'Tom Steyer', 'Elizabeth Warren'}

def candidates():
    return {'Joe Biden', 'Michael Bloomberg', 'Pete Buttigieg',
           'Tulsi Gabbard', 'Amy Klobuchar', 'Bernie Sanders',
            'Tom Steyer', 'Elizabeth Warren', 'Undecided'}

def candidate_map(cand_idx):
    d = {1: 'Joe Biden', 2: 'Michael Bloomberg', 3: 'Pete Buttigieg', 4: 'Tulsi Gabbard',
        5: 'Amy Klobuchar', 6: 'Bernie Sanders', 7: 'Tom Steyer', 8: 'Elizabeth Warren', 9: 'Undecided'}
    return d[cand_idx]

def ideology_map():
    return {1: 'Very Conservative', 2: 'Conservative', 3: 'Moderate',
            4: 'Liberal', 5: 'Very Liberal', 6: 'Not Sure'}

def index_inf(lst, el):
    # return element index if in list, inf otherwise
    if el in lst:
        return lst.index(el)
    else:
        return float('inf')


def remove(x, l):
    # removes all x from list l
    return [i for i in l if i != x]


def cleaned():

    ballots = []

    csv_df = pd.read_csv(csv_fpath)

    # select only democrats (coded in Ballot field as 2) and rankings
    rank_columns = ['1st choice', '2nd choice', '3rd choice', '4th choice',
                    '5th choice',  '6th choice', '7th choice']

    ranks_df = csv_df.loc[csv_df['Ballot'] == 2, rank_columns + ['weight']]

    for index, row in ranks_df.iterrows():

        b_ranks = []
        b_weight = row['weight']

        saw_undecided = False
        since_undecided = []

        for rank in rank_columns:

            if np.isnan(row[rank]):
                if since_undecided:
                    print('some candidates appeared after an undecided vote! debug')
                break

            row_cand = candidate_map(row[rank])

            if saw_undecided:
                since_undecided.append(row_cand)

            if row_cand == 'Undecided':
                saw_undecided = True

            if row_cand != 'Undecided':
                b_ranks.append(row_cand)

        ballots.append({'ranks': b_ranks, 'weight': b_weight})

    return ballots

def write_ideology():

    csv_df = pd.read_csv(csv_fpath)

    all_ideologies_idx = list(ideology_map().keys())
    all_ideologies = list(ideology_map().values())

    # select trump comparisons
    trump_columns = ['Biden defeats Trump', 'Bloomberg defeats Trump', 'Buttigieg defeats Trump',
                    'Gabbard defeats Trump', 'Klobuchar defeats Trump', 'Sanders defeats Trump',
                    'Steyer defeats Trump', 'Warren defeats Trump']

    df = pd.DataFrame(np.NaN, index=trump_columns, columns=all_ideologies)

    for ideo in all_ideologies_idx:

        ideo_df = csv_df.loc[csv_df['Ideology'] == ideo, :]

        for cand in trump_columns:

            subset_df = ideo_df.loc[~np.isnan(ideo_df[cand]), [cand, 'weight']]

            df.loc[cand, ideology_map()[ideo]] = sum(subset_df['weight'] * subset_df[cand])/subset_df.shape[0]

            #overwriting each loop
            all_ideo_df = csv_df.loc[~np.isnan(csv_df[cand]), [cand, 'weight']]
            df.loc[cand, 'All'] = sum(all_ideo_df['weight'] * all_ideo_df[cand])/all_ideo_df.shape[0]

    df.to_csv(ideology_fpath)


def condorcet_tables():
    """
    Returns a two condorcet tables as a pandas data frame with candidate names as row and column indices.
    One contains counts and the other contains percents.

    Each cell indicates the count/percentage of ballots that ranked the row-candidate over
    the column-candidate (including ballots that only ranked the row-candidate). When calculating percents,
    the denominator is each cell is the number of ballots that ranked the row-candidate OR the column-candidate.

    Symmetric cells about the diagonal should sum to 100 (for the percent table).
    """
    candidate_set = sorted(candidates_noUndecided())
    cleaned_ballots = cleaned()

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
        condorcet_count_df.loc[cand1, cand2] = cand1_vs_cand2_weightsum
        condorcet_count_df.loc[cand2, cand1] = cand2_vs_cand1_weightsum

        # calculate percent
        cand1_percent = (cand1_vs_cand2_weightsum / sum_weighted_ballots) * 100
        cand2_percent = (cand2_vs_cand1_weightsum / sum_weighted_ballots) * 100

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


def first_second_tables():

    candidate_set = sorted(candidates_noUndecided())
    cleaned_ballots = cleaned()

    # create data frame that will be populated and output
    percent_no_exhaust_df = pd.DataFrame(np.NaN, index=['first_choice', *candidate_set], columns=candidate_set)
    percent_df = pd.DataFrame(np.NaN, index=['first_choice', *candidate_set, 'exhaust'], columns=candidate_set)
    count_df = pd.DataFrame(np.NaN, index=['first_choice', *candidate_set, 'exhaust'], columns=candidate_set)

    # group ballots by first choice
    first_choices = {cand: [] for cand in candidate_set}
    for b in cleaned_ballots:
        if len(b['ranks']) >= 1:
            first_choices[b['ranks'][0]].append(b)
    # [first_choices[b[0]].append(b) for b in cleaned_ballots if len(b) >= 1]

    total_first_round_votes_weighted = float(0)
    for cand in first_choices:
        total_first_round_votes_weighted += sum([b['weight'] for b in first_choices[cand]])

    # add first choices to tables
    # and calculate second choices
    for cand in candidate_set:

        first_choice_count_weighted = sum([b['weight'] for b in first_choices[cand]])
        first_choice_percent = (first_choice_count_weighted / total_first_round_votes_weighted) * 100

        count_df.loc['first_choice', cand] = first_choice_count_weighted
        percent_df.loc['first_choice', cand] = first_choice_percent
        percent_no_exhaust_df.loc['first_choice', cand] = first_choice_percent

        ############################################################
        # calculate second choices, group second choices by candidate
        possible_second_choices = list(set(candidate_set) - {cand})
        second_choices = {backup_cand: [] for backup_cand in possible_second_choices + ['exhaust']}

        for b in first_choices[cand]:
            if len(b['ranks']) >= 2:
                second_choices[b['ranks'][1]].append(b)
            else:
                second_choices['exhaust'].append(b)
        # [second_choices[b[1]].append(b) if len(b) >= 2 else second_choices['exhaust'].append(b)
        # for b in first_choices[cand]]

        total_second_choices_weighted = float(0)
        total_second_choices_no_exhaust_weighted = float(0)
        for backup_cand in second_choices:
            total_second_choices_weighted += sum([b['weight'] for b in second_choices[backup_cand]])
            if backup_cand != 'exhaust':
                total_second_choices_no_exhaust_weighted += sum([b['weight'] for b in second_choices[backup_cand]])

        # count second choices and add to table
        for backup_cand in second_choices:

            second_choice_count_weighted = sum([b['weight'] for b in second_choices[backup_cand]])

            # if there are not backup votes fill with zeros
            if total_second_choices_weighted == 0:
                second_choice_percent = 0
            else:
                second_choice_percent = (second_choice_count_weighted / total_second_choices_weighted) * 100

            if total_second_choices_no_exhaust_weighted == 0:
                second_choice_percent_no_exhaust = 0
            else:
                second_choice_percent_no_exhaust = (second_choice_count_weighted / total_second_choices_no_exhaust_weighted) * 100

            count_df.loc[backup_cand, cand] = second_choice_count_weighted
            percent_df.loc[backup_cand, cand] = second_choice_percent
            if backup_cand != 'exhaust':
                percent_no_exhaust_df.loc[backup_cand, cand] = second_choice_percent_no_exhaust

    return count_df, percent_df, percent_no_exhaust_df

def rcv_single_winner():
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

    candidate_set = candidates_noUndecided()
    cand_outcomes = {cand:{'name': cand, 'round_eliminated': None, 'round_elected': None} for cand in candidate_set}

    rounds_trimmed, rounds_full, transfers, _ = deepcopy(until2rcv())

    # find round where a candidate has over 50% of active round votes
    rounds_slice_idx = 0
    done = False
    while not done:

        current_round_trimmed = rounds_trimmed[rounds_slice_idx]
        current_round_transfer = transfers[rounds_slice_idx]
        rounds_slice_idx += 1

        # check for finish condition
        round_finalists, round_tally = current_round_trimmed
        round_leader = round_finalists[0]

        round_total = sum(round_tally)

        # does round leader have the majority?
        # might need to adjust rounding here
        if round_tally[0]*2 > round_total:
            # update winner in cand_outcomes
            cand_outcomes[round_leader]['round_elected'] = rounds_slice_idx

            # update remaining round candidates as losing in this round
            for cand in cand_outcomes:
                if cand != round_leader and cand_outcomes[cand]['round_eliminated'] is None:
                    cand_outcomes[cand]['round_eliminated'] = rounds_slice_idx

            # update flag
            done = True

        else:
            # who lost this round (should be the only one with negative round transfer)?
            # update in candidate outcomes
            round_loser = [key for key, value in current_round_transfer.items() if value < 0]
            if len(round_loser) > 1:
                print('should only be one round loser with eliminated votes per round in single winner rcv. debug')
                exit(1)
            cand_outcomes[round_loser[0]]['round_eliminated'] = rounds_slice_idx

    # unnest candidate outcomes values
    cand_outcomes = [values for key, values in cand_outcomes.items()]

    return rounds_trimmed[0:rounds_slice_idx], rounds_full[0:rounds_slice_idx], \
           transfers[0:rounds_slice_idx], cand_outcomes


def until2rcv():
    """
    run an rcv election until there are two candidates remaining.
    This is might lead to more rounds than necessary to determine a winner.
    """

    # inputs
    candidate_set = candidates_noUndecided()
    bs = deepcopy(cleaned())

    # outputs
    rounds_trimmed = []
    rounds_full = []
    transfers = []
    cand_outcomes = {cand: {'name': cand, 'round_eliminated': None, 'round_elected': None} for cand in candidate_set}

    # other loop variables
    all_losers = []
    round_num = 0
    n_finalists = float('inf')

    while n_finalists > 2:

        round_num += 1

        # round results
        # tally ballots and reorder tallies
        # using active rankings for each ballot,
        # skipping empty ballots
        active_round_candidates = set([b['ranks'][0] for b in bs if b['ranks']])
        choices = Counter({cand: 0 for cand in active_round_candidates})
        for b in bs:
            if b['ranks']:
                choices[b['ranks'][0]] += b['weight']

        # sort round tallies
        round_results = list(zip(*choices.most_common()))
        # split round results into two tuples (index-matched)
        round_finalists, round_tallies = round_results
        n_finalists = len(round_finalists)

        # one the first round, eliminate any candidates with zero votes right away
        if round_num == 1:
            all_losers += [cand for cand in candidate_set if cand not in round_finalists]
            for cand in all_losers:
                # remove losers from ballots
                bs = [{'ranks': remove(cand, b['ranks']), 'weight': b['weight']} for b in bs]
                # update candidate outcomes
                cand_outcomes[cand]['round_eliminated'] = round_num

        # add in loser/no-vote candidates for full round record
        finalists_full = list(round_finalists) + all_losers
        tallies_full = list(round_tallies) + ([0] * len(all_losers))

        # find round loser
        loser_count = min(round_tallies)
        # in case of tied losers, randomly choose one to eliminate
        round_loser = choice([cand for cand, cand_tally in zip(round_finalists, round_tallies)
                              if cand_tally == loser_count])
        # update candidate outcome
        cand_outcomes[round_loser]['round_eliminated'] = round_num

        # calculate transfer from loser - find loser ballots
        round_loser_ballots = [b for b in bs if b['ranks'] and b['ranks'][0] == round_loser]
        # count distribution from loser to other candidates and exhaustion
        round_transfer = Counter({cand: 0 for cand in candidate_set})
        for b in round_loser_ballots:
            if len(b['ranks']) > 1:
                round_transfer[b['ranks'][1]] += b['weight']
            else:
                round_transfer['exhaust'] += b['weight']

        # record ballot loss from loser
        round_transfer[round_loser] = sum([b['weight'] for b in round_loser_ballots]) * -1

        # remove round loser from ballots, all ranking spots.
        # removing the round loser from all ranking spots now is equivalent
        # to waiting and skipping over an already-eliminated candidate
        # once they become the active ranking in a later round.
        bs = [{'ranks': remove(round_loser, b['ranks']), 'weight': b['weight']} for b in bs]

        # append round info to list
        transfers.append(round_transfer)
        all_losers.append(round_loser)
        rounds_trimmed.append(round_results)
        rounds_full.append([tuple(finalists_full), tuple(tallies_full)])

    # update winner
    cand_outcomes[round_finalists[0]]['round_elected'] = round_num

    # unnest candidate outcomes values
    cand_outcomes = [values for key, values in cand_outcomes.items()]

    return rounds_trimmed, rounds_full, transfers, cand_outcomes


def write_rcv():

    _, rounds_full, transfers, _ = rcv_single_winner()

    if len(rounds_full) != len(transfers):
        print('something fishy, debug')
        exit(1)
    else:
        num_rounds = len(rounds_full)

    row_names = list(candidates_noUndecided()) + ['exhaust']
    rcv_df = pd.DataFrame(np.NaN, index=row_names + ['colsum'], columns=['candidate'])
    rcv_df.loc[row_names + ['colsum'], 'candidate'] = row_names + ['colsum']

    for rnd in range(1, num_rounds + 1):

        rnd_info = {rnd_cand: rnd_tally for rnd_cand, rnd_tally in zip(*rounds_full[rnd-1])}
        rnd_info['exhaust'] = 0

        rnd_transfer = dict(transfers[rnd-1])

        # add round data
        for cand in row_names:

            #rnd_percent_col = 'r' + str(rnd) + '_percent'
            rnd_count_col = 'r' + str(rnd) + '_count'
            rnd_transfer_col = 'r' + str(rnd) + '_transfer'

            #rcv_df.loc[cand, rnd_percent_col] = round(100*(rnd_info[cand]/sum(rnd_info.values())))
            rcv_df.loc[cand, rnd_count_col] = rnd_info[cand]
            rcv_df.loc[cand, rnd_transfer_col] = rnd_transfer[cand]

        # maintain cumulative exhaust total
        if rnd != 1:
            last_rnd_count_col = 'r' + str(rnd-1) + '_count'
            last_rnd_transfer_col = 'r' + str(rnd-1) + '_transfer'
            rcv_df.loc['exhaust', rnd_count_col] = rcv_df.loc['exhaust', last_rnd_count_col] + \
                                                    rcv_df.loc['exhaust', last_rnd_transfer_col]

        # sum round columns
        rcv_df.loc['colsum', rnd_count_col] = sum(rcv_df.loc[row_names, rnd_count_col])
        rcv_df.loc['colsum', rnd_transfer_col] = sum(rcv_df.loc[row_names, rnd_transfer_col])
        #rcv_df.loc['colsum', rnd_percent_col] = sum(rcv_df.loc[row_names, rnd_percent_col])

    rcv_df.to_csv(rcv_fpath, index=False)


def main():

    # condorcet
    counts, percents = condorcet_tables()
    counts.to_csv(condorcet_count_fpath, float_format="%.2f")
    percents.to_csv(condorcet_percent_fpath, float_format="%.2f")

    # first second table
    counts, percents, percents_no_exhaust = first_second_tables()
    counts.to_csv(first_second_count_fpath, float_format="%.2f")
    percents.to_csv(first_second_percent_fpath, float_format="%.2f")
    percents_no_exhaust.to_csv(first_second_percent_noExhaust_fpath, float_format="%.2f")

    write_rcv()
    write_ideology()

    print('done')

if __name__ == '__main__':
    main()

