"""Contains CastVoteRecord_stats class which is added into CastVoteRecord.
"""

import collections
import weightedstats

import pandas as pd

import rcv_cruncher.util as util

from rcv_cruncher.marks import BallotMarks


class CastVoteRecord_stats:
    """Extra methods for CastVoteRecord class."""

    def get_stats(
        self,
        keep_decimal_type: bool = False,
        add_split_stats: bool = False,
        add_id_info: bool = True,
    ) -> pd.DataFrame:
        """Obtain the default statistics calculated by the CastVoteRecord object. Statistics are returned in pandas dataframe object.

        :param keep_decimal_type: Return the decimal class objects used by internal calculations rather than converting them to floats, defaults to False
        :type keep_decimal_type: bool, optional
        :param add_split_stats: Add extra statistics calculated for each category contained in `split_fields` columns passed to constructor, defaults to False
        :type add_split_stats: bool, optional
        :param add_id_info: Include contest ID details to returned dataframe, defaults to True
        :type add_id_info: bool, optional
        :return: A single row dataframe with statistics organized in multiple columns. If `split_fields` are passed, then extra rows are added for each category in the split columns.
        :rtype: pd.DataFrame
        """

        cvr_stats = self._summary_cvr_stat_table.copy()

        if add_id_info:
            for col in self._id_df.columns[::-1]:
                cvr_stats.insert(0, col, self._id_df[col].item())

        if add_split_stats:

            # self._make_split_filter_dict()
            self._compute_summary_cvr_split_stat_table()

            if self._summary_cvr_split_stat_table is not None:

                cvr_split_stats = self._summary_cvr_split_stat_table.copy()

                cvr_split_stats = cvr_split_stats.assign(**{col: cvr_stats.at[0, col] for col in cvr_stats.columns})
                cvr_split_stats = cvr_split_stats[
                    cvr_split_stats.columns.tolist()[-1 * len(cvr_stats.columns) :]
                    + cvr_split_stats.columns.tolist()[: -1 * len(cvr_stats.columns)]
                ]

                cvr_stats = cvr_split_stats

        if not keep_decimal_type:
            cvr_stats = cvr_stats.applymap(util.decimal2float)

        return cvr_stats

    def _compute_cvr_stat_table(self) -> None:

        cvr = self.get_cvr_dict(disaggregate=False)
        candidates = self.get_candidates()

        df = pd.DataFrame()
        df["weight"] = cvr["weight"]

        df["valid_ranks_used"] = [len(b.unique_candidates) for b in cvr["ballot_marks"]]
        df["ranks_used_times_weight"] = df["valid_ranks_used"] * df["weight"]

        df["used_last_rank"] = [True if b.marks[-1] != BallotMarks.SKIPPED else False for b in cvr["ballot_marks"]]

        df["undervote"] = [b.unique_marks == {BallotMarks.SKIPPED} for b in cvr["ballot_marks"]]
        df["ranked_single"] = df["valid_ranks_used"] == 1
        df["ranked_multiple"] = df["valid_ranks_used"] > 1
        df["ranked_3_or_more"] = df["valid_ranks_used"] > 2

        ballot_marks_no_skipped = [BallotMarks.remove_mark(b, [BallotMarks.SKIPPED]) for b in cvr["ballot_marks"]]
        first_round = [b.marks[0] if b.marks else -9999 for b in ballot_marks_no_skipped]
        df["first_round"] = pd.Series(first_round)

        df["first_round_overvote"] = df["first_round"].eq(BallotMarks.OVERVOTE)

        df["contains_overvote"] = [BallotMarks.OVERVOTE in b.unique_marks for b in cvr["ballot_marks"]]

        # contains_skipped
        # {SKIPVOTE} & {x} - {y}
        # this checks that x == SKIPVOTE and that y then != SKIPVOTE
        # (the y check is important to know whether or not the ballot contains marks
        # following the skipped rank)
        df["contains_skip"] = [
            any({BallotMarks.SKIPPED} & {x} - {y} for x, y in zip(b.marks, b.marks[1:])) for b in cvr["ballot_marks"]
        ]

        # contains_duplicate
        # remove overvotes and undervotes
        dup_check = [
            BallotMarks.remove_mark(b, [BallotMarks.SKIPPED, BallotMarks.OVERVOTE]) for b in cvr["ballot_marks"]
        ]
        # count all ranks for candidates
        counters = [collections.Counter(b.marks) for b in dup_check]
        # check if any candidates were ranked more than once
        df["contains_duplicate"] = [max(counter.values()) > 1 if counter else False for counter in counters]

        irregular_condtions = [
            "contains_overvote",
            "contains_skip",
            "contains_duplicate",
        ]
        df["irregular"] = df[irregular_condtions].any(axis="columns")

        # fully_ranked no overvotes
        candidates_combined_writeins = BallotMarks.combine_writein_marks(candidates)
        candidates_excluded_writeins = BallotMarks.remove_mark(candidates_combined_writeins, [BallotMarks.WRITEIN])
        candidate_set = candidates_excluded_writeins.unique_candidates

        ballot_marks_cleaned = [
            BallotMarks.remove_mark(b, [BallotMarks.OVERVOTE, BallotMarks.SKIPPED]) for b in cvr["ballot_marks"]
        ]
        ballot_marks_cleaned = [BallotMarks.remove_duplicate_candidate_marks(b) for b in ballot_marks_cleaned]

        fully_ranked = [
            (set(b.marks) & candidate_set) == candidate_set or
            # voters ranked every possible candidate
            len(a.marks) == len(b.marks)
            # or did not, had no skipped ranks, overvotes, or duplicates
            for a, b in zip(cvr["ballot_marks"], ballot_marks_cleaned)
        ]
        df["fully_ranked_excl_overvotes"] = fully_ranked

        # fully_ranked with overvotes
        candidates_combined_writeins = BallotMarks.combine_writein_marks(candidates)
        candidates_excluded_writeins = BallotMarks.remove_mark(candidates_combined_writeins, [BallotMarks.WRITEIN])
        candidate_set = candidates_excluded_writeins.unique_candidates

        ballot_marks_cleaned = [BallotMarks.remove_mark(b, [BallotMarks.SKIPPED]) for b in cvr["ballot_marks"]]
        ballot_marks_cleaned = [BallotMarks.remove_duplicate_candidate_marks(b) for b in ballot_marks_cleaned]

        fully_ranked = [
            (set(b.marks) & candidate_set) == candidate_set or
            # voters ranked every possible candidate
            len(a.marks) == len(b.marks)
            # or did not, had no skipped ranks, overvotes, or duplicates
            for a, b in zip(cvr["ballot_marks"], ballot_marks_cleaned)
        ]
        df["fully_ranked_incl_overvotes"] = fully_ranked

        self._cvr_stat_table = df

    def _compute_summary_cvr_stat_table(self) -> None:

        cvr = self.get_cvr_dict(disaggregate=False)
        candidates = self.get_candidates()

        s = pd.Series(dtype=object)

        candidates_no_writeins = BallotMarks.remove_mark(
            BallotMarks.combine_writein_marks(candidates), [BallotMarks.WRITEIN]
        )
        s["n_candidates"] = len(candidates_no_writeins.marks)

        s["rank_limit"] = len(cvr["ballot_marks"][0].marks)
        s["restrictive_rank_limit"] = True if s["rank_limit"] < (s["n_candidates"] - 1) else False

        # first_round_overvote
        # The number of ballots with an overvote before any valid ranking. (weighted)

        # Note that this is not the same as "exhausted by overvote". This is because
        # some jurisdictions (Maine) discard any ballot beginning with two
        # skipped rankings, and call this ballot as exhausted by skipped rankings, even if the
        # skipped rankings are followed by an overvote.

        # Other jursidictions (Minneapolis) simply skip over overvotes in a ballot.
        s["first_round_overvote"] = self._cvr_stat_table.loc[
            self._cvr_stat_table["first_round_overvote"], "weight"
        ].sum()

        # The number of voters that validly used only a single ranking. (weighted)
        s["ranked_single"] = self._cvr_stat_table.loc[self._cvr_stat_table["ranked_single"], "weight"].sum()

        # The number of voters that validly used 3 or more rankings. (weighted)
        s["ranked_3_or_more"] = self._cvr_stat_table.loc[self._cvr_stat_table["ranked_3_or_more"], "weight"].sum()

        # The number of voters that validly use more than one ranking. (weighted)
        s["ranked_multiple"] = self._cvr_stat_table.loc[self._cvr_stat_table["ranked_multiple"], "weight"].sum()

        # The number of voters that have validly used all available rankings on the
        # ballot, or that have validly ranked all non-write-in candidates. (weighted)
        s["total_fully_ranked"] = self._cvr_stat_table.loc[
            self._cvr_stat_table["fully_ranked_excl_overvotes"], "weight"
        ].sum()

        # The number of ballots that rank the same candidate more than once. (weighted)
        s["includes_duplicate_ranking"] = self._cvr_stat_table.loc[
            self._cvr_stat_table["contains_duplicate"], "weight"
        ].sum()

        # The number of ballots that have an skipped ranking followed by any other marked ranking. (weighted)
        s["includes_skipped_ranking"] = self._cvr_stat_table.loc[self._cvr_stat_table["contains_skip"], "weight"].sum()

        # This includes ballots with no marks. (weighted)
        s["total_ballots"] = self._cvr_stat_table["weight"].sum()

        # Number of ballots that either had a multiple ranking, overvote,
        # or a skipped ranking (only those followed by a mark). This includes ballots even where the irregularity was not
        # the cause of exhaustion. (weighted)
        s["total_irregular"] = self._cvr_stat_table.loc[self._cvr_stat_table["irregular"], "weight"].sum()

        # Number of ballots with at least one overvote. Not necessarily cause of exhaustion. (weighted)
        s["includes_overvote_ranking"] = self._cvr_stat_table.loc[
            self._cvr_stat_table["contains_overvote"], "weight"
        ].sum()

        # Ballots completely made up of skipped rankings (no marks). (weighted)
        s["total_undervote"] = self._cvr_stat_table.loc[self._cvr_stat_table["undervote"], "weight"].sum()

        # Mean number of validly used rankings across all non-undervote ballots. (weighted)
        weighted_sum = self._cvr_stat_table.loc[~self._cvr_stat_table["undervote"], "ranks_used_times_weight"].sum()
        s["mean_rankings_used"] = (
            weighted_sum / self._cvr_stat_table.loc[~self._cvr_stat_table["undervote"], "weight"].sum()
        )

        # Median number of validly used rankings across all non-undervote ballots. (weighted)
        # s['median_rankings_used'] = self._cvr_stat_table.loc[~self._cvr_stat_table['undervote'], 'ranks_used_times_weight'].median()

        # ranks_used = self._cvr_stat_table.loc[~self._cvr_stat_table["undervote"], "valid_ranks_used"].tolist()
        # weights = self._cvr_stat_table.loc[~self._cvr_stat_table["undervote"], "weight"].tolist()
        # weights_float = [float(i) for i in weights]
        # s["median_rankings_used"] = weightedstats.weighted_median(ranks_used, weights=weights_float)

        self._summary_cvr_stat_table = s.to_frame().transpose()

    def _make_split_filter_dict(self) -> None:

        if self.split_fields:

            cvr = self.get_cvr_dict(disaggregate=False)
            cvr_fields = list(cvr.keys())
            field_name_lower_dict = {k.lower(): k for k in cvr_fields}

            for field in self.split_fields:
                if field.lower() in field_name_lower_dict:
                    cvr_field_name = field_name_lower_dict[field.lower()]
                    cvr_field = cvr[cvr_field_name]
                    field_filter_dict = {
                        unique_val: [unique_val == i for i in cvr_field] for unique_val in set(cvr_field)
                    }
                    self._split_filter_dict.update({cvr_field_name: field_filter_dict})

    def _clean_string(self, x: str) -> str:
        return str(x).replace(":", "_").replace("/", "_").replace("\\", "_").replace(" ", "_").replace("-", "_")

    def _compute_cvr_split_stats(self, split_filter) -> pd.DataFrame:

        filtered_stat_table = self._cvr_stat_table.loc[split_filter, :]

        first_round_overvote = filtered_stat_table.loc[filtered_stat_table["first_round_overvote"], "weight"].sum()
        ranked_single = filtered_stat_table.loc[filtered_stat_table["ranked_single"], "weight"].sum()
        ranked_multiple = filtered_stat_table.loc[filtered_stat_table["ranked_multiple"], "weight"].sum()
        ranked_3_or_more = filtered_stat_table.loc[filtered_stat_table["ranked_3_or_more"], "weight"].sum()
        total_fully_ranked = filtered_stat_table.loc[filtered_stat_table["fully_ranked_excl_overvotes"], "weight"].sum()
        includes_duplicate_ranking = filtered_stat_table.loc[filtered_stat_table["contains_duplicate"], "weight"].sum()
        includes_skipped_ranking = filtered_stat_table.loc[filtered_stat_table["contains_skip"], "weight"].sum()
        total_irregular = filtered_stat_table.loc[filtered_stat_table["irregular"], "weight"].sum()
        total_ballots = filtered_stat_table["weight"].sum()
        includes_overvote_ranking = filtered_stat_table.loc[filtered_stat_table["contains_overvote"], "weight"].sum()
        total_undervote = filtered_stat_table.loc[filtered_stat_table["undervote"], "weight"].sum()

        weighted_sum = filtered_stat_table.loc[~filtered_stat_table["undervote"], "ranks_used_times_weight"].sum()
        if weighted_sum == 0:
            mean_rankings_used = 0
        else:
            mean_rankings_used = (
                weighted_sum / filtered_stat_table.loc[~filtered_stat_table["undervote"], "weight"].sum()
            )

        # ranks_used = filtered_stat_table.loc[~filtered_stat_table["undervote"], "valid_ranks_used"].tolist()
        # weights = filtered_stat_table.loc[~filtered_stat_table["undervote"], "weight"].tolist()
        # weights_float = [float(i) for i in weights]
        # median_rankings_used = weightedstats.weighted_median(ranks_used, weights=weights_float)

        filtered_summary_stat_table = pd.DataFrame(
            {
                "split_first_round_overvote": [first_round_overvote],
                "split_ranked_single": [ranked_single],
                "split_ranked_multiple": [ranked_multiple],
                "split_ranked_3_or_more": [ranked_3_or_more],
                "split_mean_rankings_used": [mean_rankings_used],
                #'split_median_rankings_used': [median_rankings_used],
                "split_total_fully_ranked": [total_fully_ranked],
                "split_includes_duplicate_ranking": [includes_duplicate_ranking],
                "split_includes_skipped_ranking": [includes_skipped_ranking],
                "split_total_irregular": [total_irregular],
                "split_total_ballots": [total_ballots],
                "split_includes_overvote_ranking": [includes_overvote_ranking],
                "split_total_undervote": [total_undervote],
            }
        )
        return filtered_summary_stat_table

    def _compute_summary_cvr_split_stat_table(self) -> None:

        if not self.split_fields:
            return

        split_df_list = []

        cvr = self.get_cvr_dict(disaggregate=False)
        cvr_fields = list(cvr.keys())
        field_name_lower_dict = {k.lower(): k for k in cvr_fields}

        for field in self.split_fields:

            if field.lower() in field_name_lower_dict:

                cvr_field_name = field_name_lower_dict[field.lower()]
                cvr_field = cvr[cvr_field_name]
                field_clean = self._clean_string(cvr_field_name)

                for unique_val in set(cvr_field):

                    field_filter = [unique_val == i for i in cvr_field]

                    # field_filter_dict = {unique_val: [unique_val == i for i in cvr_field] for unique_val in set(cvr_field)}
                    # self._split_filter_dict.update({cvr_field_name: field_filter_dict})

                    val_clean = self._clean_string(unique_val)
                    split_id = field_clean + "-" + val_clean

                    split_id_df = pd.DataFrame(
                        {
                            "split_field": [cvr_field_name],
                            "split_value": [unique_val],
                            "split_id": [split_id],
                        }
                    )
                    split_stat_df = self._compute_cvr_split_stats(field_filter)
                    split_df_list.append(pd.concat([split_id_df, split_stat_df], axis="columns"))

        self._summary_cvr_split_stat_table = pd.concat(split_df_list, axis=0, sort=False)
