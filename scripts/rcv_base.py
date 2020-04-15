from abc import abstractmethod, ABC
from collections import Counter
import numpy as np
import pandas as pd
from inspect import signature

from .rcv_reporting import RCV_Reporting
from .definitions import remove
from .misc_tabulation import candidates, cleaned


class RCV(ABC, RCV_Reporting):
    """
    Base class for all RCV variants.
    State variables are listed in __init__.
    Tabulation skeleton is in tabulate()/run_contest()
    """

    @abstractmethod
    def variant_group(self):
        """
        Should return the name of the group this rcv variant belongs to. The groups
        determine which contests are written out together in the same file. The groups and
        their corresponding output files are separate from the per-rcv-variant output file that
        are always generated.
        """
        pass

    single_winner_group = -1
    multi_winner_group = -2

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
    def win_threshold(self):
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
        self._candidate_set = candidates(ctx)
        self._cleaned_dict = cleaned(ctx)
        self._bs = [{'ranks': ranks, 'weight': weight}
                    for ranks, weight in zip(self._cleaned_dict['ranks'], self._cleaned_dict['weight'])]

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
        self._round_results = []
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
            'rounds_trimmed': [],
            'rounds_full': [],
            'transfers': [],
            'candidate_outcomes': new_outcomes,
            'final_weights': []})

    #
    def _tabulate(self):
        """
        Run the rounds of rcv contest.
        """

        while self._contest_not_complete():
            self._round_num += 1

            #############################################
            # CLEAR LAST ROUND VALUES
            self._round_results = []
            self._round_winners = []
            self._round_loser = None

            #############################################
            # CLEAN ROUND BALLOTS
            # remove inactive candidates
            self._clean_round()

            #############################################
            # COUNT ROUND RESULTS
            self._tally_active_ballots()

            # one the first round, mark any candidates with zero votes for elimination
            if self._round_num == 1:
                round_candidates, round_tallies = self._round_results
                novote_losers = [cand for cand in self._candidate_set if cand not in round_candidates]

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

            #############################################
            # UPDATE WEIGHTS
            # don't update if contest over
            if self._contest_not_complete():
                self._update_weights()

            #############################################
            # CALC ROUND TRANSFER
            if self._contest_not_complete():
                self._calc_round_transfer()
            else:
                self._tabulations[self._tab_num-1]['transfers'].append(
                    {cand: np.NaN for cand in self._candidate_set.union({'exhaust'})})

        # set final weight for each ballot
        self._tabulations[self._tab_num-1]['final_weights'] = [b['weight'] for b in self._bs]

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

        # set self.round_results
        self._round_results = round_results

        # set rounds_trimmed
        self._tabulations[self._tab_num-1]['rounds_trimmed'].append(self._round_results)

        # update rounds_full
        round_candidates, round_tallies = self._round_results
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

        self._tabulations[self._tab_num-1]['rounds_full'].append(
            [tuple(round_candidates_full), tuple(round_tallies_full)])

    #
    def _clean_round(self):
        """
        Remove any newly inactivated candidates from the ballot ranks.
        """
        for inactive_cand in self._inactive_candidates:
            if inactive_cand not in self._removed_candidates:
                self._bs = [{'ranks': remove(inactive_cand, b['ranks']), 'weight': b['weight']} for b in self._bs]
                self._removed_candidates.append(inactive_cand)

    #
    def _set_round_loser(self):
        """
        Find candidate from round with least votes.
        If more than one, choose randomly
        """
        # split round results into two tuples (index-matched)
        round_candidates, round_tallies = self._round_results

        # find round loser
        loser_count = min(round_tallies)
        # in case of tied losers, 'randomly' choose one to eliminate (the last one in alpha order)
        round_losers = sorted([cand for cand, cand_tally
                               in zip(round_candidates, round_tallies)
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
    def get_round_trimmed_tally_tuple(self, round_num, tabulation_num=1):
        """
        Return a tuple containing a list of candidates and a list of their respective vote totals. Only candidates
        that accumulated new votes in this round are included. Lists are sorted in decreasing order.
        """
        rounds_trimmed, _, _, _, _ = self._tabulations[tabulation_num-1]
        # pull round tally
        return rounds_trimmed[round_num-1]

    #
    def get_round_full_tally_tuple(self, round_num, tabulation_num=1):
        """
        Return a dictionary containing keys as candidates and values as their vote counts in the round. Includes
        zero vote candidates and those winners remaining at threshold.
        """
        _, rounds_full, _, _, _ = self._tabulations[tabulation_num-1]
        # pull round tally
        return rounds_full[round_num-1]

    #
    def get_round_trimmed_tally_dict(self, round_num, tabulation_num=1):
        """
        Return a dictionary containing keys as candidates and values as their vote counts in the round. Only candidates
        that accumulated new votes in this round are included.
        """
        # convert to dict
        return {cand: count for cand, count in zip(*self.get_round_trimmed_tally_tuple(round_num, tabulation_num))}

    #
    def get_round_full_tally_dict(self, round_num, tabulation_num=1):
        """
        Return a dictionary containing keys as candidates and values as their vote counts in the round. Includes
        zero vote candidates and those winners remaining at threshold.
        """
        # convert to dict
        return {cand: count for cand, count in zip(*self.get_round_full_tally_tuple(round_num, tabulation_num))}

    #
    def get_round_transfer_dict(self, round_num, tabulation_num=1):
        """
        Return a dictionary containing keys as candidates + 'exhaust' and values as their round net transfer
        """
        _, _, transfers, _, _ = self._tabulations[tabulation_num-1]
        # pull round transfer
        round_transfer = transfers[round_num-1]
        return round_transfer

    #
    def get_candidate_outcomes(self, tabulation_num=1):
        """
        Return a list of dictionaries {keys: name, round_elected, round_eliminated}
        """
        _, _, _, candidate_outcomes, _ = self._tabulations[tabulation_num-1]
        return candidate_outcomes.values()

    #
    def get_final_weights(self, tabulation_num=1):
        """
        Return a list of ballot weights after tabulation, index-matched with ballots
        """
        _, _, _, _, final_weights = self._tabulations[tabulation_num-1]
        return final_weights

    #
    def n_rounds(self, tabulation_num=1):
        """
        Return the number of rounds, for a given tabulation.
        """
        _, rounds_full, _, _, _ = self._tabulations[tabulation_num-1]
        return len(rounds_full)

    def n_tabulations(self):
        return self._tab_num

    def compute_contest_stats(self):
        return [f() for f in self._contest_stats()]

    def compute_tabulation_stats(self):
        return [[f(tab_num=i) for f in self._tabulation_stats]
                for i in range(1, self._tab_num+1)]