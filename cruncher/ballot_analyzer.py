# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

import logging

_log = logging.getLogger(__name__)

UNDERVOTE = -1
OVERVOTE  = -2

def get_first_round(ballot):
    """
    Return what the ballot counts towards in the first round.

    Returns self.UNDERVOTE for an UNDERVOTEd ballot.

    """
    for choice in ballot:
        if choice != UNDERVOTE:
            break
    return choice

def has_overvote(ballot):
    return OVERVOTE in ballot

def count_duplicates(ballot):
    """
    Return the max number of times the same candidate occurs on the ballot.

    """
    duplicate_count = 0
    choices = set(ballot)
    for choice in choices:
        if choice == UNDERVOTE or choice == OVERVOTE:
            continue
        count = ballot.count(choice)
        if count > duplicate_count:
            duplicate_count = count
    return duplicate_count

def has_skipped(ballot):
    ###OAB: voter has skipped a ranking (say the 2nd), and then ranked (say 3rd) for a candidate
    seen_undervote = False
    for choice in ballot:
        if choice == UNDERVOTE:
            seen_undervote = True
            continue
        if seen_undervote:
            return True
    return False

def get_effective_choices(ballot):
    """
    Return the effective choices on the ballot.

    For example:

    [UNDERVOTE, A, B] -> [A, B]
    [UNDERVOTE, A, A] -> [A]
    [A, OVERVOTE, B] -> [A]

    """
    effective_choices = []
    for choice in ballot:
        if choice == UNDERVOTE or choice in effective_choices:
            continue
        if choice == OVERVOTE:
            break
        effective_choices.append(choice)

    # Make the choices hashable (for use in a dict).
    return tuple(effective_choices)

def did_sweep(ballot, candidate_id):
    for choice in ballot:
        if choice != candidate_id:
            return False
    return True

def beats_challenger(ballot, candidate, challenger):
    """
    Return whether a candidate validly defeats a challenger.

    Return None if the ballot is inconclusive.

    """
    for choice in ballot:
        if choice == OVERVOTE:
            break
        if choice == candidate:
            return True
        if choice == challenger:
            return False

    return None

def beats_challengers(ballot, candidate, challengers):
    """
    Return whether a candidate validly defeats challengers.

    Return None if the ballot is inconclusive.

    """
    for choice in ballot:
        if choice == OVERVOTE:
            break
        if choice == candidate:
            return True
        if choice in challengers:
            return False

    return None
