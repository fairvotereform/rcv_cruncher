from abc import abstractmethod, ABC
from collections import Counter
import numpy as np
import pandas as pd
from inspect import signature

from .ballots import candidates_merged_writeIns, cleaned_writeIns_merged, ballots_writeIns_merged
from .cache_helpers import save
from .rcv_reporting import RCV_Reporting
from .definitions import remove, flatten_list, SKIPPEDRANK


class RCV(RCV_Reporting, ABC):
    """
    Base class for all RCV variants.
    State variables are listed in __init__.
    Tabulation skeleton is in tabulate()/run_contest()
    """

    @staticmethod
    @save
    def run_rcv(ctx):
        """
        Pass in a ctx dictionary and run the constructor function stored within it
        """
        return ctx['rcv_type'](ctx)

    @staticmethod
    @abstractmethod
    def variant_group():
        """
        Should return the name of the group this rcv variant belongs to. The groups
        determine which contests are written out together in the same file. The groups and
        their corresponding output files are separate from the per-rcv-variant output file that
        are always generated.
        """
        pass

    single_winner_group = 'single_winner'
    multi_winner_group = 'multi_winner'

    # override me
    @abstractmethod
    def _contest_stats(self):
        """
        Every rcv variant must specify which stats list it uses.
        Available lists should be set as rcv base methods or reporting methods.
        """
        pass

    def contest_stats_df(self):
        """
        Return a pandas data frame with a single row. Any functions that take
        'tabulation_num' as parameter return a concatenating string with the function results for each
        tabulation joined together. Any functions that do not take 'tabulation_num' just return their single value.
        """
        tabulation_list = list(range(1, self._tab_num+1))
        dct = {f.__name__:
                   [f(tabulation_num=tabulation_list)]
                   if 'tabulation_num' in signature(f).parameters
                   else [f()]
               for f in self._contest_stats()}
        return pd.DataFrame.from_dict(dct)

    def contest_stats_comments_df(self):
        return pd.DataFrame.from_dict({fun.__name__: [' '.join((fun.__doc__ or '').split())]
                                       for fun in self._contest_stats()})

    # override me
    @abstractmethod
    def _tabulation_stats(self):
        """
        Every rcv variant must specify which stats list it uses.
        Available lists should be set as rcv base methods or reporting methods.
        """
        pass

    def tabulation_stats_df(self):
        """
        Return a pandas data frame with one row per tabulation. Any functions that take
        'tabulation_num' as parameter return the value for each tabulation on that tabulation's row.
        Any functions that do not take 'tabulation_num' just return their single value, repeated on each row.
        """
        tabulation_list = list(range(1, self._tab_num+1))
        dct = {f.__name__:
                   [f(tabulation_num=i) for i in tabulation_list]
                   if 'tabulation_num' in signature(f).parameters
                   else [f() for i in tabulation_list]
               for f in self._tabulation_stats()}
        return pd.DataFrame.from_dict(dct)

    def tabulation_stats_comments_df(self):
        return pd.DataFrame.from_dict({fun.__name__: [' '.join((fun.__doc__ or '').split())]
                                       for fun in self._tabulation_stats()})

    # override me
    @abstractmethod
    def _set_round_winners(self):
        """
        This function should set self.round_winners to the list of candidates that won the round
        """
        pass

    # override me
    @abstractmethod
    def _contest_not_complete(self):
        """
        This function should return True if another round should be evaluated and False
        is the contest should complete.
        """
        pass

    # override me
    @abstractmethod
    def _calc_round_transfer(self):
        """
        This function should append a dictionary to self._tabulations[self._tab_num-1]['transfers'] containing:
        candidate names as keys, plus one key for 'exhaust' and any other keys for transfer categories
        values as round transfer flows.
        """
        pass

    # override me
    def _win_threshold(self):
        """
        This function should return the win threshold used in the contest
        OR return 'dynamic' if threshold changes with each round.
        """
        return 'NA'

    # override me, if ballots should be split/re-weighted prior to next round
    # such as in fractional transfer contests
    def _update_weights(self):
        pass

    # override me, if you need to do multiple iterations of rcv, e.x. utah sequential rcv
    def _run_contest(self):
        # run tabulation
        self._new_tabulation()
        self._tabulate()

    #
    def __init__(self, ctx):

        # STORE CONTEST INFO
        self.ctx = ctx

        # CONTEST INPUTS
        self._n_winners = ctx['num_winners']
        self._multi_winner_rounds = ctx['multi_winner_rounds']
        self._candidate_set = candidates_merged_writeIns(ctx)
        self._cleaned_dict = cleaned_writeIns_merged(ctx)
        self._bs = [{'ranks': ranks, 'weight': weight, 'weight_distrib': []}
                    for ranks, weight in zip(self._cleaned_dict['ranks'], self._cleaned_dict['weight'])]

        self.cache_dict = {}

        # STATE
        # contest-level
        self._tab_num = 0
        self._tabulations = []

        # tabulation-level
        self._inactive_candidates = []
        self._removed_candidates = []
        self._extra_votes = {}

        # round-level
        self._round_num = 0
        self._round_winners = []
        self._round_loser = None

        # RUN
        self._run_contest()

    #
    def _new_tabulation(self):
        """
        Add a new set of results to edited in the tabulations list
        """
        self._tab_num += 1
        new_outcomes = {cand: {'name': cand, 'round_eliminated': None, 'round_elected': None}
                                 for cand in self._candidate_set}
        self._tabulations.append({
            'rounds': [],
            'transfers': [],
            'candidate_outcomes': new_outcomes,
            'final_weights': [],
            'final_weight_distrib': [],
            'final_ranks': [],
            'win_threshold': None})

    #
    def _tabulate(self):
        """
        Run the rounds of rcv contest.
        """

        #############################################
        # CLEAN ROUND BALLOTS
        # remove inactive candidates
        self._clean_round()

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

            # one the first round, mark any candidates with zero votes for elimination
            if self._round_num == 1:
                round_dict = self.get_round_tally_dict(self._round_num, tabulation_num=self._tab_num)
                novote_losers = [cand for cand in self._candidate_set if round_dict[cand] == 0]

                for loser in novote_losers:
                    self._tabulations[self._tab_num-1]['candidate_outcomes'][loser]['round_eliminated'] = 0

                self._inactive_candidates += novote_losers

            #############################################
            # CHECK FOR ROUND WINNERS
            self._set_round_winners()

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
                    {cand: np.NaN for cand in self._candidate_set.union({'exhaust'})})

            #############################################
            # CLEAN ROUND BALLOTS
            # remove inactive candidates
            # don't clean if contest over
            if not_complete:
                self._clean_round()

        # record final ballot weight distributions
        self._tabulations[self._tab_num-1]['final_weight_distrib'] = \
            [b['weight_distrib'] + [(b['ranks'][0], b['weight'])] if b['ranks']
             else b['weight_distrib'] + [('empty', b['weight'])] for b in self._bs]
        # set final weight for each ballot
        self._tabulations[self._tab_num-1]['final_weights'] = [b['weight'] for b in self._bs]
        # set final ranks for each ballot
        self._tabulations[self._tab_num-1]['final_ranks'] = [b['ranks'] for b in self._bs]
        self._tabulations[self._tab_num-1]['win_threshold'] = self._win_threshold()
    #
    def _tally_active_ballots(self):
        """
        tally ballots and reorder tallies
        using active rankings for each ballot,
        skipping empty ballots

        function should:
        - set self.round_results
        - append to self._tabulations[self._tab_num-1]['rounds_trimmed']
        """
        active_round_candidates = set([b['ranks'][0] for b in self._bs if b['ranks']])
        choices = Counter({cand: 0 for cand in active_round_candidates})
        for b in self._bs:
            if b['ranks']:
                choices[b['ranks'][0]] += b['weight']

        round_results = list(zip(*choices.most_common()))

        # update rounds_full
        round_candidates, round_tallies = round_results
        round_candidates = list(round_candidates)
        round_tallies = list(round_tallies)

        # add in any extra votes (such as from threshold candidates)
        for cand in self._extra_votes:
            # add to candidate tally if they are still accumulating new votes (idk when this happens)
            # or append the candidate to the list
            if cand in round_candidates:
                round_tallies[round_candidates.index(cand)] += self._extra_votes[cand]
            else:
                round_candidates.append(cand)
                round_tallies.append(self._extra_votes[cand])

        round_inactive_candidates = [cand for cand in self._candidate_set if cand not in round_candidates]
        round_candidates_full = round_candidates + round_inactive_candidates
        round_tallies_full = round_tallies + [0] * len(round_inactive_candidates)

        tuple_list = [tuple(round_candidates_full), tuple(round_tallies_full)]
        self._tabulations[self._tab_num-1]['rounds'].append(tuple_list)

    #
    def _clean_round(self):
        """
        Remove any newly inactivated candidates from the ballot ranks.
        """
        for inactive_cand in self._inactive_candidates:
            if inactive_cand not in self._removed_candidates:
                self._bs = [{'ranks': remove(inactive_cand, b['ranks']),
                             'weight': b['weight'],
                             'weight_distrib': b['weight_distrib']}
                            for b in self._bs]
                self._removed_candidates.append(inactive_cand)

    #
    def _set_round_loser(self):
        """
        Find candidate from round with least votes.
        If more than one, choose randomly
        """

        # split round results into two tuples (index-matched)
        active_candidates, round_tallies = self.get_round_tally_tuple(self._round_num, self._tab_num,
                                                                      only_round_active_candidates=True, desc_sort=True)
        # find round loser
        loser_count = min(round_tallies)
        # in case of tied losers, 'randomly' choose one to eliminate (the last one in alpha order)
        round_losers = sorted([cand for cand, cand_tally
                               in zip(active_candidates, round_tallies)
                               if cand_tally == loser_count])
        self._round_loser = round_losers[-1]

    #
    def _update_candidates(self):
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
                self._tabulations[self._tab_num-1]['candidate_outcomes'] \
                    [self._round_loser]['round_eliminated'] = self._round_num

        # if contest is over
        else:

            # set all remaining non-winners as eliminated
            remaining_candidates = [d['name'] for d in self._tabulations[self._tab_num-1]['candidate_outcomes'].values()
                                    if d['round_elected'] is None and d['round_eliminated'] is None]
            for cand in remaining_candidates:
                self._tabulations[self._tab_num-1]['candidate_outcomes'][cand]['round_eliminated'] = self._round_num
            self._inactive_candidates += remaining_candidates

    #
    def get_round_tally_tuple(self, round_num, tabulation_num=1, only_round_active_candidates=False, desc_sort=False):
        """
        Return a dictionary containing keys as candidates and values as their vote counts in the round.
        """
        cands, tallies = self._tabulations[tabulation_num-1]['rounds'][round_num-1]

        # remove elected or eliminated candidates
        if only_round_active_candidates:
            outcomes = self._tabulations[tabulation_num-1]['candidate_outcomes']
            active_candidates = [
                cand for cand in outcomes
                if (outcomes[cand]['round_elected'] is None or outcomes[cand]['round_elected'] >= round_num)
                   and (outcomes[cand]['round_eliminated'] is None or outcomes[cand]['round_eliminated'] >= round_num)]
            tallies = [tally for idx, tally in enumerate(tallies) if cands[idx] in active_candidates]
            cands = [cand for cand in cands if cand in active_candidates]

        # sort
        if desc_sort:
            rounds = list(zip(*[(cand, tally) for cand, tally in sorted(zip(cands, tallies), key=lambda x: -x[1])]))
        else:
            rounds = [tuple(cands), tuple(tallies)]

        # pull round tally
        return rounds

    #
    def get_round_tally_dict(self, round_num, tabulation_num=1, only_round_active_candidates=False):
        """
        Return a dictionary containing keys as candidates and values as their vote counts in the round. Includes
        zero vote candidates and those winners remaining at threshold.
        """
        # convert to dict
        return {cand: count for cand, count in
                zip(*self.get_round_tally_tuple(round_num,
                                                tabulation_num,
                                                only_round_active_candidates=only_round_active_candidates))}

    #
    def get_round_transfer_dict(self, round_num, tabulation_num=1):
        """
        Return a dictionary containing keys as candidates + 'exhaust' and values as their round net transfer
        """
        transfers = self._tabulations[tabulation_num-1]['transfers']
        # pull round transfer
        round_transfer = transfers[round_num-1]
        return round_transfer

    #
    def get_candidate_outcomes(self, tabulation_num=1):
        """
        Return a list of dictionaries {keys: name, round_elected, round_eliminated}
        """
        candidate_outcomes = self._tabulations[tabulation_num-1]['candidate_outcomes']
        return list(candidate_outcomes.values())

    #
    def get_final_weights(self, tabulation_num=1):
        """
        Return a list of ballot weights after tabulation, index-matched with ballots
        """
        final_weights = self._tabulations[tabulation_num-1]['final_weights']
        return final_weights

    #
    def get_final_ranks(self, tabulation_num=1):
        """
        Return a list of ballot ranks after tabulation
        """
        final_ranks = self._tabulations[tabulation_num-1]['final_ranks']
        return final_ranks

    #
    def get_final_weight_distrib(self, tabulation_num=1):
        """
        Return a list of ballot weight distributions after tabulation
        """
        final_weights = self._tabulations[tabulation_num-1]['final_weight_distrib']
        return final_weights

    #
    def get_win_threshold(self, tabulation_num=1):
        return self._tabulations[tabulation_num-1]['win_threshold']

    #
    def candidates_with_votes(self, tabulation_num=1):
        """
        Return list of candidates with any ballot weight allotted to them.
        """
        final_weight_distrib = self.get_final_weight_distrib(tabulation_num=tabulation_num)
        final_weight_cands = list(set(t[0] for t in flatten_list(final_weight_distrib)).difference({'empty'}))
        return final_weight_cands

    #
    def n_rounds(self, tabulation_num=1):
        """
        Return the number of rounds, for a given tabulation.
        """
        rounds = self._tabulations[tabulation_num-1]['rounds']
        return len(rounds)

    def n_tabulations(self):
        return self._tab_num

    def compute_contest_stats(self):
        return [f() for f in self._contest_stats()]

    def compute_tabulation_stats(self):
        return [[f(tab_num=i) for f in self._tabulation_stats]
                for i in range(1, self._tab_num+1)]
