"""
Contains the RCV class.
Defines the class and adds in methods from rcv/stats.py and rcv/tables.py files.
"""
from __future__ import annotations
from typing import Dict, Tuple, Type, Union, List, Optional, Callable

import abc
import collections
import decimal
import random
import json
import pathlib

import pandas as pd

import rcv_cruncher.util as util

from rcv_cruncher.cvr.base import CastVoteRecord
from rcv_cruncher.marks import BallotMarks
from rcv_cruncher.rcv.stats import RCV_stats
from rcv_cruncher.rcv.tables import RCV_tables


class RCV(abc.ABC, CastVoteRecord, RCV_stats, RCV_tables):
    """
    Template class, inherits from CastVoteRecord. Creates the function skeleton for use in the definition of specific RCV variant tabulation methods. Also computes set of default statistics for CVR and RCV.
    """

    @staticmethod
    def get_variant_group(rcv_obj: Type[RCV]) -> str:
        """Convenience function for batch script. Categorizes an election as single winner or multi winner based on the number of winners.

        :type rcv_obj: Type[RCV]
        :return: String describing the election as single winner or multi winner.
        :rtype: str
        """
        return "single_winner" if len(rcv_obj._all_winners()) == 1 else "multi_winner"

    @staticmethod
    def get_variant_name(rcv_obj: Type[RCV]) -> str:
        """Convenience function for batch script. Returns name of RCV class.

        :type rcv_obj: Type[RCV]
        :return: Name of class of object passed
        :rtype: str
        """
        return rcv_obj.__class__.__name__

    @staticmethod
    def calc_winner_choice_position_distribution_table(
        rcv_obj: Type[RCV], tabulation_num: int = 1
    ) -> Optional[pd.DataFrame]:
        """Static wrapper for `RCV.get_winner_choice_position_distribution_table`.

        :param rcv_obj: RCV object or RCV subclass object
        :type rcv_obj: Type[RCV]
        :param tabulation_num: The tabulation to produce the table for, defaults to 1
        :type tabulation_num: int, optional
        :rtype: pd.DataFrame
        """
        return rcv_obj.get_winner_choice_position_distribution_table(tabulation_num=tabulation_num)

    @staticmethod
    def calc_first_choice_to_finalist_table(rcv_obj: Type[RCV], tabulation_num: int = 1) -> pd.DataFrame:
        """Static wrapper for `RCV.get_first_choice_to_finalist_table`.

        :param rcv_obj: RCV object or RCV subclass object
        :type rcv_obj: Type[RCV]
        :param tabulation_num: The tabulation to produce the table for, defaults to 1
        :type tabulation_num: int, optional
        :rtype: pd.DataFrame
        """
        return rcv_obj.get_first_choice_to_finalist_table(tabulation_num=tabulation_num)

    @staticmethod
    def calc_candidate_rank_usage_table(rcv_obj: Type[CastVoteRecord]) -> pd.DataFrame:
        """Static wrapper for `RCV.get_candidate_rank_usage_table`.

        :param rcv_obj: RCV object or RCV subclass object
        :type rcv_obj: Type[CastVoteRecord]
        :rtype: pd.DataFrame
        """
        return rcv_obj.get_candidate_rank_usage_table()

    @staticmethod
    def calc_round_by_round_table(rcv_obj: Type[RCV], tabulation_num: int = 1) -> pd.DataFrame:
        """Static wrapper for `RCV.get_round_by_round_table`.

        :param rcv_obj: RCV object or RCV subclass object
        :type rcv_obj: Type[CastVoteRecord]
        :rtype: pd.DataFrame
        """
        return rcv_obj.get_round_by_round_table(tabulation_num=tabulation_num)

    @staticmethod
    def write_first_choice_to_finalist_table(rcv_obj: Type[RCV], save_dir: Union[str, pathlib.Path] = None) -> None:
        """Wrapper for `RCV.get_first_choice_to_finalist_table` that writes out the table for each tabulation to path '{save_dir}/first_choice_to_finalist/{jurisdiction}_{date OR year}_{office}_tab{tabulation_num}.csv'

        :param rcv_obj: RCV object or RCV subclass object
        :type rcv_obj: Type[RCV]
        :param save_dir: Directory path to write tables to, defaults to None
        :type save_dir: Union[str, pathlib.Path], optional
        """
        save_path = pathlib.Path(save_dir) / "first_choice_to_finalist"
        save_path.mkdir(exist_ok=True)

        uid = rcv_obj.get_stats()[0]["unique_id"].item()
        for iTab in range(1, rcv_obj.n_tabulations() + 1):
            df = rcv_obj.get_first_choice_to_finalist_table(tabulation_num=iTab)
            df.to_csv(save_path / f"{uid}_tab{iTab}.csv")

    @staticmethod
    def write_round_by_round_table(rcv_obj: Type[RCV], save_dir: Union[str, pathlib.Path] = None) -> None:
        """Wrapper for `RCV.get_round_by_round_table` that writes out the table for each tabulation to path '{save_dir}/round_by_round_table/{jurisdiction}_{date OR year}_{office}_tab{tabulation_num}.csv'

        :param rcv_obj: RCV object or RCV subclass object
        :type rcv_obj: Type[RCV]
        :param save_dir: Directory path to write tables to, defaults to None
        :type save_dir: Union[str, pathlib.Path], optional
        """
        save_path = pathlib.Path(save_dir) / "round_by_round_table"
        save_path.mkdir(exist_ok=True)

        uid = rcv_obj.get_stats()[0]["unique_id"].item()
        for iTab in range(1, rcv_obj.n_tabulations() + 1):
            df = rcv_obj.get_round_by_round_table(tabulation_num=iTab)
            df.to_csv(save_path / f"{uid}_tab{iTab}.csv", index=False)

    @staticmethod
    def write_round_by_round_json(rcv_obj: Type[RCV], save_dir: Union[pathlib.Path, str]) -> None:
        """
        Wrapper for `RCV.get_round_by_round_dict` that writes out the dictionary for each tabulation to path '{save_dir}/round_by_round_json/{jurisdiction}_{date OR year}_{office}_tab{tabulation_num}.csv'

        :param rcv_obj: RCV object
        :type rcv_obj: Type[RCV]
        :param save_dir: Path to create "round_by_round_json" directory and write out json files.
        :type save_dir: Union[pathlib.Path, str]
        """
        save_path = pathlib.Path(save_dir) / "round_by_round_json"
        save_path.mkdir(exist_ok=True)

        uid = CastVoteRecord.calc_stats(rcv_obj)[0]["unique_id"].item()

        n_tabulations = rcv_obj.n_tabulations()
        for iTab in range(1, n_tabulations + 1):

            json_dict = rcv_obj.get_round_by_round_dict(tabulation_num=iTab)

            outfile = open(save_path / f"{uid}_tab{iTab}.json", "w")
            json.dump(json_dict, outfile)
            outfile.close()

    # override me
    @abc.abstractmethod
    def _set_round_winners(self) -> None:
        """
        Abstract method to be implemented by RCV variant subclass.
        This function should set self.round_winners to the list of candidates that won the round.
        """
        pass

    # override me
    @abc.abstractmethod
    def _contest_not_complete(self) -> bool:
        """
        Abstract method to be implemented by RCV variant subclass.
        This function should return True if another round should be evaluated and False
        is the contest should complete.

        :return: True if contest has not yet reached an end condition, False otherwise.
        :rtype: bool
        """
        pass

    # override me
    @abc.abstractmethod
    def _calc_round_transfer(self) -> None:
        """
        Abstract method to be implemented by RCV variant subclass.
        This function should append a dictionary to self._tabulations[self._tab_num-1]['transfers'] containing:
        candidate names as keys, plus one key for 'exhaust' and any other keys for transfer categories
        values as round transfer flows.
        """
        pass

    # override me
    def _win_threshold(self) -> Union[int, float, str, None]:
        """
        'Optional' abstract method.

        This function should return the win threshold, in terms of vote counts, used in the contest
        OR return 'dynamic' if threshold changes with each round.

        :return: Vote threshold used in election if static threshold used, else return 'dynamic'.
        :rtype: Optional[Union[int, float, str, None]]
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

    def __init__(
        self,
        jurisdiction: str = "",
        state: str = "",
        year: str = "",
        date: str = "",
        office: str = "",
        notes: str = "",
        parser_func: Optional[Callable] = None,
        parser_args: Optional[Dict] = None,
        parsed_cvr: Optional[Dict] = None,
        split_fields: Optional[List] = None,
        disable_aggregation: bool = False,
        exhaust_on_duplicate_candidate_marks: bool = False,
        exhaust_on_overvote_marks: bool = False,
        exhaust_on_repeated_skipped_marks: bool = False,
        treat_combined_writeins_as_exhaustable_duplicates: bool = True,
        combine_writein_marks: bool = True,
        exclude_writein_marks: bool = False,
        n_winners: Optional[int] = None,
        multi_winner_rounds: bool = False,
        bottoms_up_threshold: Optional[float] = None,
    ) -> None:
        """
        Constructor. Subclass of CastVoteRecord. Initializes CastVoteRecord superclass, applies contest rules to ballots, tabulates the election, and calculates default statistics.

        First set of arguments are identical to CastVoteRecord constructor.

        For ballot rule arguments, see `BallotMarks.new_rule_set` for a description of their meaning. In election tabulation, overvotes, skipped rankings, and duplicate candidate rankings are removed from ballots, unless they cause the ballot to become inactive due to other rule settings in which case the ballot is effectively truncated after those marks are reached.

        :param n_winners: Number of winners in the election, if applicabale. Defaults to None
        :type n_winners: Optional[int], optional
        :param multi_winner_rounds: If True, and multiple winner are possible in a single round, then they are all elected that round. If False, only the winner with the highest ballot total that round is elected. Defaults to False
        :type multi_winner_rounds: Optional[bool], optional
        :param bottoms_up_threshold: Float between 0 and 1 indicating the dynamic threshold to use in each round of a bottoms up election, defaults to None
        :type bottoms_up_threshold: Optional[float], optional
        """

        # INIT CVR
        super().__init__(
            jurisdiction,
            state,
            year,
            date,
            office,
            notes,
            parser_func,
            parser_args,
            parsed_cvr,
            split_fields,
            disable_aggregation,
        )

        # APPLY CONTEST RULES
        self._contest_rule_set_name = "__contest"
        self.add_rule_set(
            self._contest_rule_set_name,
            BallotMarks.new_rule_set(
                exclude_duplicate_candidate_marks=True,
                exclude_overvote_marks=True,
                exclude_skipped_marks=True,
                combine_writein_marks=combine_writein_marks,
                exclude_writein_marks=exclude_writein_marks,
                treat_combined_writeins_as_exhaustable_duplicates=treat_combined_writeins_as_exhaustable_duplicates,
                exhaust_on_duplicate_candidate_marks=exhaust_on_duplicate_candidate_marks,
                exhaust_on_overvote_marks=exhaust_on_overvote_marks,
                exhaust_on_repeated_skipped_marks=exhaust_on_repeated_skipped_marks,
            ),
        )

        # CONTEST INPUTS
        self._bottoms_up_threshold = None
        if bottoms_up_threshold is not None:
            self._bottoms_up_threshold = decimal.Decimal(str(bottoms_up_threshold))
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

    def get_stats(
        self,
        keep_decimal_type: bool = False,
        add_split_stats: bool = False,
        add_id_info: bool = True,
    ) -> List[pd.DataFrame]:
        """Obtain the default statistics calculated by the RCV object, these include statistics calculcated by CastVoteRecord object. Statistics are returned in pandas dataframe objects. One dataframe is returned for each tabulation in the election.

        :param keep_decimal_type: Return the decimal class objects used by internal calculations rather than converting them to floats, defaults to False
        :type keep_decimal_type: bool, optional
        :param add_split_stats: Add extra statistics calculated for each category contained in `split_fields` columns passed to constructor, defaults to False
        :type add_split_stats: bool, optional
        :param add_id_info: Include contest ID details to returned dataframe, defaults to True
        :type add_id_info: bool, optional
        :return: A single row dataframe with statistics organized in multiple columns. If `split_fields` are passed, then extra rows are added for each category in the split columns. One dataframe is returned per tabulation.
        :rtype: List[pd.DataFrame]
        """

        # add on the contest stats for each tabulation
        contest_stats = [
            pd.concat([self._summary_cvr_stat_table, df], axis="columns", sort=False)
            for df in self._summary_contest_stat_tables
        ]

        # add on the id info
        if add_id_info:
            contest_stats = [pd.concat([self._id_df, df], axis="columns", sort=False) for df in contest_stats]

        if add_split_stats:

            # self._make_split_filter_dict()
            self._compute_summary_cvr_split_stat_table()
            self._compute_summary_contest_split_stat_tables()

            cvr_split_stat_table = self._summary_cvr_split_stat_table
            contest_split_stat_tables = self._summary_contest_split_stat_tables

            if cvr_split_stat_table is not None and contest_split_stat_tables is not None:

                new_contest_stats = []
                for contest_split_stat_table in contest_split_stat_tables:
                    merged = cvr_split_stat_table.merge(
                        contest_split_stat_table,
                        on=["split_field", "split_value", "split_id"],
                    )
                    for col in self._id_df.columns.tolist():
                        merged[col] = self._id_df[col].item()
                    new_contest_stats.append(merged)

                # for stat_table, split_stat_table in zip(contest_stats, contest_split_stat_tables):

                #     # merge cvr split stats (1 per cvr) with current tabulation split stats
                #     merged = cvr_split_stat_table.merge(split_stat_table, on=['split_field', 'split_value', 'split_id'])

                #     # add in non split stat column generated in previous sections
                #     merged = merged.assign(**{col: stat_table.at[0, col]
                #                               if not isinstance(stat_table.at[0, col], tuple) else stat_table.at[0, col][0]
                #                               for col in stat_table.columns})
                #     merged = merged[
                #         merged.columns.tolist()[-1 * len(stat_table.columns):] +
                #         merged.columns.tolist()[:-1 * len(stat_table.columns)]
                #     ]

                #     new_contest_stats.append(merged)

                contest_stats = new_contest_stats

        if not keep_decimal_type:
            contest_stats = [t.applymap(util.decimal2float) for t in contest_stats]

        return contest_stats

    def _reset_ballots(self) -> None:
        contest_cvr_dl = self.get_cvr_dict(self._contest_rule_set_name, disaggregate=False)
        self._contest_cvr_ld = [
            {"ballot_marks": bm, "weight": weight, "weight_distrib": []}
            for bm, weight in zip(contest_cvr_dl["ballot_marks"], contest_cvr_dl["weight"])
        ]

    def _pre_check(self) -> None:
        """
        Any checks on the input data to make sure tabulation will be possible.
        """

        # check for all blank ballots, undervote or blank before exhaust
        ballot_sets = [b["ballot_marks"].unique_marks for b in self._contest_cvr_ld]
        if not set.union(*ballot_sets):
            raise RuntimeError(f"(tabulation={self._tab_num}) all effectively blank ballots")

    def _new_tabulation(self) -> None:
        """
        Add a new set of results for tabulation
        """
        self._tab_num += 1
        new_outcomes = {
            cand: {"name": cand, "round_eliminated": None, "round_elected": None}
            for cand in self._contest_candidates.unique_candidates
        }
        self._tabulations.append(
            {
                "rounds": [],
                "summary_transfers": [],
                "by_candidate_transfers": [],
                "candidate_outcomes": new_outcomes,
                "final_weight_distrib": [],
                "final_ranks": [],
                "initial_ranks": [],
                "ballot_round_allocation": [],
                "ballot_round_weight": [],
                "win_threshold": None,
            }
        )

    def _tabulate(self) -> None:
        """
        Run the rounds of rcv contest.
        """

        # use to mark first elimination round that occurs
        first_elimination_round = None

        # remove inactive candidates
        self._clean_ballots()

        # checks to make tabulation can proceed
        self._pre_check()

        # store initial values
        initial_ranks = [b["ballot_marks"].marks for b in self._contest_cvr_ld]
        self._tabulations[self._tab_num - 1]["initial_ranks"] = initial_ranks

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
                    self._tabulations[self._tab_num - 1]["candidate_outcomes"][loser][
                        "round_eliminated"
                    ] = self._round_num

                self._inactive_candidates += novote_losers
                first_elimination_round = False

                self._clean_ballots()

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
                self._tabulations[self._tab_num - 1]["summary_transfers"].append(
                    {cand: util.NAN for cand in self._contest_candidates.unique_candidates.union({"exhaust"})}
                )
                self._tabulations[self._tab_num - 1]["by_candidate_transfers"].append({})

            #############################################
            # CLEAN ROUND BALLOTS
            # remove inactive candidates
            # don't clean if contest over
            if not_complete:
                self._clean_ballots()

        # record final ballot weight distributions
        final_weight_distrib = [
            b["weight_distrib"] + [(b["ballot_marks"].marks[0], b["weight"])]
            if b["ballot_marks"].marks
            else b["weight_distrib"] + [("exhaust", b["weight"])]
            for b in self._contest_cvr_ld
        ]
        self._tabulations[self._tab_num - 1]["final_weight_distrib"] = final_weight_distrib

        # set final ranks for each ballot
        final_ranks = [b["ballot_marks"].marks for b in self._contest_cvr_ld]
        self._tabulations[self._tab_num - 1]["final_ranks"] = final_ranks

        self._tabulations[self._tab_num - 1]["win_threshold"] = self._win_threshold()

    def _clean_ballots(self) -> None:
        """
        Remove any newly inactivated candidates from the ballot ranks.
        """
        for inactive_cand in self._inactive_candidates:
            if inactive_cand not in self._removed_candidates:
                self._contest_cvr_ld = [
                    {
                        "ballot_marks": BallotMarks.remove_mark(b["ballot_marks"], [inactive_cand]),
                        "weight": b["weight"],
                        "weight_distrib": b["weight_distrib"],
                    }
                    for b in self._contest_cvr_ld
                ]
                self._removed_candidates.append(inactive_cand)

    def _tally_active_ballots(self) -> None:

        # tally current and distributed weights
        ballot_alloc = []
        ballot_alloc_weight = []
        vote_alloc = collections.Counter({cand: 0 for cand in self._contest_candidates.unique_candidates})

        for b in self._contest_cvr_ld:

            candidate = "exhaust" if len(b["ballot_marks"].marks) == 0 else b["ballot_marks"].marks[0]
            ballot_alloc.append(candidate)
            ballot_alloc_weight.append(b["weight"])

            if candidate != "exhaust":
                vote_alloc[candidate] += b["weight"]

            if b["weight_distrib"]:
                for candidate, weight in b["weight_distrib"]:
                    vote_alloc[candidate] += weight

        round_results = list(zip(*vote_alloc.most_common()))
        self._tabulations[self._tab_num - 1]["rounds"].append(round_results)
        self._tabulations[self._tab_num - 1]["ballot_round_allocation"].append(ballot_alloc)
        self._tabulations[self._tab_num - 1]["ballot_round_weight"].append(ballot_alloc_weight)

    def _update_candidates(self) -> None:
        """
        Update candidate outcomes
        Assume winners are to become inactive, otherwise inactivate loser
        """

        # update winner outcomes
        for winner in self._round_winners:
            self._tabulations[self._tab_num - 1]["candidate_outcomes"][winner]["round_elected"] = self._round_num
            self._inactive_candidates.append(winner)

        # if contest is not over
        if self._contest_not_complete():

            # if no winner, add loser
            if not self._round_winners:
                self._inactive_candidates.append(self._round_loser)
                self._tabulations[self._tab_num - 1]["candidate_outcomes"][self._round_loser][
                    "round_eliminated"
                ] = self._round_num

        # if contest is over
        else:

            # set all remaining non-winners as eliminated
            remaining_candidates = [
                d["name"]
                for d in self._tabulations[self._tab_num - 1]["candidate_outcomes"].values()
                if d["round_elected"] is None and d["round_eliminated"] is None
            ]
            for cand in remaining_candidates:
                self._tabulations[self._tab_num - 1]["candidate_outcomes"][cand]["round_eliminated"] = self._round_num
            self._inactive_candidates += remaining_candidates

    def _set_round_loser(self) -> None:
        """
        Find candidate from round with least votes.
        If more than one, choose randomly
        """

        # split round results into two tuples (index-matched)
        active_candidates, round_tallies = self.get_round_tally_tuple(
            self._round_num, self._tab_num, only_round_active_candidates=True
        )
        # find round loser
        # ignore zero vote candidates, they will be automtically eliminated with the first non-zero loser
        loser_count = min(i for i in round_tallies if i)

        # haven't implemented any special rules for tied losers. Print a warning if one is reached
        # if len([cand for cand, cand_tally
        #         in zip(active_candidates, round_tallies) if cand_tally == loser_count]) > 1:
        #     raise RuntimeWarning("reached a round with tied losers....")

        # in case of tied losers, choose one to eliminate (the last one in alpha order)
        round_losers = sorted(
            [cand for cand, cand_tally in zip(active_candidates, round_tallies) if cand_tally == loser_count]
        )
        self._round_loser = random.sample(round_losers, 1)[0]

    def get_round_tally_tuple(
        self,
        round_num: int,
        tabulation_num: int = 1,
        only_round_active_candidates: bool = False,
    ) -> List[Tuple[str, decimal.Decimal]]:
        """
        Return a list of (candidate name, candidate vote count) tuples for round in tabulation. Tuples are sorted in descending order by vote count and then by ascending order by candidate name.

        :param round_num: Round number for which to return vote counts for.
        :type round_num: int
        :param tabulation_num: Tabulation number from which to index round number, defaults to 1
        :type tabulation_num: int, optional
        :param only_round_active_candidates: If True, only candidate totals for candidates active in the specified round are returned. Otherwise, all candidates are returned. Defaults to False
        :type only_round_active_candidates: bool, optional
        :return: List of tuples containing candidate names and vote totals.
        :rtype: List[Tuple[str, decimal.Decimal]]
        """
        cands, tallies = self._tabulations[tabulation_num - 1]["rounds"][round_num - 1]

        # remove elected or eliminated candidates
        if only_round_active_candidates:

            outcomes = self._tabulations[tabulation_num - 1]["candidate_outcomes"]

            elected_filter = [
                (outcomes[cand]["round_elected"] is None or outcomes[cand]["round_elected"] >= round_num)
                for cand in outcomes
            ]
            eliminated_filter = [
                (outcomes[cand]["round_eliminated"] is None or outcomes[cand]["round_eliminated"] >= round_num)
                for cand in outcomes
            ]

            active_candidates = [
                cand
                for cand, elect_filt, elim_filt in zip(outcomes, elected_filter, eliminated_filter)
                if elect_filt and elim_filt
            ]
            tallies = [tally for idx, tally in enumerate(tallies) if cands[idx] in active_candidates]
            cands = [cand for cand in cands if cand in active_candidates]

        # sort
        rounds = list(zip(*[(cand, tally) for cand, tally in sorted(zip(cands, tallies), key=lambda x: (-x[1], x[0]))]))

        return rounds

    def get_round_tally_dict(
        self,
        round_num: int,
        tabulation_num: int = 1,
        only_round_active_candidates: bool = False,
    ) -> Dict[str, decimal.Decimal]:
        """
        Return a dictionary containing candidate names as keys and vote counts as values.

        :param round_num: Round number for which to return vote counts for.
        :type round_num: int
        :param tabulation_num: Tabulation number from which to index round number, defaults to 1
        :type tabulation_num: int, optional
        :param only_round_active_candidates: If True, only candidate totals for candidates active in the specified round are returned. Otherwise, all candidates are returned. Defaults to False
        :type only_round_active_candidates: bool, optional
        :return: Dictionary containing candidate names and vote totals.
        :rtype: Dict[str, decimal.Decimal]
        """
        # convert to dict
        return {
            cand: count
            for cand, count in zip(
                *self.get_round_tally_tuple(
                    round_num,
                    tabulation_num,
                    only_round_active_candidates=only_round_active_candidates,
                )
            )
        }

    def get_round_transfer_dict(
        self, round_num: int, candidate_netted: bool = True, tabulation_num: int = 1
    ) -> Union[Dict[str, decimal.Decimal], Dict[str, Dict[str, decimal.Decimal]]]:
        """Return a dictionary describing vote transfers from round specified. Keys are candidate names. If `candidate_netted` is True, an extra key 'exhaust' is included and dictionary values are the net vote counts flowing to/from a candidate. Else, values are each another dictionary containing candidate names, plus 'exhaust', as keys and vote flows from the outer key candidate to the inner key candidate.

        :param round_num: Round number to get transfer info for
        :type round_num: int
        :param candidate_netted: If True, dictionary values are net votes flows to/from a candidate. If False, dictionary values are also dictionaries containing flows broken down by candidate. Defaults to True
        :type candidate_netted: bool, optional
        :param tabulation_num: Tabulation in which to index round number, defaults to 1
        :type tabulation_num: int, optional
        :return: Dictionary of transfer vote flows.
        :rtype: Union[Dict[str, decimal.Decimal], Dict[str, Dict[str, decimal.Decimal]]]
        """
        if candidate_netted:
            transfers = self._tabulations[tabulation_num - 1]["summary_transfers"]
        else:
            transfers = self._tabulations[tabulation_num - 1]["by_candidate_transfers"]
        return transfers[round_num - 1]

    def get_candidate_outcomes(self, tabulation_num: int = 1) -> List[Dict]:
        """Return a list of dictionaries containing candidate outcome information for a given tabulation. Keys are name, round_elected, and round_eliminated. Values for round_elected and round_eliminated are either integers indicating round numbers or None.

        :param tabulation_num: Tabulation for which to return candidate outcomes, defaults to 1
        :type tabulation_num: int, optional
        :return: List of dictionaries containing candidate outcome information for a given tabulation
        :rtype: List[Dict]
        """
        candidate_outcomes = self._tabulations[tabulation_num - 1]["candidate_outcomes"]
        return list(candidate_outcomes.values())

    def get_final_weights(self, tabulation_num: int = 1, disaggregate: bool = True) -> List[decimal.Decimal]:
        """Return a list of ballot weights after tabulation.

        :param tabulation_num: Tabulation from which to return final weights, defaults to 1
        :type tabulation_num: int, optional
        :param disaggregate: If True, the internally aggregated CVR is disaggregated before return. Defaults to True.
        :type disaggregate: bool, optional
        :return: List of weights
        :rtype: List[decimal.Decimal]
        """
        final_weights = self._tabulations[tabulation_num - 1]["ballot_round_weight"][-1]

        if disaggregate and not self._disable_aggregation:

            # reduction ratio for each aggregated ballot
            initial_weights = self.get_initial_weights(disaggregate=False)
            reduct_ratio = [(initial - final) / initial for final, initial in zip(final_weights, initial_weights)]

            # apply ratio to each disaggregated weight
            disagg_info = self._disaggregation_info
            disagg_info_keys = list(self._disaggregation_info.keys())

            disagg_weights = [
                [unique_d["weight"] - (unique_d["weight"] * reduct) for unique_d in disagg_info[disagg_info_keys[idx]]]
                for idx, reduct in enumerate(reduct_ratio)
            ]
            final_weights = util.flatten_list(disagg_weights)

        return final_weights

    def get_initial_ranks(self, tabulation_num: int = 1, disaggregate: bool = True) -> List[List[str]]:
        """Ballots prior to first round tabulation, after election rules applied.

        :param tabulation_num: Tabulation number from which to get initial ranks, defaults to 1
        :type tabulation_num: int, optional
        :param disaggregate: If True, the internally aggregated CVR is disaggregated before return. Defaults to True.
        :type disaggregate: bool, optional
        :return: List of lists of candidates/marks.
        :rtype: List[List[str]]
        """
        initial_ranks = self._tabulations[tabulation_num - 1]["initial_ranks"]

        if disaggregate and not self._disable_aggregation:

            disagg_info = self._disaggregation_info
            disagg_info_keys = list(self._disaggregation_info.keys())

            initial_ranks = [
                [ranks for _ in disagg_info[disagg_info_keys[idx]]] for idx, ranks in enumerate(initial_ranks)
            ]
            initial_ranks = util.flatten_list(initial_ranks)

        return initial_ranks

    def get_initial_weights(self, tabulation_num: int = 1, disaggregate: bool = True) -> List[decimal.Decimal]:
        """Return a list of ballot weights prior to specified tabulation.

        :param tabulation_num: Tabulation from which to return final weights, defaults to 1
        :type tabulation_num: int, optional
        :param disaggregate:  If True, the internally aggregated CVR is disaggregated before return. Defaults to True.
        :type disaggregate: bool, optional
        :return: List of weights at the beginning of tabulation.
        :rtype: List[decimal.Decimal]
        """
        initial_weights = self._tabulations[tabulation_num - 1]["ballot_round_weight"][0]

        if disaggregate and not self._disable_aggregation:

            disagg_info = self._disaggregation_info
            disagg_weights = [[unique_d["weight"] for unique_d in disagg_info[key]] for key in disagg_info]
            initial_weights = util.flatten_list(disagg_weights)

        return initial_weights

    def get_final_ranks(self, tabulation_num: int = 1, disaggregate: bool = True) -> List[List]:
        """
        Return a list of ballot ranks after tabulation. Each set of ranks is a list. Ballots marks will be excluded if they violate election rules or if they are the mark of a candidate eliminated during tabulation.

        :param tabulation_num: Tabulation number from which to get initial ranks, defaults to 1
        :type tabulation_num: int, optional
        :param disaggregate: If True, the internally aggregated CVR is disaggregated before return. Defaults to True.
        :type disaggregate: bool, optional
        :return: List of lists of candidates/marks.
        :rtype: List[List[str]]

        """
        final_ranks = self._tabulations[tabulation_num - 1]["final_ranks"]

        if disaggregate and not self._disable_aggregation:

            disagg_info = self._disaggregation_info
            disagg_info_keys = list(self._disaggregation_info.keys())

            final_ranks = [[ranks for _ in disagg_info[disagg_info_keys[idx]]] for idx, ranks in enumerate(final_ranks)]
            final_ranks = util.flatten_list(final_ranks)

        return final_ranks

    def get_final_weight_distrib(
        self, tabulation_num: int = 1, disaggregate: bool = True
    ) -> List[List[Tuple[str, decimal.Decimal]]]:
        """
        Return a list of ballot weight distributions describing how much of each ballot was allocated to a winner, finalist, or exhausted. Each set of weight distributions is a ranking-weight tuple pair. Tuple pairs appear in order of weight allocation throughout the tabulation process. Ballots that exhausted have the string 'exhaust' in the ranking position of the tuple. Each weight distribution should sum to its original weight at the beginning of the tabulation.

        :param tabulation_num: Tabulation number, defaults to 1
        :type tabulation_num: int, optional
        :param disaggregate: If True, the internally aggregated CVR is disaggregated before return. Defaults to True.
        :type disaggregate: bool, optional
        :return: List of ballot weight distributions.
        :rtype: List[List[Tuple[str, decimal.Decimal]]]
        """
        final_weights = self._tabulations[tabulation_num - 1]["final_weight_distrib"]

        if disaggregate and not self._disable_aggregation:

            initial_weights = self.get_initial_weights(tabulation_num=tabulation_num, disaggregate=False)
            final_weights_percent = [
                [(t[0], t[1] / init_weight) for t in final_distrib]
                for final_distrib, init_weight in zip(final_weights, initial_weights)
            ]

            disagg_info = self._disaggregation_info
            disagg_info_keys = list(self._disaggregation_info.keys())

            final_weights = [
                [
                    [(t[0], t[1] * disagg_d["weight"]) for t in weights_percent]
                    for disagg_d in disagg_info[disagg_info_keys[idx]]
                ]
                for idx, weights_percent in enumerate(final_weights_percent)
            ]
            final_weights = util.flatten_list(final_weights)

        return final_weights

    def get_win_threshold(self, tabulation_num: int = 1) -> Union[int, float, str, decimal.Decimal]:
        """Win threshold for a given tabulation expressed as a number of votes. If threshold is not static, string 'dynamic' should be returned.

        :param tabulation_num: Tabulation number, defaults to 1
        :type tabulation_num: int, optional
        :return: Vote threshold a candidate needs to cross in order to win
        :rtype: Union[int, float, decimal.Decimal, str]
        """
        return self._tabulations[tabulation_num - 1]["win_threshold"]

    def finalist_candidates(self, tabulation_num: int = 1) -> List[str]:
        """Return list of candidates with any ballot weight allotted to them by the end of tabulation. This includes winners and non-winner finalists.

        :param tabulation_num: Tabulation from which to return finalists, defaults to 1
        :type tabulation_num: int, optional
        :return: List of candidates
        :rtype: List[str]
        """
        final_weight_distrib = self.get_final_weight_distrib(tabulation_num=tabulation_num)
        final_weight_cands = list(set(t[0] for t in util.flatten_list(final_weight_distrib)).difference({"exhaust"}))
        return final_weight_cands

    def n_rounds(self, tabulation_num: int = 1) -> int:
        """Return the number of rounds used in tabulation, for a given tabulation in the election.

        :param tabulation_num: Tabulation number, defaults to 1
        :type tabulation_num: int, optional
        :return: Number of rounds in the tabulation
        :rtype: int
        """
        rounds = self._tabulations[tabulation_num - 1]["rounds"]
        return len(rounds)

    def n_tabulations(self) -> int:
        """Returns number of tabulations in election

        :return: Number of tabulations in election
        :rtype: int
        """
        return self._tab_num
