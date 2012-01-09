# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

import codecs
import logging
import os
import sys

from .common import reraise
from .common import Error


_log = logging.getLogger(__name__)


ENCODING_DATA_FILES  = 'utf-8'


class Contest(object):

    def __init__(self, name, candidate_dict, winner_id, other_finalist_ids):

        candidate_ids = candidate_dict.keys()
        finalists = [winner_id] + other_finalist_ids

        self.name = name
        self.winner_id = winner_id
        self.candidate_dict = candidate_dict

        # TODO: change from ids.
        self.candidate_ids = candidate_ids
        self.non_winning_finalists = other_finalist_ids
        self.finalists = finalists
        self.non_finalist_ids = list(set(candidate_ids) - set(finalists))


class MasterParser(object):

    # TODO: clean up case of final_candidates None.
    #       This corresponds to all candidates being final candidates.
    def __init__(self, input_format, winning_candidate, final_candidates=None):
        self.encoding = ENCODING_DATA_FILES
        self.final_candidates = final_candidates
        self.input_format = input_format
        self.winning_candidate = winning_candidate

    def parse(self, path):
        _log.info("Reading master file: %s" % path)
        with codecs.open(path, "r", encoding=self.encoding) as f:
            contest = self.read_master_file(f)

        return contest

    def find_candidate_id(self, candidate_dict, name_to_find):
        for (candidate_id, name) in candidate_dict.iteritems():
            if name == name_to_find:
                return candidate_id
        raise Error("Candidate %s not found in dictionary." % name_to_find)

    def read_master_file(self, f):
        contest_name, candidate_dict = self.input_format.parse_contest(f)

        winner_id = self.find_candidate_id(candidate_dict, self.winning_candidate)

        # TODO: make this more elegant.  Eliminate the need for this if block.
        if self.final_candidates is None:
            candidate_ids = candidate_dict.keys()
            # Make sure the winner is not a finalist to avoid duplicates.
            finalist_ids = list(set(candidate_ids) - set([winner_id]))
        else:
            finalist_ids = []
            for candidate in self.final_candidates:
                finalist_id = self.find_candidate_id(candidate_dict, candidate)
                finalist_ids.append(finalist_id)

        contest = Contest(contest_name, candidate_dict, winner_id, finalist_ids)

        return contest


class BallotParser(object):

    def __init__(self, undervote, overvote, on_ballot, encoding=None):
        self.encoding = encoding
        self.undervote = undervote
        self.overvote = overvote
        self.on_ballot = on_ballot

    def process_contest(self, ballot_path, winner):
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

        try:
            try:
                line_number = 1
                line = f.readline()

                # First line of file, so no expected contest or voter.
                parsed_line = self.parse_ballot_line(line, 1)
                contest_id = parsed_line[0]

                while True:
                    ballot, line_number = self.read_ballot(f, parsed_line, line_number, contest_id)

                    self.on_ballot(ballot)

                    line_number += 1
                    line = f.readline()
                    if not line:
                        _log.info("Read %d lines." % line_number)
                        break

                    # First line of ballot, so no expected voter.
                    parsed_line = self.parse_ballot_line(line, 1, expected_contest_id=contest_id)
            except Error:
                raise
            except Exception, ex:
                reraise(Error(ex))
        except Error, err:
            err.add("File line number: %d" % line_number)
            reraise(err)

    def read_ballot(self, f, parsed_line, line_number, expected_contest_id):
        """
        Read and return an RCV ballot.

        Arguments:

          parsed_line: a tuple that is the first line of an RCV ballot.  The
            caller is responsible for confirming that the contest ID is correct.

          f: a file handle.

        Returns:

          a 3-tuple of integers representing the choices on an RCV ballot.
          Each integer is a candidate ID, -1 for undervote, or -2 for overvote.

        """
        try:
            try:
                contest_id, voter_id, rank, choice = parsed_line

                choices = [choice]

                line_number += 1
                line = f.readline()
                parsed_line = self.parse_ballot_line(line, 2, expected_contest_id=expected_contest_id, expected_voter_id=voter_id)
                choices.append(parsed_line[3])

                line_number += 1
                line = f.readline()
                parsed_line = self.parse_ballot_line(line, 3, expected_contest_id=expected_contest_id, expected_voter_id=voter_id)
                choices.append(parsed_line[3])
            except Error:
                raise
            except Exception, ex:
                reraise(Error(ex))
        except Error, err:
            err.add("Ballot line number: %d" % line_number)
            reraise(err)

        return choices, line_number


    def parse_ballot_line(self, line, expected_rank, expected_contest_id=None, expected_voter_id=None):
        """
        Return a parsed line, or raise an Exception on failure.

        """
        parsed_line = None
        try:
            parsed_line = self.parse_line(line)
            contest_id, voter_id, rank, choice = parsed_line

            if expected_contest_id is not None and contest_id != expected_contest_id:
                raise Exception("Expected contest id %d but got %d." % (expected_contest_id, contest_id))
            if expected_voter_id is not None and voter_id != expected_voter_id:
                raise Exception("Expected voter id %d but got %d." % (expected_voter_id, voter_id))
            if rank != expected_rank:
                raise Exception("Expected rank %d but got %d." % (expected_rank, rank))
        except Exception, ex:
            s = "Failed parsing ballot line: %s" % repr(line)
            if parsed_line is not None:
                s += "\nParsed line: %s" % repr(parsed_line)
            reraise(Error(ex, s))

        return parsed_line

    def parse_line(self, line):
        """
        Return a parsed line as a tuple.

        A sample input--

        000000700001712400000090020000331001000012600

        The corresponding return value--



        """
        # TODO: consider having this function return an object.
        contest_id = int(line[0:7])
        voter_id = int(line[7:16])
        rank = int(line[33:36])
        candidate_id = int(line[36:43])
        undervote = self.undervote if int(line[44]) else 0
        overvote = self.overvote if int(line[43]) else 0

        choice = candidate_id or undervote or overvote

        return (contest_id, voter_id, rank, choice)



