# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

import codecs
import logging
import os
import sys

from .common import reraise, Error


_log = logging.getLogger(__name__)


ENCODING_DATA_FILES  = 'utf-8'


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

    def __repr__(self):
        return "<Contest: name={0}>".format(self.name)

    @property
    def candidate_count(self):
        # Don't include WRITE-IN as a candidate.
        candidate_map = self.candidate_dict
        names = candidate_map.values()
        count = len(names)
        for (candidate_id, name) in candidate_map.iteritems():
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
                    try:
                        contest_info = contest_infos[contest_id]
                    except KeyError:
                        raise Exception("contest_infos does not contain id {0}: {1}".
                                        format(contest_id, contest_infos))
                    ballot_handler = contest_info.ballot_handler
                    ballot_handler.on_ballot(ballot)

            except Error:
                raise
            except Exception, ex:
                reraise(Error(ex))
        except Error, err:
            err.add("File line number: %s" % line)
            reraise(err)

