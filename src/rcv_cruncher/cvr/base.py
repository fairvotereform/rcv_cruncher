"""
Contains the CastVoteRecord class.
Defines the class and adds in methods from cvr/stats.py and cvr/tables.py files.
"""

from __future__ import annotations
from typing import Callable, Dict, Optional, List, Type, Union, Tuple

import decimal
import collections
import re
import pathlib

import pandas as pd

from rcv_cruncher.util import DL2LD, LD2DL
from rcv_cruncher.marks import BallotMarks
from rcv_cruncher.cvr.tables import CastVoteRecord_tables
from rcv_cruncher.cvr.stats import CastVoteRecord_stats

decimal.getcontext().prec = 30


class CastVoteRecord(CastVoteRecord_stats, CastVoteRecord_tables):
    """Class that helps read, organize, and use multiple versions
    of the same cast vote record from an election.
    """

    @staticmethod
    def calc_stats(
        cvr: Type[CastVoteRecord],
        keep_decimal_type: bool = False,
        add_split_stats: bool = False,
        add_id_info: bool = True,
    ) -> pd.DataFrame:
        """Static method wrapper around `get_stats` object method.

        :param cvr: CastVoteRecord object.
        :type cvr: Type[CastVoteRecord]
        :param keep_decimal_type: Return the decimal class objects used by internal calculations rather than converting them to floats, defaults to False
        :type keep_decimal_type: bool, optional
        :param add_split_stats: Add extra statistics calculated for each category contained in `split_fields` columns passed to constructor, defaults to False
        :type add_split_stats: bool, optional
        :param add_id_info: Include contest ID details to returned dataframe, defaults to True
        :type add_id_info: bool, optional
        :return: A single row dataframe with statistics organized in multiple columns. If `split_fields` are passed, then extra rows are added for each category in the split columns.
        :rtype: pd.DataFrame
        """
        return cvr.get_stats(
            keep_decimal_type=keep_decimal_type,
            add_split_stats=add_split_stats,
            add_id_info=add_id_info,
        )

    @staticmethod
    def write_cvr_table(
        cvr: Type[CastVoteRecord],
        save_dir: Union[str, pathlib.Path],
        table_format: str = "rank",
    ) -> None:
        """Static method wrapper around `get_cvr_table` object method that writes CVR table out to `save_dir`. File name used follows the pattern "{save_dir}/{jurisdiction}_{date OR year}_{office}.csv". All non-alphanumeric characters, besides underscores, are removed from file name components. Contest date is in mm/dd/yyyy format.

        :param cvr: CastVoteRecord object.
        :type cvr: Type[CastVoteRecord]
        :param save_dir: Directory in which to write out CVR table.
        :type save_dir: Union[str, pathlib.Path]
        :param table_format: Format in which to write out CVR. Either "rank" or "candidate". One row per ballot. "rank" format has rank numbers as column names with candidate names in row cells. "candidate" format has candidate names as column names with rank numbers filling in row cells. Defaults to "rank".
        :type table_format: str, optional
        """
        uid = cvr.get_stats()[0]["unique_id"].item()
        save_path = pathlib.Path(save_dir) / f"{uid}.csv"
        cvr.get_cvr_table(table_format=table_format).to_csv(save_path, index=False)

    @staticmethod
    def calc_cumulative_ranking_tables(
        cvr: Type[CastVoteRecord],
    ) -> Tuple[pd.DataFrame]:
        """Static method wrapper around `get_cumulative_ranking_tables` object method.

        :param cvr: CastVoteRecord object.
        :type cvr: Type[CastVoteRecord]
        :return: Cumulative ranking tables in pandas dataframe. Tuple containing both count and percent formats.
        :rtype: Tuple[pd.DataFrame]
        """
        return cvr.get_cumulative_ranking_tables()

    @staticmethod
    def write_cumulative_ranking_tables(cvr: Type[CastVoteRecord], save_dir: Union[str, pathlib.Path]) -> None:
        """Static method wrapper around `get_cumulative_ranking_tables` object method that writes tables out to `save_dir`. Two tables are written out, one containing ballot counts and one with percentages. File names used follow the pattern "{save_dir}/cumulative_ranking/{jurisdiction}_{date OR year}_{office}_{'count' OR 'percent'}.csv". All non-alphanumeric characters, besides underscores, are removed from file name components. Contest date is in mm/dd/yyyy format.

        :param cvr: CastVoteRecord object.
        :type cvr: Type[CastVoteRecord]
        :param save_dir: Directory in which to write out tables.
        :type save_dir: Union[str, pathlib.Path]
        """
        count_df, percent_df = cvr.get_cumulative_ranking_tables()
        uid = cvr.get_stats()[0]["unique_id"].item()

        save_path = pathlib.Path(save_dir) / "cumulative_ranking"
        save_path.mkdir(exist_ok=True)

        count_df.to_csv(save_path / f"{uid}_count.csv")
        percent_df.to_csv(save_path / f"{uid}_percent.csv")

    @staticmethod
    def calc_first_second_tables(cvr: Type[CastVoteRecord]) -> Tuple[pd.DataFrame]:
        """Static method wrapper around `get_first_second_tables` object method.

        :param cvr: CastVoteRecord object.
        :type cvr: Type[CastVoteRecord]
        :return: First and second choice tables in pandas dataframes. Tuple containing three tables: count table and two percentage tables, one with exhausted ballots included in percentage calculations and one without.
        :rtype: Tuple[pd.DataFrame]
        """
        return cvr.get_first_second_tables()

    @staticmethod
    def write_first_second_tables(cvr: Type[CastVoteRecord], save_dir: Union[str, pathlib.Path] = None) -> None:
        """Static method wrapper around `get_first_second_tables` object method that writes tables out to `save_dir`. Three tables are written out, one containing ballot counts, one with percentages, and another with percentages excluding exhausted ballots. File names used follow the pattern "{save_dir}/first_second_choices/{jurisdiction}_{date OR year}_{office}_{'count' OR 'percent' OR 'percent_no_exhaust'}.csv". All non-alphanumeric characters, besides underscores, are removed from file name components. Contest date is in mm/dd/yyyy format.

        :param cvr: CastVoteRecord object.
        :type cvr: Type[CastVoteRecord]
        :param save_dir: Directory in which to write out tables.
        :type save_dir: Union[str, pathlib.Path]
        """
        count_df, percent_df, percent_no_exhaust_df = cvr.get_first_second_tables()
        uid = cvr.get_stats()[0]["unique_id"].item()

        save_path = pathlib.Path(save_dir) / "first_second_choices"
        save_path.mkdir(exist_ok=True)

        count_df.to_csv(save_path / f"{uid}_count.csv")
        percent_df.to_csv(save_path / f"{uid}_percent.csv")
        percent_no_exhaust_df.to_csv(save_path / f"{uid}_percent_no_exhaust.csv")

    @staticmethod
    def calc_rank_usage_table(cvr: Type[CastVoteRecord]) -> pd.DataFrame:
        """Static method wrapper around `get_rank_usage_table` object method.

        :param cvr: CastVoteRecord object.
        :type cvr: Type[CastVoteRecord]
        :return: Pandas dataframe containing rank usage statistics across all ballots and by candidate.
        :rtype: pd.DataFrame
        """
        return cvr.get_rank_usage_table()

    @staticmethod
    def write_rank_usage_table(cvr: Type[CastVoteRecord], save_dir: Union[str, pathlib.Path] = None) -> None:
        """Static method wrapper around `get_rank_usage_table` object method that writes the table out to `save_dir`. File names used follow the pattern "{save_dir}/rank_usage/{jurisdiction}_{date OR year}_{office}.csv". All non-alphanumeric characters, besides underscores, are removed from file name components. Contest date is in mm/dd/yyyy format.

        :param cvr: CastVoteRecord object.
        :type cvr: Type[CastVoteRecord]
        :param save_dir: Directory in which to write out table.
        :type save_dir: Union[str, pathlib.Path]
        """
        df = cvr.get_rank_usage_table()
        uid = cvr.get_stats()[0]["unique_id"].item()

        save_path = pathlib.Path(save_dir) / "rank_usage"
        save_path.mkdir(exist_ok=True)

        df.to_csv(save_path / f"{uid}.csv")

    @staticmethod
    def calc_crossover_tables(cvr: Type[CastVoteRecord]) -> Tuple[pd.DataFrame]:
        """Static method wrapper around `get_crossover_tables` object method.

        :param cvr: CastVoteRecord object.
        :type cvr: Type[CastVoteRecord]
        :return: Tuples of pandas dataframes containing statistics on candidate ranking patterns near the top of the ballot. Tuple containing both count and percent formats.
        :rtype: Tuple[pd.DataFrame]
        """
        return cvr.get_crossover_tables()

    @staticmethod
    def write_crossover_tables(cvr: Type[CastVoteRecord], save_dir: Union[str, pathlib.Path] = None) -> None:
        """Static method wrapper around `get_crossover_tables` object method that writes the table out to `save_dir`. Two tables are written out, one containing ballot counts and one with percentages. File names used follow the pattern "{save_dir}/opponent_crossover/{jurisdiction}_{date OR year}_{office}_{'count' OR 'percent'}.csv". All non-alphanumeric characters, besides underscores, are removed from file name components. Contest date is in mm/dd/yyyy format.

        :param cvr: CastVoteRecord object.
        :type cvr: Type[CastVoteRecord]
        :param save_dir: Directory in which to write out tables.
        :type save_dir: Union[str, pathlib.Path]
        """
        count_df, percent_df = cvr.get_crossover_tables()
        uid = cvr.get_stats()[0]["unique_id"].item()

        save_path = pathlib.Path(save_dir) / "opponent_crossover"
        save_path.mkdir(exist_ok=True)

        count_df.to_csv(save_path / f"{uid}_count.csv")
        percent_df.to_csv(save_path / f"{uid}_percent.csv")

    @staticmethod
    def calc_condorcet_tables(cvr: Type[CastVoteRecord]) -> Tuple[pd.DataFrame]:
        """Static method wrapper around `get_condorcet_tables` object method.

        :param cvr: CastVoteRecord object.
        :type cvr: Type[CastVoteRecord]
        :return: Tuples of pandas dataframes containing statistics on head to head candidate matchups. Tuple containing both count and percent formats.
        :rtype: Tuple[pd.DataFrame]
        """
        return cvr.get_condorcet_tables()

    @staticmethod
    def write_condorcet_tables(cvr: Type[CastVoteRecord], save_dir: Union[str, pathlib.Path] = None) -> None:
        """Static method wrapper around `get_condorcet_tables` object method that writes the table out to `save_dir`. Two tables are written out, one containing ballot counts and one with percentages. File names used follow the pattern "{save_dir}/condorcet/{jurisdiction}_{date OR year}_{office}_{'count' OR 'percent'}.csv". All non-alphanumeric characters, besides underscores, are removed from file name components. Contest date is in mm/dd/yyyy format.

        :param cvr: CastVoteRecord object.
        :type cvr: Type[CastVoteRecord]
        :param save_dir: Directory in which to write out tables.
        :type save_dir: Union[str, pathlib.Path]
        """
        count_df, percent_df, condorcet_winner = cvr.get_condorcet_tables()
        uid = cvr.get_stats()[0]["unique_id"].item()

        save_path = pathlib.Path(save_dir) / "condorcet"
        save_path.mkdir(exist_ok=True)

        count_df.to_csv(
            save_path / f"{uid}_count.csv",
            index_label=f"condorcet winner: {condorcet_winner}",
        )
        percent_df.to_csv(
            save_path / f"{uid}_percent.csv",
            index_label=f"condorcet winner: {condorcet_winner}",
        )

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
    ) -> None:
        """
        Constructor for CastVoteRecord.

        Either **parser_func** and **parser_args** must both be passed or an already parsed CVR must be passed as **parsed_cvr**.

        Constructor parses CVR file, if needed, and computes default ballot statistics.

        :param jurisdiction: Name of election jurisdiction, defaults to ""
        :type jurisdiction: str, optional
        :param state: State, or broader jursidiction, of election, defaults to ""
        :type state: str, optional
        :param year: Year of election, defaults to ""
        :type year: str, optional
        :param date: Date of election in format mm/dd/yyyy, defaults to ""
        :type date: str, optional
        :param office: Office which the election is deciding, defaults to ""
        :type office: str, optional
        :param notes: Any extra notes to store about the election, defaults to ""
        :type notes: str, optional
        :param parser_func: A function from `parsers.py` or a custom function with the same signature and return type, defaults to None
        :type parser_func: Optional[Callable], optional
        :param parser_args: Dictionary of arguments and their values which are unrolled and passed to chosen `parser_func`. Works like :code:`**kwargs`. Defaults to None.
        :type parser_args: Optional[Dict], optional
        :param parsed_cvr: A CVR represented as a dictionary of lists all of equal length. The only mandatory key-value pair is 'ranks' which must contain a list of lists, all must be the same length and each must contain the string names of candidates, or special `BallotMarks` constants (SKIPPED, OVERVOTE, WRITEIN), in ranked order. One other optional special CVR key is 'weight', which will be used internally to provide weights to each ballot. Other dictionary keys are optional and arbitrary and can be used to represent other ballot information, such as ballot IDs or precinct details. Defaults to None
        :type parsed_cvr: Optional[Dict], optional
        :param split_fields: Only relevant for calculating split statistics. A list of CVR field names. Statistics will be calculated for each subcategory in a CVR field. Defaults to None
        :type split_fields: Optional[List], optional
        :param disable_aggregation: Advanced option. If True, CVR is not represented interally in aggregated form. If False, CVR remains as parsed. Defaults to False. Internal aggregation of the CVR is meant to speed up tabulation and statistics calculation, but can be incompatible with some RCV variants, such as Cambridge's STV whole ballot transfer variant.
        :type disable_aggregation: bool, optional
        """
        # ID INFO
        self.jurisdiction = jurisdiction
        self.state = state
        self.date = date
        self.year = year
        self.office = office
        self.notes = notes
        self.split_fields = split_fields
        self.unique_id = self._unique_id()

        self._disable_aggregation = disable_aggregation

        self._id_df = pd.DataFrame(
            {
                "jurisdiction": [self.jurisdiction],
                "state": [self.state],
                "date": [self.date],
                "year": [self.year],
                "office": [self.office],
                "notes": [self.notes],
                "unique_id": [self.unique_id],
            }
        )

        # DEFAULT CVR
        # - parse cvr
        if parser_func and parser_args:
            parsed_cvr = parser_func(**parser_args)

        # - validate cvr
        validated_cvr = self._validate_cvr(parsed_cvr)

        # - aggregate cvr
        self._disaggregation_info = {}
        if not self._disable_aggregation:
            cvr, self._disaggregation_info = self._aggregate_cvr(validated_cvr)
        else:
            cvr = validated_cvr

        # - make candidate set
        candidate_set = set(cvr["ranks"][0]).union(*[set(ranks) for ranks in cvr["ranks"][0:]])
        candidate_set = candidate_set.difference({BallotMarks.OVERVOTE, BallotMarks.SKIPPED})

        # - convert ranks to BallotMarks objects
        cvr["ballot_marks"] = [BallotMarks(ranks) for ranks in cvr["ranks"]]
        del cvr["ranks"]

        # - make a default rule set that is just the parsed cvr
        self._modified_cvrs = {}
        self._candidate_sets = {}
        self._rule_sets = {}

        self._default_rule_set_name = "__cvr"
        self._rule_sets.update({self._default_rule_set_name: BallotMarks.new_rule_set()})
        self._modified_cvrs.update({self._default_rule_set_name: cvr})
        self._candidate_sets.update({self._default_rule_set_name: BallotMarks(candidate_set)})

        # STAT INFO
        self._cvr_stat_table = None
        self._compute_cvr_stat_table()

        self._summary_cvr_stat_table = None
        self._compute_summary_cvr_stat_table()

        self._summary_cvr_split_stat_table = None

    # CVR MODS
    def _validate_cvr(self, cvr_dict: Dict[str, List]) -> Dict[str, List]:

        if not cvr_dict:
            raise ValueError("if no parser_func and parser_args are passed, a parsed_cvr must be passed.")

        # if parser returns a list, assume it is rank list of lists
        if isinstance(cvr_dict, list):
            cvr_dict = {
                "ranks": cvr_dict,
                "weight": [decimal.Decimal("1")] * len(cvr_dict),
            }

        if "ranks" not in cvr_dict:
            raise RuntimeError('Parsed CVR does not contain field "ranks"')

        if len(cvr_dict["ranks"]) == 0:
            raise RuntimeError("parsed ranks list is empty.")

        if "weight" not in cvr_dict:
            cvr_dict["weight"] = [decimal.Decimal("1") for _ in cvr_dict["ranks"]]

        if not isinstance(cvr_dict["weight"][0], decimal.Decimal):
            cvr_dict["weight"] = [decimal.Decimal(str(i)) for i in cvr_dict["weight"]]

        ballot_lengths = collections.Counter(len(b) for b in cvr_dict["ranks"])
        if len(ballot_lengths) > 1:
            raise RuntimeError(f"Parsed CVR contains ballots with unequal length rank lists. {str(ballot_lengths)}")

        field_lengths = {k: len(cvr_dict[k]) for k in cvr_dict}
        if len(set(field_lengths.values())) > 1:
            raise RuntimeError(f"Parsed CVR contains fields of unequal length. {str(field_lengths)}")

        return cvr_dict

    def _aggregate_cvr(self, cvr_dict: Dict[str, List]) -> Dict[str, List]:

        # any unique CVR fields?
        # unique_fields = set([k for k, v in cvr_dict.items() if k != "ranks" and len(v) == len(set(v))])
        unique_fields = set()
        unique_fields.add("weight")

        # all other fields will be used for aggregation
        aggregate_fields = sorted([k for k in cvr_dict if k not in unique_fields])

        # create hashable ID out of aggregation key value pairs
        cvr_dict["aggregation_id"] = [
            tuple((k, tuple(d[k])) if k == "ranks" else (k, d[k]) for k in aggregate_fields) for d in DL2LD(cvr_dict)
        ]

        # sum up weight by aggregate ID and store unaggregated fields for later disaggregation
        cvr_ld = DL2LD(cvr_dict)

        # maintainence of key insertion order is critical to this implementation
        disaggregation_info = {d["aggregation_id"]: [] for d in cvr_ld}
        aggregate_counter = {d["aggregation_id"]: decimal.Decimal(0) for d in cvr_ld}

        for idx, d in enumerate(cvr_ld):
            disaggregation_info[d["aggregation_id"]].append(
                {"ballot_order": idx, **{k: v for k, v in d.items() if k in unique_fields}}
            )
            aggregate_counter[d["aggregation_id"]] += d["weight"]

        aggregated_cvr_LD = [
            {
                **{k: list(v) if k == "ranks" else v for k, v in dict(agg_id).items()},
                "weight": aggregate_counter[agg_id],
            }
            for agg_id in aggregate_counter.keys()
        ]

        aggregated_cvr_DL = LD2DL(aggregated_cvr_LD)

        return aggregated_cvr_DL, disaggregation_info

    def _disaggregate_cvr(self, cvr_dict: Dict[str, List]) -> Dict[str, List]:

        disagg_info = self._disaggregation_info
        disagg_info_keys = list(self._disaggregation_info.keys())

        # copy aggregated fields and re-place unique fields removed during aggregation process
        cvr_LD = DL2LD(cvr_dict)
        cvr_LD = [
            [
                {
                    **{k: v for k, v in agg_d.items() if k != "weight"},
                    **{k: v for k, v in unique_d.items() if k != "ballot_order"},
                }
                for unique_d in disagg_info[disagg_info_keys[idx]]
            ]
            for idx, agg_d in enumerate(cvr_LD)
        ]
        cvr_LD = [d for sublist in cvr_LD for d in sublist]

        return LD2DL(cvr_LD)

    def _unique_id(self) -> str:
        pieces = []
        if self.jurisdiction:
            pieces.append(self.jurisdiction)
        if self.date:
            padded_date = "".join(
                date_piece if len(date_piece) > 1 else "0" + date_piece for date_piece in self.date.split("/")
            )
            pieces.append(padded_date)
        elif self.year:
            pieces.append(self.year)
        if self.office:
            pieces.append(self.office)
        return "_".join(re.sub("[^0-9a-zA-Z_]+", "", piece) for piece in pieces)

    def _make_modified_cvr(self, rule_set_name: str) -> None:

        if rule_set_name not in self._rule_sets:
            raise RuntimeError(f"rule set {rule_set_name} has not yet been added using add_rule_set().")

        cvr = {k: v for k, v in self.get_cvr_dict(disaggregate=False).items()}
        cvr["ballot_marks"] = [b.copy() for b in cvr["ballot_marks"]]

        for ballot in cvr["ballot_marks"]:
            ballot.apply_rules(**self._rule_sets[rule_set_name])

        self._modified_cvrs.update({rule_set_name: cvr})

    def _make_candidate_set(self, rule_set_name: str) -> None:

        if rule_set_name not in self._rule_sets:
            raise RuntimeError(f"rule set {rule_set_name} has not yet been added using add_rule_set().")

        # unpack rules
        rule_set = self._rule_sets[rule_set_name]
        combine_writeins = rule_set["combine_writein_marks"]
        exclude_writeins = rule_set["exclude_writein_marks"]

        candidate_ballot_marks = self._candidate_sets[self._default_rule_set_name].copy()
        candidate_ballot_marks.apply_rules(
            combine_writein_marks=combine_writeins,
            exclude_writein_marks=exclude_writeins,
        )

        self._candidate_sets.update({rule_set_name: candidate_ballot_marks})

    def add_rule_set(self, set_name: str, set_dict: Dict[str, Optional[bool]]) -> None:
        """Add a new rule set used to create a modified version of the CVR.

        :param set_name: Unique name given to this rule set and modified CVR.
        :type set_name: str
        :param set_dict: Dictionary of boolean rule settings. Rule options are defined in `BallotMarks.new_rule_set`.
        :type set_dict: Dict[str, Optional[bool]]
        """
        # if rule set already created, do nothing
        if set_name in self._rule_sets and set_dict == self._rule_sets[set_name]:
            return

        # if making a new rule set using the same name, delete old one
        if set_name in self._rule_sets and set_dict != self._rule_sets[set_name]:
            del self._modified_cvrs[set_name]
            del self._candidate_sets[set_name]

        self._rule_sets.update({set_name: set_dict})

    def get_cvr_dict(self, rule_set_name: Optional[str] = None, disaggregate: bool = True) -> Dict[str, List]:
        """Return CVR as dictionary of lists.

        :param rule_set_name: Name of modified CVR to return, defaults to None. If None, return default CVR.
        :type rule_set_name: Optional[str], optional
        :param disaggregate: If True, the internally aggregated CVR is disaggregated before return. Defaults to True.
        :type disaggregate: bool, optional
        :return: CVR as dictionary of lists.
        :rtype: Dict[str, List]
        """
        if rule_set_name is None:
            rule_set_name = self._default_rule_set_name

        if rule_set_name not in self._modified_cvrs:
            self._make_modified_cvr(rule_set_name)

        cvr = self._modified_cvrs[rule_set_name]

        if disaggregate and not self._disable_aggregation:
            cvr = self._disaggregate_cvr(cvr)

        return cvr

    def get_candidates(self, rule_set_name: Optional[str] = None) -> BallotMarks:
        """Returns a BallotMarks object containing the unique candidate set. The only rules which affect the candidate set are 'combine_writein_marks' and 'exclude_writein_marks'.

        :param rule_set_name: Name of modified CVR to return candidates from, defaults to None. If None, return candidates from default CVR. Defaults to None
        :type rule_set_name: Optional[str], optional
        :return: BallotMarks object containing unique candidates.
        :rtype: BallotMarks
        """
        if rule_set_name is None:
            rule_set_name = self._default_rule_set_name

        if rule_set_name not in self._candidate_sets:
            self._make_candidate_set(rule_set_name)

        return self._candidate_sets[rule_set_name]
