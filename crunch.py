#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#
"""

YAML CONFIG FILE:

Leave the "finalists" value empty if the contest was decided in the first
round.  For example:

  - label: D2
    input_data: D02
    winner: "Michela Alioto-Pier"
    finalists:

TODO: complete this.

"""

from datetime import datetime
import logging
import os
import sys

from cruncher.argparser import create_argparser
from cruncher.ballot_analyzer import BallotAnalyzer
from cruncher import common
from cruncher.common import find_in_map
from cruncher.input_format import parse_input_format
from cruncher.parser import parse_master, BallotParser, Contest
from cruncher.reporter import Reporter
from cruncher.stats import Stats


_log = logging.getLogger(__name__)


ENCODING_OUTPUT_FILE = 'utf-8'
STATS_HEADER = """\
RCV RESULTS KEY

Total:         total number of ballots, including undervotes.

Voted:         number of ballots with at least one ranking marked (or overvoted).
Undervoted:    total minus voted.

N-Candidate:   number of voted ballots with N valid distinct candidate rankings.
               A valid ranking is a ranking not preceded by an overvote.
               For example, the 0-Distinct ballots are the first-round
               overvotes, i.e. the voted ballots whose first marked ranking
               is an overvote.

Has overvote:  number of ballots with an overvoted ranking at some ranking.
Has duplicate: number of ballots with the same candidate marked more than once.
Has skipped:   number of ballots with an unmarked ranking before a marked ranking.
Irregular:     number of voted ballots with at least one of the following:
               an overvote, a duplicate candidate, or a skipped ranking (see
               above for descriptions).  Note that these categories are not
               mutually exclusive, for example an unmarked ranking followed by
               an overvoted ranking.

R1-Overvotes:  number of ballots counting as an overvote in the first round.


"""

def configure_logging(logging_level=None):
    """Configure logging for standard purposes.

    Args:
      logging_level: The minimum logging level to log.
                     Defaults to logging.INFO.

    """
    # If the stream does not define an "encoding" data attribute, the
    # logging module can throw an error like the following:
    #
    # Traceback (most recent call last):
    #   File "/System/Library/Frameworks/Python.framework/Versions/2.6/...
    #         lib/python2.6/logging/__init__.py", line 761, in emit
    #     self.stream.write(fs % msg.encode(self.stream.encoding))
    # LookupError: unknown encoding: unknown
    if logging_level is None:
        logging_level = logging.INFO

    # Create the handler.
    #
    # The stream is a file-like object to which to log.  The stream must
    # define an "encoding" data attribute, or else logging raises an error.
    stream = sys.stderr
    handler = logging.StreamHandler(stream)
    formatter = logging.Formatter("%(name)s: [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)

    # The root logger.
    logger = logging.getLogger()

    logger.setLevel(logging_level)
    logger.addHandler(handler)

    _log.debug("Debug logging enabled.")

def find_candidate_id(candidate_dict, name_to_find):
    return find_in_map(candidate_dict, name_to_find)

def get_contest_id(contest_config, contest_ids):
    """Return the contest_id for a contest_config."""
    contest_name = contest_config.get('name')
    if len(contest_ids) == 1:
        # The contest will not have a name configured if there is only one.
        assert contest_name is None
        contest_id = contest_ids.values()[0]
    else:
        contest_id = contest_ids[contest_name]
    return contest_id


def make_contest_infos(analyzer, contest_configs, contest_dict, contest_ids):
    """
    Return a dict mapping contest_id to ContestInfo object.
    """
    contest_infos = {}

    for contest_config in contest_configs:
        contest_id = get_contest_id(contest_config, contest_ids)
        contest_name, candidate_dict = contest_dict[contest_id]
        winner_id = find_candidate_id(candidate_dict, contest_config['winner'])
        
        finalist_ids = []
        for candidate in contest_config['finalists']:
            finalist_ids.append(find_candidate_id(candidate_dict, candidate))

        contest_info = {
            'contest': Contest(contest_name, candidate_dict, winner_id, finalist_ids),
            'config': contest_config, 
            'stats': Stats(candidates=candidate_dict.keys(), winner_id=winner_id),
            'analyzer': analyzer,
        }

        contest_infos[contest_id] = contest_info

    return contest_infos


def get_download_paths(election_label, input_format, input_config,
                       contest_configs, data_dir):
    """
    Return an iterable of (contest_configs, path_pair).
    """
    # A list of (contest_configs, dir_name, urls).
    # Each element of this list corresponds to a set of files that can
    # be independently downloaded and parsed.
    download_infos = []
    if 'single_source' in input_config:
        # Then all contests are contained in a single file.
        #
        # The "single_source" value should be a list.
        sources = input_config['single_source']
        download_infos.append((contest_configs, "election", sources))
    else:
        # Then each contest is contained in a separate file.

        # This can be a string or list of strings.
        election_sources = input_config['source']
        if isinstance(election_sources, str):
            election_sources = [election_sources]
        for contest_config in contest_configs:
            label = contest_config['label']

            ### OAB
            urls = ["none"] #[source % label for source in election_sources]
            ###            

            configs = [contest_config]
            download_infos.append((configs, label, urls))

    # An iterable of (contest_configs, path_pair).
    path_infos = []
    for configs, dir_name, urls in download_infos:
        if input_config['type'] == 'sf-2008':
            path_pair = input_format.get_data(election_label, dir_name, urls, data_dir)
        else:
            path_pair = input_format.get_data(contest_config)
        path_infos.append((configs, path_pair))

    return path_infos


def parse_download(analyzer, input_format, reporter, contest_configs, path_pair):
    master_path, ballot_path = path_pair

    # The contest_dict dictionary maps contest_id to (contest_name, candidate_dict).
    contest_dict = parse_master(input_format, master_path)
    contest_ids = {contest_dict[contest_id][0]: contest_id for contest_id in contest_dict.keys()}

    contest_infos = make_contest_infos(analyzer, contest_configs, contest_dict, contest_ids)

    parser = BallotParser(input_format=input_format, contest_infos=contest_infos)
    parser.parse_ballots(ballot_path)

    download_metadata = input_format.get_download_metadata(master_path)

    for contest_config in contest_configs:
        contest_id = get_contest_id(contest_config, contest_ids)
        contest_info = contest_infos[contest_id]
        reporter.add_contest(contest_info, download_metadata=download_metadata)


def main(sys_argv):
    import pdb; pdb.set_trace()

    start_time = datetime.now()
    ns = create_argparser().parse_args(sys_argv[1:])

    if not os.path.exists(ns.output_dir):
        os.mkdir(ns.output_dir)

    configure_logging(logging.DEBUG)

    election_config = common.unserialize_yaml_file(ns.config_path)

    election_label = election_config['election_label']
    election_name = election_config['election_name']
    input_config = election_config['input_format']

    input_format = parse_input_format(input_config, suppress_download=ns.suppress_download)
    analyzer = BallotAnalyzer(undervote=input_format.undervote, overvote=input_format.overvote)

    utc_now = datetime.utcnow()
    reporter = Reporter(election_name=election_name.upper(), template_path='templates/report.mustache')

    contest_configs = []
    for data in election_config['contests']:
        data['label'] = data.get('label') or data['source']
        data['finalists'] = data['finalists'] or []
        contest_configs.append(data)

    # Download all data before trying to process.  This simplifies certain
    # types of troubleshooting because we can turn off downloading for
    # subsequent runs.

    ### this should go away, just add/change feilds of YAML
    download_infos = get_download_paths(election_label, input_format, input_config,
                                       contest_configs, ns.data_dir)

    #candidate count calculated
    for contest_configs, path_pair in download_infos:
        parse_download(analyzer, input_format, reporter, contest_configs, path_pair)

    datetime_local, local_tzname = common.utc_datetime_to_local_datetime_tzname(utc_now)
    report = reporter.generate(datetime_local, local_tzname)

    try:
        print report
    except UnicodeEncodeError:
        # Windows seems to have trouble with some unicode characters, e.g. the "Ó" in GASCÓN.
        _log.warn("Error printing report to console (probably because of special characters.")

    output_path = os.path.join(ns.output_dir, "rcv_stats_%s.html" % election_label)
    common.write_to_file(report, output_path)

    print "Completed in: %s" % (datetime.now() - start_time)


if __name__ == "__main__":
    main(sys.argv)
