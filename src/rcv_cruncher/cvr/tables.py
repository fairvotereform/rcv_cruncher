"""Contains CastVoteRecord_tables class which is added into CastVoteRecord.
"""
from typing import Tuple

import pandas as pd

import rcv_cruncher.util as util

from rcv_cruncher.marks import BallotMarks


class CastVoteRecord_tables:
    """Extra methods for CastVoteRecord class."""

    def get_cvr_table(self, table_format: str = "rank", disaggregate: bool = True) -> pd.DataFrame:
        """Return the cvr as pandas dataframe. Two format options are available 'rank' or 'candidate'.

        :param table_format: Two choices for the format of CVR table, "rank" or "candidate". One ballot per row. Rank format uses rank number labels as column headers with candidate names in row cells. Candidate format puts candidate names as column headers with rank position placed in row cells. Defaults to "rank"
        :type table_format: str, optional
        :param disaggregate: If True, the interally aggregated CVR is disaggregated back to contain the same number of ballots as when it was parsed, defaults to True.
        :type disaggregate: bool, optional
        :raises RuntimeError: raised if an invalid `table_format` is passed as an argument.
        :return: Dataframe containing CVR.
        :rtype: pd.DataFrame
        """
        if table_format != "rank" and table_format != "candidate":
            raise RuntimeError('table_format argument must be "rank" or "candidate"')

        if table_format == "rank":
            tbl = self._rank_header_cvr(disaggregate)
        elif table_format == "candidate":
            tbl = self._candidate_header_cvr(disaggregate)

        return tbl

    def _rank_header_cvr(self, disaggregate: bool = True) -> pd.DataFrame:

        cvr_dict = {k: v for k, v in self.get_cvr_dict(disaggregate=disaggregate).items()}

        # assemble output_table, start with extras
        output_df = pd.DataFrame.from_dict({k: v for k, v in cvr_dict.items() if k != "ballot_marks" and k != "weight"})

        # are weights all one, then dont add to output
        if not disaggregate:
            output_df["weight"] = [float(w) for w in cvr_dict["weight"]]

        if not all([i == 1 for i in cvr_dict["weight"]]):
            output_df["weight"] = [float(w) for w in cvr_dict["weight"]]

        # how many ranks?
        num_ranks = max(len(b.marks) for b in cvr_dict["ballot_marks"])

        # make sure all ballots are lists of equal length, adding trailing 'skipped' if necessary
        full_ballots = [
            b.get_marks() + ([BallotMarks.SKIPPED] * (num_ranks - len(b.marks))) for b in cvr_dict["ballot_marks"]
        ]

        # add in rank columns
        for i in range(1, num_ranks + 1):
            output_df["rank" + str(i)] = [b[i - 1] for b in full_ballots]

        return output_df

    def _candidate_header_cvr(self, disaggregate: bool = True) -> pd.DataFrame:

        # get ballots and candidates
        ballot_dl = {k: v for k, v in self.get_cvr_dict(disaggregate=disaggregate).items()}
        candidates = self.get_candidates().get_unique_candidates()
        candidates.update({BallotMarks.OVERVOTE})

        # remove weights if all equal to 1
        if not disaggregate:
            del ballot_dl["weight"]

        if set(ballot_dl["weight"]) == {1}:
            del ballot_dl["weight"]

        # add rank limit
        ballot_dl["rank_limit"] = [len(ballot_dl["ballot_marks"][0].marks)] * len(ballot_dl["ballot_marks"])

        # convert dict of list to list of dicts
        ballot_ld = util.DL2LD(ballot_dl)

        # add candidate index information
        for b in ballot_ld:
            b.update({f"candidate_{cand}": None for cand in candidates})
            for rank_idx, cand in enumerate(b["ballot_marks"].get_marks(), start=1):
                if cand != BallotMarks.SKIPPED:
                    if not b[f"candidate_{cand}"]:
                        b[f"candidate_{cand}"] = str(rank_idx)
                    else:
                        b[f"candidate_{cand}"] += f",{rank_idx}"
            del b["ballot_marks"]

        df = pd.DataFrame(ballot_ld)
        return df.reindex(sorted(df.columns), axis=1)

    def get_rank_usage_table(self) -> pd.DataFrame:
        """Table describing rank usage patterns. Mean rankings used and distribution of valid rankings used is provided for all ballots (excluding undervotes and ballots starting with overvotes) as well as ballots separated by first choice candidate. Ballots starting with overvotes are excluded because of the inability to assign them to a first choice candidate category. For this table, ballots are used without any contest rules applied. Skipped ranks, overvotes, and duplicate rankings are not counted valid rankings.

        :return: Rank usage dataframe
        :rtype: pd.DataFrame
        """

        # get candidate set
        candidate_set = BallotMarks.combine_writein_marks(self.get_candidates())
        candidate_set_names = sorted(candidate_set.get_unique_candidates())
        candidate_set_codes = candidate_set.get_unique_candidates()

        cvr_dict = self.get_cvr_dict(disaggregate=False)

        rank_limit = len(cvr_dict["ballot_marks"][0].marks)

        # get ballots
        ballot_set = [
            {"ballot_marks": bm, "weight": weight} for bm, weight in zip(cvr_dict["ballot_marks"], cvr_dict["weight"])
        ]
        # remove skipped ranks
        ballot_set = [
            {
                "ballot_marks": BallotMarks.remove_mark(b["ballot_marks"], [BallotMarks.SKIPPED]),
                "weight": b["weight"],
            }
            for b in ballot_set
        ]
        # remove empty ballots and those that start with overvote
        ballot_set = [
            b
            for b in ballot_set
            if len(b["ballot_marks"].marks) >= 1 and b["ballot_marks"].marks[0] != BallotMarks.OVERVOTE
        ]
        # combine writeins
        ballot_set = [
            {
                "ballot_marks": BallotMarks.combine_writein_marks(b["ballot_marks"]),
                "weight": b["weight"],
            }
            for b in ballot_set
        ]
        # remove other overvotes
        ballot_set = [
            {
                "ballot_marks": BallotMarks.remove_mark(b["ballot_marks"], [BallotMarks.OVERVOTE]),
                "weight": b["weight"],
            }
            for b in ballot_set
        ]
        # remove duplicate rankings
        ballot_set = [
            {
                "ballot_marks": BallotMarks.remove_duplicate_candidate_marks(b["ballot_marks"]),
                "weight": b["weight"],
            }
            for b in ballot_set
        ]

        # set up df
        all_ballots_label = "Any candidate"
        n_ballots_label = "Number of Ballots (excluding undervotes and ballots with first round overvote)"
        mean_label = "Mean Valid Rankings Used (excluding duplicates)"
        dist_count_labels = [f"{i} Valid Rankings Used - Count" for i in range(1, rank_limit + 1)]
        dist_percent_labels = [f"{i} Valid Rankings Used - Percent" for i in range(1, rank_limit + 1)]

        rows = [all_ballots_label] + candidate_set_names
        cols = [n_ballots_label, mean_label] + dist_count_labels + dist_percent_labels
        df = pd.DataFrame(index=rows, columns=cols)
        df.index.name = "Ballots with first choice:"

        # compute stats for all ballots
        ballot_total = sum(b["weight"] for b in ballot_set)
        mean_rankings = sum(len(b["ballot_marks"].marks) * b["weight"] for b in ballot_set) / ballot_total

        df.loc[all_ballots_label, n_ballots_label] = ballot_total
        df.loc[all_ballots_label, mean_label] = mean_rankings

        for idx, i in enumerate(range(1, rank_limit + 1)):
            dist_count = sum(b["weight"] for b in ballot_set if len(b["ballot_marks"].marks) == i)
            df.loc[all_ballots_label, dist_count_labels[idx]] = dist_count
            df.loc[all_ballots_label, dist_percent_labels[idx]] = 100 * dist_count / ballot_total

        # group ballots by first choice
        first_choices = {cand: [] for cand in candidate_set_codes}
        for b in ballot_set:
            first_choices[b["ballot_marks"].marks[0]].append(b)

        for cand in candidate_set_codes:

            first_choice_ballot_total = sum(b["weight"] for b in first_choices[cand])
            df.loc[cand, n_ballots_label] = first_choice_ballot_total

            if first_choices[cand]:

                df.loc[cand, mean_label] = (
                    sum(len(b["ballot_marks"].marks) * b["weight"] for b in first_choices[cand])
                    / first_choice_ballot_total
                )

                for idx, i in enumerate(range(1, rank_limit + 1)):
                    dist_count = sum(b["weight"] for b in first_choices[cand] if len(b["ballot_marks"].marks) == i)
                    df.loc[cand, dist_count_labels[idx]] = dist_count
                    df.loc[cand, dist_percent_labels[idx]] = 100 * dist_count / first_choice_ballot_total

            else:

                df.loc[cand, mean_label] = 0

                for idx, _ in enumerate(range(1, rank_limit + 1)):
                    df.loc[cand, dist_count_labels[idx]] = 0
                    df.loc[cand, dist_percent_labels[idx]] = 0

        return df.applymap(util.decimal2float)

    def get_crossover_tables(self) -> Tuple[pd.DataFrame]:
        """Table describing co-ranking patterns between candidates. For each subset of ballots organized by first choice candidate, one in each row of the table, the frequency with which all candidates appear in the top 3 ranks of ballots in that subset is calculated. For this table, ballots are used without any contest rules applied.

        :return: Tuple of two pandas dataframes. The first contains counts, the second percentages.
        :rtype: Tuple[pd.DataFrame]
        """

        # get candidate set
        candidate_set = BallotMarks.combine_writein_marks(self.get_candidates())
        candidate_set_names = sorted(candidate_set.get_unique_candidates())

        ballot_dict = self.get_cvr_dict(disaggregate=False)
        ballot_weights = ballot_dict["weight"]
        ballot_marks = [BallotMarks.remove_mark(b, [BallotMarks.SKIPPED]) for b in ballot_dict["ballot_marks"]]
        ballot_marks = [BallotMarks.combine_writein_marks(b) for b in ballot_marks]
        ballot_set = [{"ballot_marks": ranks, "weight": weight} for ranks, weight in zip(ballot_marks, ballot_weights)]

        index_label = "Ballots with first choice:"
        n_ballots_label = "Number of Ballots"

        colname_dict = {cand: cand + " ranked in top 3" for cand in candidate_set_names}

        rows = candidate_set_names
        cols = [n_ballots_label] + list(colname_dict.values())
        count_df = pd.DataFrame(index=rows, columns=cols)
        count_df.index.name = index_label
        percent_df = pd.DataFrame(index=rows, columns=cols)
        percent_df.index.name = index_label

        # group ballots by first choice
        first_choices = {cand: [] for cand in candidate_set_names}
        for b in ballot_set:
            if len(b["ballot_marks"].marks) >= 1 and b["ballot_marks"].marks[0] != BallotMarks.OVERVOTE:
                first_choices[b["ballot_marks"].marks[0]].append(b)

        for cand in candidate_set_names:

            n_first_choice = sum(b["weight"] for b in first_choices[cand])
            count_df.loc[cand, n_ballots_label] = n_first_choice
            percent_df.loc[cand, n_ballots_label] = n_first_choice

            for opponent in candidate_set_names:

                if n_first_choice:
                    crossover_ballots = [
                        True if opponent in b["ballot_marks"].marks[0 : min(3, len(b["ballot_marks"].marks))] else False
                        for b in first_choices[cand]
                    ]
                    crossover_val = sum(b["weight"] for b, flag in zip(first_choices[cand], crossover_ballots) if flag)
                    count_df.loc[cand, colname_dict[opponent]] = crossover_val
                    percent_df.loc[cand, colname_dict[opponent]] = crossover_val * 100 / n_first_choice
                else:
                    count_df.loc[cand, colname_dict[opponent]] = 0
                    percent_df.loc[cand, colname_dict[opponent]] = 0

        # convert decimal to float
        count_df = count_df.astype(float).round(3)
        percent_df = percent_df.astype(float).round(3)

        return count_df, percent_df

    def _get_annotated_cvr_table(self):
        dfs = [self._rank_header_cvr(), self._cvr_stat_table]
        return pd.concat(dfs, axis="columns", sort=False)
