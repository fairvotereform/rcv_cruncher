# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

import logging


_log = logging.getLogger(__name__)


class BallotAnalyzer(object):

    def __init__(self, undervote, overvote):
        self.overvote = overvote
        self.undervote = undervote

    def get_first_round(self, ballot):
        """
        Return what the ballot counts towards in the first round.

        Returns self.undervote for an undervoted ballot.

        """
        for choice in ballot:
            if choice != self.undervote:
                break
        return choice

    def has_overvote(self, ballot):
        return self.overvote in ballot

    def count_duplicates(self, ballot):
        """
        Return the max number of times the same candidate occurs on the ballot.

        """
        duplicate_count = 0
        choices = set(ballot)
        for choice in choices:
            if choice == self.undervote or choice == self.overvote:
                continue
            count = ballot.count(choice)
            if count > duplicate_count:
                duplicate_count = count
        return duplicate_count

    def has_skipped(self, ballot):
        seen_undervote = False
        for choice in ballot:
            if choice == self.undervote:
                seen_undervote = True
                continue
            if seen_undervote:
                return True
        return False

    def get_effective_choices(self, ballot):
        """
        Return the effective choices on the ballot.

        For example:

        [UNDERVOTE, A, B] -> [A, B]
        [UNDERVOTE, A, A] -> [A]
        [A, OVERVOTE, B] -> [A]

        """
        effective_choices = []
        for choice in ballot:
            if choice == self.undervote or choice in effective_choices:
                continue
            if choice == self.overvote:
                break
            effective_choices.append(choice)

        return effective_choices

    def did_sweep(self, ballot, candidate_id):
        for choice in ballot:
            if choice != candidate_id:
                return False
        return True

    def beats_challenger(self, ballot, candidate, challenger):
        """
        Return whether a candidate validly defeats a challenger.

        Return None if the ballot is inconclusive.

        """
        for choice in ballot:
            if choice == self.overvote:
                break
            if choice == candidate:
                return True
            if choice == challenger:
                return False

        return None

    def beats_challengers(self, ballot, candidate, challengers):
        """
        Return whether a candidate validly defeats challengers.

        Return None if the ballot is inconclusive.

        """
        for choice in ballot:
            if choice == self.overvote:
                break
            if choice == candidate:
                return True
            if choice in challengers:
                return False

        return None
