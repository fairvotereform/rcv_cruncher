# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

from datetime import datetime
import glob
import logging
import os
import urlparse
from zipfile import ZipFile

from . import common
from .common import ensure_dir
from .common import reraise
from .common import write_to_file
from .common import Error
from . import downloading


_log = logging.getLogger(__name__)

DOWNLOAD_DIRECTORY_PREFIX = 'download_'
UNZIP_DIRECTORY_NAME = 'download'


def parse_input_format(config, suppress_download=False):
    format_type = config['type']

    if format_type == 'rcv-calc':
        cls = RCVCalcFormat
    elif format_type == 'sf-2008':
        cls = SF2008Format
    else:
        raise Exception("Unknown input format: %s" % repr(format_type))

    format = cls(config, suppress_download=suppress_download)
    return format


def get_path(dir_path, file_glob):
    """
    Return the path in dir_path matching file_glob.

    """
    glob_path = os.path.join(dir_path, file_glob)
    paths = glob.glob(glob_path)

    if len(paths) < 1:
        raise AssertionError("No path found matching: %s" % glob_path)
    if len(paths) > 1:
        raise AssertionError("More than one path found matching: %s" % glob_path)

    return paths[0]


def most_recent_download_dir(contest_dir):

    file_name = DOWNLOAD_DIRECTORY_PREFIX + "*"
    glob_path = os.path.join(contest_dir, file_name)
    paths = glob.glob(glob_path)

    if not paths:
        raise Exception("Downloaded files not found in: %s" % contest_dir)

    paths.sort()

    return paths[-1]


def download_url(url, download_dir):
    target_dir = os.path.join(download_dir, UNZIP_DIRECTORY_NAME)
    ensure_dir(target_dir)

    parsed = urlparse.urlparse(url)
    path = parsed.path
    basename = os.path.basename(path)

    if not basename.endswith(".zip"):
        # Then just download the file directly.
        target_path = os.path.join(target_dir, basename)
        downloading.download(url, target_path)
        return
    # Otherwise, we have a zip file.

    zip_path = os.path.join(download_dir, basename)

    downloading.download(url, zip_path)

    zip_file = ZipFile(zip_path, 'r')
    zip_file.extractall(target_dir)


def download_data(urls, contest_dir):
    """
    Download and extract the election zip file.

    Arguments:

      urls: an URL of list of URLs.

    """
    if isinstance(urls, str):
        urls = [urls]

    utc_now = datetime.utcnow()

    ensure_dir(contest_dir)
    readme_path = os.path.join(contest_dir, 'README.txt')
    write_to_file(u"This directory should be empty except for auto-downloaded directories.", readme_path)

    download_dir_name = DOWNLOAD_DIRECTORY_PREFIX + utc_now.strftime("%Y%m%d_%H%M%S")
    download_dir = os.path.join(contest_dir, download_dir_name)
    ensure_dir(download_dir)

    for url in urls:
        download_url(url, download_dir)

    metadata = downloading.create_download_metadata(urls, utc_now)

    text = """\
# This file is auto-generated.  Do not modify this file.
# Date time strings are in ISO 8601 format YYYY-MM-DDTHH:MM:SS.
"""

    text += common.yaml_serialize(metadata)

    info_path = os.path.join(download_dir, common.INFO_FILE_NAME)
    write_to_file(text, info_path)


class RCVCalcFormat(object):

    """
    Input format for pre-2008 elections.  Using David Cary's RcvCalc-formatted data.

    """

    def __init__(self, config):

        self.undervote = None
        self.overvote  = None

        self.input_dir = config['input_dir']

    def get_download_metadata(self, master_path):
        return downloading.DownloadMetadata()

    def get_data(self, election_label, contest_label, contest_config, data_dir):
        """
        Return master and ballot paths.

        """
        file_prefix = contest_config['input_data']

        master_file = "%s-Cntl.txt" % file_prefix
        ballot_file = "%s-Ballots.txt" % file_prefix

        make_path = lambda file_name: os.path.join(self.input_dir, file_name)

        paths = map(make_path, [master_file, ballot_file])

        return paths

    def parse_contest(self, f):
        """
        Parse contest data from the given file, and return contest data.

        """
        candidate_dict = {}

        while True:
            line = f.readline()
            if not line:
                break

            parsed = line.split(":")
            record_type = parsed[0]

            if record_type == 'Title':
                contest_name = parsed[2].strip()
            elif record_type == 'Candidate':
                label = parsed[1].strip()
                name = parsed[2].strip()

                candidate_dict[label] = name
            elif record_type == 'OverVote':
                overvote = parsed[1].strip()
            elif record_type == 'UnderVote':
                undervote = parsed[1].strip()

        # TODO: these values should be set more deliberately rather
        #       than as side effects.
        self.overvote = overvote
        self.undervote = undervote

        return contest_name, candidate_dict

    def read_ballot(self, f, line, line_number):
        """
        Read and return an RCV ballot.

        Example:

            '%# 0062 %# JM>DH>--'

        """
        parts = line.split()
        ballot = parts[-1]
        choices = ballot.split('>')

        return choices, line_number


class SF2008Format(object):

    def __init__(self, config, output_encoding=None, suppress_download=False):

        self.expected_contest_id = None
        self.undervote = -1
        self.overvote  = -2

        # This can be a string or list of strings.
        election_sources = config['source']
        ballot_file_glob = config['ballot_file_glob']
        master_file_glob = config['master_file_glob']

        if isinstance(election_sources, str):
            election_sources = [election_sources]

        self.election_sources = election_sources
        self.ballot_file_glob = ballot_file_glob
        self.master_file_glob = master_file_glob
        self.suppress_download = suppress_download

    def get_download_metadata(self, master_path):
        unzipped_dir = os.path.dirname(master_path)
        info_path = os.path.join(unzipped_dir, os.pardir, common.INFO_FILE_NAME)
        download_dict = common.unserialize_yaml_file(info_path)

        download_metadata = downloading.DownloadMetadata()
        download_metadata.__dict__ = download_dict

        return download_metadata

    def get_data(self, election_label, contest_label, contest_config, data_dir):
        """
        Download data if necessary, and return master and ballot paths.

        """
        if data_dir is None:
            raise Exception("Need to provide data directory.")

        contest_source = contest_config['source']

        urls = []
        for election_source in self.election_sources:
            url = election_source % contest_source
            urls.append(url)

        master_file_glob = self.master_file_glob
        ballot_file_glob = self.ballot_file_glob

        ensure_dir(data_dir)

        election_dir = os.path.join(data_dir, election_label)
        ensure_dir(election_dir)

        contest_dir = os.path.join(election_dir, contest_label)

        if not self.suppress_download:
            download_data(urls, contest_dir)
        download_dir = most_recent_download_dir(contest_dir)

        _log.info("Using most recent download directory: %s" % download_dir)

        unzip_dir = os.path.join(download_dir, UNZIP_DIRECTORY_NAME)
        master_path = get_path(unzip_dir, master_file_glob)
        ballot_path = get_path(unzip_dir, ballot_file_glob)

        return master_path, ballot_path

    def _parse_master_line(self, line):
        """
        Parse the line, and return a tuple.

        A sample line--

        "Candidate 0000120JANET REILLY                                      0000001000000700"

        """
        # We only care about the first three fields: Record_Type, Id, and Description.
        record_type = line[0:10].strip()
        record_id = int(line[10:17])
        description = line[17:67].strip()

        return record_type, record_id, description

    def parse_contest(self, f):
        """
        Parse contest data from the given file, and return contest data.

        """
        candidate_dict = {}

        while True:
            line = f.readline()
            if not line:
                break

            record_type, record_id, description = self._parse_master_line(line)

            if record_type == "Contest":
                contest_id = record_id
                contest_name = description
                continue

            if record_type == "Candidate":
                candidate_dict[record_id] = description

        self.expected_contest_id = contest_id

        return contest_name, candidate_dict

    def read_ballot(self, f, line, line_number):
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
            parsed_line = self._parse_ballot_line(line, 1)

            try:
                contest_id, voter_id, rank, choice = parsed_line

                choices = [choice]

                line_number += 1
                line = f.readline()
                parsed_line = self._parse_ballot_line(line, 2, expected_voter_id=voter_id)
                choices.append(parsed_line[3])

                line_number += 1
                line = f.readline()
                parsed_line = self._parse_ballot_line(line, 3, expected_voter_id=voter_id)
                choices.append(parsed_line[3])
            except Error:
                raise
            except Exception, ex:
                reraise(Error(ex))
        except Error, err:
            err.add("Ballot line number: %d" % line_number)
            reraise(err)

        return choices, line_number

    def _parse_ballot_line(self, line, expected_rank, expected_voter_id=None):
        """
        Return a parsed line, or raise an Exception on failure.

        """
        parsed_line = None
        try:
            parsed_line = self.parse_line(line)
            contest_id, voter_id, rank, choice = parsed_line

            if contest_id != self.expected_contest_id:
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

