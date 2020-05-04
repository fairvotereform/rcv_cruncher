"""
This file contains classes for RCV contest types.
"""
from copy import copy

from .rcv_base import RCV
#from .rcv_reporting import RCV_Reporting
from inspect import isclass, signature
import pandas as pd

def get_rcv_dict():
    """
    Return dictionary of rcv classes, class_name: class_obj (constructor function)
    """
    return {key: value for key, value in globals().items()
            if isclass(value) and key != "get_parser_dict" and value.__module__ == __name__}


class rcv_single_winner(RCV):
    """
    Single winner rcv contest.
    - Winner is candidate to first achieve more than half the active round votes.
    - Votes are transferred from losers each round.
    """
    def __init__(self, ctx):
        super().__init__(ctx)

    def variant_group(self):
        return self.single_winner_group

    def _contest_stats(self):
        """
        Every rcv variant must specify which stats list it uses.
        Available lists should be set as rcv base methods or reporting methods.
        """
        return self.single_winner_stats()

    def _tabulation_stats(self):
        """
        Every rcv variant must specify which stats list it uses.
        Available lists should be set as rcv base methods or reporting methods.
        """
        return self.single_winner_stats()

    #
    def _set_round_winners(self):
        """
        This function should set self._round_winners to the list of candidates that won the round

        single winner rules:
        - winner is candidate with > 50% of round vote
        """
        round_candidates, round_tallies = self._round_results
        if round_tallies[0]*2 > sum(round_tallies):
            self._round_winners = [round_candidates[0]]


    def _calc_round_transfer(self):
        """
        This function should append a dictionary to self.transfers containing:
        candidate names as keys, plus one key for 'exhaust' and any other keys for transfer categories
        values as round transfer flows.

        rules:
        - transfer votes from round loser
        """
        # calculate transfer
        transfer_dict = {cand: 0 for cand in self._candidate_set.union({'exhaust'})}
        for b in self._bs:
            if len(b['ranks']) > 0 and b['ranks'][0] == self._round_loser:
                if len(b['ranks']) > 1:
                    transfer_dict[b['ranks'][1]] += b['weight']
                else:
                    transfer_dict['exhaust'] += b['weight']

        transfer_dict[self._round_loser] = sum(transfer_dict.values()) * -1
        self._tabulations[self._tab_num-1]['transfers'].append(transfer_dict)
        
    #
    def _contest_not_complete(self):
        """
        This function should return True if another round should be evaluated and False
        is the contest should complete.

        single winner rules:
        - Stop contest once a winner is found.
        """
        candidate_outcomes = self._tabulations[self._tab_num-1]['candidate_outcomes']
        all_rounds_elected = [d['round_elected'] is not None for d in candidate_outcomes.values()]
        if any(all_rounds_elected):
            return False
        else:
            return True


class sequential_rcv(rcv_single_winner):
    """
    Sequential RCV elections used to elect multiple winners. Winners are elected one-by-one in repeated single winner
    RCV elections, each time with the previous winners effectively treated as eliminated.
    """
    def __init__(self, ctx):
        super().__init__(ctx)

    def variant_group(self):
        return self.multi_winner_group

    def _contest_stats(self):
        """
        Every rcv variant must specify which stats list it uses.
        Available lists should be set as rcv base methods or reporting methods.
        """
        return self.multi_winner_stats()

    def _tabulation_stats(self):
        """
        Every rcv variant must specify which stats list it uses.
        Available lists should be set as rcv base methods or reporting methods.
        """
        return self.single_winner_stats()

    # overwrite tabulate to run multiple single winner elections
    def _run_contest(self):

        winners = []
        self._tab_num = 0
        self._tabulations = []
        
        # continue until the number of winners is reached OR until candidates run out
        while len(winners) != self._n_winners and len(self._candidate_set - set(winners)) != 0:
            
            self._new_tabulation()

            # reset inputs
            self._bs = [{'ranks': ranks, 'weight': weight}
                       for ranks, weight in zip(self._cleaned_dict['ranks'], self._cleaned_dict['weight'])]

            # STATE
            # tabulation-level
            self._inactive_candidates = copy(winners) # mark previous iteration winners as inactive
            self._removed_candidates = []
            self._extra_votes = {}

            # round-level
            self._round_num = 0

            # calculate single winner rcv
            self._tabulate()

            # get winner and store results
            tabulation_outcomes = self._tabulations[self._tab_num-1]['candidate_outcomes']
            winners.append([d['name'] for d in tabulation_outcomes.values() if d['round_elected'] is not None][0])


class until2rcv(rcv_single_winner):
    """
    Run single winner contest all the way down to final two canidates.
    """
    def __init__(self, ctx):
        super().__init__(ctx)

    def variant_group(self):
        return self.single_winner_group

    def _contest_stats(self):
        """
        Every rcv variant must specify which stats list it uses.
        Available lists should be set as rcv base methods or reporting methods.
        """
        return self.single_winner_stats()

    def _tabulation_stats(self):
        """
        Every rcv variant must specify which stats list it uses.
        Available lists should be set as rcv base methods or reporting methods.
        """
        return self.single_winner_stats()

    #
    def _set_round_winners(self):
        """
        This function should set self._round_winners to the list of candidates that won the round

        single winner rules:
        - winner is candidate with more votes when there are only two candidates left
        """
        round_candidates, round_tallies = self._round_results
        if len(round_candidates) == 2:
            self._round_winners = [round_candidates[0]]


# class stv_whole_ballot:
#     pass


class stv_fractional_ballot(RCV):
    """
    Multi-winner elections with fractional ballot transfer.
    - Win threshold is set as the (# first round votes)/(# of seats + 1).
    - Any winner is eliminated and has their surplus redistributed. Percent of each
    ballot redistributed is equal to (# of votes winner has -- minus the threshold)/(# of votes winner has).
    - If no winners in round, candidate with least votes in a round is eliminated and has votes transferred.
    """
    def __init__(self, ctx):
        super().__init__(ctx)

    def variant_group(self):
        return self.multi_winner_group

    def _contest_stats(self):
        """
        Every rcv variant must specify which stats list it uses.
        Available lists should be set as rcv base methods or reporting methods.
        """
        return self.multi_winner_stats()

    def _tabulation_stats(self):
        """
        Every rcv variant must specify which stats list it uses.
        Available lists should be set as rcv base methods or reporting methods.
        """
        return self.multi_winner_stats()

    #
    def _set_round_winners(self):
        """
        This function should set self._round_winners to the list of candidates that won the round

        rules:
        - candidate is winner when they receive more than threshold.
        - last #winners candidates are automatically elected.
        """

        # process of elimination?
        # If 2 candidates have been elected and two more are still needed BUT only 2 remain,
        # then they are automatically elected.
        candidate_outcomes = self._tabulations[self._tab_num-1]['candidate_outcomes']
        round_candidates, _ = self._round_results
        n_remaining_candidates = len(round_candidates)
        n_elected_candidates = len([d for d in candidate_outcomes.values()
                                    if d['round_elected'] is not None])
        if n_remaining_candidates + n_elected_candidates == self._n_winners:
            self._round_winners = round_candidates
            return

        # any threshold winners?
        threshold = self.win_threshold()
        all_winners = [cand for cand, tally in zip(*self._round_results) if tally > threshold]
        if self._multi_winner_rounds:
            self._round_winners = all_winners
        else:
            self._round_winners = [all_winners[0]]


    def _update_weights(self):
        """
        If surplus needs to be transferred, change weights on winner ballots to reflect remaining
        active ballot proportion.

        rules:
        - reduce weights of ballots ranking the winner by the amount
        """

        round_dict = self.get_round_full_tally_dict(self._round_num, tabulation_num=self._tab_num)
        threshold = self.win_threshold()

        for winner in self._round_winners:

            # fractional surplus to transfer from each winner ballot
            surplus_percent = (round_dict[winner] - threshold) / round_dict[winner]

            # if surplus to transfer is non-zero
            if surplus_percent:

                # which ballots had the winner on top
                # and need to be fractionally split
                new = []
                for b in self._bs:
                    if b['ranks'] and b['ranks'][0] == winner:
                        new.append({'ranks': b['ranks'], 'weight': b['weight'] * surplus_percent})
                    else:
                        new.append(b)
                self._bs = new

            # record threshold level vote count in extra votes for winner
            # to ensure they get added back into later round counts
            self._extra_votes.update({winner: threshold})

    #
    def _calc_round_transfer(self):
        """
        This function should append a dictionary to self.transfers containing:
        candidate names as keys, plus one key for 'exhaust' and any other keys for transfer categories
        values as round transfer flows.

        rules:
        - transfer votes from round loser or winner
        """
        if self._round_winners:
            transfer_candidates = self._round_winners
        else:
            transfer_candidates = [self._round_loser]

        # calculate transfer
        transfer_dict = {cand: 0 for cand in self._candidate_set.union({'exhaust'})}
        for b in self._bs:
            if len(b['ranks']) > 0 and b['ranks'][0] in transfer_candidates:

                if len(b['ranks']) > 1:
                    transfer_dict[b['ranks'][1]] += b['weight']
                else:
                    transfer_dict['exhaust'] += b['weight']

                # mark transfer outflow
                transfer_dict[b['ranks'][0]] += b['weight'] * -1

        self._tabulations[self._tab_num-1]['transfers'].append(transfer_dict)

    #
    def _contest_not_complete(self):
        """
        This function should return True if another round should be evaluated and False
        is the contest should complete.

        rules:
        - Stop once num_winners are elected.
        """
        candidate_outcomes = self._tabulations[self._tab_num-1]['candidate_outcomes']
        all_rounds_elected = [d['round_elected'] is not None for d in candidate_outcomes.values()]
        if sum(all_rounds_elected) == self._n_winners:
            return False
        else:
            return True

    #
    def win_threshold(self):
        """
        This function should return the win threshold used in the contest
        OR return 'dynamic' if threshold changes for each possible winner.

        rules:
        - # of votes in first round /(# to elect + 1)
        """
        if not self._tabulations[self._tab_num-1]['rounds_full']:
            print("Threshold depends on first round count. " +
                  "Don't call win_threshold() before first call to tally_active_ballots()")
            raise RuntimeError

        first_round_dict = self.get_round_full_tally_dict(1, tabulation_num=self._tab_num)
        first_round_active_votes = sum(first_round_dict.values())
        return first_round_active_votes / (self._n_winners + 1)


class rcv_multiWinner_thresh15(RCV):
    """
    Multi winner contest. When all candidates in a round have more than 15% of the round votes, they are all winners.
    - In a no winner round, the candidate with least votes is eliminated and ballots transferred.
    """
    def __init__(self, ctx):
        super().__init__(ctx)

    def variant_group(self):
        return self.multi_winner_group

    def _contest_stats(self):
        """
        Every rcv variant must specify which stats list it uses.
        Available lists should be set as rcv base methods or reporting methods.
        """
        return self.multi_winner_stats()

    def _tabulation_stats(self):
        """
        Every rcv variant must specify which stats list it uses.
        Available lists should be set as rcv base methods or reporting methods.
        """
        return self.multi_winner_stats()

    #
    def _set_round_winners(self):
        """
        This function should set self._round_winners to the list of candidates that won the round

        single winner rules:
        - winner is candidate with > 50% of round vote
        """
        round_candidates, round_tallies = self._round_results
        threshold = sum(round_tallies) * 0.15
        if all(i > threshold for i in round_tallies):
            self._round_winners = list(round_candidates)


    def _calc_round_transfer(self):
        """
        This function should append a dictionary to self.transfers containing:
        candidate names as keys, plus one key for 'exhaust' and any other keys for transfer categories
        values as round transfer flows.

        rules:
        - transfer votes from round loser
        """

        # calculate transfer
        transfer_dict = {cand: 0 for cand in self._candidate_set.union({'exhaust'})}
        for b in self._bs:
            if len(b['ranks']) > 0 and b['ranks'][0] == self._round_loser:
                if len(b['ranks']) > 1:
                    transfer_dict[b['ranks'][1]] += b['weight']
                else:
                    transfer_dict['exhaust'] += b['weight']

        transfer_dict[self._round_loser] = sum(transfer_dict.values()) * -1
        self._tabulations[self._tab_num-1]['transfers'].append(transfer_dict)

    #
    def _contest_not_complete(self):
        """
        This function should return True if another round should be evaluated and False
        is the contest should complete.

        single winner rules:
        - Contest is over when all winner are found, they are all 'elected' at once.
        """
        candidate_outcomes = self._tabulations[self._tab_num-1]['candidate_outcomes']
        all_rounds_elected = [d['round_elected'] is not None for d in candidate_outcomes.values()]
        if any(all_rounds_elected):
            return False
        else:
            return True


class rcv_multiWinner_thresh15_keepUndeclared(rcv_multiWinner_thresh15):
    """
    Multi winner contest. When all candidates in a round have more than 15% of the round votes, they are all winners.
    - In a no winner round, the candidate with least votes is eliminated and ballots transferred.
    - If there is a candidate called "(undeclared)" it is treated as un-defeatable.
    """
    def __init__(self, ctx):
        super().__init__(ctx)

    def _set_round_loser(self):
        """
        Find candidate from round with least votes.
        If more than one, choose randomly

        rules:
        - '(undeclared)' candidate cannot lose
        """
        # split round results into two tuples (index-matched)
        round_candidates, round_tallies = self._round_results

        # '(undeclared)' cannot be a loser
        undeclared_idx = round_candidates.index('(undeclared)')
        del round_candidates[undeclared_idx]
        del round_tallies[undeclared_idx]

        # find round loser
        loser_count = min(round_tallies)
        # in case of tied losers, 'randomly' choose one to eliminate (the last one in alpha order)
        round_losers = sorted([cand for cand, cand_tally
                               in zip(round_candidates, round_tallies)
                               if cand_tally == loser_count])
        self._round_loser = round_losers[-1]

