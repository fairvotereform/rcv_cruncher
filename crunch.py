import shutil
from argparse import ArgumentParser
from shutil import copyfile

# cruncher imports
from scripts.definitions import *
from scripts.contests import *
from scripts.ballots import *
from scripts.rcv_variants import *
from scripts.rcv_reporting import *
from scripts.rcv_base import *
from scripts.write_out import *

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
    # confirm cvr location
    cvr_dir_path = dname + "/config.csv"
    if os.path.isfile(cvr_dir_path) is False:
        raise RuntimeError("config.csv is not rcv_cruncher directory.")

    for index, row in pd.read_csv(cvr_dir_path).iterrows():
        config_dict = {row["field"]: row["value"]}

    if "cvr_dir_path" not in config_dict:
        raise RuntimeError("field 'cvr_dir_path' not present in config.csv")

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

    if os.path.isdir(result_log_dir + "/scripts") is False:
        os.mkdir(result_log_dir + "/scripts")

    for script_file in glob.glob("scripts/*"):
        if script_file.split("\\")[1][0] != "_":
            shutil.copy2(script_file, result_log_dir + "/scripts")

    if os.path.isdir(result_log_dir + "/rcv_parsers") is False:
        os.mkdir(result_log_dir + "/rcv_parsers")

    for parser_file in glob.glob("rcv_parsers/*"):
        if parser_file.split("\\")[1][0] != "_":
            shutil.copy2(parser_file, result_log_dir + "/rcv_parsers")

    shutil.copy2(contest_set_path + "/contest_set.csv", result_log_dir)
    shutil.copy2(contest_set_path + "/output_config.csv", result_log_dir)

    ########################
    # load manifest
    contest_set = load_contest_set(contest_set_path, path_prefix=config_dict['cvr_dir_path'])

    ########################
    # confirm parsed cvrs

    # check results dir
    cvr_dir = contest_set_path + '/converted_cvr'
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

    # store contest_set and output config in log folder
    shutil.copy2(contest_set_path + "/contest_set.csv", result_log_dir)
    shutil.copy2(contest_set_path + "/output_config.csv", result_log_dir)
    shutil.copy2(contest_set_path + "/../contest_set_key.csv", result_log_dir)

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
    progress_inc = 1
    progress_total = 15
    # loop through contests and tabulate the elections
    for idx, contest in enumerate(valid_contests):

        print(str(idx+1) + ' of ' + str(len(valid_contests)) + ' ' + contest['unique_id'] + ' ...')

        # create RCV obj + tabulate
        progress(progress_inc, progress_total, status="tabulating")
        progress_inc += 1
        rcv_obj = RCV.run_rcv(contest)

        # stats double check
        if STATS_CHECK:
            progress(progress_inc, progress_total, status="check stats")
            progress_inc += 1
            stats_debugs.append(stats_check(rcv_obj))

        ########################
        # RESULTS-BASED OUTPUTS

        if 'per_rcv_type_stats' in output_config and output_config['per_rcv_type_stats']:
            progress(progress_inc, progress_total, status="store tabulation stats")
            progress_inc += 1
            if not rcv_variant_stats_df_dict[rcv_obj.__class__.__name__]:
                rcv_variant_stats_df_dict[rcv_obj.__class__.__name__].append(rcv_obj.tabulation_stats_comments_df())
            rcv_variant_stats_df_dict[rcv_obj.__class__.__name__].append(rcv_obj.tabulation_stats_df())

        if 'per_rcv_group_stats' in output_config and output_config['per_rcv_group_stats']:
            progress(progress_inc, progress_total, status="store contest stats")
            progress_inc += 1
            if not rcv_group_stats_df_dict[rcv_obj.variant_group()]:
                rcv_group_stats_df_dict[rcv_obj.variant_group()].append(rcv_obj.contest_stats_comments_df())
            rcv_group_stats_df_dict[rcv_obj.variant_group()].append(rcv_obj.contest_stats_df())

        if 'candidate_details' in output_config and output_config['candidate_details']:
            progress(progress_inc, progress_total, status="store candidate details")
            progress_inc += 1
            candidate_details_dfs.append(prepare_candidate_details(rcv_obj))

        if 'round_by_round' in output_config and output_config['round_by_round']:
            progress(progress_inc, progress_total, status="write round by round results")
            progress_inc += 1
            write_rcv_rounds(rcv_obj, results_dir)

        if 'ballot_stats_debug' in output_config and output_config['ballot_stats_debug']:
            progress(progress_inc, progress_total, status="ballot stats debug")
            progress_inc += 1
            write_ballot_debug_info(rcv_obj, results_dir)

        if 'cvr_ballot_allocation' in output_config and output_config['cvr_ballot_allocation']:
            progress(progress_inc, progress_total, status="write cvr with final allocations")
            progress_inc += 1
            write_converted_cvr_annotated(rcv_obj, results_dir)

        ################
        # BALLOT-BASED OUTPUTS

        if 'condorcet' in output_config and output_config['condorcet']:
            progress(progress_inc, progress_total, status="write condorcet table")
            progress_inc += 1
            write_condorcet_tables(contest, results_dir)

        if 'first_second_choices' in output_config and output_config['first_second_choices']:
            progress(progress_inc, progress_total, status="write first and second choices table")
            progress_inc += 1
            write_first_second_tables(contest, results_dir)

        if 'cumulative_ranking' in output_config and output_config['cumulative_ranking']:
            progress(progress_inc, progress_total, status="write cumulative ranking table")
            progress_inc += 1
            write_cumulative_ranking_tables(contest, results_dir)

        if 'rank_usage' in output_config and output_config['rank_usage']:
            progress(progress_inc, progress_total, status="write rank usage table")
            progress_inc += 1
            write_rank_usage_tables(contest, results_dir)

        if 'crossover_support' in output_config and output_config['crossover_support']:
            progress(progress_inc, progress_total, status="write crossover support table")
            progress_inc += 1
            write_opponent_crossover_tables(contest, results_dir)

        if 'first_choice_to_finalist' in output_config and output_config['first_choice_to_finalist']:
            progress(progress_inc, progress_total, status="write first choice to finalist table")
            progress_inc += 1
            write_first_to_finalist_tables(contest, results_dir)

        progress(progress_total, progress_total, status="")
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

