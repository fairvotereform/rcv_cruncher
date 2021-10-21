"""Contains RCV_tables class which is added into RCV.
"""

from typing import Optional, Union, Tuple, Dict

import itertools
import pandas as pd

from rcv_cruncher.util import NAN
from rcv_cruncher.marks import BallotMarks
import rcv_cruncher.util as util


class RCV_tables:
    """Extra methods added into RCV class"""

    def get_condorcet_tables(self) -> Tuple[Union[pd.DataFrame, Optional[str]]]:
        """
        Returns a two condorcet tables as a pandas data frame with candidate names as row and column indices.
        One contains counts and the other contains percents. Also return the name of the condorcet winner, or None.

        Each cell indicates the count/percentage of ballots that ranked the row-candidate over
        the column-candidate (including ballots that only ranked the row-candidate). When calculating percents,
        the denominator is each cell is the number of ballots that ranked the row-candidate OR the column-candidate.

        Symmetric cells about the diagonal should sum to 100 (for the percent table).

        Ballots used in condorcet calculation have election rules applied to them.

        :return: Tuple containing count table, percent table, and name of condorcet winner.
        :rtype: Tuple[Union[pd.DataFrame, Optional[str]]]
        """

        candidate_set = self.get_candidates()
        candidate_set = BallotMarks.combine_writein_marks(candidate_set)
        # candidate_set = BallotMarks.remove_mark(candidate_set, BallotMarks.WRITEIN)
        candidate_set = sorted(candidate_set.unique_candidates)

        cleaned_dict = self.get_cvr_dict(self._contest_rule_set_name, disaggregate=False)
        ballot_set = [
            {"ranks": ranks.marks, "weight": weight}
            for ranks, weight in zip(cleaned_dict["ballot_marks"], cleaned_dict["weight"])
        ]

        # create data frame that will be populated and output
        condorcet_percent_df = pd.DataFrame(util.NAN, index=candidate_set, columns=candidate_set)
        condorcet_count_df = pd.DataFrame(util.NAN, index=candidate_set, columns=candidate_set)

        # turn ballot-lists into ballot-dict with
        # key 'id' containing a unique integer id for the ballot
        # key 'ranks' containing the original ballot-list
        ballot_dicts = [{"id": ind, "ballot": ballot} for ind, ballot in enumerate(ballot_set)]

        # make dictionary with candidate as key, and value as list of ballot-dicts
        # that contain their name in any rank
        cand_ballot_dict = {
            cand: [ballot for ballot in ballot_dicts if cand in ballot["ballot"]["ranks"]] for cand in candidate_set
        }

        # all candidate pairs
        cand_pairs = itertools.combinations(candidate_set, 2)

        for pair in cand_pairs:
            cand1 = pair[0]
            cand2 = pair[1]

            # get the union of their ballots
            combined_ballot_list = cand_ballot_dict[cand1] + cand_ballot_dict[cand2]
            uniq_pair_ballots = list({v["id"]: v["ballot"] for v in combined_ballot_list}.values())

            uniq_pair_ballots_weights = [ballot["weight"] for ballot in uniq_pair_ballots]
            sum_weighted_ballots = sum(uniq_pair_ballots_weights)

            # which ballots rank cand1 above cand2?
            cand1_vs_cand2 = [
                util.index_inf(b["ranks"], cand1) < util.index_inf(b["ranks"], cand2) for b in uniq_pair_ballots
            ]
            cand1_vs_cand2_weightsum = sum(
                weight * flag for weight, flag in zip(uniq_pair_ballots_weights, cand1_vs_cand2)
            )

            # the remainder then must rank cand2 over cand1
            cand2_vs_cand1 = [not i for i in cand1_vs_cand2]
            cand2_vs_cand1_weightsum = sum(
                weight * flag for weight, flag in zip(uniq_pair_ballots_weights, cand2_vs_cand1)
            )

            # add counts to df
            condorcet_count_df.loc[cand1, cand2] = cand1_vs_cand2_weightsum
            condorcet_count_df.loc[cand2, cand1] = cand2_vs_cand1_weightsum

            # calculate percent
            if sum_weighted_ballots:
                cand1_percent = (cand1_vs_cand2_weightsum / sum_weighted_ballots) * 100
                cand2_percent = (cand2_vs_cand1_weightsum / sum_weighted_ballots) * 100
            else:
                cand1_percent = 0
                cand2_percent = 0

            # add to df
            condorcet_percent_df.loc[cand1, cand2] = cand1_percent
            condorcet_percent_df.loc[cand2, cand1] = cand2_percent

        # find condorcet winner and set index name to include winner
        condorcet_winner = None

        if len(candidate_set) == 1:

            condorcet_winner = candidate_set[0]
        else:

            for cand in candidate_set:

                not_cand = set(candidate_set) - {cand}
                all_winner = all(condorcet_percent_df.loc[cand, not_cand] > 50)

                if all_winner:
                    if condorcet_winner is None:
                        condorcet_winner = cand
                    else:
                        raise RuntimeError("developer error. more than 1 condorcet winner is possible.")

        # convert decimal to float
        condorcet_count_df = condorcet_count_df.astype(float).round(3)
        condorcet_percent_df = condorcet_percent_df.astype(float).round(3)

        return condorcet_count_df, condorcet_percent_df, condorcet_winner

    def get_first_second_tables(self) -> Tuple[pd.DataFrame]:
        """
        Return pandas dataframes containing first and second choice candidate distributions across ballots. The first row of the table contains the first choice distribution. The following rows in each column indicate the second choice distribution for only the ballots in each first choice ballot pile. Percentages in the first row should sum to 100, and each column below the first row should sum to 100. Ballots used for calculation have election rules applied to them.

        Three versions of the dataframe are returned: one containing ballot counts and two containing ballot percentages. Two percentage dataframes are included, one with an exhaustion category for second choices and one without.

        :return: Tuple containing count table, percentage table, and percentage table without exhausted second choices
        :rtype: Tuple[pd.DataFrame]
        """

        candidate_set = BallotMarks.combine_writein_marks(self.get_candidates())
        candidate_set = sorted(candidate_set.unique_candidates)

        cleaned_dict = self.get_cvr_dict(self._contest_rule_set_name, disaggregate=False)
        ballot_set = [
            {"ranks": ranks.marks, "weight": weight}
            for ranks, weight in zip(cleaned_dict["ballot_marks"], cleaned_dict["weight"])
        ]

        # create data frame that will be populated and output
        percent_no_exhaust_df = pd.DataFrame(util.NAN, index=["first_choice", *candidate_set], columns=candidate_set)
        percent_df = pd.DataFrame(
            util.NAN,
            index=["first_choice", *candidate_set, "exhaust"],
            columns=candidate_set,
        )
        count_df = pd.DataFrame(
            util.NAN,
            index=["first_choice", *candidate_set, "exhaust"],
            columns=candidate_set,
        )

        # group ballots by first choice
        first_choices = {cand: [] for cand in candidate_set}
        for b in ballot_set:
            if len(b["ranks"]) >= 1:
                first_choices[b["ranks"][0]].append(b)

        # sum total first round votes
        total_first_round_votes = 0
        for cand in first_choices:
            total_first_round_votes += sum([b["weight"] for b in first_choices[cand]])

        # add first choices to tables
        # and calculate second choices
        for cand in candidate_set:

            ############################################################
            # update first round table values
            first_choice_count = sum([b["weight"] for b in first_choices[cand]])
            first_choice_percent = (first_choice_count / total_first_round_votes) * 100

            count_df.loc["first_choice", cand] = first_choice_count
            percent_df.loc["first_choice", cand] = first_choice_percent
            percent_no_exhaust_df.loc["first_choice", cand] = first_choice_percent

            ############################################################
            # calculate second choices, group second choices by candidate
            possible_second_choices = list(set(candidate_set) - {cand})
            second_choices = {backup_cand: [] for backup_cand in possible_second_choices + ["exhaust"]}

            # group ballots by second choices
            for b in first_choices[cand]:
                if len(b["ranks"]) >= 2:
                    second_choices[b["ranks"][1]].append(b["weight"])
                else:
                    second_choices["exhaust"].append(b["weight"])

            # sum total second round votes
            total_second_choices = 0
            total_second_choices_no_exhaust = 0
            for backup_cand in second_choices:
                total_second_choices += sum(second_choices[backup_cand])
                if backup_cand != "exhaust":
                    total_second_choices_no_exhaust += sum(second_choices[backup_cand])

            # count second choices and add to table
            for backup_cand in second_choices:

                # fill in second choice values in table
                second_choice_count = sum(second_choices[backup_cand])

                # if there are not backup votes fill with zeros
                if total_second_choices == 0:
                    second_choice_percent = 0
                else:
                    second_choice_percent = (second_choice_count / total_second_choices) * 100

                if total_second_choices_no_exhaust == 0:
                    second_choice_percent_no_exhaust = 0
                else:
                    second_choice_percent_no_exhaust = (second_choice_count / total_second_choices_no_exhaust) * 100

                count_df.loc[backup_cand, cand] = second_choice_count
                percent_df.loc[backup_cand, cand] = second_choice_percent
                if backup_cand != "exhaust":
                    percent_no_exhaust_df.loc[backup_cand, cand] = second_choice_percent_no_exhaust

        count_df = count_df.astype(float).round(3)
        percent_df = percent_df.astype(float).round(3)
        percent_no_exhaust_df = percent_no_exhaust_df.astype(float).round(3)

        return count_df, percent_df, percent_no_exhaust_df

    def get_cumulative_ranking_tables(self) -> Tuple[pd.DataFrame]:
        """
        Return cumulative ranking tables. Rows are candidate names and columns are rank numbers.
        Reading across columns, the tables show the accumulating count/percentage of ballots that marked
        a candidate as more ranks are considered. The final column shows the count/percentage of ballots
        that never marked the candidate. Ballots used for calculation have election rules applied to them.

        :return: Tuple containing count table and percentage table
        :rtype: Tuple[pd.DataFrame]
        """

        # get inputs
        candidate_set = BallotMarks.combine_writein_marks(self.get_candidates())
        candidate_set = sorted(candidate_set.unique_candidates)

        # ballot rank limit
        ballot_length = self.get_stats()[0]["rank_limit"].item()

        # get cleaned ballots
        cleaned_dict = self.get_cvr_dict(self._contest_rule_set_name, disaggregate=False)
        ballot_set = [
            {
                "ranks": ranks.marks + (["NA"] * (ballot_length - len(ranks.marks))),
                "weight": weight,
            }
            for ranks, weight in zip(cleaned_dict["ballot_marks"], cleaned_dict["weight"])
        ]

        # total ballots
        total_ballots = sum([d["weight"] for d in ballot_set])

        # create data frame that will be populated and output
        col_names = ["Rank " + str(i + 1) for i in range(ballot_length)] + ["Did Not Rank"]
        cumulative_percent_df = pd.DataFrame(util.NAN, index=candidate_set, columns=col_names)
        cumulative_count_df = pd.DataFrame(util.NAN, index=candidate_set, columns=col_names)

        # tally candidate counts by rank
        rank_counts = []
        for rank in range(0, ballot_length):
            rank_cand_set = set([b["ranks"][rank] for b in ballot_set]) - {"NA"}
            current_rank_count = {cand: 0 for cand in rank_cand_set}
            for cand in rank_cand_set:
                current_rank_count[cand] = sum(b["weight"] for b in ballot_set if cand == b["ranks"][rank])
            rank_counts.append(current_rank_count)

        # accumulate ballot counts that rank candidates
        cumulative_counter = {cand: 0 for cand in candidate_set}
        for rank in range(0, ballot_length):
            for cand in candidate_set:
                # if candidate has any marks for this rank, accumulate them
                if cand in rank_counts[rank]:
                    cumulative_counter[cand] += rank_counts[rank][cand]
                # update tables
                cumulative_count_df.loc[cand, "Rank " + str(rank + 1)] = cumulative_counter[cand]
                cumulative_percent_df.loc[cand, "Rank " + str(rank + 1)] = (
                    cumulative_counter[cand] * 100 / total_ballots
                )

        # fill in Did Not Rank column
        for cand in candidate_set:
            cumulative_count_df.loc[cand, "Did Not Rank"] = total_ballots - cumulative_counter[cand]
            cumulative_percent_df.loc[cand, "Did Not Rank"] = (
                (total_ballots - cumulative_counter[cand]) * 100 / total_ballots
            )

        cumulative_count_df = cumulative_count_df.astype(float).round(3)
        cumulative_percent_df = cumulative_percent_df.astype(float).round(3)

        return cumulative_count_df, cumulative_percent_df

    def _get_winner_choice_position_distribution_table(self, tabulation_num: int = 1) -> Optional[pd.DataFrame]:
        """[summary]

        :param tabulation_num: [description], defaults to 1
        :type tabulation_num: int, optional
        :raises RuntimeError: [description]
        :return: [description]
        :rtype: Optional[pd.DataFrame]
        """

        winner = self._tabulation_winner(tabulation_num=tabulation_num)
        contest_cvr_dl = self.get_cvr_dict(rule_set_name=self._contest_rule_set_name, disaggregate=False)

        if len(winner) > 1:
            return None

        winner = winner[0]
        rank_limit = self.get_stats()[0]["rank_limit"].item()
        winner_final_round_count = self._final_round_winner_vote(tabulation_num=tabulation_num)
        final_weight_distrib = self.get_final_weight_distrib(tabulation_num=tabulation_num)

        winner_positions = {k: 0 for k in range(1, rank_limit + 1)}
        for b, weight, final_distrib in zip(
            contest_cvr_dl["ballot_marks"],
            contest_cvr_dl["weight"],
            final_weight_distrib,
        ):

            if winner == final_distrib[-1][0]:
                winner_position = b.marks.index(winner)
                winner_positions[winner_position + 1] += weight

        if sum(winner_positions.values()) != winner_final_round_count:
            raise RuntimeError()

        winner_positions = {k: 100 * v / winner_final_round_count for k, v in winner_positions.items()}

        choice_position_df = self.stats()[0][
            [
                "jurisdiction",
                "state",
                "date",
                "year",
                "office",
                "unique_id",
                "winner",
                "rank_limit",
                "n_candidates",
                "n_rounds",
            ]
        ]

        for position, percent in sorted(winner_positions.items()):
            choice_position_df[f"choice{position}"] = float(round(percent, 2))

        return choice_position_df

    def get_first_choice_to_finalist_table(self, tabulation_num: int = 1) -> pd.DataFrame:
        """Create a pandas dataframe describing the first choice candidate distribution and which finalist candidate those ballots ended the tabulation allocated to.

        :param tabulation_num: tabulation number, defaults to 1
        :type tabulation_num: int, optional
        :return: table
        :rtype: pd.DataFrame
        """

        df = None

        # who had any ballot weight allotted
        finalist_candidates = list(self.finalist_candidates(tabulation_num=tabulation_num))
        if "exhaust" not in finalist_candidates:
            finalist_candidates.append("exhaust")
        candidate_set = sorted(self._contest_candidates.unique_candidates)

        ballot_set = [
            {"ranks": ranks, "weight": weight, "weight_distrib": distrib}
            for ranks, weight, distrib in zip(
                self.get_initial_ranks(tabulation_num=tabulation_num, disaggregate=False),
                self.get_initial_weights(tabulation_num=tabulation_num, disaggregate=False),
                self.get_final_weight_distrib(tabulation_num=tabulation_num, disaggregate=False),
            )
        ]

        index_label = "Ballots with first choice:"
        n_ballots_label = "Number of Ballots"

        colname_dict = {cand: "% of votes to " + cand for cand in finalist_candidates}

        rows = candidate_set
        cols = [n_ballots_label] + list(colname_dict.values())
        df = pd.DataFrame(index=rows, columns=cols + ["percent_sum"])
        df.index.name = index_label

        # group ballots by first choice
        first_choices = {cand: [] for cand in candidate_set}
        for b in ballot_set:
            if len(b["ranks"]) >= 1 and b["ranks"][0] in first_choices:
                first_choices[b["ranks"][0]].append(b)

        for cand in candidate_set:

            total_first_choice_ballots = sum(b["weight"] for b in first_choices[cand])
            df.loc[cand, n_ballots_label] = total_first_choice_ballots

            if total_first_choice_ballots:

                redistrib = {opponent: 0 for opponent in finalist_candidates}
                for b in first_choices[cand]:
                    for el in b["weight_distrib"]:
                        if el[0] == "exhaust":
                            redistrib["exhaust"] += el[1]
                        else:
                            redistrib[el[0]] += el[1]

                redistrib_total_check = 0
                for opponent in redistrib:
                    redistrib_percent = redistrib[opponent] / total_first_choice_ballots * 100
                    df.loc[cand, colname_dict[opponent]] = redistrib_percent
                    redistrib_total_check += redistrib_percent
                df.loc[cand, "percent_sum"] = redistrib_total_check

            else:
                for opponent in finalist_candidates:
                    df.loc[cand, colname_dict[opponent]] = 0
                df.loc[cand, "percent_sum"] = 0

        df = df.astype(float).round(3)
        return df

    def get_round_by_round_table(self, tabulation_num: int = 1) -> pd.DataFrame:
        """Create a table containing round by round details for the tabulation.

        :param tabulation_num: tabulation number, defaults to 1
        :type tabulation_num: int, optional
        :return: round by round table
        :rtype: pd.DataFrame
        """

        num_rounds = self.n_rounds(tabulation_num=tabulation_num)

        first_round_exhaust = self.get_stats()[tabulation_num - 1]["total_pretally_exhausted"].item()

        # get rcv results
        first_round_dict = self.get_round_tally_dict(1, tabulation_num=tabulation_num)
        rounds_full = [self.get_round_tally_tuple(i, tabulation_num=tabulation_num) for i in range(1, num_rounds + 1)]
        transfers = [self.get_round_transfer_dict(i, tabulation_num=tabulation_num) for i in range(1, num_rounds + 1)]

        # reformat contest outputs into useful dicts
        cand_outcomes = self.get_candidate_outcomes(tabulation_num=tabulation_num)

        # reorder candidate names
        # winners in ascending order of round won
        # followed by losers in descending order of round lost
        reorder_dicts = []
        for d in cand_outcomes:

            if d["round_elected"]:
                d["order"] = -1 * (1 / d["round_elected"])
            else:
                d["order"] = 1 / d["round_eliminated"]

            reorder_dicts.append(d)

        ordered_candidates_names = [
            d["name"]
            for d in sorted(
                reorder_dicts,
                key=lambda x: (x["order"], -first_round_dict[x["name"]], x["name"]),
            )
        ]

        # setup data frame
        row_names = ordered_candidates_names + ["exhaust"]
        rcv_df = pd.DataFrame(NAN, index=row_names + ["colsum"], columns=["candidate"])
        rcv_df.loc[row_names + ["colsum"], "candidate"] = row_names + ["colsum"]

        # loop through rounds
        for rnd in range(1, num_rounds + 1):

            rnd_info = {rnd_cand: rnd_tally for rnd_cand, rnd_tally in zip(*rounds_full[rnd - 1])}
            rnd_info["exhaust"] = 0

            rnd_transfer = dict(transfers[rnd - 1])

            # add round data
            for cand in row_names:

                rnd_percent_col = "r" + str(rnd) + "_active_percent"
                rnd_count_col = "r" + str(rnd) + "_count"
                rnd_transfer_col = "r" + str(rnd) + "_transfer"

                rcv_df.loc[cand, rnd_percent_col] = 100 * (rnd_info[cand] / sum(rnd_info.values()))
                rcv_df.loc[cand, rnd_count_col] = rnd_info[cand]
                rcv_df.loc[cand, rnd_transfer_col] = rnd_transfer[cand]

            # maintain cumulative exhaust total
            if rnd == 1:
                rcv_df.loc["exhaust", rnd_count_col] = first_round_exhaust
            else:
                last_rnd_count_col = "r" + str(rnd - 1) + "_count"
                last_rnd_transfer_col = "r" + str(rnd - 1) + "_transfer"
                current_rnd_count_val = sum(
                    rcv_df.loc["exhaust", [last_rnd_count_col, last_rnd_transfer_col]].astype(float)
                )
                rcv_df.loc["exhaust", rnd_count_col] = current_rnd_count_val

            # sum round columns
            rcv_df.loc["colsum", rnd_count_col] = sum(rcv_df.loc[row_names, rnd_count_col].astype(float))
            rcv_df.loc["colsum", rnd_transfer_col] = sum(rcv_df.loc[row_names, rnd_transfer_col].astype(float))
            rcv_df.loc["colsum", rnd_percent_col] = sum(rcv_df.loc[row_names, rnd_percent_col].astype(float))

        # convert from decimal to float
        rcv_df.loc[row_names + ["colsum"], rcv_df.columns != "candidate"] = (
            rcv_df.loc[row_names + ["colsum"], rcv_df.columns != "candidate"].astype(float).round(3)
        )

        # remove rownames
        rcv_df = rcv_df.reset_index(drop=True)
        return rcv_df

    def _get_annotated_cvr_table(self):
        dfs = [super().annotated_cvr_table(), self._contest_stat_table]
        return pd.concat(dfs, axis="columns", sort=False)

    # def outcome_cvr_table(self):

    #     dfs = []
    #     for iTab in range(1, self.n_tabulations()+1):

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

    #     cvr_allocation_dir = results_dir / 'cvr_ballot_allocation'
    #     util.verifyDir(cvr_allocation_dir)

    #     if cvr_format == 'rank':
    #         cvr_allocation_dir = cvr_allocation_dir / "rank_format"
    #     elif cvr_format == 'candidate':
    #         cvr_allocation_dir = cvr_allocation_dir / "candidate_format"
    #     util.verifyDir(cvr_allocation_dir)

    #

    def get_round_by_round_dict(self, tabulation_num: int = 1) -> Dict:
        """Create a dictionary containing election round by round information that matches the nesting structure of RCVIS upload format.

        :param tabulation_num: tabulation number, defaults to 1
        :type tabulation_num: int, optional
        :return: Dictionary containing election round by round details
        :rtype: Dict
        """

        # get rcv results
        n_rounds = self.n_rounds(tabulation_num=tabulation_num)
        tally_tuples = [
            self.get_round_tally_tuple(round_num=i, tabulation_num=tabulation_num) for i in range(1, n_rounds + 1)
        ]
        transfer_dicts = [
            self.get_round_transfer_dict(round_num=i, tabulation_num=tabulation_num) for i in range(1, n_rounds + 1)
        ]

        outcomes = self.get_candidate_outcomes(tabulation_num=tabulation_num)

        json_dict = {
            "config": {
                "notes": self.get_stats()[tabulation_num - 1]["notes"].item(),
                "date": self.get_stats()[tabulation_num - 1]["date"].item(),
                "jurisdiction": self.get_stats()[tabulation_num - 1]["jurisdiction"].item(),
                "office": self.get_stats()[tabulation_num - 1]["office"].item(),
                "threshold": (
                    self._win_threshold()
                    if not (self._win_threshold() or isinstance(self._win_threshold(), str))
                    else 0
                ),
            },
            "results": [],
        }

        for i in range(0, n_rounds):

            round_num = i + 1
            tally_dict = {cand: str(int(tally)) for cand, tally in zip(*tally_tuples[i]) if tally > 0}
            transfer_list = []

            # who had an outcomes this round
            elected = [d for d in outcomes if d["round_elected"] == round_num]
            eliminated = [d for d in outcomes if d["round_eliminated"] == round_num]

            for d in elected:
                transfer_list.append({"elected": d["name"], "transfers": {}})

            for d in eliminated:
                if i == n_rounds - 1:  # no final round transfer
                    transfer_list.append({"eliminated": d["name"], "transfers": {}})
                elif transfer_dicts[i][d["name"]] == 0:  # zero vote elimination, no votes transferred
                    transfer_list.append({"eliminated": d["name"], "transfers": {}})
                else:  # loser transfer
                    # remove negative transfer
                    round_transfer = {key: str(int(val)) for key, val in transfer_dicts[i].items() if val > 0}
                    if "exhaust" in round_transfer:  # small rename
                        round_transfer["exhausted"] = round_transfer["exhaust"]
                        del round_transfer["exhaust"]
                    transfer_list.append({"eliminated": d["name"], "transfers": round_transfer})

            json_dict["results"].append(
                {
                    "round": round_num,
                    "tally": tally_dict,
                    "tallyResults": transfer_list,
                }
            )

        return json_dict

    def _get_candidate_rank_usage_table(self) -> pd.DataFrame:
        """[summary]

        :return: [description]
        :rtype: [type]
        """

        # set up vars
        contest_candidates = self._contest_candidates.unique_candidates
        rank_limit = self._summary_cvr_stat_table["rank_limit"].item()
        candidate_outcomes = {dikt["name"]: dikt for dikt in self.get_candidate_outcomes(tabulation_num=1)}
        first_round_dict = self.get_round_tally_dict(round_num=1, tabulation_num=1)
        first_round_leader = sorted(first_round_dict.items(), key=lambda x: -x[1])[0][0]

        contest_cvr_dl = self.get_cvr_dict(self._contest_rule_set_name, disaggregate=False)
        contest_cvr_ld = [
            {"ballot_marks": bm, "weight": weight}
            for bm, weight in zip(contest_cvr_dl["ballot_marks"], contest_cvr_dl["weight"])
        ]

        # set up dataframe
        df_columns = (
            [
                "contestID",
                "rank_limit",
                "n_rounds",
                "rcv_type",
                "winner",
                "first_round_percent",
                "first_round_count",
                "round_elected",
                "round_eliminated",
            ]
            + [f"ranked_{i}" for i in range(1, rank_limit + 1)]
            + [
                "ranked_2_or_more",
                "ranked_3_or_more",
                "mean_ranked",
                "all_candidate_mean_ranked",
                "non_leader_mean_ranked",
                "non_leader_no_writein_mean_ranked",
            ]
        )
        df = pd.DataFrame(None, index=contest_candidates, columns=df_columns)

        # fill precomputed columns
        df["contestID"] = self._id_df["unique_id"].item()
        df["rank_limit"] = rank_limit
        df["n_rounds"] = self._summary_contest_stat_tables[0]["n_rounds"].item()
        df["rcv_type"] = self._summary_contest_stat_tables[0]["rcv_type"].item()
        df["winner"] = [
            True if candidate in self._tabulation_winner(tabulation_num=1) else False for candidate in df.index
        ]
        df["round_elected"] = [candidate_outcomes[candidate]["round_elected"] for candidate in df.index]
        df["round_eliminated"] = [candidate_outcomes[candidate]["round_eliminated"] for candidate in df.index]
        df["first_round_percent"] = [
            100 * first_round_dict[candidate] / sum(first_round_dict.values()) for candidate in df.index
        ]
        df["first_round_count"] = [first_round_dict[candidate] for candidate in df.index]

        # count rank usage by candidate
        rank_usage_count = {candidate: {i: 0 for i in range(1, rank_limit + 1)} for candidate in contest_candidates}
        for ballot in contest_cvr_ld:
            if ballot["ballot_marks"].marks:
                first_candidate = ballot["ballot_marks"].marks[0]
                ranks_used = len(ballot["ballot_marks"].marks)
                rank_usage_count[first_candidate][ranks_used] += ballot["weight"]

        # convert counts to percent and add to table
        all_candidate_rank_usage = {i: 0 for i in range(1, rank_limit + 1)}
        non_leader_rank_usage = {i: 0 for i in range(1, rank_limit + 1)}
        non_leader_no_writein_rank_usage = {i: 0 for i in range(1, rank_limit + 1)}
        for candidate, candidate_rank_usage in rank_usage_count.items():

            candidate_total_ballots = sum(candidate_rank_usage.values())
            for ranks_used, ranks_used_count in candidate_rank_usage.items():

                all_candidate_rank_usage[ranks_used] += ranks_used_count

                if candidate != first_round_leader:
                    non_leader_rank_usage[ranks_used] += ranks_used_count

                if candidate != BallotMarks.WRITEIN:
                    non_leader_no_writein_rank_usage[ranks_used] += ranks_used_count

                df.loc[candidate, f"ranked_{ranks_used}"] = 0
                if candidate_total_ballots:
                    df.loc[candidate, f"ranked_{ranks_used}"] = 100 * ranks_used_count / candidate_total_ballots

            df.loc[candidate, "ranked_2_or_more"] = 0
            df.loc[candidate, "ranked_3_or_more"] = 0
            if candidate_total_ballots:
                ranked_2_or_more = sum(count for ranks_used, count in candidate_rank_usage.items() if ranks_used > 1)
                ranked_3_or_more = sum(count for ranks_used, count in candidate_rank_usage.items() if ranks_used > 2)
                df.loc[candidate, "ranked_2_or_more"] = 100 * ranked_2_or_more / candidate_total_ballots
                df.loc[candidate, "ranked_3_or_more"] = 100 * ranked_3_or_more / candidate_total_ballots

            df.loc[candidate, "mean_ranked"] = 0
            if candidate_total_ballots:
                weighted_sum = sum(count * ranks_used for ranks_used, count in candidate_rank_usage.items())
                df.loc[candidate, "mean_ranked"] = weighted_sum / candidate_total_ballots

        all_candidate_weighted_sum = sum(count * ranks_used for ranks_used, count in all_candidate_rank_usage.items())
        non_leader_weighted_sum = sum(count * ranks_used for ranks_used, count in non_leader_rank_usage.items())
        non_leader_no_writein_weighted_sum = sum(
            count * ranks_used for ranks_used, count in non_leader_no_writein_rank_usage.items()
        )

        if sum(all_candidate_rank_usage.values()):
            df["all_candidate_mean_ranked"] = all_candidate_weighted_sum / sum(all_candidate_rank_usage.values())
        if sum(non_leader_rank_usage.values()):
            df["non_leader_mean_ranked"] = non_leader_weighted_sum / sum(non_leader_rank_usage.values())
        if sum(non_leader_no_writein_rank_usage.values()):
            df["non_leader_no_writein_mean_ranked"] = non_leader_no_writein_weighted_sum / sum(
                non_leader_no_writein_rank_usage.values()
            )

        return df
