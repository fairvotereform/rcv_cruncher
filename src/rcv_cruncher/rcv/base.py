from __future__ import annotations
from typing import (Dict, Tuple, Type, Union, List, Optional)

import abc
import collections
import decimal

import pandas as pd

import rcv_cruncher.util as util

from rcv_cruncher.cvr.base import CastVoteRecord
from rcv_cruncher.marks import BallotMarks
from rcv_cruncher.rcv.stats import RCV_stats
from rcv_cruncher.rcv.tables import RCV_tables


class RCV(abc.ABC, CastVoteRecord, RCV_stats, RCV_tables):

    @staticmethod
    def get_variant_group(rcv_obj: Type[RCV]) -> str:
        return 'single_winner' if len(rcv_obj._all_winners()) == 1 else 'multi_winner'

    @staticmethod
    def get_variant_name(rcv_obj: Type[RCV]) -> str:
        return rcv_obj.__class__.__name__

    # override me
    @abc.abstractmethod
    def _set_round_winners(self) -> None:
        """
        This function should set self.round_winners to the list of candidates that won the round
        """
        pass

    # override me
    @abc.abstractmethod
    def _contest_not_complete(self) -> bool:
        """
        This function should return True if another round should be evaluated and False
        is the contest should complete.
        """
        pass

    # override me
    @abc.abstractmethod
    def _calc_round_transfer(self) -> None:
        """
        This function should append a dictionary to self._tabulations[self._tab_num-1]['transfers'] containing:
        candidate names as keys, plus one key for 'exhaust' and any other keys for transfer categories
        values as round transfer flows.
        """
        pass

    # override me
    def _win_threshold(self) -> Optional[Union[int, float]]:
        """
        This function should return the win threshold used in the contest
        OR return 'dynamic' if threshold changes with each round.
        """
        return None

    # override me, if ballots should be split/re-weighted prior to next round
    # such as in fractional transfer contests
    def _update_weights(self) -> None:
        pass

    # override me, if you need to do multiple iterations of rcv, e.x. utah sequential rcv
    def _run_contest(self) -> None:
        # run tabulation
        self._new_tabulation()
        self._tabulate()

    def __init__(self,
                 exhaust_on_duplicate_candidate_marks: bool = False,
                 exhaust_on_overvote_marks: bool = False,
                 exhaust_on_repeated_skipped_marks: bool = False,
                 treat_combined_writeins_as_exhaustable_duplicates: bool = True,
                 combine_writein_marks: bool = True,
                 exclude_writein_marks: bool = False,
                 n_winners: Optional[int] = None,
                 multi_winner_rounds: Optional[bool] = None,
                 *args, **kwargs) -> None:

        # INIT CVR
        super().__init__(*args, **kwargs)

        # APPLY CONTEST RULES
        self._contest_rule_set_name = '__contest'
        self.add_rule_set(self._contest_rule_set_name,
                          BallotMarks.new_rule_set(
                              combine_writein_marks=combine_writein_marks,
                              exclude_writein_marks=exclude_writein_marks,
                              exclude_duplicate_candidate_marks=True,
                              exclude_overvote_marks=True,
                              exclude_skipped_marks=True,
                              treat_combined_writeins_as_exhaustable_duplicates=treat_combined_writeins_as_exhaustable_duplicates,
                              exhaust_on_duplicate_candidate_marks=exhaust_on_duplicate_candidate_marks,
                              exhaust_on_overvote_marks=exhaust_on_overvote_marks,
                              exhaust_on_repeated_skipped_marks=exhaust_on_repeated_skipped_marks
                          ))

        # CONTEST INPUTS
        self._n_winners = n_winners
        self._multi_winner_rounds = multi_winner_rounds
        self._contest_candidates = self.get_candidates(self._contest_rule_set_name)
        self._contest_cvr_ld = None
        self._reset_ballots()

        # INIT STATE INFO

        # contest-level
        self._tab_num = 0
        self._tabulations = []

        # tabulation-level
        self._inactive_candidates = []
        self._removed_candidates = []

        # round-level
        self._round_num = 0
        self._round_winners = []
        self._round_loser = None

        # RUN
        self._run_contest()

        # CONTEST STATS
        self._contest_stat_table = None
        self._compute_contest_stat_table()

        self._summary_contest_stat_tables = None
        self._compute_summary_contest_stat_tables()

        self._summary_contest_split_stat_tables = None

    def stats(self,
              keep_decimal_type: bool = False,
              add_split_stats: bool = False,
              add_id_info: bool = True) -> pd.DataFrame:

        # start with cvr stats, 1 set per cvr
        cvr_stats = self._summary_cvr_stat_table.copy()

        # add on the contest stats for each tabulation
        contest_stats = [pd.concat([cvr_stats, df], axis='columns', sort=False)
                         for df in self._summary_contest_stat_tables]

        # add on the id info
        if add_id_info:
            contest_stats = [pd.concat([self._id_df, df], axis='columns', sort=False)
                             for df in contest_stats]

        if add_split_stats:

            self._make_split_filter_dict()
            self._compute_summary_cvr_split_stat_table()
            self._compute_summary_contest_split_stat_tables()
            cvr_split_stat_table = self._summary_cvr_split_stat_table
            contest_split_stat_tables = self._summary_contest_split_stat_tables

            if cvr_split_stat_table is not None and contest_split_stat_tables is not None:

                new_contest_stats = []
                for stat_table, split_stat_table in zip(contest_stats, contest_split_stat_tables):

                    # merge cvr split stats (1 per cvr) with current tabulation split stats
                    merged = cvr_split_stat_table.merge(split_stat_table, on=['split_field', 'split_value', 'split_id'])

                    # add in non split stat column generated in previous sections
                    merged = merged.assign(**{col: stat_table.at[0, col]
                                              if not isinstance(stat_table.at[0, col], tuple) else stat_table.at[0, col][0]
                                              for col in stat_table.columns})
                    merged = merged[
                        merged.columns.tolist()[-1 * len(stat_table.columns):] +
                        merged.columns.tolist()[:-1 * len(stat_table.columns)]
                    ]

                    new_contest_stats.append(merged)

                contest_stats = new_contest_stats

        if not keep_decimal_type:
            contest_stats = [t.applymap(util.decimal2float) for t in contest_stats]

        return contest_stats

    def _reset_ballots(self) -> None:
        contest_cvr_dl = self.get_cvr_dict(self._contest_rule_set_name)
        self._contest_cvr_ld = [{'ballot_marks': bm, 'weight': weight, 'weight_distrib': []}
                                for bm, weight in zip(contest_cvr_dl['ballot_marks'], contest_cvr_dl['weight'])]

    def _pre_check(self) -> None:
        """
        Any checks on the input data to make sure tabulation will be possible.
        """

        # check for all blank ballots, undervote or blank before exhaust
        ballot_sets = [b['ballot_marks'].unique_marks for b in self._contest_cvr_ld]
        if not set.union(*ballot_sets):
            raise RuntimeError(f"(tabulation={self._tab_num}) all effectively blank ballots")

    def _new_tabulation(self) -> None:
        """
        Add a new set of results for tabulation
        """
        self._tab_num += 1
        new_outcomes = {cand: {'name': cand, 'round_eliminated': None, 'round_elected': None}
                        for cand in self._contest_candidates.unique_candidates}
        self._tabulations.append(
            {
                'rounds': [],
                'transfers': [],
                'candidate_outcomes': new_outcomes,
                'final_weights': [],
                'final_weight_distrib': [],
                'final_ranks': [],
                'initial_ranks': [],
                'initial_weights': [],
                'win_threshold': None
            }
        )

    def _tabulate(self) -> None:
        """
        Run the rounds of rcv contest.
        """

        # use to mark first elimination round that occurs
        first_elimination_round = None

        # remove inactive candidates
        self._clean_round()

        # checks to make tabulation can proceed
        self._pre_check()

        # store initial values
        initial_ranks = [b['ballot_marks'].marks for b in self._contest_cvr_ld]
        self._tabulations[self._tab_num-1]['initial_ranks'] = initial_ranks

        initial_weights = [b['weight'] for b in self._contest_cvr_ld]
        self._tabulations[self._tab_num-1]['initial_weights'] = initial_weights

        not_complete = self._contest_not_complete()
        while not_complete:
            self._round_num += 1

            #############################################
            # CLEAR LAST ROUND VALUES
            self._round_winners = []
            self._round_loser = None

            #############################################
            # COUNT ROUND RESULTS
            self._tally_active_ballots()

            #############################################
            # CHECK FOR ROUND WINNERS
            self._set_round_winners()

            # on the first elimination round, mark any candidates with zero votes for elimination
            if first_elimination_round is None and not self._round_winners:
                round_dict = self.get_round_tally_dict(self._round_num, tabulation_num=self._tab_num)
                novote_losers = [cand for cand in self._contest_candidates.unique_candidates if round_dict[cand] == 0]

                for loser in novote_losers:
                    self._tabulations[self._tab_num-1]['candidate_outcomes'][loser]['round_eliminated'] = self._round_num

                self._inactive_candidates += novote_losers
                first_elimination_round = False

            #############################################
            # IDENTIFY ROUND LOSER
            self._set_round_loser()

            #############################################
            # UPDATE inactive candidate list using round winner/loser
            self._update_candidates()

            # update complete flag
            not_complete = self._contest_not_complete()

            #############################################
            # UPDATE WEIGHTS
            # don't update if contest over
            if not_complete:
                self._update_weights()

            #############################################
            # CALC ROUND TRANSFER
            if not_complete:
                self._calc_round_transfer()
            else:
                self._tabulations[self._tab_num-1]['transfers'].append(
                    {cand: util.NAN for cand in self._contest_candidates.unique_candidates.union({'exhaust'})})

            #############################################
            # CLEAN ROUND BALLOTS
            # remove inactive candidates
            # don't clean if contest over
            if not_complete:
                self._clean_round()

        # record final ballot weight distributions
        final_weight_distrib = [b['weight_distrib'] + [(b['ballot_marks'].marks[0], b['weight'])]
                                if b['ballot_marks'].marks else b['weight_distrib'] + [('empty', b['weight'])]
                                for b in self._contest_cvr_ld]
        self._tabulations[self._tab_num-1]['final_weight_distrib'] = final_weight_distrib

        # set final weight for each ballot
        final_weights = [b['weight'] for b in self._contest_cvr_ld]
        self._tabulations[self._tab_num-1]['final_weights'] = final_weights

        # set final ranks for each ballot
        final_ranks = [b['ballot_marks'].marks for b in self._contest_cvr_ld]
        self._tabulations[self._tab_num-1]['final_ranks'] = final_ranks

        self._tabulations[self._tab_num-1]['win_threshold'] = self._win_threshold()

    def _clean_round(self) -> None:
        """
        Remove any newly inactivated candidates from the ballot ranks.
        """
        for inactive_cand in self._inactive_candidates:
            if inactive_cand not in self._removed_candidates:
                self._contest_cvr_ld = [
                    {
                        'ballot_marks': BallotMarks.remove_mark(b['ballot_marks'], [inactive_cand]),
                        'weight': b['weight'],
                        'weight_distrib': b['weight_distrib']
                    }
                    for b in self._contest_cvr_ld]
                self._removed_candidates.append(inactive_cand)

    def _tally_active_ballots(self) -> None:

        # tally current and distributed weights
        vote_alloc = collections.Counter({cand: 0 for cand in self._contest_candidates.unique_candidates})

        for b in self._contest_cvr_ld:
            if b['ballot_marks'].marks:
                vote_alloc[b['ballot_marks'].marks[0]] += b['weight']
            if b['weight_distrib']:
                for candidate, weight in b['weight_distrib']:
                    vote_alloc[candidate] += weight

        round_results = list(zip(*vote_alloc.most_common()))
        self._tabulations[self._tab_num-1]['rounds'].append(round_results)

    def _update_candidates(self) -> None:
        """
        Update candidate outcomes
        Assume winners are to become inactive, otherwise inactivate loser
        """

        # update winner outcomes
        for winner in self._round_winners:
            self._tabulations[self._tab_num-1]['candidate_outcomes'][winner]['round_elected'] = self._round_num
            self._inactive_candidates.append(winner)

        # if contest is not over
        if self._contest_not_complete():

            # if no winner, add loser
            if not self._round_winners:
                self._inactive_candidates.append(self._round_loser)
                self._tabulations[self._tab_num-1]['candidate_outcomes'][self._round_loser]['round_eliminated'] = self._round_num

        # if contest is over
        else:

            # set all remaining non-winners as eliminated
            remaining_candidates = [d['name'] for d in self._tabulations[self._tab_num-1]['candidate_outcomes'].values()
                                    if d['round_elected'] is None and d['round_eliminated'] is None]
            for cand in remaining_candidates:
                self._tabulations[self._tab_num-1]['candidate_outcomes'][cand]['round_eliminated'] = self._round_num
            self._inactive_candidates += remaining_candidates

    def _set_round_loser(self) -> None:
        """
        Find candidate from round with least votes.
        If more than one, choose randomly
        """

        # split round results into two tuples (index-matched)
        active_candidates, round_tallies = self.get_round_tally_tuple(self._round_num, self._tab_num,
                                                                      only_round_active_candidates=True, desc_sort=True)
        # find round loser
        # ignore zero vote candidates, they will be automtically eliminated with the first non-zero loser
        loser_count = min(i for i in round_tallies if i)

        # haven't implemented any special rules for tied losers. Print a warning if one is reached
        if len([cand for cand, cand_tally
                in zip(active_candidates, round_tallies) if cand_tally == loser_count]) > 1:
            raise RuntimeWarning("reached a round with tied losers....")

        # in case of tied losers, choose one to eliminate (the last one in alpha order)
        round_losers = sorted([cand for cand, cand_tally
                               in zip(active_candidates, round_tallies)
                               if cand_tally == loser_count])
        self._round_loser = round_losers[-1]

    def get_round_tally_tuple(self,
                              round_num: int,
                              tabulation_num: int = 1,
                              only_round_active_candidates: bool = False,
                              desc_sort: bool = False) -> List[Tuple[str], Tuple[decimal.Decimal]]:
        """
        Return a dictionary containing keys as candidates and values as their vote counts in the round.
        """
        cands, tallies = self._tabulations[tabulation_num-1]['rounds'][round_num-1]

        # remove elected or eliminated candidates
        if only_round_active_candidates:

            outcomes = self._tabulations[tabulation_num-1]['candidate_outcomes']

            elected_filter = [(outcomes[cand]['round_elected'] is None or outcomes[cand]['round_elected'] >= round_num)
                              for cand in outcomes]
            eliminated_filter = [(outcomes[cand]['round_eliminated'] is None or outcomes[cand]['round_eliminated'] >= round_num)
                                 for cand in outcomes]

            active_candidates = [cand for cand, elect_filt, elim_filt in zip(outcomes, elected_filter, eliminated_filter)
                                 if elect_filt and elim_filt]
            tallies = [tally for idx, tally in enumerate(tallies) if cands[idx] in active_candidates]
            cands = [cand for cand in cands if cand in active_candidates]

        # sort
        if desc_sort:
            rounds = list(zip(*[(cand, tally) for cand, tally in sorted(zip(cands, tallies), key=lambda x: -x[1])]))
        else:
            rounds = [tuple(cands), tuple(tallies)]

        return rounds

    def get_round_tally_dict(self,
                             round_num: int,
                             tabulation_num: int = 1,
                             only_round_active_candidates: bool = False) -> Dict[str, decimal.Decimal]:
        """
        Return a dictionary containing keys as candidates and values as their vote counts in the round. Includes
        zero vote candidates and those winners remaining at threshold.
        """
        # convert to dict
        return {cand: count for cand, count in
                zip(*self.get_round_tally_tuple(round_num,
                                                tabulation_num,
                                                only_round_active_candidates=only_round_active_candidates))}

    def get_round_transfer_dict(self,
                                round_num: int,
                                tabulation_num: int = 1) -> Dict[str, decimal.Decimal]:
        """
        Return a dictionary containing keys as candidates + 'exhaust' and values as their round net transfer
        """
        transfers = self._tabulations[tabulation_num-1]['transfers']
        return transfers[round_num-1]

    def get_candidate_outcomes(self, tabulation_num: int = 1) -> Dict[str, Optional[int]]:
        """
        Return a list of dictionaries {keys: name, round_elected, round_eliminated}
        """
        candidate_outcomes = self._tabulations[tabulation_num-1]['candidate_outcomes']
        return list(candidate_outcomes.values())

    def get_final_weights(self, tabulation_num: int = 1) -> List[decimal.Decimal]:
        """
        Return a list of ballot weights after tabulation, index-matched with ballots
        """
        final_weights = self._tabulations[tabulation_num-1]['final_weights']
        return final_weights

    def get_initial_ranks(self, tabulation_num: int = 1) -> List[List[str]]:
        """
        Return a list of ballot ranks prior to tabulation, but after an initial cleaning. Each set of ranks is a list.
        """
        initial_ranks = self._tabulations[tabulation_num-1]['initial_ranks']
        return initial_ranks

    def get_initial_weights(self, tabulation_num: int = 1) -> List[decimal.Decimal]:
        """
        Return a list of ballot weights prior to tabulation, but after an initial cleaning. Each set of ranks is a list.
        """
        initial_weights = self._tabulations[tabulation_num-1]['initial_weights']
        return initial_weights

    def get_final_ranks(self, tabulation_num: int = 1) -> List[List[str]]:
        """
        Return a list of ballot ranks after tabulation. Each set of ranks is a list.
        """
        final_ranks = self._tabulations[tabulation_num-1]['final_ranks']
        return final_ranks

    def get_final_weight_distrib(self, tabulation_num: int = 1) -> List[List[Tuple[str, decimal.Decimal]]]:
        """
        Return a list of ballot weight distributions after tabulation. Each set of weight distributions
        is a ranking-weight tuple pair. Ballots that exhausted have the string 'empty' in the ranking position of
        the tuple.
        """
        final_weights = self._tabulations[tabulation_num-1]['final_weight_distrib']
        return final_weights

    def get_win_threshold(self, tabulation_num: int = 1) -> Optional[Union[int, float]]:
        return self._tabulations[tabulation_num-1]['win_threshold']

    def finalist_candidates(self, tabulation_num: int = 1) -> List[str]:
        """
        Return list of candidates with any ballot weight allotted to them by the end of tabulation.
        """
        final_weight_distrib = self.get_final_weight_distrib(tabulation_num=tabulation_num)
        final_weight_cands = list(set(t[0] for t in util.flatten_list(final_weight_distrib)).difference({'empty'}))
        return final_weight_cands

    def n_rounds(self, tabulation_num: int = 1) -> int:
        """
        Return the number of rounds, for a given tabulation.
        """
        rounds = self._tabulations[tabulation_num-1]['rounds']
        return len(rounds)

    def n_tabulations(self) -> int:
        return self._tab_num
