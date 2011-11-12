# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

import codecs
import logging
import os
import sys

_log = logging.getLogger(__name__)


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class Contest(object):

    def __init__(self, name, id, candidate_dict, winner_id, other_finalist_ids):

        candidate_ids = candidate_dict.keys()
        finalists = [winner_id] + other_finalist_ids

        self.id = id
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
    def __init__(self, encoding, winning_candidate, final_candidates=None):
        self.encoding = encoding
        self.winning_candidate = winning_candidate
        self.final_candidates = final_candidates

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
        candidate_dict = {}

        while True:
            line = f.readline()
            if not line:
                break

            record_type, record_id, description = self.parse_master_line(line)

            if record_type == "Contest":
                contest_id = record_id
                contest_name = description
                continue

            if record_type == "Candidate":
                candidate_dict[record_id] = description

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

        contest = Contest(contest_name, contest_id, candidate_dict, winner_id, finalist_ids)

        return contest

    def parse_master_line(self, line):
        """
        Parse the line, and return a tuple.

        A sample line--

        "Candidate 0000120JANET REILLY                                      0000001000000700"

        """
        # We only care about the first three fields: Record_Type, Id, and Description.
        record_type = line[0:10].strip()
        id = int(line[10:17])
        description = line[17:67].strip()

        return record_type, id, description



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

        line = f.readline()
        parsed_line = self.parse_line(line)
        contest_id = parsed_line[0]

        line_index = 1

        try:
            while True:
                try:
                    ballot = self.read_ballot(parsed_line, f)
                except Exception:
                    print "Error reading line..."
                    print line_index
                    print parsed_line
                    exit()

                self.on_ballot(ballot)

                line = f.readline()
                if not line:
                    break
                line_index += 3

                parsed_line = self.parse_line(line)
                if parsed_line[0] != contest_id:
                    raise Exception("Expected contest id: %s" % expected_contest_id)

        except Error as e:
            _log.error("Error processing ballot beginning at line %s" % line_index)
            raise e


    def read_ballot(self, parsed_line, f):
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
        contest_id, voter_id, rank, choice = parsed_line

        if rank != 1:
            raise Error("Expected rank: 1")

        choices = [choice]

        line = f.readline()
        parsed_line = self.parse_ballot_line(contest_id, voter_id, 2, line)
        choices.append(parsed_line[3])

        line = f.readline()
        parsed_line = self.parse_ballot_line(contest_id, voter_id, 3, line)
        choices.append(parsed_line[3])

        return choices


    def parse_ballot_line(self, expected_contest_id, expected_voter_id, expected_rank, line):
        """
        Return a parsed line, or raise an Exception on failure.

        """
        parsed_line = self.parse_line(line)

        if parsed_line[0] != expected_contest_id:
            raise Error("Expected contest id: %s" % expected_contest_id)
        if parsed_line[1] != expected_voter_id:
            raise Error("Expected voter id: %s" % expected_voter_id)
        if parsed_line[2] != expected_rank:
            raise Error("Expected rank: %s" % expected_rank)

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



