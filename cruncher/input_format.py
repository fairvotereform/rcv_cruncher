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
from .common import write_to_file
from . import downloading
from .ballot_analyzer import UNDERVOTE, OVERVOTE

_log = logging.getLogger(__name__)

DOWNLOAD_DIRECTORY_PREFIX = 'download_'
UNZIP_DIRECTORY_NAME = 'download'

def parse_input_format(config):
    return {
        'rcv-calc': RCVCalcFormat,
        'sf-2008': SF2008Format,
        'mn': MNCalcFormat}[config]()

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
    _log.info("downloading url: %s", url)
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

class MNCalcFormat(object):
    skip_first = True
    
    def read_ballot(self, f, line, line_number):
        choices = [{'undervote': UNDERVOTE, 'overvote': OVERVOTE}.get(i,i)
                     for i in line.split(',')[1:-1]]
    
        if choices == ['','','']: #MSP data sometimes ends with total line and blank candidates
            return False
        return 1, choices, line_number

class RCVCalcFormat(object):
    skip_first = False

    """
    Input format for pre-2008 elections.  Using David Cary's RcvCalc-formatted data.

    """

    def __init__(self):

        self.undervote = None 
        self.overvote  = None 

    def get_download_metadata(self, _):
        return downloading.DownloadMetadata()

    def parse_master_file(self, f):
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

        self.overvote = overvote
        self.undervote = undervote

        return {1: (contest_name, candidate_dict)}

    def read_ballot(self, _, line, line_number):
        """
        Read and return an RCV ballot.

        Example:

            '%# 0062 %# JM>DH>--'

        """
        parts = line.split()
        ballot = parts[-1]
       
        ### OAB 
        choices = [{self.undervote: UNDERVOTE, self.overvote: OVERVOTE}.get(i,i) for i in ballot.split('>')]
        return int(parts[-3]), choices, line_number

def get_data(ns, input_config, election_label, dir_name, urls):
    """
    Download data if necessary, and return master and ballot paths.

    """
    if ns.data_dir is None:
        raise Exception("Need to provide data directory.")

    ensure_dir(ns.data_dir)
    election_dir = os.path.join(ns.data_dir, election_label)
    ensure_dir(election_dir)
    contest_dir = os.path.join(election_dir, dir_name)

    if not ns.suppress_download:
        download_data(urls, contest_dir)
    download_dir = most_recent_download_dir(contest_dir)

    _log.info("Using most recent download directory: %s", download_dir)

    unzip_dir = os.path.join(download_dir, UNZIP_DIRECTORY_NAME)
    master_path = get_path(unzip_dir, input_config['master_file_glob'])
    ballot_path = get_path(unzip_dir, input_config['ballot_file_glob'])

    return master_path, ballot_path



class SF2008Format(object):
    skip_first = False

    def get_download_metadata(self, master_path):
        unzipped_dir = os.path.dirname(master_path)
        info_path = os.path.join(unzipped_dir, os.pardir, common.INFO_FILE_NAME)
        download_dict = common.unserialize_yaml_file(info_path)

        download_metadata = downloading.DownloadMetadata()
        download_metadata.__dict__ = download_dict

        return download_metadata

    def parse_master_file(self, f):
        """
        Parse contest data from the given file, and return contest data.
        Some sample lines:
        Candidate 0000111JUAN-ANTONIO CARBALLO                             0000001000002700
        Contest   0000027Board of Supervisors, District 2                  0000038000000000
        """
        contest_dict = {}

        while True:
            line = f.readline()
            if not line:
                break

            record_type = line[0:10].strip()
            record_id = int(line[10:17])
            description = line[17:67].strip()
            # For candidate rows, this is the contest ID.
            other_id = int(line[74:81])

            if record_type == "Contest":
                contest_data = contest_dict.setdefault(record_id, [None, {}])
                contest_data[0] = description
                continue

            if record_type == "Candidate":
                _, candidate_dict = contest_dict.setdefault(other_id, [None, {}])
                candidate_dict[record_id] = description

        return contest_dict

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

        ### OAB removing limit on ballot choices, also LBYL
        rank = 1
        choices = []
        contest_id = None
        voter_id = None
        while True:
            parsed_line = self._parse_ballot_line(line, rank, contest_id, voter_id)
            if not parsed_line:
                f.seek(-len(line),1)
                line_number -= 1
                break
            contest_id, voter_id, _, choice = parsed_line
            choices.append(choice)
            line_number += 1
            rank += 1
            line = f.readline()
            if not line:
                break

        return contest_id, choices, line_number
    
    def _parse_ballot_line(self, line, expected_rank, expected_contest_id=None, expected_voter_id=None):
        """
        Return a parsed line, or False on failure.
        A sample input--

        000000700001712400000090020000331001000012600

        """
        contest_id = int(line[0:7])
        if expected_contest_id is not None and contest_id != expected_contest_id:
            return False

        voter_id = int(line[7:16])
        if expected_voter_id is not None and voter_id != expected_voter_id:
            return False

        rank = int(line[33:36])
        if expected_rank is not None and rank != expected_rank:
            return False
        
        candidate_id = int(line[36:43])
        undervote = UNDERVOTE if int(line[44]) else 0
        overvote = OVERVOTE if int(line[43]) else 0
        choice = candidate_id or undervote or overvote

        return (contest_id, voter_id, rank, choice)

