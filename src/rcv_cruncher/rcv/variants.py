
from typing import (List)

import abc
import copy
import decimal

from rcv_cruncher.marks import BallotMarks
from rcv_cruncher.rcv.base import RCV


def get_rcv_dict():
    """
    Return dictionary of rcv classes, class_name: class_obj (constructor function)
    """
    return {
        'Until2': Until2,
        'STVWholeBallot': STVWholeBallot,
        'STVFractionalBallot': STVFractionalBallot,
        'Sequential': Sequential,
        'SingleWinner': SingleWinner,
        'BottomsUp15': BottomsUp15
    }


class SingleWinner(RCV):
    """
    Single winner rcv contest.
    - Winner is candidate to first achieve more than half the active round votes.
    - Votes are transferred from losers each round.
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _contest_stats(self) -> List:
        """
        Every rcv variant must specify which stats list it uses.
        Available lists should be set as rcv base methods or reporting methods.
        """
        return self.single_winner_stats

    def _set_round_winners(self) -> None:
        """
        This function should set self._round_winners to the list of candidates that won the round

        single winner rules:
        - winner is candidate with > 50% of round vote
        """
        round_candidates, round_tallies = self.get_round_tally_tuple(self._round_num, self._tab_num,
                                                                     only_round_active_candidates=True, desc_sort=True)
        if round_tallies[0]*2 > sum(round_tallies):
            self._round_winners = [round_candidates[0]]

    def _calc_round_transfer(self) -> None:
        """
        This function should append a dictionary to self.transfers containing:
        candidate names as keys, plus one key for 'exhaust' and any other keys for transfer categories
        values as round transfer flows.

        rules:
        - transfer votes from round loser
        """
        # calculate transfer
        transfer_dict = {cand: 0 for cand in self._contest_candidates.unique_candidates.union({'exhaust'})}
        for b in self._contest_cvr_ld:
            if len(b['ballot_marks'].marks) > 0 and b['ballot_marks'].marks[0] == self._round_loser:
                if len(b['ballot_marks'].marks) > 1:
                    transfer_dict[b['ballot_marks'].marks[1]] += b['weight']
                else:
                    transfer_dict['exhaust'] += b['weight']

        transfer_dict[self._round_loser] = sum(transfer_dict.values()) * -1
        self._tabulations[self._tab_num-1]['transfers'].append(transfer_dict)

    def _contest_not_complete(self) -> bool:
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


class Sequential(SingleWinner):
    """
    Sequential RCV elections used to elect multiple winners. Winners are elected one-by-one in repeated single winner
    RCV elections, each time with the previous winners effectively treated as eliminated.
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    # overwrite _run_contest to run multiple single winner elections
    def _run_contest(self) -> None:

        winners = []
        self._tab_num = 0
        self._tabulations = []

        # continue until the number of winners is reached OR until candidates run out
        while len(winners) != self._n_winners and len(self._contest_candidates - set(winners)) != 0:

            self._new_tabulation()

            # reset inputs
            self._reset_ballots()

            # tabulation-level
            self._inactive_candidates = copy.copy(winners)  # mark previous iteration winners as inactive
            self._removed_candidates = []

            # round-level
            self._round_num = 0

            # calculate single winner rcv
            self._tabulate()

            # get winner and store results
            tabulation_outcomes = self._tabulations[self._tab_num-1]['candidate_outcomes']
            winners.append([d['name'] for d in tabulation_outcomes.values() if d['round_elected'] is not None][0])


class Until2(SingleWinner):
    """
    Run single winner contest all the way down to final two canidates.
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _set_round_winners(self) -> None:
        """
        This function should set self._round_winners to the list of candidates that won the round

        single winner rules:
        - winner is candidate with more votes when there are only two candidates left
        """
        round_candidates, _ = self.get_round_tally_tuple(self._round_num, self._tab_num,
                                                         only_round_active_candidates=True, desc_sort=True)
        if len(round_candidates) == 2:
            self._round_winners = [round_candidates[0]]


class STV(RCV, abc.ABC):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

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

    def _contest_not_complete(self) -> bool:
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

    def _win_threshold(self) -> decimal.Decimal:
        """
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


class STVWholeBallot(STV):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        weights = set(b['weight'] for b in self._contest_cvr_ld)
        if len(weights) != 1:
            # see _removal_ballots
            raise RuntimeError('ballots with unequal weights will not work with current implementation')

    def _removal_ballots(self, candidate, default_as_true=True) -> List[bool]:

        if default_as_true:
            # marks all ballots to be transferred
            to_remove = [True] * len(self._contest_cvr_ld)
        else:
            to_remove = [False] * len(self._contest_cvr_ld)

        # all ballots are transferred for non-winners
        if candidate not in self._round_winners:
            return to_remove

        thresh = self._win_threshold()
        ballot_weight = self._contest_cvr_ld[0]['weight']  # assuming equal weighted ballots
        continuing_candidates = set(self._contest_candidates) - set(self._inactive_candidates)

        # total and surplus
        cand_total = self.get_round_tally_dict(self._round_num, self._tab_num)[candidate]
        surplus = cand_total - thresh

        # skip factor for determining transferred ballots
        surplus_factor = int(round(cand_total/surplus))

        # pull out ballots that counted towards this winning candidate
        cand_ballots = [(idx, b) for idx, b in enumerate(self._contest_cvr_ld)
                        if b['ballot_marks'].marks and b['ballot_mark'].marks[0] == candidate]

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

            unseen_idx = [idx for idx, _ in enumerate(cand_ballots) if idx not in seen_idxs]
            non_transfer_continuing = [bool(set(b[1]['ballot_marks'].marks).intersection(continuing_candidates))
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

    def _calc_round_transfer(self) -> None:
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

            combined_removal_ballots = [False] * len(self._contest_cvr_ld)
            for idx in range(0, len(self._contest_cvr_ld)):
                if any(flag_list[idx] for flag_list in all_removal_ballots):
                    combined_removal_ballots[idx] = True

            for b, is_transfer in zip(self._contest_cvr_ld, combined_removal_ballots):

                if is_transfer:

                    if len(b['ballot_marks'].marks) == 0:
                        print('this shouldnt happen.')
                        raise RuntimeError

                    remaining_candidates = [cand for cand in b['ballot_marks'].marks if cand not in self._round_winners]
                    if len(remaining_candidates) == 0:
                        # exhausted
                        transfer_dict['exhaust'] += b['weight']
                    elif len(remaining_candidates) > 0:
                        # transfer to another candidate
                        transfer_dict[remaining_candidates[0]] += b['weight']

                    # include outflow
                    transfer_dict[b['ballot_marks'].marks[0]] += b['weight'] * -1

        else:
            transfer_candidates = [self._round_loser]

            # calculate transfer
            transfer_dict = {cand: 0 for cand in self._candidate_set.union({'exhaust'})}
            for b in self._contest_cvr_ld:
                if len(b['ballot_marks'].marks) > 0 and b['ballot_marks'].marks[0] in transfer_candidates:

                    if len(b['ballot_marks'].marks) > 1:
                        transfer_dict[b['ballot_marks'].marks[1]] += b['weight']
                    else:
                        transfer_dict['exhaust'] += b['weight']

                    # mark transfer outflow
                    transfer_dict[b['ballot_marks'].marks[0]] += b['weight'] * -1

        self._tabulations[self._tab_num-1]['transfers'].append(transfer_dict)

    def _clean_round(self) -> None:
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
                    self._contest_cvr_ld = [
                        {
                            'ballot_marks': BallotMarks.remove_mark(b['ballot_marks'], [inactive_cand]),
                            'weight': b['weight'],
                            'weight_distrib': b['weight_distrib']
                        }
                        for b in self._contest_cvr_ld]
                    self._removed_candidates.append(inactive_cand)

        # remove all other candidates before winners. This mostly matters in the first round when all
        # zero-vote candidates are removed. That is the only time a loser and a winner might both be inactivated in the
        # same round. It may also happen in the last round, but transfer calculations at that point have no impact.
        remove_bool_lists = []
        for winner in winners:
            remove_bool_lists.append(self._removal_ballots(winner, default_as_true=True))

        for winner, to_remove in zip(winners, remove_bool_lists):
            self._contest_cvr_ld = [
                {
                    'ballot_marks': BallotMarks.remove_mark(b['ballot_marks'], [inactive_cand]),
                    'weight': b['weight'],
                    'weight_distrib': b['weight_distrib']
                }
                if is_remove else b
                for b, is_remove in zip(self._contest_cvr_ld, to_remove)]


class STVFractionalBallot(STV):
    """
    Multi-winner elections with fractional ballot transfer.
    - Win threshold is set as the (# first round votes)/(# of seats + 1).
    - Any winner is eliminated and has their surplus redistributed. Percent of each
    ballot redistributed is equal to (# of votes winner has -- minus the threshold)/(# of votes winner has).
    - If no winners in round, candidate with least votes in a round is eliminated and has votes transferred.
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _update_weights(self) -> None:
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
                for b in self._contest_cvr_ld:
                    if b['ballot_marks'].marks and b['ballot_marks'].marks[0] == winner:

                        # record ballot weight allotted to winner
                        winner_weight = b['weight'] * (1 - surplus_percent)
                        new_weight_distrib = b['weight_distrib'] + [(winner, winner_weight)]

                        # remaining weight
                        remaining_weight = b['weight'] * surplus_percent

                        # adjust ballot's current weight
                        new.append(
                            {
                                'ranks': b['ballot_marks'].marks,
                                'weight': remaining_weight,
                                'weight_distrib': new_weight_distrib
                            })
                    else:
                        new.append(b)
                self._contest_cvr_ld = new

    #
    def _calc_round_transfer(self) -> None:
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
            if len(b['ballot_marks'].marks) > 0 and b['ballot_marks'].marks[0] in transfer_candidates:

                remaining_candidates = [cand for cand in b['ballot_marks'].marks if cand not in transfer_candidates]
                if remaining_candidates:
                    transfer_dict[remaining_candidates[0]] += b['weight']
                else:
                    transfer_dict['exhaust'] += b['weight']

                # mark transfer outflow
                transfer_dict[b['ballot_marks'].marks[0]] += b['weight'] * -1

        self._tabulations[self._tab_num-1]['transfers'].append(transfer_dict)


class BottomsUp15(RCV):
    """
    Multi winner contest. When all candidates in a round have more than 15% of the round votes, they are all winners.
    - In a no winner round, the candidate with least votes is eliminated and ballots transferred.
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _set_round_winners(self) -> None:
        """
        This function should set self._round_winners to the list of candidates that won the round
        """
        round_candidates, round_tallies = self.get_round_tally_tuple(self._round_num, self._tab_num,
                                                                     only_round_active_candidates=True)
        threshold = sum(round_tallies) * decimal.Decimal('0.15')
        if all(i > threshold for i in round_tallies):
            self._round_winners = list(round_candidates)

    def _calc_round_transfer(self) -> None:
        """
        This function should append a dictionary to self.transfers containing:
        candidate names as keys, plus one key for 'exhaust' and any other keys for transfer categories
        values as round transfer flows.

        rules:
        - transfer votes from round loser
        """

        # calculate transfer
        transfer_dict = {cand: 0 for cand in self._candidate_set.union({'exhaust'})}
        for b in self._contest_cvr_ld:
            if len(b['ballot_marks'].marks) > 0 and b['ballot_marks'].marks[0] == self._round_loser:
                if len(b['ballot_marks'].marks) > 1:
                    transfer_dict[b['ballot_marks'].marks[1]] += b['weight']
                else:
                    transfer_dict['exhaust'] += b['weight']

        transfer_dict[self._round_loser] = sum(transfer_dict.values()) * -1
        self._tabulations[self._tab_num-1]['transfers'].append(transfer_dict)

    def _contest_not_complete(self) -> None:
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
