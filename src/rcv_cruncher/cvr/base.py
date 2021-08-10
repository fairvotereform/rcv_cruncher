from __future__ import annotations
from typing import (Callable, Dict, Optional, List, Type, Union, Tuple)

import decimal
import collections
import re
import pathlib

import pandas as pd

from rcv_cruncher.marks import BallotMarks
from rcv_cruncher.cvr.tables import CastVoteRecord_tables
from rcv_cruncher.cvr.stats import CastVoteRecord_stats

decimal.getcontext().prec = 30


class CastVoteRecord(CastVoteRecord_stats, CastVoteRecord_tables):

    @staticmethod
    def get_stats(cvr: Type[CastVoteRecord],
                  keep_decimal_type: bool = False,
                  add_split_stats: bool = False,
                  add_id_info: bool = True) -> pd.DataFrame:
        return cvr.stats(keep_decimal_type=keep_decimal_type,
                         add_split_stats=add_split_stats,
                         add_id_info=add_id_info)

    @staticmethod
    def write_cvr_table(cvr: Type[CastVoteRecord],
                        table_format: str = "rank",
                        save_dir: Union[str, pathlib.Path] = None) -> None:
        uid = cvr.stats()[0]['unique_id'].item()
        save_path = pathlib.Path(save_dir) / f'{uid}.csv'
        cvr.cvr_table(table_format=table_format).to_csv(save_path, index=False)

    @staticmethod
    def get_cumulative_ranking_tables(cvr: Type[CastVoteRecord]) -> Tuple[pd.DataFrame]:
        return cvr.cumulative_ranking_tables()

    @staticmethod
    def write_cumulative_ranking_tables(cvr: Type[CastVoteRecord],
                                        save_dir: Union[str, pathlib.Path] = None) -> None:
        count_df, percent_df = cvr.cumulative_ranking_tables()
        uid = cvr.stats()[0]['unique_id'].item()

        save_path = pathlib.Path(save_dir) / 'cumulative_ranking'
        save_path.mkdir(exist_ok=True)

        count_df.to_csv(save_path / f'{uid}_count.csv')
        percent_df.to_csv(save_path / f'{uid}_percent.csv')

    @staticmethod
    def get_first_second_tables(cvr: Type[CastVoteRecord]) -> Tuple[pd.DataFrame]:
        return cvr.first_second_tables()

    @staticmethod
    def write_first_second_tables(cvr: Type[CastVoteRecord],
                                  save_dir: Union[str, pathlib.Path] = None) -> None:
        count_df, percent_df, percent_no_exhaust_df = cvr.first_second_tables()
        uid = cvr.stats()[0]['unique_id'].item()

        save_path = pathlib.Path(save_dir) / 'first_second_choices'
        save_path.mkdir(exist_ok=True)

        count_df.to_csv(save_path / f'{uid}_count.csv')
        percent_df.to_csv(save_path / f'{uid}_percent.csv')
        percent_no_exhaust_df.to_csv(save_path / f'{uid}_percent_no_exhaust.csv')

    @staticmethod
    def get_rank_usage_table(cvr: Type[CastVoteRecord]) -> Tuple[pd.DataFrame]:
        return cvr.rank_usage_table()

    @staticmethod
    def write_rank_usage_table(cvr: Type[CastVoteRecord],
                               save_dir: Union[str, pathlib.Path] = None) -> None:
        df = cvr.rank_usage_table()
        uid = cvr.stats()[0]['unique_id'].item()

        save_path = pathlib.Path(save_dir) / 'rank_usage'
        save_path.mkdir(exist_ok=True)

        df.to_csv(save_path / f'{uid}.csv')

    @staticmethod
    def get_crossover_table(cvr: Type[CastVoteRecord]) -> pd.DataFrame:
        return cvr.crossover_table()

    @staticmethod
    def write_crossover_table(cvr: Type[CastVoteRecord],
                              save_dir: Union[str, pathlib.Path] = None) -> None:
        count_df, percent_df = cvr.crossover_tables()
        uid = cvr.stats()[0]['unique_id'].item()

        save_path = pathlib.Path(save_dir) / 'opponent_crossover'
        save_path.mkdir(exist_ok=True)

        count_df.to_csv(save_path / f'{uid}_count.csv')
        percent_df.to_csv(save_path / f'{uid}_percent.csv')

    @staticmethod
    def get_condorcet_tables(cvr: Type[CastVoteRecord]) -> Tuple[pd.DataFrame]:
        return cvr.condorcet_tables()

    @staticmethod
    def write_condorcet_tables(cvr: Type[CastVoteRecord],
                               save_dir: Union[str, pathlib.Path] = None) -> None:
        count_df, percent_df, condorcet_winner = cvr.condorcet_tables()
        uid = cvr.stats()[0]['unique_id'].item()

        save_path = pathlib.Path(save_dir) / 'condorcet'
        save_path.mkdir(exist_ok=True)

        count_df.to_csv(save_path / f'{uid}_count.csv', index_label=f'condorcet winner: {condorcet_winner}')
        percent_df.to_csv(save_path / f'{uid}_percent.csv', index_label=f'condorcet winner: {condorcet_winner}')

    def __init__(self,
                 jurisdiction: str = "",
                 state: str = "",
                 year: str = "",
                 date: str = "",
                 office: str = "",
                 notes: str = "",
                 parser_func: Optional[Callable] = None,
                 parser_args: Optional[Dict] = None,
                 parsed_cvr: Optional[Dict] = None,
                 split_fields: Optional[List] = None) -> None:

        # ID INFO
        self.jurisdiction = jurisdiction
        self.state = state
        self.date = date
        self.year = year
        self.office = office
        self.notes = notes
        self.split_fields = split_fields
        self.unique_id = self._unique_id()

        self._id_df = pd.DataFrame({
            'jurisdiction': [self.jurisdiction],
            'state': [self.state],
            'date': [self.date],
            'year': [self.year],
            'office': [self.office],
            'notes': [self.notes],
            'unique_id': [self.unique_id]
        })

        self._parsed_cvr = self._prepare_parsed_cvr(parser_func=parser_func,
                                                    parser_args=parser_args,
                                                    parsed_cvr=parsed_cvr)
        self._modified_cvrs = {}
        self._candidate_sets = {}
        self._rule_sets = {}

        # make a default rule set that is just the parsed cvr
        self._default_rule_set_name = '__cvr'
        self.add_rule_set(self._default_rule_set_name, BallotMarks.new_rule_set())

        # STAT INFO

        self._cvr_stat_table = None
        self._compute_cvr_stat_table()

        self._summary_cvr_stat_table = None
        self._compute_summary_cvr_stat_table()

        self._split_filter_dict = {}
        self._summary_cvr_split_stat_table = None

    # CVR MODS
    def _prepare_parsed_cvr(self,
                            parser_func: Optional[Callable] = None,
                            parser_args: Optional[Dict] = None,
                            parsed_cvr: Optional[Dict[str, List]] = None) -> Dict[str, List]:

        if parser_func and parser_args:
            parsed_cvr = parser_func(**parser_args)

        if not parsed_cvr:
            raise ValueError('if no parser_func and parser_args are passed, a parsed_cvr must be passed.')

        # if parser returns a list, assume it is rank list of lists
        if isinstance(parsed_cvr, list):
            parsed_cvr = {
                'ranks': parsed_cvr,
                'weight': [decimal.Decimal('1')] * len(parsed_cvr)
            }

        if 'ranks' not in parsed_cvr:
            raise RuntimeError('Parsed CVR does not contain field "ranks"')

        if len(parsed_cvr['ranks']) == 0:
            raise RuntimeError('parsed ranks list is empty.')

        if 'weight' not in parsed_cvr:
            parsed_cvr['weight'] = [decimal.Decimal('1') for _ in parsed_cvr['ranks']]

        if not isinstance(parsed_cvr['weight'][0], decimal.Decimal):
            parsed_cvr['weight'] = [decimal.Decimal(str(i)) for i in parsed_cvr['weight']]

        parsed_cvr['ballot_marks'] = [BallotMarks(ranks) for ranks in parsed_cvr['ranks']]
        del parsed_cvr['ranks']

        ballot_lengths = collections.Counter(len(b.marks) for b in parsed_cvr['ballot_marks'])
        if len(ballot_lengths) > 1:
            raise RuntimeError(f'Parsed CVR contains ballots with unequal length rank lists. {str(ballot_lengths)}')

        field_lengths = {k: len(parsed_cvr[k]) for k in parsed_cvr}
        if len(set(field_lengths.values())) > 1:
            raise RuntimeError(f'Parsed CVR contains fields of unequal length. {str(field_lengths)}')

        return parsed_cvr

    def _unique_id(self) -> str:
        pieces = []
        if self.jurisdiction:
            pieces.append(self.jurisdiction)
        if self.date:
            padded_date = "".join(date_piece if len(date_piece) > 1 else "0" + date_piece
                                  for date_piece in self.date.split("/"))
            pieces.append(padded_date)
        elif self.year:
            pieces.append(self.year)
        if self.office:
            pieces.append(self.office)
        return "_".join(re.sub('[^0-9a-zA-Z_]+', '', piece) for piece in pieces)

    def _make_modified_cvr(self, rule_set_name: str) -> None:

        if rule_set_name not in self._rule_sets:
            raise RuntimeError(f'rule set {rule_set_name} has not yet been added using add_rule_set().')

        cvr = {k: v for k, v in self._parsed_cvr.items()}
        cvr['ballot_marks'] = [b.copy() for b in cvr['ballot_marks']]

        for ballot in cvr['ballot_marks']:
            ballot.apply_rules(**self._rule_sets[rule_set_name])

        self._modified_cvrs.update({rule_set_name: cvr})

    def _make_candidate_set(self, rule_set_name: str) -> None:

        if rule_set_name not in self._rule_sets:
            raise RuntimeError(f'rule set {rule_set_name} has not yet been added using add_rule_set().')

        cvr = self._parsed_cvr

        # unpack rules
        rule_set = self._rule_sets[rule_set_name]
        combine_writeins = rule_set['combine_writein_marks']
        exclude_writeins = rule_set['exclude_writein_marks']

        candidate_ballot_marks = BallotMarks(set.union(*[b.unique_candidates for b in cvr['ballot_marks']]))
        candidate_ballot_marks.apply_rules(combine_writein_marks=combine_writeins, exclude_writein_marks=exclude_writeins)

        self._candidate_sets.update({rule_set_name: candidate_ballot_marks})

    def add_rule_set(self, set_name: str, set_dict: Dict[str, Optional[bool]]) -> None:

        # if rule set already created, do nothing
        if set_name in self._rule_sets and set_dict == self._rule_sets[set_name]:
            return

        # if making a new rule set using the same name, delete old one
        if set_name in self._rule_sets and set_dict != self._rule_sets[set_name]:
            del self._modified_cvrs[set_name]
            del self._candidate_sets[set_name]

        self._rule_sets.update({set_name: set_dict})

    def get_cvr_dict(self, rule_set_name: Optional[str] = None) -> Dict[str, List]:

        if rule_set_name is None:
            rule_set_name = self._default_rule_set_name

        if rule_set_name not in self._modified_cvrs:
            self._make_modified_cvr(rule_set_name)

        return self._modified_cvrs[rule_set_name]

    def get_candidates(self, rule_set_name: Optional[str] = None) -> BallotMarks:

        if rule_set_name is None:
            rule_set_name = self._default_rule_set_name

        if rule_set_name not in self._candidate_sets:
            self._make_candidate_set(rule_set_name)

        return self._candidate_sets[rule_set_name]
