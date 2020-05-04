from argparse import ArgumentParser

# cruncher imports
from scripts.definitions import *
from scripts.contests import *
from scripts.misc_tabulation import *
from scripts.ballots import *
from scripts.rcv_variants import *
from scripts.rcv_reporting import *
from scripts.rcv_base import *

import scripts.cache_helpers as cache

STATS_CHECK = True

def stats_double_check(contest):
    """
    Calculate several totals a second way to make sure some identity equations hold.
    """

    obj = RCV.run_rcv(contest)
    all_candidates = candidates(contest)
    ballot_ranks = ballots(contest)['ranks']
    cleaned_ranks = cleaned(contest)['ranks']
    ballot_weights = ballots(contest)['weight']
    n_ballots = sum(ballot_weights)

    undervotes = obj.undervote()
    n_undervote = obj.total_undervote()
    n_ranked_single = obj.ranked_single()
    n_ranked_multiple = obj.ranked_multiple()

    # right now just test first tabulations
    for iTab in [1]:

        ############################
        # calculated outputs
        first_round_active = obj.first_round_active_votes(tabulation_num=iTab)
        final_round_active = obj.final_round_active_votes(tabulation_num=iTab)
        n_exhaust = obj.total_exhausted(tabulation_num=iTab)

        ############################
        # intermediary recalculations
        # ballots which are only overvotes and skips

        first_round_exhausted = [True for under, b in zip(undervotes, cleaned_ranks) if not under and b == []]
        n_first_round_exhausted = sum(weight * flag for weight, flag in zip(ballot_weights, first_round_exhausted))

        ############################
        # secondary crosschecks
        # add up numbers a second way to make sure they match

        # The number of exhausted ballots should equal
        # the difference between the first round active ballots and the final round active ballots
        # PLUS any ballot exhausted in the first round due to overvote or repeated skipped ranks
        n_exhaust_crosscheck = first_round_active - final_round_active + n_first_round_exhausted

        # The number of undervote ballots should equal
        # the difference between the total number of ballots and
        # the first round active ballots,
        n_undervote_crosscheck = n_ballots - first_round_active - n_first_round_exhausted

        n_ranked_single_crosscheck = sum([weight for i, weight in zip(ballot_ranks, ballot_weights)
                                          if len(set(i) & all_candidates) == 1])

        n_ranked_multiple_crosscheck = sum([weight for i, weight in zip(ballot_ranks, ballot_weights)
                                            if len(set(i) & all_candidates) > 1])

        problem = False
        if round(n_exhaust_crosscheck, 3) != round(n_exhaust, 3):
            problem = True
        if round(n_undervote_crosscheck, 3) != round(n_undervote, 3):
            problem = True
        if round(n_ranked_single_crosscheck, 3) != round(n_ranked_single, 3):
            problem = True
        if round(n_ranked_multiple_crosscheck, 3) != round(n_ranked_multiple, 3):
            problem = True

        if problem:
            print(obj.unique_id(tabulation_num=iTab) + ' ********* stat_double_check: failed. debug')


def write_converted_cvr(contest, results_dir):
    """
    Convert cvr into common csv format and write out
    """
    outfile = results_dir + "/" + contest["dop"] + ".csv"
    if os.path.isfile(outfile) is False:
        cvr = convert_cvr(contest)
        cvr.to_csv(outfile, index=False)

def write_condorcet_tables(contest, results_dir):
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

    condorcet_table_dir = results_dir + '/condorcet'
    verifyDir(condorcet_table_dir)

    counts.to_csv(condorcet_table_dir + "/" + contest["dop"] + "_count.csv", float_format="%.2f")
    percents.to_csv(condorcet_table_dir + "/" + contest["dop"] + "_percent.csv", float_format="%.2f")

def write_first_second_tables(contest, results_dir):
    """
    Calculate and write first choice - second choice tables (both count and percents) for contest
    """
    counts, percents, percents_no_exhaust = first_second_tables(contest)

    first_second_table_dir = results_dir + '/first_second'
    verifyDir(first_second_table_dir)

    counts.to_csv(first_second_table_dir + "/" + contest["dop"] + "_count.csv", float_format="%.2f")
    percents.to_csv(first_second_table_dir + "/" + contest["dop"] + "_percent.csv", float_format="%.2f")
    percents_no_exhaust.to_csv(first_second_table_dir + "/" + contest["dop"] + "_percent_no_exhaust.csv",
                               float_format="%.2f")

def write_cumulative_ranking_tables(contest, results_dir):
    """
    Calculate and write cumulative ranking tables (both count and percent) for contest
    """
    counts, percents = cumulative_ranking_tables(contest)

    cumulative_ranking_dir = results_dir + '/cumulative_ranking'
    verifyDir(cumulative_ranking_dir)

    counts.to_csv(cumulative_ranking_dir + "/" + contest['dop'] + "_count.csv", float_format="%.2f")
    percents.to_csv(cumulative_ranking_dir + "/" + contest['dop'] + "_percent.csv", float_format="%.2f")

def write_rank_usage_tables(contest, results_dir):
    """
    Calculate and write rank usage statistics.
    """
    df = rank_usage_tables(contest)

    rank_usage_table_dir = results_dir + '/rank_usage'
    verifyDir(rank_usage_table_dir)

    df.to_csv(rank_usage_table_dir + "/" + contest['dop'] + '.csv', float_format='%.2f')

def write_opponent_crossover_tables(contest, results_dir):
    """
    Calculate crossover support between candidates and write table.
    """
    count_df, percent_df = crossover_table(contest)

    opponent_crossover_table_dir = results_dir + '/crossover_support'
    verifyDir(opponent_crossover_table_dir)

    count_df.to_csv(opponent_crossover_table_dir + "/" + contest['dop'] + '_count.csv', float_format='%.2f')
    percent_df.to_csv(opponent_crossover_table_dir + "/" + contest['dop'] + '_percent.csv', float_format='%.2f')

def write_first_to_finalist_tables(contest, results_dir):
    """
    Calculate distribution of ballots allocated to non-winners during first round and their transfer
    to eventual winners.
    """
    df = first_choice_to_finalist_table(contest)

    first_to_finalist_table_dir = results_dir + '/first_choice_to_finalist_tab1'
    verifyDir(first_to_finalist_table_dir)

    df.to_csv(first_to_finalist_table_dir + '/' + contest['dop'] + '.csv', float_format='%.2f')

def prepare_candidate_details(obj):
    """
    Return pandas data frame of candidate info with round-by-round vote counts
    """
    all_dfs = []

    for iTab in range(1, obj.n_tabulations()+1):

        raceID = obj.unique_id(tabulation_num=iTab)
        n_rounds = obj.n_rounds(tabulation_num=iTab)

        # get rcv results
        rounds_full = [obj.get_round_full_tally_tuple(i, tabulation_num=iTab) for i in range(1, n_rounds+1)]
        cand_outcomes = obj.get_candidate_outcomes(tabulation_num=iTab)

        # reformat contest outputs into useful dicts
        cand_outcomes_dict = {d['name']: d for d in cand_outcomes}
        rounds_full_dict = [{cand: float(count) for cand, count in zip(*rnd_count)}
                            for rnd_count in rounds_full]

        # reorder candidate names
        # winners in ascending order of round won
        # followed by losers in descending order of round lost
        reorder_dicts = []
        for d in cand_outcomes:

            # don't add candidates if they received zero votes in the first round.
            if rounds_full_dict[0][d['name']] == 0:
                continue

            if d['round_elected']:
                d['order'] = -1 * (1/d['round_elected'])
            else:
                d['order'] = 1/d['round_eliminated']

            reorder_dicts.append(d)

        ordered_candidates_names = [d['name'] for d in sorted(reorder_dicts, key=lambda x: x['order'])]

        # create table
        colnames = ['raceID', 'candidate', 'round_elected', 'round_eliminated'] + \
                   ['round_' + str(i) + '_vote' for i in range(1, n_rounds + 1)]

        # assemble rows
        cand_rows = []
        for cand in ordered_candidates_names:

            cand_rows.append([raceID,
                              cand,
                              cand_outcomes_dict[cand]['round_elected'],
                              cand_outcomes_dict[cand]['round_eliminated']] + \
                             [d[cand] for d in rounds_full_dict])

        df = pd.DataFrame(cand_rows, columns=colnames)
        all_dfs.append(df)

    return all_dfs


def write_candidate_details(all_detail_dfs, results_dir):
    """
    Concatenate all candidate details and write out file
    """
    df = pd.concat(all_detail_dfs, axis=0, ignore_index=True, sort=False)
    df.to_csv(results_dir + '/candidate_details.csv', index=False)


def write_rcv(obj, results_dir):
    """
    Write out rcv contest round-by-round counts and transfers
    """

    for iTab in range(1, obj.n_tabulations()+1):

        num_rounds = obj.n_rounds(tabulation_num=iTab)

        # get rcv results
        rounds_full = [obj.get_round_full_tally_tuple(i, tabulation_num=iTab) for i in range(1, num_rounds+1)]
        transfers = [obj.get_round_transfer_dict(i, tabulation_num=iTab) for i in range(1, num_rounds+1)]

        # setup data frame
        row_names = list(candidates(obj.ctx)) + ['exhaust']
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
                rcv_df.loc[cand, rnd_transfer_col] = float(rnd_transfer[cand])

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

        round_by_round_dir = results_dir + '/round_by_round'
        verifyDir(round_by_round_dir)

        if obj.n_tabulations() > 1:
            rcv_df.to_csv(round_by_round_dir + '/' + obj.ctx['dop'] + '_tab' + str(iTab) + '.csv', index=False)
        else:
            rcv_df.to_csv(round_by_round_dir + '/' + obj.ctx['dop'] + '.csv', index=False)

def main():

    ###########################
    # get the path of this file
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    # initialize global func dict across all cruncher imports
    # necessary for cache_helpers
    gbls = globals()
    gbls.update({RCV.run_rcv.__name__: RCV.run_rcv})
    cache.set_global_dict(gbls)

    ###########################
    # parse args
    p = ArgumentParser()
    p.add_argument('--contest_set', default='all_contests')

    args = p.parse_args()
    contest_set_name = args.contest_set

    ##########################
    # confirm contest set
    contest_set_path = dname + '/contest_sets/' + contest_set_name
    verifyDir(contest_set_path, make_if_missing=False, error_msg_tail='is not an existing folder in contest_sets')

    ###########################
    # remove old time files
    time_fpath = "contest_sets/time.csv"
    if os.path.isfile(time_fpath):
        os.remove(time_fpath)

    ########################
    # cache outputs
    cache_dir = contest_set_path + '/cache'
    cache.set_cache_dir(cache_dir)

    ########################
    # check results dir
    results_dir = contest_set_path + '/results'
    verifyDir(results_dir)

    ########################
    # load manifest
    contest_set = load_contest_set(contest_set_path)

    ########################
    # confirm parsed cvrs

    # check results dir
    cvr_dir = contest_set_path + '/common_cvr'
    verifyDir(cvr_dir)
    set_cvr_dir(cvr_dir)

    for idx, contest in enumerate(sorted(contest_set, key=lambda x: x['year'])):
        print('convert cvr: ' + str(idx) + ' of ' + str(len(contest_set)) + ' ' + contest['dop'], end='')
        write_converted_cvr(contest, cvr_dir)
        print('\b' * 100, end='')
    print('convert cvr: ' + str(len(contest_set)) + ' of ' + str(len(contest_set)) + ' contests complete')

    ########################
    # read output config
    output_config = read_output_config(contest_set_path)
    if not any(output_config.values()):
        print("no outputs marked as True in output_config.csv. Exiting.")
        return

    ########################
    # produce results
    rcv_variant_names = list(get_rcv_dict().keys())
    rcv_variant_df_dict = {variant_name: [] for variant_name in rcv_variant_names}
    all_rcv_variants = []

    # remove un-implemented contest types
    invalid_contests = []
    valid_contests = []
    for contest in sorted(contest_set, key=lambda x: x['year']):

        rcv_variant_name = contest['rcv_type'].__name__
        if rcv_variant_name in rcv_variant_df_dict:
            valid_contests.append(contest)
        else:
            invalid_contests.append(dop(contest))

    # loop through contests and tabulate the elections
    for idx, contest in enumerate(valid_contests):

        print('tabulation: ' + str(idx) + ' of ' + str(len(valid_contests)) + ' ' + contest['dop'], end='')

        # create RCV obj
        rcv_obj = RCV.run_rcv(contest)
        # add to lists
        rcv_variant_name = contest['rcv_type'].__name__
        rcv_variant_df_dict[rcv_variant_name].append(rcv_obj)
        all_rcv_variants.append(rcv_obj)

        print('\b' * 100, end='')

    print('tabulation: ' + str(len(valid_contests)) + ' of ' + str(len(valid_contests)) + ' contests complete')

    # stats double check
    if STATS_CHECK:
        print('--double check stats ...')
        for contest in valid_contests:
            stats_double_check(contest)

    ########################
    # results outputs

    ########################
    # RESULTS-BASED OUTPUTS

    # write per-variant outputs
    if 'per_rcv_type_stats' in output_config and output_config['per_rcv_type_stats']:
        for idx, variant in enumerate(rcv_variant_df_dict.keys()):
            print('per_rcv_type_stats: ' + str(idx) + ' of ' +
                  str(len(rcv_variant_df_dict.keys())) + ' ' + variant, end='')
            if rcv_variant_df_dict[variant]:
                df = pd.concat([obj.tabulation_stats_df() for obj in rcv_variant_df_dict[variant]],
                               axis=0, ignore_index=True, sort=False)
                df.to_csv(results_dir + '/' + variant + '.csv', index=False)
            print('\b' * 100, end='')
        print('per_rcv_type_stats: ' + str(len(rcv_variant_df_dict.keys())) + ' of ' +
              str(len(rcv_variant_df_dict.keys())) + ' groups complete')

    # write per-group outputs
    if 'per_rcv_group_stats' in output_config and output_config['per_rcv_group_stats']:
        group_set = set(obj.variant_group() for obj in all_rcv_variants)
        for idx, group in enumerate(group_set):
            print('per_rcv_group_stats: ' + str(idx) + ' of ' + str(len(group_set)) + ' ' + group, end='')
            group_objs = [obj for obj in all_rcv_variants if obj.variant_group() == group]
            df = pd.concat([obj.contest_stats_df() for obj in group_objs],
                           axis=0, ignore_index=True, sort=False)
            df.to_csv(results_dir + '/group_' + group + '.csv', index=False)
            print('\b' * 100, end='')
        print('per_rcv_group_stats: ' + str(len(group_set)) + ' of ' + str(len(group_set)) + ' groups complete')

    if 'round_by_round' in output_config and output_config['round_by_round']:
        for idx, contest in enumerate(all_rcv_variants):
            print('round_by_round: ' + str(idx) + ' of ' +
                  str(len(all_rcv_variants)) + ' ' + contest.ctx['dop'], end='')
            write_rcv(contest, results_dir)
            print('\b' * 100, end='')
        print('round_by_round: ' + str(len(all_rcv_variants)) + ' of ' +
              str(len(all_rcv_variants)) + ' contests complete')

    if 'candidate_details' in output_config and output_config['candidate_details']:
        candidate_details_dfs = []
        for idx, contest in enumerate(all_rcv_variants):
            print('candidate_details: ' + str(idx) + ' of ' +
                  str(len(all_rcv_variants)) + ' ' + contest.ctx['dop'], end='')
            candidate_details_dfs.append(prepare_candidate_details(contest))
            print('\b' * 100, end='')
        write_candidate_details(flatten_list(candidate_details_dfs), results_dir)
        print('candidate_details: ' + str(len(all_rcv_variants)) + ' of ' +
              str(len(all_rcv_variants)) + ' contests complete')

    ################
    # BALLOT-BASED OUTPUTS

    if 'condorcet' in output_config and output_config['condorcet']:
        for idx, contest in enumerate(valid_contests):
            print('condorcet: ' + str(idx) + ' of ' + str(len(valid_contests)) + ' ' + contest['dop'], end='')
            write_condorcet_tables(contest, results_dir)
            print('\b' * 100, end='')
        print('condorcet: ' + str(len(valid_contests)) + ' of ' + str(len(valid_contests)) + ' contests complete')

    if 'first_second_choices' in output_config and output_config['first_second_choices']:
        for idx, contest in enumerate(valid_contests):
            print('first_second_choices: ' + str(idx) + ' of ' +
                  str(len(valid_contests)) + ' ' + contest['dop'], end='')
            write_first_second_tables(contest, results_dir)
            print('\b' * 100, end='')
        print('first_second_choices: ' + str(len(valid_contests)) + ' of ' + str(len(valid_contests)) + ' contests complete')

    if 'cumulative_rankings' in output_config and output_config['cumulative_rankings']:
        for idx, contest in enumerate(valid_contests):
            print('cumulative_rankings: ' + str(idx) + ' of ' + str(len(valid_contests)) + ' ' + contest['dop'], end='')
            write_cumulative_ranking_tables(contest, results_dir)
            print('\b' * 100, end='')
        print('cumulative_rankings: ' + str(len(valid_contests)) + ' of ' + str(len(valid_contests)) + ' contests complete')

    if 'rank_usage' in output_config and output_config['rank_usage']:
        for idx, contest in enumerate(valid_contests):
            print('rank_usage: ' + str(idx) + ' of ' + str(len(valid_contests)) + ' ' + contest['dop'], end='')
            write_rank_usage_tables(contest, results_dir)
            print('\b' * 100, end='')
        print('rank_usage: ' + str(len(valid_contests)) + ' of ' + str(len(valid_contests)) + ' contests complete')

    if 'crossover_support' in output_config and output_config['crossover_support']:
        for idx, contest in enumerate(valid_contests):
            print('crossover_support: ' + str(idx) + ' of ' + str(len(valid_contests)) + ' ' + contest['dop'], end='')
            write_opponent_crossover_tables(contest, results_dir)
            print('\b' * 100, end='')
        print('crossover_support: ' + str(len(valid_contests)) + ' of ' + str(len(valid_contests)) + ' contests complete')

    if 'first_choice_to_finalist' in output_config and output_config['first_choice_to_finalist']:
        for idx, contest in enumerate(valid_contests):
            print('first_choice_to_finalist: ' + str(idx) + ' of ' +
                  str(len(valid_contests)) + ' ' + contest['dop'], end='')
            write_first_to_finalist_tables(contest, results_dir)
            print('\b' * 100, end='')
        print('first_choice_to_finalist: ' + str(len(valid_contests)) + ' of ' +
          str(len(valid_contests)) + ' contests complete')

    if invalid_contests:
        print()
        print("the following contests in the contest_set did not have an programmed rcv_type")
        print("and are therefore not included in the contest stats outputs: ")
        for contest in invalid_contests:
            print(contest)


if __name__ == '__main__':
    main()

