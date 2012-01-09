# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

import logging


_log = logging.getLogger(__name__)


def parse_input_format(config):
    return StandardFormat(config)


class StandardFormat(object):

    def __init__(self, config):

        self.ballot_file_glob = config['ballot_file_glob']
        self.election_source = config['source']
        self.master_file_glob = config['master_file_glob']

