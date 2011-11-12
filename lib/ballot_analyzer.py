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
            if choice is not self.undervote:
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
            if choice is self.undervote or choice is self.overvote:
                continue
            count = ballot.count(choice)
            if count > duplicate_count:
                duplicate_count = count
        return duplicate_count
    
    def has_skipped(self, ballot):
        seen_undervote = False
        for choice in ballot:
            if choice is self.undervote:
                seen_undervote = True
                continue
            if seen_undervote:
                return True
        return False

    def get_set_of_validly_ranked(self, ballot):
        """
        Return the validly ranked candidates as a set.

        """
        candidates = set()
        for choice in ballot:
            if choice is self.undervote:
                continue
            if choice is self.overvote:
                break
            candidates.add(choice)

        return candidates

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
            if choice is self.overvote:
                break
            if choice is candidate:
                return True
            if choice is challenger:
                return False

        return None

    def beats_challengers(self, ballot, candidate, challengers):
        """
        Return whether a candidate validly defeats challengers.

        Return None if the ballot is inconclusive.

        """
        for choice in ballot:
            if choice is self.overvote:
                break
            if choice is candidate:
                return True
            if choice in challengers:
                return False

        return None
