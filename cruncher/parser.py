# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

import codecs
import logging
from cruncher.stats import increment_dict_total
from .common import reraise, Error
import ballot_analyzer as analyzer

_log = logging.getLogger(__name__)

def on_ballot(ballot, contest_info):
    """
    Update stats based on the given ballot.

    """
    stats = contest_info['stats']
    winner = contest_info['winner_id']
    set_of_finalists = set(contest_info['finalists'])
    stats.total += 1
    first_round = analyzer.get_first_round(ballot)
    if first_round == analyzer.UNDERVOTE:
        stats.undervotes += 1
        return

    # Now check for various types of irregularities.
    duplicate_count = analyzer.count_duplicates(ballot)
    if duplicate_count > 1:
        stats.duplicates[duplicate_count] += 1
        has_duplicate = True
    else:
        has_duplicate = False

    has_overvote = analyzer.has_overvote(ballot)
    has_skipped = analyzer.has_skipped(ballot)

    if has_overvote:
        stats.has_overvote += 1
    if has_skipped:
        stats.has_skipped += 1
    if has_overvote or has_duplicate or has_skipped:
        stats.irregular += 1

    if first_round == analyzer.OVERVOTE:
        stats.first_round_overvotes += 1
        # Return since all remaining analysis needs effective choices.
        return

    effective_choices = analyzer.get_effective_choices(ballot)
    number_ranked = len(effective_choices)

    stats.add_number_ranked(first_round, number_ranked)

    for index in range(number_ranked):
        candidate = effective_choices[index]
        stats.ballot_position[candidate][index] += 1

    ### Ballot length hard coded here:
    if number_ranked == 3 and set_of_finalists.isdisjoint(effective_choices):
        stats.truly_exhausted[first_round] += 1
    if winner in effective_choices:
        stats.ranked_winner[first_round] += 1
    if not set_of_finalists.isdisjoint(effective_choices):
        stats.ranked_finalist[first_round] += 1
    else:
        # Then no finalist is validly ranked on the ballot.
        if analyzer.OVERVOTE in ballot:
            stats.exhausted_by_overvote += 1
    if analyzer.did_sweep(ballot, first_round):
        stats.did_sweep[first_round] += 1

    non_winning_finalists = list(set_of_finalists - set([winner]))
    if analyzer.beats_challengers(ballot, winner, non_winning_finalists):
        stats.final_round_winner_total += 1

    # Calculate condorcet pairs against winner.
    for non_winner in list(set(contest_info['candidate_ids']) - set([winner])):
        did_winner_win = analyzer.beats_challenger(ballot, winner, non_winner)
        if did_winner_win is None:
            continue
        if did_winner_win:
            stats.add_condorcet_winner(winner, non_winner)
        else:
            stats.add_condorcet_winner(non_winner, winner)

    # Track orderings and combinations.
    increment_dict_total(stats.combinations, frozenset(effective_choices))
    increment_dict_total(stats.orderings, effective_choices)

def parse_master(input_format, path):
    _log.info("Reading master file: %s" % path)
    with codecs.open(path, "r", encoding='utf-8') as f:
        contest_dict = input_format.parse_master_file(f)

    return contest_dict

def parse_ballots(input_format, contest_infos, path):
    # Parsing the ballot file is faster without specifying an encoding.
    # The ballot file is just integers, so an encoding is not necessary.
    _log.info("Reading ballots: %s" % path)
    with open(path, "r") as f:
        line_number = 0
        try:
            try:
                while True:
                    line_number += 1
                    line = f.readline()
                    if not line:
                        line_number -= 1  # since there was no line after all.
                        _log.info("Read %d lines." % line_number)
                        break

                    contest_id, ballot, line_number = input_format.read_ballot(f, line, line_number)
                    contest_info = contest_infos[contest_id]
                    on_ballot(ballot, contest_info)

            except Error:
                raise
            except Exception, ex:
                reraise(Error(ex))
        except Error, err:
            err.add("File line number: %s" % line)
            reraise(err)

