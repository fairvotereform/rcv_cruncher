# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

from datetime import datetime
import glob
import logging
import os
from zipfile import ZipFile

from . import common
from .common import ensure_dir
from .common import write_to_file
from . import downloading


_log = logging.getLogger(__name__)


DOWNLOAD_DIRECTORY_PREFIX = 'download_'
UNZIP_DIRECTORY_NAME = 'download'


def parse_input_format(config):
    format_type = config['type']

    if format_type == 'rcv-calc':
        format = RCVCalcFormat(config)
    elif format_type == 'sf-2008':
        format = SF2008Format(config)
    else:
        raise Exception("Unknown input format: %s" % repr(format_type))

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


def download_data(url, contest_dir):
    """
    Download and extract the election zip file.

    """
    utc_now = datetime.utcnow()

    ensure_dir(contest_dir)
    readme_path = os.path.join(contest_dir, 'README.txt')
    write_to_file(u"This directory should be empty except for auto-downloaded directories.", readme_path)

    download_dir_name = DOWNLOAD_DIRECTORY_PREFIX + utc_now.strftime("%Y%m%d_%H%M%S")
    download_dir = os.path.join(contest_dir, download_dir_name)
    ensure_dir(download_dir)

    zip_path = os.path.join(download_dir, '%s%szip' % (UNZIP_DIRECTORY_NAME, os.extsep))

    downloading.download(url, zip_path)

    unzip_dir = os.path.join(download_dir, UNZIP_DIRECTORY_NAME)
    zip_file = ZipFile(zip_path, 'r')
    zip_file.extractall(unzip_dir)

    metadata = downloading.create_download_metadata(url, utc_now)

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

        self.input_dir = config['input_dir']

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

        return contest_name, candidate_dict


class SF2008Format(object):

    def __init__(self, config, output_encoding=None):

        self.ballot_file_glob = config['ballot_file_glob']
        self.election_source = config['source']
        self.master_file_glob = config['master_file_glob']

    def get_data(self, election_label, contest_label, contest_config, data_dir):
        """
        Download data if necessary, and return master and ballot paths.

        """
        if data_dir is None:
            raise Exception("Need to provide data directory.")

        contest_source = contest_config['source']

        source = self.election_source + contest_source
        master_file_glob = self.master_file_glob
        ballot_file_glob = self.ballot_file_glob

        ensure_dir(data_dir)

        election_dir = os.path.join(data_dir, election_label)
        ensure_dir(election_dir)

        contest_dir = os.path.join(election_dir, contest_label)

        download_data(source, contest_dir)
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

        return contest_name, candidate_dict

