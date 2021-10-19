"""
A set of tests that are shared with the Universal RCV Tabulator.
These tests each have three files:
    1. A configuration file
    2. A CVR file
    3. An expected output file

The RCV cruncher does not support all RCV variants that the Tabulator does.
Still, it should produce the same results on most of these contests.

While we have not documented the file formats here, we hope that the RCV Tests
submodule will eventually contain its own documentation which we can reference from here.
"""

import decimal
import json
import os
import pytest
from rcvformats.schemas import universaltabulator
from unittest import TestCase

import rcv_cruncher
import rcv_cruncher.parsers as parsers

def get_candidate_codes_dict(test_config: dict) -> dict:
    """
    The config file has a list of candidates, each of which is a dictionary
    containing a code, a candidate name, and whether or not the candidate has been
    eliminated.

    This converts that format into a dict mapping codes to names, for use in converting
    data from CVR data (where short codes are important) to more human-ingestible formats
    where the actual name is useful.
    """
    codes_dict = {}
    for c in test_config['candidates']:
        codes_dict[c['code']] = c['name']

    # Handle undeclared write-in
    write_in_code = test_config['cvrFileSources'][0]['undeclaredWriteInLabel']
    codes_dict[write_in_code] = "Undeclared Write-ins"

    return codes_dict

def get_events_each_round(rcv: rcv_cruncher.RCV, codes_dict: dict) -> list:
    """
    For each round, return a dict of events.
    Each dict of events is a key, value pair where the key is a candidate name and
    the value is either 'eliminated' or 'elected'.
    """
    outcomes = rcv.get_candidate_outcomes()
    events = [{}] * rcv.n_rounds()
    for outcome in outcomes:
        round_eliminated = outcome['round_eliminated']
        round_elected = outcome['round_elected']
        if round_eliminated is not None:
            events[round_eliminated-1] = {codes_dict[outcome['name']]: 'eliminated'}
        if round_elected is not None:
            events[round_elected-1] = {codes_dict[outcome['name']]: 'elected'}
    return events

def get_tally_results(rcv: rcv_cruncher.RCV,
                      codes_dict: dict,
                      what_happened_each_round: list,
                      round_i_1indexed: int) -> dict:
    """
    Creates the "tallyResults" dict for round_i, a list of who was elected/eliminated
    this round and where their votes went.
    """
    # Gather data about the round
    round_transfer_dict = rcv.get_round_transfer_dict(round_i_1indexed)
    what_happened_this_round = what_happened_each_round[round_i_1indexed - 1]

    # Only meaningful if there is exactly 1 event
    if not what_happened_this_round:
        return []
    if len(what_happened_this_round) > 1:
        raise NotImplementedError("Only one event per round is supported, but found " +
                                  what_happened_this_round)

    # Get that 1 event
    what_happened_name = next(iter(what_happened_this_round.values()))
    what_happened_event = next(iter(what_happened_this_round.keys()))

    # Begin building the dictionary
    tally_results = {what_happened_name: what_happened_event, 'transfers': {}}

    # Build the 'transfers' dict
    for code, val in round_transfer_dict.items():
        if code == 'exhaust':
            name = 'Inactive Ballots'
        else:
            name = codes_dict[code]
        if val != 0 and not val.is_nan():
            tally_results['transfers'][name] = str(val)

    return [tally_results]

def to_urcvt_format(rcv: rcv_cruncher.RCV, test_config: dict) -> dict:
    """
    Given a tabulated election and its corresponding config file,
    produce a UniversalTabulator-Compatible summary file.
    """
    codes_dict = get_candidate_codes_dict(test_config)
    what_happened_each_round = get_events_each_round(rcv, codes_dict)

    data = {}
    data['config'] = {
        'contest': test_config['outputSettings']['contestName'],
        'date': test_config['outputSettings']['contestDate'],
        'jurisdiction': test_config['outputSettings']['contestJurisdiction'],
        'office': test_config['outputSettings']['contestOffice'],
        'threshold': rcv.get_win_threshold() or 0
    }
    data['results'] = []
    for i in range(rcv.n_rounds()):
        round_i_1indexed = i + 1
        round_tally_dict = rcv.get_round_tally_dict(round_i_1indexed)
        data['results'].append({
            'round': round_i_1indexed,
            'tally': {codes_dict[key]: str(val) for key, val in round_tally_dict.items()},
            'tallyResults': get_tally_results(rcv, codes_dict, what_happened_each_round, round_i_1indexed)
        })


    schema = universaltabulator.SchemaV0()
    is_valid = schema.validate_data(data)
    if not is_valid:
        print(schema.last_error())
    assert is_valid

    return data

# We know this fails currently
@pytest.mark.xfail
def test_all():
    """
    Opens each directory in the tests, looks for the config file and expected summary file,
    and attempts to tabulate the corresponding CVR.
    """
    all_tests_directory_path = './tests/contest_sets/urcvt-tests/'
    each_dir = os.listdir(all_tests_directory_path)

    successes = 0
    errors = []
    for this_test_dir_name in each_dir:
        if not os.path.isdir(os.path.join(all_tests_directory_path, this_test_dir_name)):
            # Ignore README, license, etc
            continue

        try:
            run_test(all_tests_directory_path, this_test_dir_name)
            successes += 1
        except Exception as e:
            errors.append((this_test_dir_name, e))
    for e in errors:
        print('\033[1m%-50s\033[0;0m:  %s' % (e[0], e[1]))
    assert successes > 0

def run_test(all_tests_directory_path, this_test_dir_name):
    """
    Attempts to tabulate whatever is in the given directory.
    """
    # Construct filenames
    test_path = os.path.join(all_tests_directory_path, this_test_dir_name)
    config_path = os.path.join(test_path, this_test_dir_name + '_config.json')
    expected_summary_path = os.path.join(test_path, this_test_dir_name + '_expected_summary.json')

    # Open config file
    with open(config_path, 'r') as f:
        test_config = json.load(f)

    # Read the CVR path
    cvr_path = os.path.join(test_path, test_config['cvrFileSources'][0]['filePath'])

    # TODO after this point, need to customize the tests to load the CVRs correctly
    if os.path.isdir(cvr_path):
        raise NotImplementedError("Cannot load CVR directories: " + cvr_path)

    rcv = rcv_cruncher.SingleWinner(
            jurisdiction='Minneapolis',
            state='MN',
            year='2017',
            office='Mayor',
            parser_func=parsers.cruncher_csv,
            parser_args={'cvr_path': cvr_path},
            exhaust_on_duplicate_candidate_marks=True,
            exhaust_on_overvote_marks=True,
            combine_writein_marks=True)
    urcvt_format = to_urcvt_format(rcv, test_config)

    with open(expected_summary_path, 'r') as f:
        expected_data = json.load(f)

    TestCase().assertDictEqual(expected_data, urcvt_format)
