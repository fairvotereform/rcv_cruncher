from argparse import ArgumentParser
from pprint import pprint
import csv
import os
import pandas as pd

# cruncher imports
from scripts.contests import *
from scripts.ballot_stats import *
#from scripts.precincts import *
from scripts.tabulation import *
from scripts.rcv_variants import *

import scripts.cache_helpers as cache


def write_stats(contest):
    """
    Run each function in 'func_list' on contest
    """
    results = {}
    for f in contest['func_list']:
        results[f.__name__] = f(contest)

    contest['results_fid'].writerow([results[fun.__name__] for fun in contest['func_list']])


def stats_double_check(contest):

    ############################
    # calculated outputs
    all_candidates = candidates(contest)
    first_round_active = first_round_active_votes(contest)
    final_round_active = final_round_active_votes(contest)
    n_exhaust = total_exhausted(contest)
    n_undervote = total_undervote(contest)
    n_ballots = len(ballots(contest)['ranks'])
    n_ranked_single = ranked_single(contest)
    n_ranked_multiple = ranked_multiple(contest)

    n_first_round_exhaust_by_overvote = 0
    if contest['break_on_overvote']:
        n_first_round_exhaust_by_overvote = first_round_overvote(contest)

    n_first_round_exhaust_by_skipped_rankings = 0
    if contest['break_on_repeated_skipvotes']:
        n_first_round_exhaust_by_skipped_rankings = sum(i == 0 for i in repeated_skipvote_ind(contest))

    ############################
    # secondary crosschecks
    # add up numbers a second way to make sure they match

    # The number of exhausted ballots should equal
    # the difference between the first round active ballots and the final round active ballots
    # PLUS any ballot exhausted in the first round due to overvote or repeated skipped ranks
    n_exhaust_crosscheck = first_round_active - final_round_active + \
                           n_first_round_exhaust_by_overvote + n_first_round_exhaust_by_skipped_rankings

    # The number of undervote ballots should equal
    # the difference between the total number of ballots and
    # the first round active ballots,
    n_undervote_crosscheck = n_ballots - first_round_active - \
                             n_first_round_exhaust_by_overvote - n_first_round_exhaust_by_skipped_rankings

    n_ranked_single_crosscheck = sum(len(set(i) & all_candidates) == 1 for i in ballots(contest)['ranks'])
    n_ranked_multiple_crosscheck = sum(len(set(i) & all_candidates) > 1 for i in ballots(contest)['ranks'])

    problem = False
    if n_exhaust_crosscheck != n_exhaust:
        problem = True
    if n_undervote_crosscheck != n_undervote:
        problem = True
    if n_ranked_single_crosscheck != n_ranked_single:
        problem = True
    if n_ranked_multiple_crosscheck != n_ranked_multiple:
        problem = True

    if problem:
        print(' ********* stat_double_check: failed', end='')


def write_converted_cvr(contest):
    """
    Convert cvr into common csv format and write out
    """
    cvr = convert_cvr(contest)
    cvr.to_csv(contest['common_cvr_dir'] + "/" + contest["dop"] + ".csv", index=False)


def write_condorcet_tables(contest):
    """
    Calculate and write condorcet tables (both count and percents) for contest
    """
    counts, percents, condorcet_winner = condorcet_tables(contest)

    if condorcet_winner:
        condorcet_str = "condorcet winner: " + condorcet_winner
    else:
        condorcet_str = "condorcet winner: None"

    counts.index.name = condorcet_str
    percents.index.name = condorcet_str

    counts.to_csv(contest['condorcet_table_dir'] + "/" + contest["dop"] + "_count.csv", float_format="%.2f")
    percents.to_csv(contest['condorcet_table_dir'] + "/" + contest["dop"] + "_percent.csv", float_format="%.2f")


def write_first_second_tables(contest):
    """
    Calculate and write first choice - second choice tables (both count and percents) for contest
    """
    counts, percents, percents_no_exhaust = first_second_tables(contest)
    counts.to_csv(contest['first_second_table_dir'] + "/" + contest["dop"] + "_count.csv", float_format="%.2f")
    percents.to_csv(contest['first_second_table_dir'] + "/" + contest["dop"] + "_percent.csv", float_format="%.2f")
    percents_no_exhaust.to_csv(contest['first_second_table_dir'] + "/" + contest["dop"] + "_percent_no_exhaust.csv",
                               float_format="%.2f")


def prepare_candidate_details(contest):
    """
    Return pandas data frame of candidate info with round-by-round vote counts
    """
    raceID = contest['unique_id']
    rounds_full = round_by_round_full(contest)
    cand_outcomes = candidate_outcomes(contest)
    n_rounds = len(rounds_full)

    # reformat contest outputs into useful dicts
    cand_outcomes_dict = {d['name']: d for d in cand_outcomes}
    rounds_full_dict = [{cand: float(count) for cand, count in zip(*rnd_count)}
                        for rnd_count in rounds_full]

    colnames = ['raceID', 'candidate', 'round_elected', 'round_eliminated'] + \
               ['round_' + str(i) + '_vote' for i in range(1, n_rounds + 1)]

    cand_rows = []
    for cand in candidates(contest):
        cand_rows.append([raceID,
                          cand,
                          cand_outcomes_dict[cand]['round_elected'],
                          cand_outcomes_dict[cand]['round_eliminated']] + \
                         [d[cand] for d in rounds_full_dict])

    df = pd.DataFrame(cand_rows, columns=colnames)
    return df


def write_candidate_details(contest_set, candidate_details_fpath):
    """
    Concatenate all candidate details and write out file
    """
    df = pd.concat([contest['candidate_details'] for contest in contest_set if 'candidate_details' in contest],
                   axis=0, ignore_index=True, sort=False)
    df.to_csv(candidate_details_fpath, index=False)


def write_rcv(ctx):
    """
    Write out rcv contest round-by-round counts and transfers
    """
    # get rcv results
    rounds_full = round_by_round_full(ctx)
    transfers = round_by_round_transfers(ctx)

    if len(rounds_full) != len(transfers):
        print('something fishy, debug')
        exit(1)
    else:
        num_rounds = len(rounds_full)

    # setup data frame
    row_names = list(candidates(ctx)) + ['exhaust']
    rcv_df = pd.DataFrame(np.NaN, index=row_names + ['colsum'], columns=['candidate'])
    rcv_df.loc[row_names + ['colsum'], 'candidate'] = row_names + ['colsum']

    # loop through rounds
    for rnd in range(1, num_rounds + 1):

        rnd_info = {rnd_cand: rnd_tally for rnd_cand, rnd_tally in zip(*rounds_full[rnd-1])}
        rnd_info['exhaust'] = 0

        rnd_transfer = dict(transfers[rnd-1])

        # add round data
        for cand in row_names:

            rnd_percent_col = 'r' + str(rnd) + '_percent'
            rnd_count_col = 'r' + str(rnd) + '_count'
            rnd_transfer_col = 'r' + str(rnd) + '_transfer'

            rcv_df.loc[cand, rnd_percent_col] = round(float(100*(rnd_info[cand]/sum(rnd_info.values()))), 3)
            rcv_df.loc[cand, rnd_count_col] = float(rnd_info[cand])
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
        rcv_df.loc['colsum', rnd_percent_col] = sum(rcv_df.loc[row_names, rnd_percent_col])

    # remove count columns
    # for rnd in range(1, num_rounds + 1):
    #     rcv_df = rcv_df.drop('r' + str(rnd) + '_count', axis=1)

    rcv_df.to_csv(ctx['round_by_round_dir'] + '/' + ctx['dop'] + '.csv', index=False)


def main():

    # initialize global func dict across all cruncher imports
    # necessary for cache_helpers
    cache.set_global_dict(globals())

    ###########################
    # get the path of this file
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    ###########################
    # parse args
    p = ArgumentParser()
    p.add_argument('--skip_condorcet_tables', action='store_true')
    p.add_argument('--precincts', action='store_true')
    p.add_argument('--contest_set', default='all_contests')

    args = p.parse_args()
    skip_condorcet_tables = args.skip_condorcet_tables
    add_precinct_funcs = args.precincts
    contest_set_name = args.contest_set

    ##########################
    # confirm contest set
    contest_set_path = dname + '/contest_sets/' + contest_set_name
    if os.path.isdir(contest_set_path) is False:
        print(contest_set_name + ' is not an existing folder in contest_sets/')
        exit(1)

    ########################
    # cache outputs
    cache_dir = contest_set_path + '/cache'
    cache.set_cache_dir(cache_dir)

    ########################
    # results outputs
    results_dir = contest_set_path + '/results'
    if os.path.isdir(results_dir) is False:
        os.mkdir(results_dir)

    condorcet_table_dir = results_dir + '/condorcet'
    if os.path.isdir(condorcet_table_dir) is False:
        os.mkdir(condorcet_table_dir)

    first_second_table_dir = results_dir + '/first_second'
    if os.path.isdir(first_second_table_dir) is False:
        os.mkdir(first_second_table_dir)

    round_by_round_dir = results_dir + '/round_by_round'
    if os.path.isdir(round_by_round_dir) is False:
        os.mkdir(round_by_round_dir)

    candidate_details_fpath = results_dir + '/candidate_details.csv'
    single_winner_results_fpath = results_dir + '/single_winner.csv'
    multi_winner_results_fpath = results_dir + '/multi_winner.csv'

    ###########################
    # cvr conversion outputs
    common_cvr_dir = contest_set_path + '/common_cvr'
    if os.path.isdir(common_cvr_dir) is False:
        os.mkdir(common_cvr_dir)

    ###########################
    # read/build func list
    single_winner_func_fpath = contest_set_path + '/single_winner.txt'
    multi_winner_func_fpath = contest_set_path + '/multi_winner.txt'

    if os.path.isfile(single_winner_func_fpath):

        single_winner_func_file = open(single_winner_func_fpath)
        single_winner_func_list = [eval(i.strip('\n')) for i in single_winner_func_file]
        single_winner_func_file.close()

        # currently only applying precinct data to single_winner_output
        if add_precinct_funcs:
            single_winner_func_list += ethnicity_stats_func_list()
    else:
        print('no single_winner.txt function list found, no results will be written for single winner contests')
        single_winner_func_list = []

    if os.path.isfile(multi_winner_func_fpath):
        multi_winner_func_file = open(multi_winner_func_fpath)
        multi_winner_func_list = [eval(i.strip('\n')) for i in multi_winner_func_file]
        multi_winner_func_file.close()
    else:
        print('no multi_winner.txt function list found, no results will be written for multi winner contests')
        multi_winner_func_list = []

    ########################
    # load manifest
    contest_set = load_contest_set(contest_set_path)

    ########################
    # produce results

    single_winner_rcv_set = [rcv_single_winner]
    multi_winner_rcv_set = []
    #multi_winner_rcv_set = [rcv_multiWinner_thresh15, stv_fractional_ballot, stv_whole_ballot]

    # write stats files column names
    if single_winner_func_list:
        single_winner_results_fid = open(single_winner_results_fpath, 'w', newline='')
        single_winner_results_csv = csv.writer(single_winner_results_fid)
        # write column names
        single_winner_results_csv.writerow([fun.__name__ for fun in single_winner_func_list])
        # write column notes
        single_winner_results_csv.writerow([' '.join((fun.__doc__ or '').split())
                                            for fun in single_winner_func_list])

    if multi_winner_func_list:
        multi_winner_results_fid = open(multi_winner_results_fpath, 'w', newline='')
        multi_winner_results_csv = csv.writer(multi_winner_results_fid)
        # write column names
        multi_winner_results_csv.writerow([fun.__name__ for fun in multi_winner_func_list])
        # write column notes
        multi_winner_results_csv.writerow([' '.join((fun.__doc__ or '').split())
                                           for fun in multi_winner_func_list])

    # loop through contests
    no_stats_contests = []
    for contest in sorted(contest_set, key=lambda x: x['date']):

        print()
        print(contest['dop'], end='')

        contest['common_cvr_dir'] = common_cvr_dir
        write_converted_cvr(contest)

        contest['first_second_table_dir'] = first_second_table_dir
        write_first_second_tables(contest)

        contest['condorcet_table_dir'] = condorcet_table_dir
        write_condorcet_tables(contest)

        if contest['rcv_type'] in single_winner_rcv_set and single_winner_func_list:

            contest['func_list'] = single_winner_func_list
            contest['results_fid'] = single_winner_results_csv

        elif contest['rcv_type'] in multi_winner_rcv_set and multi_winner_func_list:

            contest['func_list'] = multi_winner_func_list
            contest['results_fid'] = multi_winner_results_csv

        else:  # no available rcv_type specified in contest_set, move to next one
            no_stats_contests.append(contest)
            continue

        contest['round_by_round_dir'] = round_by_round_dir
        write_rcv(contest)

        write_stats(contest)
        stats_double_check(contest)

        contest['candidate_details'] = prepare_candidate_details(contest)

    write_candidate_details(contest_set, candidate_details_fpath)

    if no_stats_contests:
        print("the following contests in the contest_set did not have an active rcv_type", end='')
        print(" and are therefore not included in the contest stats outputs: ")
        for contest in no_stats_contests:
            print(contest['contest'])


if __name__ == '__main__':
    main()

