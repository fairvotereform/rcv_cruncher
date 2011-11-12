# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

import logging


_log = logging.getLogger(__name__)


class Stats(object):

    def __init__(self, candidates, winner_id):

        number_ranked = {}  # grouped by first-round choice.
        ranked_winner = {}  # grouped by first-round choice.
        ranked_finalist = {}  # grouped by first-round choice.
        truly_exhausted = {}  # grouped by first-round choice.
        did_sweep = {}
        validly_ranked = {}

        for candidate_id in candidates:
            number_ranked[candidate_id] = 3 * [0]  # [ranked3, ranked2, ranked1]
            ranked_winner[candidate_id] = 0
            ranked_finalist[candidate_id] = 0
            truly_exhausted[candidate_id] = 0
            did_sweep[candidate_id] = 0
            validly_ranked[candidate_id] = 0

        # Initialize condorcet pairs against the winner.
        condorcet = {}
        for candidate_id in candidates:
            if candidate_id == winner_id:
                continue
            condorcet[(candidate_id, winner_id)] = 0
            condorcet[(winner_id, candidate_id)] = 0

        self.total = 0
        self.undervotes = 0
        self.has_overvote = 0
        self.has_skipped = 0
        self.irregular = 0
        self.first_round_overvotes = 0
        self.exhausted_by_overvote = 0  # excludes first-round overvotes.

        # The total of the winner in the final round.
        # There may be more than two finalists in the final round.
        self.final_round_winner_total = 0

        self.duplicates = {2: 0, 3: 0}

        self._condorcet = condorcet
        self._number_ranked = number_ranked

        self.ranked_winner = ranked_winner
        self.ranked_finalist = ranked_finalist
        self.truly_exhausted = truly_exhausted
        self.did_sweep = did_sweep

        # TODO: this is slightly redundant with ranked_winner, etc.
        # Maybe we should store this by candidate so we can eliminate
        # self.ranked_winner and self.ranked_finalist?
        self.validly_ranked = validly_ranked


    @property
    def voted(self):
        """
        Get the number of voted ballots.

        """
        return self.total - self.undervotes

    @property
    def first_round_continuing(self):
        return self.voted - self.first_round_overvotes

    @property
    def final_round_continuing(self):
        return sum([value for value in self.ranked_finalist.values()])

    @property
    def exhausted(self):
        """
        Does not include first-round overvotes or exhausted by overvote.

        """
        return self.first_round_continuing - (self.final_round_continuing + self.exhausted_by_overvote)

    @property
    def truly_exhausted_total(self):
        return sum([value for value in self.truly_exhausted.values()])

    def get_first_round(self, candidate_id):
        """
        Return the first-round count for a candidate.

        """
        return sum(self._number_ranked[candidate_id])

    def add_number_ranked(self, candidate_id, number_ranked):
        index = 3 - number_ranked
        self._number_ranked[candidate_id][index] += 1

    def get_number_ranked(self, candidate_id):
        """
        Return the number ranked as a list: [ranked3, ranked2, ranked1].

        """
        return list(self._number_ranked[candidate_id])

    def add_condorcet_winner(self, winning_id, losing_id):
        self._condorcet[(winning_id, losing_id)] += 1

    def get_condorcet_support(self, candidate_id1, candidate_id2):
        win_count = self._condorcet[(candidate_id1, candidate_id2)]
        lose_count = self._condorcet[(candidate_id2, candidate_id1)]

        total_count = win_count + lose_count

        return (win_count, total_count)


