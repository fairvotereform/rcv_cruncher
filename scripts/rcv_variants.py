from abc import abstractmethod, ABC
from collections import Counter
import numpy as np

from .definitions import remove
from .tabulation import candidates, cleaned

class RCV(ABC):

    # override me
    @abstractmethod
    def set_round_winners(self):
        """
        This function should set self.round_winners to the list of candidates that won the round
        """
        pass

    # override me
    @abstractmethod
    def calc_round_transfer(self):
        """
        This function should append a dictionary to self.transfers containing:
        candidate names as keys, plus one key for 'exhaust' and any other keys for transfer categories
        values as round transfer flows.
        """
        pass

    # override me
    @abstractmethod
    def contest_not_complete(self):
        """
        This function should return True if another round should be evaluated and False
        is the contest should complete.
        """
        pass

    # override me
    @abstractmethod
    def win_threshold(self):
        """
        This function should return the win threshold used in the contest
        OR return 'dynamic' if threshold changes with each round.
        """
        pass

    # override me, if ballots should be split/re-weighted prior to next round
    # such as in fractional transfer contests
    def update_weights(self):
        pass

    # override me, if you need to do multiple iterations of rcv, e.x. utah sequential rcv
    def tabulate(self):
        self.run_contest()


    def __init__(self, ctx):

        # inputs
        self.num_winners = ctx['num_winners']
        self.multi_winner_rounds = ctx['multi_winner_rounds']
        self.candidate_set = candidates(ctx)
        self.cleaned_dict = cleaned(ctx)
        self.bs = [{'ranks': ranks, 'weight': weight}
                   for ranks, weight in zip(self.cleaned_dict['ranks'], self.cleaned_dict['weight'])]

        # outputs
        self.rounds_trimmed = []
        self.rounds_full = []
        self.transfers = []
        self.candidate_outcomes = {cand: {'name': cand, 'round_eliminated': None, 'round_elected': None}
                                    for cand in self.candidate_set}
        self.final_weights = []

        # round variables
        self.extra_votes = {}
        self.round_num = 0
        self.round_results = []
        self.round_winners = []
        self.round_loser = None
        self.inactive_candidates = []
        self.removed_candidates = []

        # run the contest
        self.tabulate()

    #
    def results(self):
        d = {'rounds_trimmed': self.rounds_trimmed,
             'rounds_full': self.rounds_full,
             'transfers': self.transfers,
             'candidate_outcomes': self.candidate_outcomes.values(),
             'final_weights': self.final_weights}
        return d

    #
    def run_contest(self):
        """
        Run the rounds of rcv contest.
        """

        while self.contest_not_complete():
            self.round_num += 1

            #############################################
            # CLEAR LAST ROUND VALUES
            self.round_results = []
            self.round_winners = []
            self.round_loser = None

            #############################################
            # CLEAN ROUND BALLOTS
            # remove inactive candidates
            self.clean_round()

            #############################################
            # COUNT ROUND RESULTS
            self.tally_active_ballots()

            # one the first round, mark any candidates with zero votes for elimination
            if self.round_num == 1:
                round_candidates, round_tallies = self.round_results
                novote_losers = [cand for cand in self.candidate_set if cand not in round_candidates]

                for loser in novote_losers:
                    self.candidate_outcomes[loser]['round_eliminated'] = 0

                self.inactive_candidates += novote_losers

            #############################################
            # CHECK FOR ROUND WINNERS
            self.set_round_winners()

            #############################################
            # IDENTIFY ROUND LOSER
            self.set_round_loser()

            #############################################
            # UPDATE inactive candidate list using round winner/loser
            self.update_candidates()

            #############################################
            # UPDATE WEIGHTS
            # don't update if contest over
            if self.contest_not_complete():
                self.update_weights()

            #############################################
            # CALC ROUND TRANSFER
            if self.contest_not_complete():
                self.calc_round_transfer()
            else:
                self.transfers.append({cand: np.NaN for cand in self.candidate_set.union({'exhaust'})})

        # set final weight for each ballot
        self.final_weights = [b['weight'] for b in self.bs]

    #
    def tally_active_ballots(self):
        """
        tally ballots and reorder tallies
        using active rankings for each ballot,
        skipping empty ballots

        function should:
        - set self.round_results
        - append to self.rounds_trimmed
        """
        active_round_candidates = set([b['ranks'][0] for b in self.bs if b['ranks']])
        choices = Counter({cand: 0 for cand in active_round_candidates})
        for b in self.bs:
            if b['ranks']:
                choices[b['ranks'][0]] += b['weight']

        round_results = list(zip(*choices.most_common()))

        # set self.round_results
        self.round_results = round_results

        # set rounds_trimmed
        self.rounds_trimmed.append(self.round_results)

        # update rounds_full
        round_candidates, round_tallies = self.round_results
        round_candidates = list(round_candidates)
        round_tallies = list(round_tallies)

        # add in any extra votes (such as from threshold candidates)
        for cand in self.extra_votes:
            round_candidates.append(cand)
            round_tallies.append(self.extra_votes[cand])

        round_inactive_candidates = [cand for cand in self.candidate_set if cand not in round_candidates]
        round_candidates_full = round_candidates + round_inactive_candidates
        round_tallies_full = round_tallies + [0] * len(round_inactive_candidates)

        self.rounds_full.append([tuple(round_candidates_full), tuple(round_tallies_full)])

    #
    def clean_round(self):
        """
        Remove any newly inactivated candidates from the ballot ranks.
        """
        for inactive_cand in self.inactive_candidates:
            if inactive_cand not in self.removed_candidates:
                self.bs = [{'ranks': remove(inactive_cand, b['ranks']), 'weight': b['weight']} for b in self.bs]
                self.removed_candidates.append(inactive_cand)

    #
    def set_round_loser(self):
        """
        Find candidate from round with least votes.
        If more than one, choose randomly
        """
        # split round results into two tuples (index-matched)
        round_candidates, round_tallies = self.round_results

        # find round loser
        loser_count = min(round_tallies)
        # in case of tied losers, 'randomly' choose one to eliminate (the last one in alpha order)
        round_losers = sorted([cand for cand, cand_tally
                               in zip(round_candidates, round_tallies)
                               if cand_tally == loser_count])
        self.round_loser = round_losers[-1]

    #
    def update_candidates(self):
        """
        Update candidate outcomes
        Assume winners are to become inactive, otherwise inactivate loser
        """

        # update winner outcomes
        for winner in self.round_winners:
            self.candidate_outcomes[winner]['round_elected'] = self.round_num
            self.inactive_candidates.append(winner)

        # if contest is not over
        if self.contest_not_complete():

            # if no winner, add loser
            if not self.round_winners:
                self.inactive_candidates.append(self.round_loser)
                self.candidate_outcomes[self.round_loser]['round_eliminated'] = self.round_num

        # if contest is over
        else:

            # set all remaining non-winners as eliminated
            remaining_candidates = [d['name'] for d in self.candidate_outcomes.values()
                                    if d['round_elected'] is None and d['round_eliminated'] is None]
            for cand in remaining_candidates:
                self.candidate_outcomes[cand]['round_eliminated'] = self.round_num
            self.inactive_candidates += remaining_candidates

    #
    def get_round_dict(self, round_num):
        """
        Return a dictionary containing keys as candidates and values as their vote counts in the round
        """
        round_results = self.rounds_full[round_num-1]
        return {cand: count for cand, count in zip(*round_results)}

    #
    def n_rounds(self):
        """
        Return the number of rounds.
        """
        return len(self.rounds_full)


class rcv_single_winner(RCV):

    #
    def set_round_winners(self):
        """
        This function should set self.round_winners to the list of candidates that won the round

        single winner rules:
        - winner is candidate with > 50% of round vote
        """
        round_candidates, round_tallies = self.round_results
        if round_tallies[0]*2 > sum(round_tallies):
            self.round_winners = [round_candidates[0]]


    def calc_round_transfer(self):
        """
        This function should append a dictionary to self.transfers containing:
        candidate names as keys, plus one key for 'exhaust' and any other keys for transfer categories
        values as round transfer flows.

        rules:
        - transfer votes from round loser
        """
        # calculate transfer
        transfer_dict = {cand: 0 for cand in self.candidate_set.union({'exhaust'})}
        for b in self.bs:
            if len(b['ranks']) > 0 and b['ranks'][0] == self.round_loser:
                if len(b['ranks']) > 1:
                    transfer_dict[b['ranks'][1]] += b['weight']
                else:
                    transfer_dict['exhaust'] += b['weight']

        transfer_dict[self.round_loser] = sum(transfer_dict.values()) * -1
        self.transfers.append(transfer_dict)

    #
    def contest_not_complete(self):
        """
        This function should return True if another round should be evaluated and False
        is the contest should complete.

        single winner rules:
        - Stop contest once a winner is found.
        """
        all_rounds_elected = [d['round_elected'] is not None for d in self.candidate_outcomes.values()]
        if any(all_rounds_elected):
            return False
        else:
            return True

    #
    def win_threshold(self):
        """
        This function should return the win threshold used in the contest
        OR return 'dynamic' if threshold changes for each possible winner.

        rules:
        - winner has more than half the active votes in a round
        """
        last_round_active_votes = sum(self.get_round_dict(self.n_rounds()).values())
        return last_round_active_votes/2


class stv_whole_ballot:
    pass


class stv_fractional_ballot(RCV):

    #
    def set_round_winners(self):
        """
        This function should set self.round_winners to the list of candidates that won the round

        rules:
        - candidate is winner when they receive more than threshold.
        - last #winners candidates are automatically elected.
        """

        # process of elimination?
        # If 2 candidates have been elected and two more are still needed BUT only 2 remain,
        # then they are automatically elected.
        round_candidates, _ = self.round_results
        n_remaining_candidates = len(round_candidates)
        n_elected_candidates = len([d for d in self.candidate_outcomes.values()
                                    if d['round_elected'] is not None])
        if n_remaining_candidates + n_elected_candidates == self.num_winners:
            self.round_winners = round_candidates
            return

        # any threshold winners?
        threshold = self.win_threshold()
        all_winners = [cand for cand, tally in zip(*self.round_results) if tally > threshold]
        if self.multi_winner_rounds:
            self.round_winners = all_winners
        else:
            self.round_winners = [all_winners[0]]


    def update_weights(self):
        """
        If surplus needs to be transferred, change weights on winner ballots to reflect remaining
        active ballot proportion.

        rules:
        - reduce weights of ballots ranking the winner by the amount
        """

        round_dict = self.get_round_dict(self.round_num)
        threshold = self.win_threshold()

        for winner in self.round_winners:

            # fractional surplus to transfer from each winner ballot
            surplus_percent = (round_dict[winner] - threshold) / round_dict[winner]

            # if surplus to transfer is non-zero
            if surplus_percent:

                # which ballots had the winner on top
                # and need to be fractionally split
                new = []
                for b in self.bs:
                    if b['ranks'] and b['ranks'][0] == winner:
                        new.append({'ranks': b['ranks'], 'weight': b['weight'] * surplus_percent})
                    else:
                        new.append(b)
                self.bs = new

            # record threshold level vote count in extra votes for winner
            # to ensure they get added back into later round counts
            self.extra_votes.update({winner: threshold})

    #
    def calc_round_transfer(self):
        """
        This function should append a dictionary to self.transfers containing:
        candidate names as keys, plus one key for 'exhaust' and any other keys for transfer categories
        values as round transfer flows.

        rules:
        - transfer votes from round loser or winner
        """
        if self.round_winners:
            transfer_candidates = self.round_winners
        else:
            transfer_candidates = [self.round_loser]

        # calculate transfer
        transfer_dict = {cand: 0 for cand in self.candidate_set.union({'exhaust'})}
        for b in self.bs:
            if len(b['ranks']) > 0 and b['ranks'][0] in transfer_candidates:

                if len(b['ranks']) > 1:
                    transfer_dict[b['ranks'][1]] += b['weight']
                else:
                    transfer_dict['exhaust'] += b['weight']

                # mark transfer outflow
                transfer_dict[b['ranks'][0]] += b['weight'] * -1

        self.transfers.append(transfer_dict)

    #
    def contest_not_complete(self):
        """
        This function should return True if another round should be evaluated and False
        is the contest should complete.

        rules:
        - Stop once num_winners are elected.
        """
        all_rounds_elected = [d['round_elected'] is not None for d in self.candidate_outcomes.values()]
        if sum(all_rounds_elected) == self.num_winners:
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
        if not self.rounds_full:
            print("Threshold depends on first round count. " +
                  "Don't call win_threshold() before first call to tally_active_ballots()")
            raise RuntimeError

        first_round_active_votes = sum(self.get_round_dict(1).values())
        return first_round_active_votes / (self.num_winners + 1)


class sequential_rcv:
    pass

class rcv_multiWinner_thresh15(RCV):

    #
    def set_round_winners(self):
        """
        This function should set self.round_winners to the list of candidates that won the round

        single winner rules:
        - winner is candidate with > 50% of round vote
        """
        round_candidates, round_tallies = self.round_results
        threshold = sum(round_tallies) * 0.15
        if all(i > threshold for i in round_tallies):
            self.round_winners = list(round_candidates)


    def calc_round_transfer(self):
        """
        This function should append a dictionary to self.transfers containing:
        candidate names as keys, plus one key for 'exhaust' and any other keys for transfer categories
        values as round transfer flows.

        rules:
        - transfer votes from round loser
        """

        # calculate transfer
        transfer_dict = {cand: 0 for cand in self.candidate_set.union({'exhaust'})}
        for b in self.bs:
            if len(b['ranks']) > 0 and b['ranks'][0] == self.round_loser:
                if len(b['ranks']) > 1:
                    transfer_dict[b['ranks'][1]] += b['weight']
                else:
                    transfer_dict['exhaust'] += b['weight']

        transfer_dict[self.round_loser] = sum(transfer_dict.values()) * -1
        self.transfers.append(transfer_dict)

    #
    def contest_not_complete(self):
        """
        This function should return True if another round should be evaluated and False
        is the contest should complete.

        single winner rules:
        - Contest is over when all winner are found, they are all 'elected' at once.
        """
        all_rounds_elected = [d['round_elected'] is not None for d in self.candidate_outcomes.values()]
        if any(all_rounds_elected):
            return False
        else:
            return True

    #
    def win_threshold(self):
        """
        This function should return the win threshold used in the contest
        OR return 'dynamic' if threshold changes for each possible winner.

        rules:
        - 15% of round votes
        """
        last_round_active_votes = sum(self.get_round_dict(self.n_rounds()).values())
        return last_round_active_votes * 0.15


class rcv_multiWinner_thresh15_keepUndeclared(rcv_multiWinner_thresh15):

    def set_round_loser(self):
        """
        Find candidate from round with least votes.
        If more than one, choose randomly

        rules:
        - '(undeclared)' candidate cannot lose
        """
        # split round results into two tuples (index-matched)
        round_candidates, round_tallies = self.round_results

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
        self.round_loser = round_losers[-1]
