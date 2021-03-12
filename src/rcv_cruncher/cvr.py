import copy
import decimal

import pandas as pd

from typing import (Callable, Dict, Optional, Set)

import rcv_cruncher.util as util
import rcv_cruncher.package_types as types

decimal.getcontext().prec = 30


class CVR:

    @staticmethod
    def new_rule_set(combine_writeins: Optional[bool] = None,
                     exclude_writeins: Optional[bool] = None,
                     treat_combined_writeins_as_duplicates: Optional[bool] = None,
                     exhaust_on_duplicate_rankings: Optional[bool] = None,
                     exclude_duplicates: Optional[bool] = None,
                     exhaust_on_overvote: Optional[bool] = None,
                     exclude_overvotes: Optional[bool] = None,
                     exhaust_on_repeated_skipped_rankings: Optional[bool] = None,
                     exclude_skipped_rankings: Optional[bool] = None,) -> Dict:
        return {
            'combine_writeins': combine_writeins,
            'exclude_writeins': exclude_writeins,
            'treat_combined_writeins_as_duplicates': treat_combined_writeins_as_duplicates,
            'exhaust_on_duplicate_rankings': exhaust_on_duplicate_rankings,
            'exhaust_on_overvote': exhaust_on_overvote,
            'exhaust_on_repeated_skipped_rankings': exhaust_on_repeated_skipped_rankings,
            'exclude_duplicates': exclude_duplicates,
            'exclude_overvotes': exclude_overvotes,
            'exclude_skipped_rankings': exclude_skipped_rankings
        }

    def __init__(self, parser_func: Callable, parser_args: Dict,
                 jurisdiction: str, state: str, year: str, date: str, office: str, notes: Optional[str]) -> None:

        self.jurisdiction = jurisdiction
        self.state = state
        self.date = date
        self.office = office
        self.notes = notes

        parsed_cvr = parser_func(**parser_args)

        # if parser returns a list, assume it is rank list of lists
        if isinstance(parsed_cvr, list):
            parsed_cvr = {
                'ranks': parsed_cvr,
                'weight': [decimal.Decimal('1')] * len(parsed_cvr)
            }

        if 'ranks' not in parsed_cvr:
            raise RuntimeError(f'Dictionary returned by parser function {parser_func.__name__} does not contain field "ranks"')

        self._parsed_cvr = parsed_cvr
        self._modified_cvrs = {}
        self._candidate_sets = {}
        self._rule_sets = {}

        # make a default rule set that is just the parsed cvr
        self._default_rule_set_name = '__'
        self.add_rule_set(self._default_rule_set_name, self.new_rule_set())

    def _make_modified_cvr(self, rule_set_name: str) -> None:

        if rule_set_name not in self._rule_sets:
            raise RuntimeError(f'rule set {rule_set_name} has not yet been added using add_rule_set().')

        cvr = copy.deepcopy(self._parsed_cvr)

        # unpack rules
        rule_set = self._rule_sets[rule_set_name]

        combine_writeins = rule_set['combine_writins']
        exclude_writeins = rule_set['exclude_writeins']

        treat_combined_writeins_as_duplicates = rule_set['treat_combined_writeins_as_duplicates']

        exhaust_on_duplicate_rankings = rule_set['exhaust_on_duplicate_rankings']
        exclude_duplicates = rule_set['exclude_duplicates']

        exhaust_on_overvote = rule_set['exhaust_on_overvote']
        exclude_overvotes = rule_set['exclude_overvotes']

        exhaust_on_repeated_skipped_rankings = rule_set['exhaust_on_repeated_skipped_rankings']
        exclude_skipped_rankings = rule_set['exclude_skipped_rankings']

        # apply rules

        # has to occur before exhaustion by duplicates is computed
        if combine_writeins and treat_combined_writeins_as_duplicates:
            cvr['ranks'] = [util.combine_writeins(b) for b in cvr['ranks']]

        new_ranks = []
        for b in cvr['ranks']:
            new_ballot = []
            # look at successive pairs of rankings - zip list with itself offset by 1
            for elem_a, elem_b in zip(b, b[1:]+[None]):

                skipped_rankings_present = {elem_a, elem_b} == {util.BallotMarks.SKIPPEDRANK}
                if exhaust_on_repeated_skipped_rankings and skipped_rankings_present:
                    break

                overvote_present = elem_a == util.BallotMarks.OVERVOTE
                if exhaust_on_overvote and overvote_present:
                    break

                duplicate_ranking_present = elem_a in new_ballot
                if exhaust_on_duplicate_rankings and duplicate_ranking_present:
                    break

                new_ballot.append(elem_a)
            new_ranks.append(new_ballot)

        if exclude_duplicates:
            new_ranks = [util.remove_dup(b) for b in new_ranks]

        # has to occur after to duplicates are excluded
        if combine_writeins and not treat_combined_writeins_as_duplicates:
            new_ranks = [util.combine_writeins(b) for b in new_ranks]

        if exclude_overvotes:
            new_ranks = [util.remove(util.BallotMarks.OVERVOTE, b) for b in new_ranks]

        if exclude_skipped_rankings:
            new_ranks = [util.remove(util.BallotMarks.SKIPPEDRANK, b) for b in new_ranks]

        if exclude_writeins:
            new_ranks = [util.remove(util.BallotMarks.WRITEIN, b) for b in new_ranks]

        cvr['ranks'] = new_ranks

        self._modified_cvrs.update({rule_set_name: cvr})

    def _make_candidate_set(self, rule_set_name: str) -> None:

        if rule_set_name not in self._rule_sets:
            raise RuntimeError(f'rule set {rule_set_name} has not yet been added using add_rule_set().')

        cvr = copy.deepcopy(self._parsed_cvr)

        # unpack rules
        rule_set = self._rule_sets[rule_set_name]

        combine_writeins = rule_set['combine_writins']
        exclude_writeins = rule_set['exclude_writeins']

        candidate_set = set()
        for b in cvr['ranks']:
            candidate_set.update(b)

        candidate_set = candidate_set - {util.BallotMarks.OVERVOTE, util.BallotMarks.SKIPPEDRANK}

        if combine_writeins:
            candidate_set = set(util.combine_writeins(candidate_set))

            # safety check
            uncaught_writeins = [cand for cand in candidate_set
                                 if cand != util.BallotMarks.WRITEIN and ('write' in cand.lower() or 'uwi' in cand.lower())]
            if len(uncaught_writeins) > 0:
                raise RuntimeError('(developer error) more than one writein remaining after combine step.')

        if exclude_writeins:
            candidate_set = candidate_set - {util.BallotMarks.WRITEIN}

        self._candidate_sets.update({rule_set_name: candidate_set})

    def add_rule_set(self, set_name: str, set_dict: Dict[str, Optional[bool]]) -> None:
        self._rule_sets.update({set_name: set_dict})

        # if the set name matches an already computed cvr, delete that cvr
        if set_name in self._modified_cvrs:
            del self._modified_cvrs[set_name]

    def get_cvr(self, rule_set_name: Optional[str]) -> types.BallotDictOfLists:

        if rule_set_name is None:
            rule_set_name = self._default_rule_set_name

        if rule_set_name not in self._modified_cvrs:
            self._make_modified_cvr(rule_set_name)

        return self._modified_cvrs[rule_set_name]

    def get_candidate_set(self, rule_set_name: Optional[str]) -> Set:

        if rule_set_name is None:
            rule_set_name = self._default_rule_set_name

        if rule_set_name not in self._candidate_sets:
            self._make_candidate_set(rule_set_name)

        return self._candidate_sets[rule_set_name]

    def get_cvr_table(self, table_format: str = "rank"):

        if table_format != "rank" and table_format != "candidate":
            raise RuntimeError('table_format argument must be "rank" or "candidate"')

        if table_format == "rank":
            return self._rank_header_cvr()
        elif table_format == "candidate":
            return self._candidate_header_cvr()

    def _rank_header_cvr(self):

        ballot_dict = copy.deepcopy(self.get_cvr(self._default_rule_set_name))
        bs = ballot_dict['ranks']
        weight = ballot_dict['weight']
        del ballot_dict['ranks']
        del ballot_dict['weight']

        # how many ranks?
        num_ranks = max(len(i) for i in bs)

        # make sure all ballots are lists of equal length, adding trailing 'skipped' if necessary
        bs = [b + ([util.BallotMarks.SKIPPEDRANK] * (num_ranks - len(b))) for b in bs]

        # assemble output_table, start with extras
        output_df = pd.DataFrame.from_dict(ballot_dict)

        # are weights all one, then dont add to output
        if not all([i == 1 for i in weight]):
            output_df['weight'] = [float(w) for w in weight]

        # add in rank columns
        for i in range(1, num_ranks + 1):
            output_df['rank' + str(i)] = [b[i-1] for b in bs]

        return output_df

    def _candidate_header_cvr(self):

        # get ballots and candidates
        ballot_dl = copy.deepcopy(self.get_cvr(self._default_rule_set_name))
        candidate_set = copy.deepcopy(self.get_candidate_set(self._default_rule_set_name))

        # remove weights if all equal to 1
        if set(ballot_dl['weight']) == {1}:
            del ballot_dl['weight']

        # add rank limit
        ballot_dl['rank_limit'] = len(ballot_dl['ranks'][0])

        # convert dict of list to list of dicts
        ballot_ld = util.DL2LD(ballot_dl)

        # add candidate index information
        for b in ballot_ld:
            b.update({f"candidate_{cand}": None for cand in candidate_set})
            for rank_idx, cand in enumerate(b['ranks'], start=1):
                if cand in b:
                    b[cand] = rank_idx
            del b['ranks']

        df = pd.DataFrame(ballot_ld)
        return df.reindex(sorted(df.columns), axis=1)
