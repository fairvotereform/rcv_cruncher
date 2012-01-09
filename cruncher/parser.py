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

    def __init__(self, input_format, on_ballot, encoding=None):
        self.encoding = encoding
        self.input_format = input_format
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

        line_number = 0
        input_format = self.input_format

        try:
            try:
                while True:
                    line = f.readline()
                    if not line:
                        _log.info("Read %d lines." % line_number)
                        break
                    line_number += 1

                    ballot, line_number = input_format.read_ballot(f, line, line_number)

                    self.on_ballot(ballot)

            except Error:
                raise
            except Exception, ex:
                reraise(Error(ex))
        except Error, err:
            err.add("File line number: %d" % line_number)
            reraise(err)

