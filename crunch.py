from argparse import ArgumentParser
from pprint import pprint
import csv
import os
import pandas as pd

# cruncher imports
from scripts.contests import *
from scripts.ballot_stats import *
from scripts.precincts import *
from scripts.tabulation import *

import scripts.cache_helpers as cache


def write_stats(contest):
    """
    Run each function in 'func_list' on contest
    """
    results = {}
    for f in contest['func_list']:
        results[f.__name__] = f(contest)

    contest['results_fid'].writerow([results[fun.__name__] for fun in contest['func_list']])


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
    counts, percents, _ = condorcet_tables(contest)
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

    candidate_details_dir = results_dir + '/candidate_details'
    if os.path.isdir(candidate_details_dir) is False:
        os.mkdir(candidate_details_dir)

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
    multi_winner_rcv_set = [rcv_multiWinner_thresh15, stv_fractional_ballot]
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

        print(contest['dop'])

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

        write_stats(contest)
        #write_candidate_details(contest)

    if no_stats_contests:
        print("the following contests in the contest_set did not have an active rcv_type", end='')
        print(" and are therefore not included in the contest stats outputs: ")
        for contest in no_stats_contests:
            print(contest['contest'])


if __name__ == '__main__':
    main()

