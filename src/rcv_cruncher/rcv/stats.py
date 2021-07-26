
from typing import List

import collections

import pandas as pd

# import rcv_cruncher.util as util

from rcv_cruncher.marks import BallotMarks
from rcv_cruncher.util import InactiveType


class RCV_stats:
    """
    Mixin containing all reporting stats. Can be overriden by any rcv variant.
    """

    def _exhaustion_categories(self, *, tabulation_num=1):
        """
        Returns a list with constants indicating why each ballot
        was exhausted in a single-winner rcv contest.

        Possible list values are:

        - UNDERVOTE : if the ballot was undervote, and therefore neither active nor exhaustable.

        - NOT_EXHAUSTED: if finalist was present on the ballot and was ranked higher than an exhaust condition
        (overvote or repeated_skipvotes)

        - PRETALLY_EXHAUST: if the ballot was exahusted by overvote or skipped rankings prior to being counted in the first round.

        - POSTTALLY_EXHAUSTED_BY_OVERVOTE: overvote rules apply to contest, and an overvote is encountered prior to a
        final round candidate or another exhaust condition.

        - POSTTALLY_EXHAUSTED_BY_REPEATED_SKIPVOTE: skipped rankings rules apply to contest, and two or more repeated skipped
         rankings are encountered prior to a final round candidate or another exhaust condition. The skipped rankings
          must be followed by a non-skipped ranking for this condition to apply.

        - POSTTALLY_EXHAUSTED_BY_DUPLICATE_RANKING: repeated rankings rules apply to contest, and a candidate that had already appeared
         on the ballot is encountered again prior to a final round candidate or another exhaust condition.

        - POSTTALLY_EXHAUSTED_BY_ABSTENTION: if the ballot is rank restricted, then a ballot receives this label if the final
        rank was skipped. If the ballot is not rank restricted, then all ballots that do not reach another exhaust
        condition and do not rank a final round candidate receive this label.

        - POSTTALLY_EXHAUSTED_BY_RANK_LIMIT: if the ballot is rank restricted, then a ballot recieves this label if the final
        rank was marked. If the ballot is not rank restricted, then no ballots recieve this label.

        rank restricted ballot: less than or equal to n-2 ranks, where n is number of candidates (not counting writeins).
        """

        restrictive_rank_limit = self._summary_cvr_stat_table['restrictive_rank_limit'].item()

        used_last_rank_list = self._cvr_stat_table['used_last_rank']
        initial_ranks_list = self.get_initial_ranks(tabulation_num=tabulation_num)
        final_ranks_list = self.get_final_ranks(tabulation_num=tabulation_num)
        ballot_marks_list = self.get_cvr_dict(self._contest_rule_set_name)['ballot_marks']

        why_exhaust = []
        # loop through each ballot
        for used_last_rank, inital_ranks, final_ranks, ballot_marks in zip(
            used_last_rank_list, initial_ranks_list, final_ranks_list, ballot_marks_list):

            # if the exhaust status is already known
            if ballot_marks.inactive_type == BallotMarks.UNDERVOTE:
                why_exhaust.append(InactiveType.UNDERVOTE)

            elif ballot_marks.inactive_type == BallotMarks.PRETALLY_EXHAUST or not inital_ranks:
                why_exhaust.append(InactiveType.PRETALLY_EXHAUST)

            # if the ballot still had some ranks at the end of tabulation
            # then it wasnt exhausted
            elif final_ranks:
                why_exhaust.append(InactiveType.NOT_EXHAUSTED)

            elif ballot_marks.inactive_type == BallotMarks.MAYBE_EXHAUSTED_BY_DUPLICATE_RANKING:
                why_exhaust.append(InactiveType.POSTTALLY_EXHAUSTED_BY_DUPLICATE_RANKING)

            elif ballot_marks.inactive_type == BallotMarks.MAYBE_EXHAUSTED_BY_REPEATED_SKIPPED_RANKING:
                why_exhaust.append(InactiveType.POSTTALLY_EXHAUSTED_BY_REPEATED_SKIPPED_RANKING)

            elif ballot_marks.inactive_type == BallotMarks.MAYBE_EXHAUSTED_BY_OVERVOTE:
                why_exhaust.append(InactiveType.POSTTALLY_EXHAUSTED_BY_OVERVOTE)

            elif restrictive_rank_limit and used_last_rank:
                why_exhaust.append(InactiveType.POSTTALLY_EXHAUSTED_BY_RANK_LIMIT)
            else:
                why_exhaust.append(InactiveType.POSTTALLY_EXHAUSTED_BY_ABSTENTION)

        return why_exhaust

    ####################
    # CONTEST INFO

    # def split_id(self):
    #     """
    #     String describing which field and value the cvr ballots were filtered on. If no filtering done, it is empty.
    #     """
    #     return self._split_id

    # def split_field(self):
    #     return self._split_field

    # def split_value(self):
    #     return self._split_value.replace(":", "_").replace("/", "_").replace("\\", "_").replace(" ", "_").replace("-", "_")

    # def file_stub(self, *, tabulation_num=None):

    #     stub = ""
    #     if not self.split_id():
    #         stub += self.unique_id()
    #     else:
    #         stub += self.split_id()

    #     if tabulation_num:
    #         stub += '_tab-' + str(tabulation_num)

    #     return stub

    ####################
    # OUTCOME STATS

    def _winner(self, tabulation_num=1):
        '''
        The winner(s) of the election.
        '''
        return ", ".join([str(w) for w in self._tabulation_winner(tabulation_num=tabulation_num)])

    def _all_winners(self):
        """
        Return contest winner names in order of election.
        """
        # accumulate winners across tabulations
        winners = []
        for i in range(1, self.n_tabulations() + 1):
            winners += self._tabulation_winner(tabulation_num=i)
        return winners

    def _tabulation_winner(self, tabulation_num=1):
        """
        Return winners from tabulation.
        """
        elected_candidates = [d for d in self.get_candidate_outcomes(tabulation_num=tabulation_num)
                              if d['round_elected'] is not None]
        for candidate in elected_candidates:
            round_dict = self.get_round_tally_dict(candidate['round_elected'], tabulation_num=tabulation_num)
            candidate['elected_vote'] = round_dict[candidate['name']]
        return [d['name'] for d in sorted(elected_candidates, key=lambda x: (x['round_elected'], -x['elected_vote'], x['name']))]

    def _condorcet(self, tabulation_num=1):
        '''
        Is the winner the condorcet winner?
        The condorcet winner is the candidate that would win a 1-on-1 election versus
        any other candidate in the election. Note that this calculation depends on
        jurisdiction dependant rule variations.

        In the case of multi-winner elections, this result will only pertain to the first candidate elected.
        '''

        contest_cvr_dl = self.get_cvr_dict(self._contest_rule_set_name)
        contest_cvr_ld = [{'ballot_marks': bm, 'weight': weight}
                          for bm, weight in zip(contest_cvr_dl['ballot_marks'], contest_cvr_dl['weight'])]

        cands = self._contest_candidates
        if len(cands.unique_candidates) == 1:
            return True

        winner = self._tabulation_winner(tabulation_num=tabulation_num)[0]
        losers = [cand for cand in cands.unique_candidates if cand != winner]

        net = collections.Counter()
        for b in contest_cvr_ld:
            for loser in losers:

                # does winner or loser appear first on this ballot?
                ballot_contrib = 0
                for mark in b['ballot_marks'].marks:
                    if mark == winner:
                        ballot_contrib = b['weight']
                        break
                    if mark == loser:
                        ballot_contrib = -1 * b['weight']
                        break

                # accumulate
                net.update({loser: ballot_contrib})

        # any negative net values indicate a head-to-head where contest winner loses
        if min(net.values()) > 0:
            return True
        else:
            return False

    def _come_from_behind(self, tabulation_num=1):
        """
        "yes" if rcv winner is not first round leader, else "no".

        In the case of multi-winner elections, this result will only pertain to the first candidate elected.
        """
        if self._first_round_winner_place(tabulation_num=tabulation_num) != 1:
            return True
        else:
            return False

    def _final_round_active_votes(self, tabulation_num=1):
        '''
        The number of votes that were awarded to any candidate in the final round. (weighted)
        '''
        n_rounds = self.n_rounds(tabulation_num=tabulation_num)
        tally_dict = self.get_round_tally_dict(n_rounds, tabulation_num=tabulation_num)
        return sum(tally_dict.values())

    def _final_round_winner_percent(self, tabulation_num=1):
        '''
        The percent of votes for the winner in the final round.
        If more than one winner, return the final round count for the first winner elected. (weighted)
        '''
        n_rounds = self.n_rounds(tabulation_num=tabulation_num)
        tally_dict = self.get_round_tally_dict(n_rounds, tabulation_num=tabulation_num)
        winner = self._tabulation_winner(tabulation_num=tabulation_num)
        return (tally_dict[winner[0]] / sum(tally_dict.values())) * 100

    def _final_round_winner_vote(self, tabulation_num=1):
        '''
        The percent of votes for the winner in the final round.
        If more than one winner, return the final round count for the first winner elected. (weighted)
        '''
        n_rounds = self.n_rounds(tabulation_num=tabulation_num)
        tally_dict = self.get_round_tally_dict(n_rounds, tabulation_num=tabulation_num)
        winner = self._tabulation_winner(tabulation_num=tabulation_num)
        return tally_dict[winner[0]]

    def _final_round_winner_votes_over_first_round_active(self, tabulation_num=1):
        '''
        The number of votes the winner receives in the final round divided by the
        number of valid votes in the first round. Reported as percentage.

        If more than one winner, return the final round count for the first winner elected. (weighted)
        '''
        first_round_active_votes = sum(self.get_round_tally_dict(1, tabulation_num=tabulation_num).values())
        return (self._final_round_winner_vote(tabulation_num=tabulation_num) / first_round_active_votes) * 100

    def _first_round_winner_place(self, tabulation_num=1):
        '''
        In terms of first round votes, what place the eventual winner came in.
        In the case of multi-winner elections, this result will only pertain to the first candidate elected.
        '''
        winner = self._tabulation_winner(tabulation_num=tabulation_num)[0]
        tally_tuple = self.get_round_tally_tuple(1, tabulation_num=tabulation_num,
                                                 only_round_active_candidates=True, desc_sort=True)

        # account for ties
        winner_place = None
        for order_rank, unique_tally_val in enumerate(sorted(set(tally_tuple[1]), reverse=True), start=1):
            for cand, tally in zip(*tally_tuple):
                if winner == cand and tally == unique_tally_val:
                    winner_place = order_rank

        return winner_place

    def _first_round_winner_percent(self, tabulation_num=1):
        '''
        The percent of votes for the winner in the first round.
        In the case of multi-winner elections, this result will only pertain to the first candidate elected. (weighted)
        '''
        winner = self._tabulation_winner(tabulation_num=tabulation_num)
        tally_dict = self.get_round_tally_dict(1, tabulation_num=tabulation_num, only_round_active_candidates=True)
        return tally_dict[winner[0]] / sum(tally_dict.values()) * 100

    def _first_round_winner_vote(self, tabulation_num=1):
        '''
        The number of votes for the winner in the first round.
        In the case of multi-winner elections, this result will only pertain to the first candidate elected. (weighted)
        '''
        winner = self._tabulation_winner(tabulation_num=tabulation_num)
        tally_dict = self.get_round_tally_dict(1, tabulation_num=tabulation_num, only_round_active_candidates=True)
        return tally_dict[winner[0]]

    def _number_of_winners(self):
        """
        Number of winners a contest had.
        """
        return len(self._all_winners())

    def _ranked_winner(self, tabulation_num=1):
        """
        Number of ballots with a non-overvote mark for the winner. (weighted) (filtered)
        """
        contest_cvr_dl = self.get_cvr_dict(self._contest_rule_set_name)
        contest_cvr_ld = [{'ballot_marks': bm, 'weight': weight}
                          for bm, weight in zip(contest_cvr_dl['ballot_marks'], contest_cvr_dl['weight'])]

        winners = self._tabulation_winner(tabulation_num=tabulation_num)
        winner_marked = [bool(set(winners).intersection(b['ballot_marks'].unique_marks)) for b in contest_cvr_ld]
        return sum(b['weight'] for flag, b in zip(winner_marked, contest_cvr_ld) if flag)

    def _win_threshold(self, tabulation_num=1):
        """
        Election threshold, if static, otherwise NA
        """
        return self.get_win_threshold(tabulation_num=tabulation_num)

    def _winners_consensus_value(self, tabulation_num=1):
        '''
        The percentage of valid first round votes that rank any winner in the top 3.
        '''
        first_round_active_votes = sum(self.get_round_tally_dict(1, tabulation_num=tabulation_num).values())
        return (self._winner_in_top_3(tabulation_num=tabulation_num) / first_round_active_votes) * 100

    def _winner_in_top_3(self, tabulation_num=1):
        """
        Number of ballots that ranked any winner in the top 3 ranks. (weighted)
        """
        contest_cvr_dl = self.get_cvr_dict(self._contest_rule_set_name)
        contest_cvr_ld = [{'ballot_marks': bm, 'weight': weight}
                          for bm, weight in zip(contest_cvr_dl['ballot_marks'], contest_cvr_dl['weight'])]

        winner = self._tabulation_winner(tabulation_num=tabulation_num)
        top3 = [b['ballot_marks'].marks[:min(3, len(b['ballot_marks'].marks))] for b in contest_cvr_ld]
        top3_check = [bool(set(winner).intersection(b)) for b in top3]
        return sum(b['weight'] for flag, b in zip(top3_check, contest_cvr_ld) if flag)

    def _compute_contest_stat_table(self):

        cvr = self.get_cvr_dict(self._contest_rule_set_name)

        df = pd.DataFrame()

        # ADD WEIGHTS
        df['weight'] = cvr['weight']
        for iTab in range(1, self._tab_num+1):
            df[f'final_weight{iTab}'] = self.get_final_weights(tabulation_num=iTab)

        # EXHAUSTION STATS
        for iTab in range(1, self._tab_num+1):
            exhaust_type = self._exhaustion_categories(tabulation_num=iTab)
            df[f'exhaust_type{iTab}'] = pd.Series(exhaust_type, dtype='category')

        for iTab in range(1, self._tab_num+1):
            exhaust_type_str = f'exhaust_type{iTab}'
            df[f'pretally_exhausted{iTab}'] = df[exhaust_type_str].eq(
                InactiveType.PRETALLY_EXHAUST)
            df[f'posttally_exhausted_by_overvote{iTab}'] = df[exhaust_type_str].eq(
                InactiveType.POSTTALLY_EXHAUSTED_BY_OVERVOTE)
            df[f'posttally_exhausted_by_repeated_skipped_rankings{iTab}'] = df[exhaust_type_str].eq(
                InactiveType.POSTTALLY_EXHAUSTED_BY_REPEATED_SKIPPED_RANKING)
            df[f'posttally_exhausted_by_abstention{iTab}'] = df[exhaust_type_str].eq(
                InactiveType.POSTTALLY_EXHAUSTED_BY_ABSTENTION)
            df[f'posttally_exhausted_by_rank_limit{iTab}'] = df[exhaust_type_str].eq(
                InactiveType.POSTTALLY_EXHAUSTED_BY_RANK_LIMIT)
            df[f'posttally_exhausted_by_duplicate_rankings{iTab}'] = df[exhaust_type_str].eq(
                InactiveType.POSTTALLY_EXHAUSTED_BY_DUPLICATE_RANKING)

            all_posttally_conditions = [
                f'posttally_exhausted_by_overvote{iTab}',
                f'posttally_exhausted_by_repeated_skipped_rankings{iTab}',
                f'posttally_exhausted_by_abstention{iTab}',
                f'posttally_exhausted_by_rank_limit{iTab}',
                f'posttally_exhausted_by_duplicate_rankings{iTab}'
            ]
            df['posttally_exhausted'+str(iTab)] = df[all_posttally_conditions].any(axis='columns')

            exh_by_rank_limit_fully_ranked = self._cvr_stat_table['fully_ranked_incl_overvotes'] & \
                df[exhaust_type_str].eq(InactiveType.POSTTALLY_EXHAUSTED_BY_RANK_LIMIT)
            df[f'posttally_exhausted_by_rank_limit_fully_ranked{iTab}'] = exh_by_rank_limit_fully_ranked

        self._contest_stat_table = df

    def _compute_summary_contest_stat_tables(self) -> None:

        tabulation_stats = []

        for iTab in range(1, self._tab_num+1):

            s = pd.Series(dtype='float64')

            s['rcv_type'] = self.__class__.__name__

            exhaust_on_overvote = self._rule_sets[self._contest_rule_set_name]['exhaust_on_overvote_marks']
            exhaust_on_repeated_skipped = self._rule_sets[self._contest_rule_set_name]['exhaust_on_repeated_skipped_marks']
            exhaust_on_duplicate = self._rule_sets[self._contest_rule_set_name]['exhaust_on_duplicate_candidate_marks']
            combine_writeins = self._rule_sets[self._contest_rule_set_name]['combine_writein_marks']
            exclude_writeins = self._rule_sets[self._contest_rule_set_name]['exclude_writein_marks']
            treat_writeins = self._rule_sets[self._contest_rule_set_name]['treat_combined_writeins_as_exhaustable_duplicates']

            s['n_winners'] = self._n_winners
            s['bottoms_up_threshold'] = self._bottoms_up_threshold
            s['exhaust_on_overvote_marks'] = exhaust_on_overvote
            s['exhaust_on_repeated_skipped_marks'] = exhaust_on_repeated_skipped
            s['exhaust_on_duplicate_candidate_marks'] = exhaust_on_duplicate
            s['combine_writein_marks'] = combine_writeins
            s['exclude_writein_marks'] = exclude_writeins
            s['treat_combined_writeins_as_exhaustable_duplicates'] = treat_writeins

            s['number_of_tabulation_winners'] = len(self._tabulation_winner(tabulation_num=iTab))
            s['number_of_contest_winners'] = len(self._all_winners())

            s['tabulation_num'] = iTab
            s['winner'] = self._winner(tabulation_num=iTab)
            s['n_rounds'] = self.n_rounds(tabulation_num=iTab)
            s['winners_consensus_value'] = self._winners_consensus_value(tabulation_num=iTab)

            first_round_active_votes = sum(self.get_round_tally_dict(1, tabulation_num=iTab).values())
            s['first_round_active_votes'] = first_round_active_votes

            final_round_active_votes = sum(self.get_round_tally_dict(s['n_rounds'], tabulation_num=iTab).values())
            s['final_round_active_votes'] = final_round_active_votes

            weight = self._contest_stat_table[f'final_weight{iTab}']

            pretally = sum(self._contest_stat_table[f'pretally_exhausted{iTab}'] * weight)
            s['total_pretally_exhausted'] = pretally

            posttally = sum(self._contest_stat_table[f'posttally_exhausted{iTab}'] * weight)
            s['total_posttally_exhausted'] = posttally

            posttally_overvote = sum(self._contest_stat_table[f'posttally_exhausted_by_overvote{iTab}'] * weight)
            s['total_posttally_exhausted_by_overvote'] = posttally_overvote

            posttally_skipped = sum(self._contest_stat_table[f'posttally_exhausted_by_repeated_skipped_rankings{iTab}'] * weight)
            s['total_posttally_exhausted_by_skipped_rankings'] = posttally_skipped

            posttally_abstention = sum(self._contest_stat_table[f'posttally_exhausted_by_abstention{iTab}'] * weight)
            s['total_posttally_exhausted_by_abstention'] = posttally_abstention

            posttally_duplicate = sum(self._contest_stat_table[f'posttally_exhausted_by_duplicate_rankings{iTab}'] * weight)
            s['total_posttally_exhausted_by_duplicate_rankings'] = posttally_duplicate

            posttally_rank_limit = sum(self._contest_stat_table[f'posttally_exhausted_by_rank_limit{iTab}'] * weight)
            s['total_posttally_exhausted_by_rank_limit'] = posttally_rank_limit

            posttally_rank_limit_full = sum(self._contest_stat_table[f'posttally_exhausted_by_rank_limit_fully_ranked{iTab}'] * weight)
            s['total_posttally_exhausted_by_rank_limit_fully_ranked'] = posttally_rank_limit_full
            s['total_posttally_exhausted_by_rank_limit_partially_ranked'] = posttally_rank_limit - posttally_rank_limit_full

            if len(self._tabulation_winner(tabulation_num=iTab)) == 1:

                s['first_round_winner_vote'] = self._first_round_winner_vote(tabulation_num=iTab)
                s['final_round_winner_vote'] = self._final_round_winner_vote(tabulation_num=iTab)
                s['first_round_winner_percent'] = self._first_round_winner_percent(tabulation_num=iTab)
                s['final_round_winner_percent'] = self._final_round_winner_percent(tabulation_num=iTab)
                s['first_round_winner_place'] = self._first_round_winner_place(tabulation_num=iTab)
                s['condorcet'] = self._condorcet(tabulation_num=iTab)
                s['come_from_behind'] = self._come_from_behind(tabulation_num=iTab)
                s['ranked_winner'] = self._ranked_winner(tabulation_num=iTab)

                final_over_first = self._final_round_winner_votes_over_first_round_active(tabulation_num=iTab)
                s['final_round_winner_votes_over_first_round_active'] = final_over_first

                s['static_win_threshold'] = None

            else:

                s['first_round_winner_vote'] = None
                s['final_round_winner_vote'] = None
                s['first_round_winner_percent'] = None
                s['final_round_winner_percent'] = None
                s['first_round_winner_place'] = None
                s['final_round_winner_votes_over_first_round_active'] = None
                s['condorcet'] = None
                s['come_from_behind'] = None
                s['ranked_winner'] = None

                s['static_win_threshold'] = self.get_win_threshold(tabulation_num=iTab)

            tabulation_stats.append(s.to_frame().transpose())

        self._summary_contest_stat_tables = tabulation_stats

    def _compute_contest_split_stats(self, split_filter: List[bool]) -> pd.DataFrame:

        tabulation_split_stats = []

        filtered_stat_table = self._contest_stat_table.loc[split_filter, :]

        for iTab in range(1, self._tab_num+1):

            s = pd.Series()

            weight = filtered_stat_table[f'final_weight{iTab}']

            pretally = sum(filtered_stat_table[f'pretally_exhausted{iTab}'] * weight)
            s['split_total_pretally_exhausted'] = pretally

            posttally = sum(filtered_stat_table[f'posttally_exhausted{iTab}'] * weight)
            s['split_total_posttally_exhausted'] = posttally

            posttally_overvote = sum(filtered_stat_table[f'posttally_exhausted_by_overvote{iTab}'] * weight)
            s['split_total_posttally_exhausted_by_overvote'] = posttally_overvote

            posttally_skipped = sum(filtered_stat_table[f'posttally_exhausted_by_repeated_skipped_rankings{iTab}'] * weight)
            s['split_total_posttally_exhausted_by_skipped_rankings'] = posttally_skipped

            posttally_abstention = sum(filtered_stat_table[f'posttally_exhausted_by_abstention{iTab}'] * weight)
            s['split_total_posttally_exhausted_by_abstention'] = posttally_abstention

            posttally_rank_limit = sum(filtered_stat_table[f'posttally_exhausted_by_rank_limit{iTab}'] * weight)
            s['split_total_posttally_exhausted_by_rank_limit'] = posttally_rank_limit

            posttally_rank_limit_full = sum(filtered_stat_table[f'posttally_exhausted_by_rank_limit_fully_ranked{iTab}'] * weight)
            s['split_total_posttally_exhausted_by_rank_limit_fully_ranked'] = posttally_rank_limit_full
            s['split_total_posttally_exhausted_by_rank_limit_partially_ranked'] = posttally_rank_limit - posttally_rank_limit_full

            posttally_duplicate = sum(filtered_stat_table[f'posttally_exhausted_by_duplicate_rankings{iTab}'] * weight)
            s['split_total_posttally_exhausted_by_duplicate_rankings'] = posttally_duplicate

            tabulation_split_stats.append(s.to_frame().transpose())

        return tabulation_split_stats

    def _compute_summary_contest_split_stat_tables(self) -> None:

        if not self._split_filter_dict:
            return

        split_tabulation_stat_df_list = [[] for _ in range(self._tab_num)]

        for field in self._split_filter_dict:
            field_clean = self._clean_string(field)

            for unique_val in self._split_filter_dict[field]:
                val_clean = self._clean_string(unique_val)
                split_id = field_clean + "-" + val_clean

                split_id_df = pd.DataFrame({
                    'split_field': [field],
                    'split_value': [unique_val],
                    'split_id': [split_id]
                    })
                split_stat_df_list = self._compute_contest_split_stats(self._split_filter_dict[field][unique_val])

                for split_stat_df_idx, split_stat_df in enumerate(split_stat_df_list):
                    split_tabulation_stat_df_list[split_stat_df_idx].append(
                        pd.concat([split_id_df, split_stat_df], axis='columns'))

        summary_contest_split_stat_tables = [pd.concat(split_stat_list, axis=0, ignore_index=True, sort=False)
                                             for split_stat_list in split_tabulation_stat_df_list]
        self._summary_contest_split_stat_tables = summary_contest_split_stat_tables
