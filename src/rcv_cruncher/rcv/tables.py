
class RCV_tables:

    pass

    # def ballot_debug_df(self, *, tabulation_num=1):
    #     """
    #     Return pandas data frame with ranks as well stats on exhaustion, ranked_multiple ...
    #     """

    #     stat_names = [
    #         'contains_duplicate',
    #         f'pretally_exhausted{tabulation_num}',
    #         f'posttally_exhausted{tabulation_num}',
    #         f'posttally_exhausted_by_abstention{tabulation_num}',
    #         f'posttally_exhausted_by_overvote{tabulation_num}',
    #         f'posttally_exhausted_by_rank_limit{tabulation_num}',
    #         f'posttally_exhausted_by_skipped_rankings{tabulation_num}',
    #         f'posttally_exhausted_by_duplicate_rankings{tabulation_num}',
    #         'first_round_overvote',
    #         'fully_ranked',
    #         'contains_overvote',
    #         'ranked_multiple',
    #         'ranked_single',
    #         'undervote',
    #         'irregular'
    #     ]

    #     dct = {stat_name: list(self._stat_table[stat_name]) for stat_name in stat_names}
    #     dct['used_last_rank'] = self.used_last_rank()

    #     # get ballot info
    #     ballot_dict = copy.deepcopy(ballots.input_ballots(self.ctx, combine_writeins=False))
    #     bs = ballot_dict['ranks']

    #     # how many ranks?
    #     num_ranks = max(len(i) for i in bs)

    #     # make sure all ballots are lists of equal length, adding trailing 'skipped' if necessary
    #     bs = [b + ([util.BallotMarks.SKIPPEDRANK] * (num_ranks - len(b))) for b in bs]

    #     # add in rank columns
    #     ranks = {}
    #     for i in range(1, num_ranks + 1):
    #         ranks['rank' + str(i)] = [b[i - 1] for b in bs]

    #     # assemble output_table, start with extras
    #     return pd.DataFrame.from_dict({**ranks, **dct})

# def first_choice_to_finalist_table(rcv_obj):

#     dfs = []
#     for iTab in range(1, rcv_obj.n_tabulations()+1):

#         # who had any ballot weight allotted
#         finalist_candidates = list(rcv_obj.finalist_candidates(tabulation_num=iTab)) + ['exhaust']
#         candidate_set = sorted(ballots.candidates(rcv_obj.ctx))

#         ballot_set = [{'ranks': ranks, 'weight': weight, 'weight_distrib': distrib}
#                       for ranks, weight, distrib
#                       in zip(rcv_obj.get_initial_ranks(tabulation_num=iTab),
#                              rcv_obj.get_initial_weights(tabulation_num=iTab),
#                              rcv_obj.get_final_weight_distrib(tabulation_num=iTab))]

#         index_label = "Ballots with first choice:"
#         n_ballots_label = "Number of Ballots"

#         colname_dict = {cand: "% of votes to " + cand for cand in finalist_candidates}

#         rows = candidate_set
#         cols = [n_ballots_label] + list(colname_dict.values())
#         df = pd.DataFrame(index=rows, columns=cols + ['percent_sum'])
#         df.index.name = index_label

#         # group ballots by first choice
#         first_choices = {cand: [] for cand in candidate_set}
#         for b in ballot_set:
#             if len(b['ranks']) >= 1 and b['ranks'][0] in first_choices:
#                 first_choices[b['ranks'][0]].append(b)

#         for cand in candidate_set:

#             total_first_choice_ballots = sum(b['weight'] for b in first_choices[cand])
#             df.loc[cand, n_ballots_label] = total_first_choice_ballots

#             if total_first_choice_ballots:

#                 redistrib = {opponent: 0 for opponent in finalist_candidates}
#                 for b in first_choices[cand]:
#                     for el in b['weight_distrib']:
#                         if el[0] == 'empty':
#                             redistrib['exhaust'] += el[1]
#                         else:
#                             redistrib[el[0]] += el[1]

#                 redistrib_total_check = 0
#                 for opponent in redistrib:
#                     redistrib_percent = redistrib[opponent] / total_first_choice_ballots * 100
#                     df.loc[cand, colname_dict[opponent]] = redistrib_percent
#                     redistrib_total_check += redistrib_percent
#                 df.loc[cand, 'percent_sum'] = redistrib_total_check

#             else:
#                 for opponent in finalist_candidates:
#                     df.loc[cand, colname_dict[opponent]] = 0
#                 df.loc[cand, 'percent_sum'] = 0

#         df = df.astype(float).round(3)

#         dfs.append(df)

#     return dfs


# def round_by_round(rcv_obj):

#     rcv_dfs = []

#     for iTab in range(1, rcv_obj.n_tabulations()+1):

#         num_rounds = rcv_obj.n_rounds(tabulation_num=iTab)

#         first_round_exhaust = rcv_obj.total_pretally_exhausted(tabulation_num=iTab)

#         # get rcv results
#         rounds_full = [rcv_obj.get_round_tally_tuple(i, tabulation_num=iTab) for i in range(1, num_rounds + 1)]
#         transfers = [rcv_obj.get_round_transfer_dict(i, tabulation_num=iTab) for i in range(1, num_rounds + 1)]

#         # reformat contest outputs into useful dicts
#         cand_outcomes = rcv_obj.get_candidate_outcomes(tabulation_num=iTab)

#         # reorder candidate names
#         # winners in ascending order of round won
#         # followed by losers in descending order of round lost
#         reorder_dicts = []
#         for d in cand_outcomes:

#             if d['round_elected']:
#                 d['order'] = -1 * (1 / d['round_elected'])
#             else:
#                 d['order'] = 1 / d['round_eliminated']

#             reorder_dicts.append(d)

#         ordered_candidates_names = [d['name'] for d in sorted(reorder_dicts, key=lambda x: x['order'])]

#         # setup data frame
#         row_names = ordered_candidates_names + ['exhaust']
#         rcv_df = pd.DataFrame(util.NAN, index=row_names + ['colsum'], columns=['candidate'])
#         rcv_df.loc[row_names + ['colsum'], 'candidate'] = row_names + ['colsum']

#         # loop through rounds
#         for rnd in range(1, num_rounds + 1):

#             rnd_info = {rnd_cand: rnd_tally for rnd_cand, rnd_tally in zip(*rounds_full[rnd-1])}
#             rnd_info['exhaust'] = 0

#             rnd_transfer = dict(transfers[rnd-1])

#             # add round data
#             for cand in row_names:

#                 rnd_percent_col = 'r' + str(rnd) + '_active_percent'
#                 rnd_count_col = 'r' + str(rnd) + '_count'
#                 rnd_transfer_col = 'r' + str(rnd) + '_transfer'

#                 rcv_df.loc[cand, rnd_percent_col] = 100*(rnd_info[cand]/sum(rnd_info.values()))
#                 rcv_df.loc[cand, rnd_count_col] = rnd_info[cand]
#                 rcv_df.loc[cand, rnd_transfer_col] = rnd_transfer[cand]

#             # maintain cumulative exhaust total
#             if rnd == 1:
#                 rcv_df.loc['exhaust', rnd_count_col] = first_round_exhaust
#             else:
#                 last_rnd_count_col = 'r' + str(rnd-1) + '_count'
#                 last_rnd_transfer_col = 'r' + str(rnd-1) + '_transfer'
#                 current_rnd_count_val = sum(rcv_df.loc['exhaust', [last_rnd_count_col, last_rnd_transfer_col]].astype(float))
#                 rcv_df.loc['exhaust', rnd_count_col] = current_rnd_count_val

#             # sum round columns
#             rcv_df.loc['colsum', rnd_count_col] = sum(rcv_df.loc[row_names, rnd_count_col].astype(float))
#             rcv_df.loc['colsum', rnd_transfer_col] = sum(rcv_df.loc[row_names, rnd_transfer_col].astype(float))
#             rcv_df.loc['colsum', rnd_percent_col] = sum(rcv_df.loc[row_names, rnd_percent_col].astype(float))

#         # # convert from decimal to float
#         rcv_df.loc[row_names + ['colsum'], rcv_df.columns != "candidate"] = \
#             rcv_df.loc[row_names + ['colsum'], rcv_df.columns != "candidate"].astype(float).round(3)

#         # remove rownames
#         rcv_df = rcv_df.reset_index(drop=True)

#         rcv_dfs.append(rcv_df)

#     return rcv_dfs

    # def ballot_debug_df(self, *, tabulation_num=1):
    #     """
    #     Return pandas data frame with ranks as well stats on exhaustion, ranked_multiple ...
    #     """

    #     stat_names = [
    #         'contains_duplicate',
    #         f'pretally_exhausted{tabulation_num}',
    #         f'posttally_exhausted{tabulation_num}',
    #         f'posttally_exhausted_by_abstention{tabulation_num}',
    #         f'posttally_exhausted_by_overvote{tabulation_num}',
    #         f'posttally_exhausted_by_rank_limit{tabulation_num}',
    #         f'posttally_exhausted_by_skipped_rankings{tabulation_num}',
    #         f'posttally_exhausted_by_duplicate_rankings{tabulation_num}',
    #         'first_round_overvote',
    #         'fully_ranked',
    #         'contains_overvote',
    #         'ranked_multiple',
    #         'ranked_single',
    #         'undervote',
    #         'irregular'
    #     ]

    #     dct = {stat_name: list(self._stat_table[stat_name]) for stat_name in stat_names}
    #     dct['used_last_rank'] = self.used_last_rank()

    #     # get ballot info
    #     ballot_dict = copy.deepcopy(ballots.input_ballots(self.ctx, combine_writeins=False))
    #     bs = ballot_dict['ranks']

    #     # how many ranks?
    #     num_ranks = max(len(i) for i in bs)

    #     # make sure all ballots are lists of equal length, adding trailing 'skipped' if necessary
    #     bs = [b + ([util.BallotMarks.SKIPPEDRANK] * (num_ranks - len(b))) for b in bs]

    #     # add in rank columns
    #     ranks = {}
    #     for i in range(1, num_ranks + 1):
    #         ranks['rank' + str(i)] = [b[i - 1] for b in bs]

    #     # assemble output_table, start with extras
    #     return pd.DataFrame.from_dict({**ranks, **dct})
