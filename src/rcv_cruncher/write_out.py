
# import os

# import pandas as pd

# import rcv_cruncher.ballots as ballots
# import rcv_cruncher.misc_tabulation as misc_tabulation
# import rcv_cruncher.util as util


# def write_converted_cvr(contest, results_dir, cvr_format='rank'):
#     """
#     Convert cvr into common csv format and write out
#     """
#     uid = contest['uid'] if not contest.get('split_id') else contest.get('split_id')

#     if cvr_format == 'rank':
#         format_dir = results_dir / "rank_format"
#     elif cvr_format == 'candidate':
#         format_dir = results_dir / "candidate_format"
#     util.verifyDir(format_dir)

#     outfile = format_dir / f"{uid}.csv"

#     cvr = ballots.cvr_table(contest, table_format=cvr_format)
#     cvr.to_csv(util.longname(outfile), index=False)


# def write_converted_cvr_annotated(rcv_obj, results_dir, cvr_format='candidate'):
#     """
#     Convert cvr into common csv format, with appended columns and write out
#     """
#     cvr_allocation_dir = results_dir / 'cvr_ballot_allocation'
#     util.verifyDir(cvr_allocation_dir)

#     if cvr_format == 'rank':
#         cvr_allocation_dir = cvr_allocation_dir / "rank_format"
#     elif cvr_format == 'candidate':
#         cvr_allocation_dir = cvr_allocation_dir / "candidate_format"
#     util.verifyDir(cvr_allocation_dir)

#     for iTab in range(1, rcv_obj.n_tabulations()+1):

#         # get cvr df
#         cvr = ballots.cvr_table(rcv_obj.ctx, table_format=cvr_format)
#         cvr['ballot_split_ID'] = cvr.index + 1
#         cvr['exhaustion_check'] = rcv_obj.exhaustion_check(tabulation_num=iTab)

#         # duplicate ballot rows in df for each time the ballot was split
#         final_weight_distrib = rcv_obj.get_final_weight_distrib(tabulation_num=iTab)

#         # convert final weights to string
#         str_convert = []
#         for tl in final_weight_distrib:
#             str_convert.append(";".join([pair[0] + ":" + str(float(pair[1])) for pair in tl]))

#         # duplicate rows
#         cvr['final_round_allocation'] = str_convert
#         split_allocation = cvr['final_round_allocation'].str.split(';').apply(pd.Series, 1).stack()
#         split_allocation.index = split_allocation.index.droplevel(-1)
#         split_allocation.name = 'final_round_allocation'
#         del cvr['final_round_allocation']
#         cvr = cvr.join(split_allocation)

#         # split allocation column out to candidate and weight
#         cvr[['final_allocation', 'weight']] = cvr.final_round_allocation.str.split(":", expand=True)

#         # create allocation column that marks all inactive ballots as 'inactive' and
#         # inactive_type column that marks all candidates as 'NA' but specifies the kind of inactive ballot
#         # exhausted, undervote, etc
#         cvr['inactive_type'] = cvr['final_allocation']

#         # inactive_type column
#         cvr.loc[cvr['inactive_type'] != 'empty', 'inactive_type'] = 'NA'
#         cvr.loc[cvr['inactive_type'] == 'empty', 'inactive_type'] = cvr.loc[cvr['inactive_type'] == 'empty', 'exhaustion_check']

#         # final_allocation_column
#         cvr['final_allocation'] = cvr['final_allocation'].replace(to_replace="empty", value="inactive")

#         # remove intermediate columns
#         del cvr['final_round_allocation']
#         del cvr['exhaustion_check']

#         # reorder columns
#         ballot_split_ID_col = cvr.pop('ballot_split_ID')
#         cvr.insert(0, 'ballot_split_ID', ballot_split_ID_col)

#         uid = rcv_obj.file_stub(tabulation_num=iTab)
#         outfile = cvr_allocation_dir / f'{uid}_ballot_allocation.csv'
#         cvr.to_csv(util.longname(outfile), index=False)


# def write_condorcet_tables(contest, results_dir):
#     """
#     Calculate and write condorcet tables (both count and percents) for contest
#     """
#     counts, percents, condorcet_winner = misc_tabulation.condorcet_tables(contest)

#     if condorcet_winner:
#         condorcet_str = "condorcet winner: " + condorcet_winner
#     else:
#         condorcet_str = "condorcet winner: None"

#     counts.index.name = condorcet_str
#     percents.index.name = condorcet_str

#     condorcet_table_dir = results_dir / 'condorcet'
#     util.verifyDir(condorcet_table_dir)

#     uid = contest['uid'] if not contest.get('split_id') else contest.get('split_id')
#     counts.to_csv(util.longname(condorcet_table_dir / f"{uid}_condorcet_count.csv"), float_format="%.2f")
#     percents.to_csv(util.longname(condorcet_table_dir / f"{uid}_condorcet_percent.csv"), float_format="%.2f")


# def write_first_second_tables(contest, results_dir):
#     """
#     Calculate and write first choice - second choice tables (both count and percents) for contest
#     """
#     counts, percents, percents_no_exhaust = misc_tabulation.first_second_tables(contest)

#     first_second_table_dir = results_dir / 'first_second'
#     util.verifyDir(first_second_table_dir)

#     uid = contest['uid'] if not contest.get('split_id') else contest.get('split_id')
#     counts.to_csv(util.longname(first_second_table_dir / f"{uid}_first_second_choices_count.csv"), float_format="%.2f")
#     percents.to_csv(util.longname(first_second_table_dir / f"{uid}_first_second_choices_percent.csv"), float_format="%.2f")
#     percents_no_exhaust.to_csv(
#       util.longname(first_second_table_dir / f"{uid}_first_second_choices_percent_no_exhaust.csv"), float_format="%.2f")

# def write_cumulative_ranking_tables(contest, results_dir):
#     """
#     Calculate and write cumulative ranking tables (both count and percent) for contest
#     """
#     counts, percents = misc_tabulation.cumulative_ranking_tables(contest)

#     cumulative_ranking_dir = results_dir / 'cumulative_ranking'
#     util.verifyDir(cumulative_ranking_dir)

#     uid = contest['uid'] if not contest.get('split_id') else contest.get('split_id')
#     counts.to_csv(util.longname(cumulative_ranking_dir / f"{uid}_cumulative_ranking_count.csv"), float_format="%.2f")
#     percents.to_csv(util.longname(cumulative_ranking_dir / f"{uid}_cumulative_ranking_percent.csv"), float_format="%.2f")


# def write_rank_usage_tables(contest, results_dir):
#     """
#     Calculate and write rank usage statistics.
#     """
#     df = misc_tabulation.rank_usage_tables(contest)

#     rank_usage_table_dir = results_dir / 'rank_usage'
#     util.verifyDir(rank_usage_table_dir)

#     uid = contest['uid'] if not contest.get('split_id') else contest.get('split_id')
#     df.to_csv(util.longname(rank_usage_table_dir / f'{uid}_rank_usage.csv'), float_format='%.2f')


# def write_opponent_crossover_tables(contest, results_dir):
#     """
#     Calculate crossover support between candidates and write table.
#     """
#     count_df, percent_df = misc_tabulation.crossover_table(contest)

#     opponent_crossover_table_dir = results_dir / 'crossover_support'
#     util.verifyDir(opponent_crossover_table_dir)

#     uid = contest['uid'] if not contest.get('split_id') else contest.get('split_id')
#     count_df.to_csv(util.longname(opponent_crossover_table_dir / f'{uid}_crossover_support_count.csv'), float_format='%.2f')
#     percent_df.to_csv(util.longname(opponent_crossover_table_dir / f'{uid}_crossover_support_percent.csv'), float_format='%.2f')


# def write_first_to_finalist_tables(rcv_obj, results_dir):
#     """
#     Calculate distribution of ballots allocated to non-finalists during first round and their transfer
#     to eventual finalists.
#     """

#     first_to_finalist_table_dir = results_dir / 'first_choice_to_finalist'
#     util.verifyDir(first_to_finalist_table_dir)

#     dfs = misc_tabulation.first_choice_to_finalist_table(rcv_obj)

#     for iTab in range(1, len(dfs) + 1):
#         uid = rcv_obj.file_stub(tabulation_num=iTab)
#         csv_fname = first_to_finalist_table_dir / f'{uid}_first_to_finalist.csv'
#         dfs[iTab-1].to_csv(util.longname(csv_fname), float_format='%.2f')


# def prepare_candidate_details(obj):
#     """
#     Return pandas data frame of candidate info with round-by-round vote counts
#     """
#     all_dfs = []

#     for iTab in range(1, obj.n_tabulations()+1):

#         uid = obj.file_stub(tabulation_num=iTab)
#         n_rounds = obj.n_rounds(tabulation_num=iTab)

#         # get rcv results
#         rounds_full = [obj.get_round_tally_tuple(i, tabulation_num=iTab) for i in range(1, n_rounds + 1)]
#         cand_outcomes = obj.get_candidate_outcomes(tabulation_num=iTab)

#         # reformat contest outputs into useful dicts
#         cand_outcomes_dict = {d['name']: d for d in cand_outcomes}
#         rounds_full_dict = [{cand: float(count) for cand, count in zip(*rnd_count)}
#                             for rnd_count in rounds_full]

#         # reorder candidate names
#         # winners in ascending order of round won
#         # followed by losers in descending order of round lost
#         reorder_dicts = []
#         for d in cand_outcomes:

#             # don't add candidates if they received zero votes throughout the contest.
#             if sum(rounds_dict[d['name']] for rounds_dict in rounds_full_dict) == 0:
#                 continue

#             if d['round_elected']:
#                 d['order'] = -1 * (1/d['round_elected'])
#             else:
#                 d['order'] = 1/d['round_eliminated']

#             reorder_dicts.append(d)

#         ordered_candidates_names = [d['name'] for d in sorted(reorder_dicts, key=lambda x: x['order'])]

#         # create table
#         colnames = ['unique_id', 'candidate', 'round_elected', 'round_eliminated'] + \
#                    ['round_' + str(i) + '_vote' for i in range(1, n_rounds + 1)]

#         # assemble rows
#         cand_rows = []
#         for cand in ordered_candidates_names:

#             cand_rows.append([uid,
#                               cand,
#                               cand_outcomes_dict[cand]['round_elected'],
#                               cand_outcomes_dict[cand]['round_eliminated']] +
#                              [d[cand] for d in rounds_full_dict])

#         df = pd.DataFrame(cand_rows, columns=colnames)
#         all_dfs.append(df)

#     return all_dfs


# def write_rcv_rounds(obj, results_dir):
#     """
#     Write out rcv contest round-by-round counts and transfers
#     """

#     round_by_round_dir = results_dir / 'round_by_round'
#     util.verifyDir(round_by_round_dir)

#     rcv_dfs = misc_tabulation.round_by_round(obj)

#     for iTab, rcv_df in enumerate(rcv_dfs, start=1):
#         uid = obj.file_stub(tabulation_num=iTab)
#         rcv_df.to_csv(util.longname(round_by_round_dir / f'{uid}_round_by_round.csv'), index=False)


# def write_ballot_debug_info(obj, results_dir):
#     """
#     Write ballot debug CVR
#     """
#     for iTab in range(1, obj.n_tabulations()+1):

#         ballot_debug_df = obj.ballot_debug_df(tabulation_num=iTab)

#         output_dir = results_dir / 'ballot_stats_debug'
#         util.verifyDir(output_dir)

#         uid = obj.file_stub(tabulation_num=iTab)
#         ballot_debug_df.to_csv(util.longname(output_dir / f'{uid}_ballot_debug.csv'), index=False)
