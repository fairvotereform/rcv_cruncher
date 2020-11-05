import shutil
from argparse import ArgumentParser
from shutil import copyfile

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
TABULATION_CHECK = True

def stats_check(obj):
    """
    Calculate several totals a second way to make sure some identity equations hold.
    """

    all_candidates = candidates(obj.ctx)
    ballot_ranks = ballots(obj.ctx)['ranks']
    cleaned_ranks = cleaned(obj.ctx)['ranks']
    ballot_weights = ballots(obj.ctx)['weight']
    n_ballots = sum(ballot_weights)

    undervotes = obj.undervote()
    n_undervote = obj.total_undervote()
    n_ranked_single = obj.ranked_single()
    n_ranked_multiple = obj.ranked_multiple()

    debug_ids = []
    # right now just test first tabulations
    for iTab in [1]:

        ############################
        # calculated outputs

        weight_distribs = obj.get_final_weight_distrib(tabulation_num=iTab)
        weight_distrib_sum = sum([sum(i[1] for i in weight_distrib) for weight_distrib in weight_distribs])

        first_round_active = obj.first_round_active_votes(tabulation_num=iTab)
        final_round_active = obj.final_round_active_votes(tabulation_num=iTab)
        n_exhaust = obj.total_posttally_exhausted(tabulation_num=iTab) + obj.total_pretally_exhausted(tabulation_num=iTab)

        ############################
        # intermediary recalculations
        # ballots which are only overvotes and skips

        n_first_round_exhausted = obj.total_ballots() - obj.total_undervote() - obj.first_round_active_votes(tabulation_num=iTab)

        tab_exhausts = [float(obj.get_round_transfer_dict(iRound, tabulation_num=iTab)['exhaust']) for
                                 iRound in range(1, obj.n_rounds(tabulation_num=iTab)+1)]
        cumulative_exhaust = sum(i for i in tab_exhausts if not np.isnan(i))

        ############################
        # secondary crosschecks
        # add up numbers a second way to make sure they match

        # The number of exhausted ballots should equal
        # the difference between the first round active ballots and the final round active ballots
        # PLUS any ballot exhausted in the first round due to overvote or repeated skipped ranks
        n_exhaust_crosscheck1 = first_round_active - final_round_active + n_first_round_exhausted
        n_exhaust_crosscheck2 = cumulative_exhaust + n_first_round_exhausted

        # The number of exhausted ballots calculated in the reporting class should match
        # the sum total of exhausted ballots contained in all the round transfers

        # The number of undervote ballots should equal
        # the difference between the total number of ballots and
        # the first round active ballots,
        n_undervote_crosscheck = n_ballots - first_round_active - n_first_round_exhausted

        n_ranked_single_crosscheck = sum([weight for i, weight in zip(ballot_ranks, ballot_weights)
                                          if len(set(i) & all_candidates) == 1])

        n_ranked_multiple_crosscheck = sum([weight for i, weight in zip(ballot_ranks, ballot_weights)
                                            if len(set(i) & all_candidates) > 1])

        problem = False
        if float(weight_distrib_sum) != float(n_ballots):
            problem = True
        if round(n_exhaust_crosscheck1, 3) != round(n_exhaust, 3):
            problem = True
        if round(n_exhaust_crosscheck2, 3) != round(n_exhaust, 3):
            problem = True
        if round(n_undervote_crosscheck, 3) != round(n_undervote, 3):
            problem = True
        if round(n_ranked_single_crosscheck, 3) != round(n_ranked_single, 3):
            problem = True
        if round(n_ranked_multiple_crosscheck, 3) != round(n_ranked_multiple, 3):
            problem = True

        if problem:
            debug_ids.append((obj.unique_id(tabulation_num=iTab), obj.ctx['contest_set_line_df']))
    return debug_ids

def tabulation_check(obj):

    debug_ids = []

    for iTab in range(1, obj.n_tabulations() + 1):

        reported = "reported_results/_completed/" + obj.unique_id(tabulation_num=iTab) + '.csv'
        if os.path.isfile(reported):

            # get tabulated and reported results
            reported_final_round_df = pd.read_csv(reported)
            reported_dict = {r['candidates']: r['final_round_count'] for idx, r in reported_final_round_df.iterrows()}

            tabulated_final_round_dict = obj.get_round_tally_dict(round_num=obj.n_rounds(tabulation_num=iTab),
                                                                  tabulation_num=iTab)
            tabulated_final_round_dict['exhaust'] = obj.total_posttally_exhausted(tabulation_num=iTab)

            tabulated_win_threshold = obj.win_threshold(tabulation_num=iTab)

            # do tabulations match without modification?
            match = True
            for tabulated_cand in tabulated_final_round_dict:
                if tabulated_final_round_dict[tabulated_cand] != reported_dict[tabulated_cand]:
                    match = False

            # if there was a mismatch, does bringing winners down to threshold create a match?
            if not match and tabulated_win_threshold != 'NA':

                for tabulated_cand in tabulated_final_round_dict:
                    if tabulated_cand != 'exhaust':
                        if tabulated_final_round_dict[tabulated_cand] > tabulated_win_threshold:
                            diff = tabulated_final_round_dict[tabulated_cand] - tabulated_win_threshold
                            tabulated_final_round_dict['exhaust'] += diff
                            tabulated_final_round_dict[tabulated_cand] = tabulated_win_threshold

                match = True
                for tabulated_cand in tabulated_final_round_dict:
                    if tabulated_final_round_dict[tabulated_cand] != reported_dict[tabulated_cand]:
                        match = False

            # still a mismatch, record the mismatch
            if not match:
                debug_ids.append(("mismatch with reported results for " + obj.unique_id(tabulation_num=iTab),
                                  obj.ctx['contest_set_line_df']))

        else:
            debug_ids.append(("missing reported results for " + obj.unique_id(tabulation_num=iTab),
                              obj.ctx['contest_set_line_df']))

    return debug_ids

def write_converted_cvr(contest, results_dir):
    """
    Convert cvr into common csv format and write out
    """
    outfile = results_dir + "/" + contest["unique_id"] + ".csv"
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

    counts.to_csv(condorcet_table_dir + "/" + contest["unique_id"] + "_count.csv", float_format="%.2f")
    percents.to_csv(condorcet_table_dir + "/" + contest["unique_id"] + "_percent.csv", float_format="%.2f")

def write_first_second_tables(contest, results_dir):
    """
    Calculate and write first choice - second choice tables (both count and percents) for contest
    """
    counts, percents, percents_no_exhaust = first_second_tables(contest)

    first_second_table_dir = results_dir + '/first_second'
    verifyDir(first_second_table_dir)

    counts.to_csv(first_second_table_dir + "/" + contest["unique_id"] + "_count.csv", float_format="%.2f")
    percents.to_csv(first_second_table_dir + "/" + contest["unique_id"] + "_percent.csv", float_format="%.2f")
    percents_no_exhaust.to_csv(first_second_table_dir + "/" + contest["unique_id"] + "_percent_no_exhaust.csv",
                               float_format="%.2f")

def write_cumulative_ranking_tables(contest, results_dir):
    """
    Calculate and write cumulative ranking tables (both count and percent) for contest
    """
    counts, percents = cumulative_ranking_tables(contest)

    cumulative_ranking_dir = results_dir + '/cumulative_ranking'
    verifyDir(cumulative_ranking_dir)

    counts.to_csv(cumulative_ranking_dir + "/" + contest['unique_id'] + "_count.csv", float_format="%.2f")
    percents.to_csv(cumulative_ranking_dir + "/" + contest['unique_id'] + "_percent.csv", float_format="%.2f")

def write_rank_usage_tables(contest, results_dir):
    """
    Calculate and write rank usage statistics.
    """
    df = rank_usage_tables(contest)

    rank_usage_table_dir = results_dir + '/rank_usage'
    verifyDir(rank_usage_table_dir)

    df.to_csv(rank_usage_table_dir + "/" + contest['unique_id'] + '.csv', float_format='%.2f')

def write_opponent_crossover_tables(contest, results_dir):
    """
    Calculate crossover support between candidates and write table.
    """
    count_df, percent_df = crossover_table(contest)

    opponent_crossover_table_dir = results_dir + '/crossover_support'
    verifyDir(opponent_crossover_table_dir)

    count_df.to_csv(opponent_crossover_table_dir + "/" + contest['unique_id'] + '_count.csv', float_format='%.2f')
    percent_df.to_csv(opponent_crossover_table_dir + "/" + contest['unique_id'] + '_percent.csv', float_format='%.2f')

def write_first_to_finalist_tables(contest, results_dir):
    """
    Calculate distribution of ballots allocated to non-winners during first round and their transfer
    to eventual winners.
    """
    df = first_choice_to_finalist_table(contest)

    first_to_finalist_table_dir = results_dir + '/first_choice_to_finalist_tab1'
    verifyDir(first_to_finalist_table_dir)

    df.to_csv(first_to_finalist_table_dir + '/' + contest['unique_id'] + '_tab1.csv', float_format='%.2f')

def prepare_candidate_details(obj):
    """
    Return pandas data frame of candidate info with round-by-round vote counts
    """
    all_dfs = []

    for iTab in range(1, obj.n_tabulations()+1):

        raceID = obj.unique_id(tabulation_num=iTab)
        n_rounds = obj.n_rounds(tabulation_num=iTab)

        # get rcv results
        rounds_full = [obj.get_round_tally_tuple(i, tabulation_num=iTab) for i in range(1, n_rounds + 1)]
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

            # don't add candidates if they received zero votes throughout the contest.
            if sum(rounds_dict[d['name']] for rounds_dict in rounds_full_dict) == 0:
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

def write_rcv_rounds(obj, results_dir):
    """
    Write out rcv contest round-by-round counts and transfers
    """
    for iTab in range(1, obj.n_tabulations()+1):

        num_rounds = obj.n_rounds(tabulation_num=iTab)

        first_round_exhaust = obj.total_pretally_exhausted(tabulation_num=iTab)

        # get rcv results
        rounds_full = [obj.get_round_tally_tuple(i, tabulation_num=iTab) for i in range(1, num_rounds + 1)]
        transfers = [obj.get_round_transfer_dict(i, tabulation_num=iTab) for i in range(1, num_rounds + 1)]

        # setup data frame
        row_names = list(candidates_merged_writeIns(obj.ctx)) + ['exhaust']
        rcv_df = pd.DataFrame(np.NaN, index=row_names + ['colsum'], columns=['candidate'])
        rcv_df.loc[row_names + ['colsum'], 'candidate'] = row_names + ['colsum']

        # loop through rounds
        for rnd in range(1, num_rounds + 1):

            rnd_info = {rnd_cand: rnd_tally for rnd_cand, rnd_tally in zip(*rounds_full[rnd-1])}
            rnd_info['exhaust'] = 0

            rnd_transfer = dict(transfers[rnd-1])

            # add round data
            for cand in row_names:

                rnd_percent_col = 'r' + str(rnd) + '_active_percent'
                rnd_count_col = 'r' + str(rnd) + '_count'
                rnd_transfer_col = 'r' + str(rnd) + '_transfer'

                rcv_df.loc[cand, rnd_percent_col] = round(float(100*(rnd_info[cand]/sum(rnd_info.values()))), 3)
                rcv_df.loc[cand, rnd_count_col] = float(rnd_info[cand])
                rcv_df.loc[cand, rnd_transfer_col] = float(rnd_transfer[cand])

            # maintain cumulative exhaust total
            if rnd == 1:
                rcv_df.loc['exhaust', rnd_count_col] = first_round_exhaust
            else:
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

        rcv_df.to_csv(round_by_round_dir + '/' + obj.ctx['unique_id'] + '_tab' + str(iTab) + '.csv', index=False)

def write_ballot_debug_info(obj, results_dir):
    """
    Write ballot debug CVR
    """
    for iTab in range(1, obj.n_tabulations()+1):

        ballot_debug_df = obj.ballot_debug_df(tabulation_num=iTab)

        output_dir = results_dir + '/ballot_stats_debug'
        verifyDir(output_dir)

        ballot_debug_df.to_csv(output_dir + "/" + obj.ctx['unique_id'] + '_ballot_debug.csv', index=False)

def main():

    ###########################
    # project dir
    dname = project_root()
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
    p.add_argument('--make_debug_contest_set', action='store_true')

    args = p.parse_args()
    contest_set_name = args.contest_set
    make_debug_contest_set = args.make_debug_contest_set

    ##########################
    # confirm contest set
    contest_set_path = dname + '/contest_sets/' + contest_set_name
    verifyDir(contest_set_path, make_if_missing=False, error_msg_tail='is not an existing folder in contest_sets')

    ###########################
    # remove old time files
    time_fpath = "contest_sets/variant_time.csv"
    if os.path.isfile(time_fpath):
        os.remove(time_fpath)

    time_fpath = "contest_sets/reporting_time.csv"
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

    # copy these scripts into results
    result_log_dir = results_dir + "/_log"
    verifyDir(result_log_dir)

    shutil.copy2("crunch.py", result_log_dir)
    for script_file in glob.glob("scripts/*"):
        if script_file.split("\\")[1][0] != "_":
            shutil.copy2(script_file, result_log_dir)

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
        print('convert cvr: ' + str(idx) + ' of ' + str(len(contest_set)) + ' ' + contest['unique_id'], end='')
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
    candidate_details_dfs = []
    rcv_variant_stats_df_dict = {variant_name: [] for variant_name in get_rcv_dict().keys()}
    rcv_group_stats_df_dict = {variant_group: [] for variant_group in
                               set(g.variant_group() for g in get_rcv_dict().values())}

    # remove un-implemented contest types
    invalid_contests = []
    valid_contests = []
    for contest in sorted(contest_set, key=lambda x: x['year']):

        rcv_variant_name = contest['rcv_type'].__name__
        if rcv_variant_name in rcv_variant_stats_df_dict:
            valid_contests.append(contest)
        else:
            invalid_contests.append(contest)

    stats_debugs = []
    progress_total = 15
    # loop through contests and tabulate the elections
    for idx, contest in enumerate(valid_contests):

        print(str(idx+1) + ' of ' + str(len(valid_contests)) + ' ' + contest['unique_id'] + ' ...')

        # create RCV obj + tabulate
        progress(1, progress_total, status="tabulating")
        rcv_obj = RCV.run_rcv(contest)

        # stats double check
        if STATS_CHECK:
            progress(2, progress_total, status="check stats")
            stats_debugs.append(stats_check(rcv_obj))

        ########################
        # RESULTS-BASED OUTPUTS

        if 'per_rcv_type_stats' in output_config and output_config['per_rcv_type_stats']:
            progress(4, progress_total, status="store tabulation stats")
            if not rcv_variant_stats_df_dict[rcv_obj.__class__.__name__]:
                rcv_variant_stats_df_dict[rcv_obj.__class__.__name__].append(rcv_obj.tabulation_stats_comments_df())
            rcv_variant_stats_df_dict[rcv_obj.__class__.__name__].append(rcv_obj.tabulation_stats_df())

        if 'per_rcv_group_stats' in output_config and output_config['per_rcv_group_stats']:
            progress(5, progress_total, status="store contest stats")
            if not rcv_group_stats_df_dict[rcv_obj.variant_group()]:
                rcv_group_stats_df_dict[rcv_obj.variant_group()].append(rcv_obj.contest_stats_comments_df())
            rcv_group_stats_df_dict[rcv_obj.variant_group()].append(rcv_obj.contest_stats_df())

        if 'candidate_details' in output_config and output_config['candidate_details']:
            progress(6, progress_total, status="store candidate details")
            candidate_details_dfs.append(prepare_candidate_details(rcv_obj))

        if 'round_by_round' in output_config and output_config['round_by_round']:
            progress(7, progress_total, status="write round by round results")
            write_rcv_rounds(rcv_obj, results_dir)

        if 'ballot_stats_debug' in output_config and output_config['ballot_stats_debug']:
            progress(8, progress_total, status="ballot stats debug")
            write_ballot_debug_info(rcv_obj, results_dir)

        ################
        # BALLOT-BASED OUTPUTS

        if 'condorcet' in output_config and output_config['condorcet']:
            progress(9, progress_total, status="write condorcet table")
            write_condorcet_tables(contest, results_dir)

        if 'first_second_choices' in output_config and output_config['first_second_choices']:
            progress(10, progress_total, status="write first and second choices table")
            write_first_second_tables(contest, results_dir)

        if 'cumulative_rankings' in output_config and output_config['cumulative_rankings']:
            progress(11, progress_total, status="write cumulative ranking table")
            write_cumulative_ranking_tables(contest, results_dir)

        if 'rank_usage' in output_config and output_config['rank_usage']:
            progress(12, progress_total, status="write rank usage table")
            write_rank_usage_tables(contest, results_dir)

        if 'crossover_support' in output_config and output_config['crossover_support']:
            progress(13, progress_total, status="write crossover support table")
            write_opponent_crossover_tables(contest, results_dir)

        if 'first_choice_to_finalist' in output_config and output_config['first_choice_to_finalist']:
            progress(14, progress_total, status="write first choice to finalist table")
            write_first_to_finalist_tables(contest, results_dir)

        progress(15, progress_total, status="")
        print("")

    print()
    print("Write stored results")
    if 'per_rcv_group_stats' in output_config and output_config['per_rcv_group_stats']:
        print("write group stats ...")
        for group in rcv_group_stats_df_dict:
            if rcv_group_stats_df_dict[group]:
                df = pd.concat(rcv_group_stats_df_dict[group], axis=0, ignore_index=True, sort=False)
                df.to_csv(results_dir + '/group_' + group + '.csv', index=False)

    if 'per_rcv_group_stats_masterDBfmt' in output_config and output_config['per_rcv_group_stats_masterDBfmt']:
        print("write group stats in masterDB order ...")
        for group in rcv_group_stats_df_dict:
            format_fpath = "master_db_format/" + group + "_columns.csv"
            if rcv_group_stats_df_dict[group] and os.path.isfile(format_fpath):

                # read in column order
                fmt_df = pd.read_csv(format_fpath)
                fmt_order = fmt_df['cruncher_col'].tolist()

                df = pd.concat(rcv_group_stats_df_dict[group], axis=0, ignore_index=True, sort=False)
                df = df.reindex(fmt_order, axis=1)
                df.to_csv(results_dir + '/group_' + group + '_masterDBfmt.csv', index=False)

    if 'per_rcv_type_stats' in output_config and output_config['per_rcv_type_stats']:
        print("Write tabulation stats ...")
        for variant in rcv_variant_stats_df_dict:
            if rcv_variant_stats_df_dict[variant]:
                df = pd.concat(rcv_variant_stats_df_dict[variant], axis=0, ignore_index=True, sort=False)
                df.to_csv(results_dir + '/' + variant + '.csv', index=False)

    if 'candidate_details' in output_config and output_config['candidate_details']:
        print("Write candidate details ...")
        df = pd.concat(flatten_list(candidate_details_dfs), axis=0, ignore_index=True, sort=False)
        df.to_csv(results_dir + '/candidate_details.csv', index=False)

    if invalid_contests:

        invald_fname = 'contest_sets/' + contest_set_name + '/invalid.txt'

        invalid_f = open(invald_fname, 'w')
        for invalid in invalid_contests:
            invalid_f.write(invalid + "/n")
        invalid_f.close()

        print(str(len(invalid_contests)) + " contests did not have a programmed rcv_type (" +
              ",".join(list(rcv_dict.keys())) + "). They are listed in " + invald_fname)

    stats_debugs = flatten_list(stats_debugs)
    if stats_debugs:

        stats_fname = 'contest_sets/' + contest_set_name + '/stats_consistency_check.txt'

        stats_f = open(stats_fname, 'w')
        for debug_str in stats_debugs:
            stats_f.write(debug_str[0] + "\n")
        stats_f.close()

        print(str(len(stats_debugs)) + " contests failed the stats consistency check. " +
              "They are listed in " + stats_fname)

    # make debug version of contest set
    all_debugs = stats_debugs
    if make_debug_contest_set and all_debugs:

        debug_contest_set_dir = 'contest_sets/' + contest_set_name + '_debug'
        if not os.path.isdir(debug_contest_set_dir):
            os.mkdir(debug_contest_set_dir)

        debug_contest_set_fname = debug_contest_set_dir + '/contest_set.csv'
        pd.concat([t[1] for t in all_debugs]).to_csv(debug_contest_set_fname, index=False)

        copyfile('contest_sets/' + contest_set_name + '/output_config.csv',
                 debug_contest_set_dir + '/output_config.csv')

        print('Debug contest set created at ' + debug_contest_set_dir +
              '. Contests that have failed consistency checks have been copied there.')

    print("DONE!")

if __name__ == '__main__':
    main()

