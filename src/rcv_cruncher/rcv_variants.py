
import abc
import copy
import decimal

import rcv_cruncher.rcv_base as rcv_base
import rcv_cruncher.util as util


def get_rcv_dict():
    """
    Return dictionary of rcv classes, class_name: class_obj (constructor function)
    """
    return {
        'until2rcv': until2rcv,
        'stv_whole_ballot': stv_whole_ballot,
        'stv_fractional_ballot': stv_fractional_ballot,
        'sequential_rcv': sequential_rcv,
        'rcv_single_winner': rcv_single_winner,
        'rcv_multiWinner_thresh15': rcv_multiWinner_thresh15
    }


class rcv_single_winner(rcv_base.RCV):
    """
    Single winner rcv contest.
    - Winner is candidate to first achieve more than half the active round votes.
    - Votes are transferred from losers each round.
    """
    def __init__(self, ctx):
        super().__init__(ctx)

    @staticmethod
    def variant_group():
        return rcv_base.RCV.single_winner_group

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
        round_candidates, round_tallies = self.get_round_tally_tuple(self._round_num, self._tab_num,
                                                                     only_round_active_candidates=True, desc_sort=True)
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

    @staticmethod
    def variant_group():
        return rcv_single_winner.multi_winner_group

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

    # overwrite _run_contest to run multiple single winner elections
    def _run_contest(self):

        winners = []
        self._tab_num = 0
        self._tabulations = []

        # continue until the number of winners is reached OR until candidates run out
        while len(winners) != self._n_winners and len(self._candidate_set - set(winners)) != 0:

            self._new_tabulation()

            # reset inputs
            self._bs = [{'ranks': ranks, 'weight': weight, 'weight_distrib': []}
                        for ranks, weight in zip(self._cleaned_dict['ranks'], self._cleaned_dict['weight'])]

            # STATE
            # tabulation-level
            self._inactive_candidates = copy.copy(winners)  # mark previous iteration winners as inactive
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
        round_candidates, round_tallies = self.get_round_tally_tuple(self._round_num, self._tab_num,
                                                                     only_round_active_candidates=True, desc_sort=True)
        if len(round_candidates) == 2:
            self._round_winners = [round_candidates[0]]


class stv(rcv_base.RCV, abc.ABC):

    def __init__(self, ctx):
        super().__init__(ctx)

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
        round_candidates, round_tally = self.get_round_tally_tuple(self._round_num, self._tab_num,
                                                                   only_round_active_candidates=True, desc_sort=True)
        n_remaining_candidates = len([d for d in candidate_outcomes.values()
                                      if d['round_elected'] is None and d['round_eliminated'] is None])
        n_elected_candidates = len([d for d in candidate_outcomes.values()
                                    if d['round_elected'] is not None])
        if n_remaining_candidates + n_elected_candidates == self._n_winners:
            self._round_winners = round_candidates
            return

        # any threshold winners?
        threshold = self._win_threshold()
        all_winners = [cand for cand, tally in zip(round_candidates, round_tally) if tally > threshold]
        if all_winners and self._multi_winner_rounds:
            self._round_winners = all_winners
        elif all_winners:
            self._round_winners = [all_winners[0]]

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

    def _win_threshold(self):
        """
        This function should return the win threshold used in the contest
        OR return 'dynamic' if threshold changes for each possible winner.

        rules:
        - # of votes in first round /(# to elect + 1)
        """
        if not self._tabulations[self._tab_num-1]['rounds']:
            print("Threshold depends on first round count. " +
                  "Don't call win_threshold() before first call to tally_active_ballots()")
            raise RuntimeError

        first_round_dict = self.get_round_tally_dict(1, tabulation_num=self._tab_num)
        first_round_active_votes = sum(first_round_dict.values())
        return int((first_round_active_votes / (self._n_winners + 1)) + 1)

    def _tabulation_stats(self):
        return self.multi_winner_stats()

    @staticmethod
    def variant_group():
        return rcv_base.RCV.multi_winner_group

    def _contest_stats(self):
        return self.multi_winner_stats()


class stv_whole_ballot(stv):

    def __init__(self, ctx):
        super().__init__(ctx)
        if len(set(self._cleaned_dict['weight'])) != 1:
            # see _removal_ballots
            raise RuntimeError('ballots with different weights will not work with current implementation')

    def _removal_ballots(self, candidate, default_as_true=True):

        if default_as_true:
            # marks all ballots to be transferred
            to_remove = [True for b in self._bs]
        else:
            to_remove = [False for b in self._bs]

        # all ballots are transferred for non-winners
        if candidate not in self._round_winners:
            return to_remove

        thresh = self._win_threshold()
        ballot_weight = self._bs[0]['weight']  # assuming equal weighted ballots
        continuing_candidates = set(self._candidate_set) - set(self._inactive_candidates)

        # total and surplus
        cand_total = self.get_round_tally_dict(self._round_num, self._tab_num)[candidate]
        surplus = cand_total - thresh

        # skip factor for determining transferred ballots
        surplus_factor = int(round(cand_total/surplus))

        # pull out ballots that counted towards this winning candidate
        cand_ballots = [(idx, b) for idx, b in enumerate(self._bs) if b['ranks'] and b['ranks'][0] == candidate]

        # mark all ballot belonging to candidate as not-transfer
        for ballot in cand_ballots:
            to_remove[ballot[0]] = False

        seen_idxs = []
        used_idxs = []
        for offset in range(0, surplus_factor):

            # start_idx = offset
            start_idx = surplus_factor + offset - 1
            skip_factor = surplus_factor

            print((start_idx, len(cand_ballots), skip_factor))
            for idx in range(start_idx, len(cand_ballots), skip_factor):

                print(idx)

                if idx in seen_idxs or idx in used_idxs:
                    raise RuntimeError("should this happen?")

                # enough ballots have been marked for transfer
                if cand_total <= thresh:
                    break

                # if current ballot has a next choice that is a continuing candidate,
                ranks = cand_ballots[idx][1]['ranks']
                if set(ranks).intersection(continuing_candidates):
                    # mark it for transfer
                    to_remove[cand_ballots[idx][0]] = True
                    # decrement candidate total
                    cand_total -= ballot_weight
                    used_idxs.append(idx)

                seen_idxs.append(idx)

        if cand_total > thresh:

            unseen_idx = [idx for idx, b in enumerate(cand_ballots) if idx not in seen_idxs]
            non_transfer_continuing = [bool(set(b[1]['ranks']).intersection(continuing_candidates))
                                       for idx, b in enumerate(cand_ballots) if idx not in used_idxs]
            non_transfer_ballot_idx = [b[0] for idx, b in enumerate(cand_ballots) if idx not in used_idxs]

            if any(flag for idx, flag in enumerate(non_transfer_continuing) if idx not in unseen_idx):
                print("some un-chosen ballots have continuing candidates")
                raise RuntimeError
            else:
                for idx in non_transfer_ballot_idx:
                    if cand_total <= thresh:
                        break
                    to_remove[idx] = True
                    cand_total -= ballot_weight

        if cand_total > thresh:
            raise RuntimeError

        return to_remove

    def _calc_round_transfer(self):
        """
        This function should append a dictionary to self.transfers containing:
        candidate names as keys, plus one key for 'exhaust' and any other keys for transfer categories
        values as round transfer flows.

        rules:
        - transfer votes from round loser or winner
        """
        if self._round_winners:

            transfer_dict = {cand: 0 for cand in self._candidate_set.union({'exhaust'})}

            # collect flags indicating
            all_removal_ballots = []
            for winner in self._round_winners:
                all_removal_ballots.append(self._removal_ballots(winner, default_as_true=False))

            combined_removal_ballots = [False for b in self._bs]
            for idx in range(0, len(self._bs)):
                if any(flag_list[idx] for flag_list in all_removal_ballots):
                    combined_removal_ballots[idx] = True

            for b, is_transfer in zip(self._bs, combined_removal_ballots):

                if is_transfer:

                    if len(b['ranks']) == 0:
                        print('this shouldnt happen.')
                        raise RuntimeError

                    remaining_candidates = [cand for cand in b['ranks'] if cand not in self._round_winners]
                    if len(remaining_candidates) == 0:
                        # exhausted
                        transfer_dict['exhaust'] += b['weight']
                    elif len(remaining_candidates) > 0:
                        # transfer to another candidate
                        transfer_dict[remaining_candidates[0]] += b['weight']

                    # include outflow
                    transfer_dict[b['ranks'][0]] += b['weight'] * -1

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

    def _clean_round(self):
        """
        Remove any newly inactivated candidates from the ballot ranks. But only remove previous round winners
        from specified ballots
        """
        winners = []
        for inactive_cand in self._inactive_candidates:
            if inactive_cand not in self._removed_candidates:
                if inactive_cand in self._round_winners:
                    winners.append(inactive_cand)
                    self._removed_candidates.append(inactive_cand)
                else:
                    self._bs = [{'ranks': util.remove(inactive_cand, b['ranks']),
                                 'weight': b['weight'],
                                 'weight_distrib': b['weight_distrib']}
                                for b in self._bs]
                    self._removed_candidates.append(inactive_cand)

        # remove all other candidates before winners. This mostly matters in the first round when all
        # zero-vote candidates are removed. That is the only time a loser and a winner might both be inactivated in the
        # same round. It may also happen in the last round, but transfer calculations at that point have no impact.
        remove_bool_lists = []
        for winner in winners:
            remove_bool_lists.append(self._removal_ballots(winner, default_as_true=True))

        for winner, to_remove in zip(winners, remove_bool_lists):
            self._bs = [{'ranks': util.remove(winner, b['ranks']),
                         'weight': b['weight'],
                         'weight_distrib': b['weight_distrib']}
                        if is_remove else b
                        for b, is_remove in zip(self._bs, to_remove)]

        # all_removal_ballots = []
        # for winner in winners:
        #     all_removal_ballots.append(self._removal_ballots(winner, default_as_true=True))
        #
        # combined_removal_ballots = [False for b in self._bs]
        # for idx in range(0, len(self._bs)):
        #     if any(flag_list[idx] for flag_list in all_removal_ballots):
        #         combined_removal_ballots[idx] = True
        #
        # for winner in winners:
        #     self._bs = [{'ranks': remove(winner, b['ranks']),
        #                  'weight': b['weight'],
        #                  'weight_distrib': b['weight_distrib']}
        #                 if is_remove else b
        #                 for b, is_remove in zip(self._bs, combined_removal_ballots)]


class stv_fractional_ballot(stv):
    """
    Multi-winner elections with fractional ballot transfer.
    - Win threshold is set as the (# first round votes)/(# of seats + 1).
    - Any winner is eliminated and has their surplus redistributed. Percent of each
    ballot redistributed is equal to (# of votes winner has -- minus the threshold)/(# of votes winner has).
    - If no winners in round, candidate with least votes in a round is eliminated and has votes transferred.
    """
    def __init__(self, ctx):
        super().__init__(ctx)

    def _update_weights(self):
        """
        If surplus needs to be transferred, change weights on winner ballots to reflect remaining
        active ballot proportion.

        rules:
        - reduce weights of ballots ranking the winner by the amount
        """

        round_dict = self.get_round_tally_dict(self._round_num, tabulation_num=self._tab_num)
        threshold = self._win_threshold()

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

                        # record ballot weight allotted to winner
                        winner_weight = b['weight'] * (1 - surplus_percent)
                        new_weight_distrib = b['weight_distrib'] + [(winner, winner_weight)]

                        # remaining weight
                        remaining_weight = b['weight'] * surplus_percent

                        # adjust ballot's current weight
                        new.append({'ranks': b['ranks'], 'weight': remaining_weight,
                                    'weight_distrib': new_weight_distrib})
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

                remaining_candidates = [cand for cand in b['ranks'] if cand not in transfer_candidates]
                if remaining_candidates:
                    transfer_dict[remaining_candidates[0]] += b['weight']
                else:
                    transfer_dict['exhaust'] += b['weight']

                # mark transfer outflow
                transfer_dict[b['ranks'][0]] += b['weight'] * -1

        self._tabulations[self._tab_num-1]['transfers'].append(transfer_dict)


class rcv_multiWinner_thresh15(rcv_base.RCV):
    """
    Multi winner contest. When all candidates in a round have more than 15% of the round votes, they are all winners.
    - In a no winner round, the candidate with least votes is eliminated and ballots transferred.
    """
    def __init__(self, ctx):
        super().__init__(ctx)

    @staticmethod
    def variant_group():
        return rcv_base.RCV.multi_winner_group

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
        """
        round_candidates, round_tallies = self.get_round_tally_tuple(self._round_num, self._tab_num,
                                                                     only_round_active_candidates=True)
        threshold = sum(round_tallies) * decimal.Decimal('0.15')
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

# class rcv_multiWinner_thresh15_keepUndeclared(rcv_multiWinner_thresh15):
#     """
#     Multi winner contest. When all candidates in a round have more than 15% of the round votes, they are all winners.
#     - In a no winner round, the candidate with least votes is eliminated and ballots transferred.
#     - If there is a candidate called "(undeclared)" it is treated as un-defeatable.
#     """
#     def __init__(self, ctx):
#         super().__init__(ctx)

#     def _set_round_loser(self):
#         """
#         Find candidate from round with least votes.
#         If more than one, choose randomly

#         rules:
#         - '(undeclared)' candidate cannot lose
#         """
#         # split round results into two tuples (index-matched)
#         round_candidates, round_tallies = self.get_round_tally_tuple(self._round_num, self._tab_num,
#                                                                      only_round_active_candidates=True, desc_sort=True)

#         round_candidates = list(round_candidates)
#         round_tallies = list(round_tallies)

#         # '(undeclared)' cannot be a loser
#         if '(undeclared)' in round_candidates:
#             undeclared_idx = round_candidates.index('(undeclared)')
#             del round_candidates[undeclared_idx]
#             del round_tallies[undeclared_idx]

#         # find round loser
#         loser_count = min(round_tallies)
#         # in case of tied losers, 'randomly' choose one to eliminate (the last one in alpha order)
#         round_losers = sorted([cand for cand, cand_tally
#                                in zip(round_candidates, round_tallies)
#                                if cand_tally == loser_count])
#         self._round_loser = round_losers[-1]
