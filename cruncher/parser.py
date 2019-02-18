# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

import codecs
import logging
from cruncher.stats import increment_dict_total
from .common import reraise, Error


_log = logging.getLogger(__name__)


ENCODING_DATA_FILES  = 'utf-8'

def on_ballot(ballot, analyzer, contest, stats):
    """
    Update stats based on the given ballot.

    """

    candidates = contest.candidate_ids
    winner = contest.winner_id
    finalists = contest.finalists
    non_winning_finalists = contest.non_winning_finalists


    set_of_finalists = set(finalists)
    non_winners = list(set(candidates) - set([winner]))


    stats.total += 1

    first_round = analyzer.get_first_round(ballot)

    if first_round == analyzer.undervote:
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

    if first_round == analyzer.overvote:
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
        if analyzer.overvote in ballot:
            stats.exhausted_by_overvote += 1
    if analyzer.did_sweep(ballot, first_round):
        stats.did_sweep[first_round] += 1

    if analyzer.beats_challengers(ballot, winner, non_winning_finalists):
        stats.final_round_winner_total += 1

    # Calculate condorcet pairs against winner.
    for non_winner in non_winners:
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
    with codecs.open(path, "r", encoding=ENCODING_DATA_FILES) as f:
        contest_dict = input_format.parse_master_file(f)

    return contest_dict


class Contest(object):

    def __init__(self, name, candidate_dict, winner_id, other_finalist_ids):

        candidate_ids = candidate_dict.keys()

        if not other_finalist_ids:
            # Then all candidates are finalists.
            other_finalist_ids = candidate_ids
            elimination_rounds = False
        else:
            elimination_rounds = True

        # Make sure the winner is not a finalist to avoid duplicates.
        other_finalist_ids = list(set(other_finalist_ids) - set([winner_id]))

        finalists = [winner_id] + other_finalist_ids

        self.name = name
        self.winner_id = winner_id
        self.candidate_dict = candidate_dict

        # TODO: change from ids.
        self.candidate_ids = candidate_ids
        self.non_winning_finalists = other_finalist_ids
        self.finalists = finalists
        self.non_finalist_ids = list(set(candidate_ids) - set(finalists))
        self.elimination_rounds = elimination_rounds

    @property
    def candidate_count(self):
        # Don't include WRITE-IN as a candidate.
        candidate_map = self.candidate_dict
        names = candidate_map.values()
        count = len(names)
        for (_, name) in candidate_map.iteritems():
            if name.upper() == "WRITE-IN":
                count -= 1
        return count


class BallotParser(object):

    def __init__(self, input_format, contest_infos):
        # Parsing the ballot file is faster without specifying an encoding.
        # The ballot file is just integers, so an encoding is not necessary.
        self.encoding = None

        self.contest_infos = contest_infos
        self.input_format = input_format

    def parse_ballots(self, ballot_path):
        self.read_ballot_path(ballot_path)

    def read_ballot_path(self, path):
        _log.info("Reading ballots: %s" % path)

        def open_path(path):
            if self.encoding is None:
                return open(path, "r")
            else:
                return codecs.open(path, "r", encoding=self.encoding)

        with open_path(path) as f:
            self.process_ballot_file(f)

    def process_ballot_file(self, f):

        line_number = 0
        contest_infos = self.contest_infos
        input_format = self.input_format

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
                    on_ballot(ballot, contest_info["analyzer"], contest_info["contest"], contest_info["stats"])

            except Error:
                raise
            except Exception, ex:
                reraise(Error(ex))
        except Error, err:
            err.add("File line number: %s" % line)
            reraise(err)

