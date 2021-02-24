# flake8: noqa

import csv
import glob
import json
import math
import os
import re
import collections
import decimal
from rcv_cruncher.ballots import cvr
import xmltodict

import pandas as pd

import rcv_cruncher.util as util

decimal.getcontext().prec = 30


def get_parser_dict():
    """Return dictionary of parsers defined in parsers.py

    Returns:
        dictionary: {parser name: parser function object}
    """
    return {
        "burlington2006": burlington2006,
        "cruncher_csv": cruncher_csv,
        "dominion5_2": dominion5_2,
        "dominion5_4": dominion5_4,
        "dominion5_10": dominion5_10,
        "ep": ep,
        "maine": maine,
        "minneapolis": minneapolis,
        "old": old,
        "prm": prm,
        "santafe": santafe,
        "santafe_id": santafe_id,
        "optech": optech,
        #"sf": sf,
        "sf2005": sf2005,
        #"sfnoid": sfnoid,
        "surveyUSA": surveyUSA,
        "unisyn": unisyn,
        "utah": utah
    }


def cruncher_csv(ctx):
    """Reads ballot ranking information stored in csv format.

    Args:
        ctx (dictionary): A dictionary containing key "cvr_path" which points to the cvr file containing ranking information of each ballot. Alternatively, if a key "converted_path" is present in the dictionary, it will be preferred to the "cvr_path" key. Ranking data must be in columns that follow a "rank#" pattern ("rank1", "rank2", etc). Ranking column must appear in order in the csv file.

        If a file called "candidate_codes.csv" exists in the same directory, it will be read and values from the "code" column that are
        found in the cvr file ranks will be replaced values in the "candidate" columns.

    Raises:
        RuntimeError: Error raised if not all parsed rank lists are the same length.

    Returns:
        dictionary: Dictionary containing, at least, two keys, "ranks" containing ballot ranks as list of lists and "weight" containing weight values in the input csv or all 1s if weight column was not present in csv file. Any other columns in csv file will also be included in returned dictionary.
    """

    cvr_path = ctx['converted_path'] if 'converted_path' in ctx else ctx['cvr_path']
    df = pd.read_csv(cvr_path, encoding="utf8")

    # find rank columns
    rank_col = [col for col in df.columns if 'rank' in col.lower()]

    # ensure rank columns are strings
    df[rank_col] = df[rank_col].astype(str)

    # if candidate codes file exist, swap in names
    candidate_codes_fpath = cvr_path.parent / 'candidate_codes.csv'
    if os.path.isfile(candidate_codes_fpath):

        cand_codes = pd.read_csv(candidate_codes_fpath, encoding="utf8")
        cand_codes_dict = {str(code): cand for code, cand in zip(cand_codes['code'], cand_codes['candidate'])}
        replace_dict = {col: cand_codes_dict for col in rank_col}

        df = df.replace(replace_dict)

    # replace skipped ranks and overvotes with constants
    df = df.replace({col: {'under': util.BallotMarks.SKIPPEDRANK,
                           'skipped': util.BallotMarks.SKIPPEDRANK,
                           'undervote': util.BallotMarks.SKIPPEDRANK,
                           'over': util.BallotMarks.OVERVOTE,
                           'overvote': util.BallotMarks.OVERVOTE}
                    for col in rank_col})

    df = df.fillna(util.BallotMarks.SKIPPEDRANK)

    # pull out rank lists
    rank_col_list = [df[col].tolist() for col in rank_col]
    rank_lists = [list(rank_tuple) for rank_tuple in list(zip(*rank_col_list))]

    # double check all ballot ranks are equal length
    if not all([len(i) == len(rank_lists[0]) for i in rank_lists]):
        raise RuntimeError("not all rank lists are same length. debug")

    # assemble dict
    dct = {'ranks': rank_lists}

    # add in non-rank columns
    for col in df.columns:
        if col not in rank_col:
            dct[col] = df[col].tolist()

    # add weight if not present in csv
    if 'weight' not in dct:
        dct['weight'] = [decimal.Decimal('1') for b in dct['ranks']]
    else:
        dct['weight'] = [decimal.Decimal(str(w)) for w in dct['weight']]

    return dct

def dominion5_4(ctx):

    path = ctx['cvr_path']

    # load manifests, with ids as keys
    with open(path / 'ContestManifest.json', encoding="utf8") as f:
        for i in json.load(f)['List']:
            if i['Description'] == ctx['office']:
                current_contest_id = i['Id']
                current_contest_rank_limit = i['NumOfRanks']

    candidate_manifest = {}
    with open(path / 'CandidateManifest.json', encoding="utf8") as f:
        for i in json.load(f)['List']:
            candidate_manifest[i['Id']] = i['Description']

    precinctPortion_manifest = {}
    with open(path / 'PrecinctPortionManifest.json', encoding="utf8") as f:
        for i in json.load(f)['List']:
            precinctPortion_manifest[i['Id']] = {'Portion': i['Description'], 'PrecinctId': i['PrecinctId']}

    precinct_manifest = {}
    if os.path.isfile(path / 'PrecinctManifest.json'):
        with open(path / 'PrecinctManifest.json', encoding="utf8") as f:
            for i in json.load(f)['List']:
                precinct_manifest[i['Id']] = i['Description']

    ballotType_manifest = {}
    with open(path / 'BallotTypeManifest.json', encoding="utf8") as f:
        for i in json.load(f)['List']:
            ballotType_manifest[i['Id']] = i['Description']

    countingGroup_manifest = {}
    with open(path / 'CountingGroupManifest.json', encoding="utf8") as f:
        for i in json.load(f)['List']:
            countingGroup_manifest[i['Id']] = i['Description']

    ballotTypeContest_manifest = {}
    with open(path / 'BallotTypeContestManifest.json', encoding="utf8") as f:
        for i in json.load(f)['List']:

            if i['ContestId'] not in ballotTypeContest_manifest.keys():
                ballotTypeContest_manifest[i['ContestId']] = []

            ballotTypeContest_manifest[i['ContestId']].append(i['BallotTypeId'])

    # read in ballots
    ballot_ranks = []
    ballot_IDs = []
    ballot_precinctPortions = []
    ballot_precincts = []
    ballot_types = []
    ballot_countingGroups = []
    with open(path / 'CvrExport.json', encoding="utf8") as f:
        for contests in json.load(f)['Sessions']:

            # ballotID
            ballotID_search = re.search('Images\\\\(.*)\*\.\*', contests['ImageMask'])
            if ballotID_search:
                ballotID = ballotID_search.group(1)
            else:
                print('regex is not working correctly. debug')
                exit(1)

            countingGroup = countingGroup_manifest[contests['CountingGroupId']]

            # for each session use original, or if isCurrent is False,
            # use modified
            if contests['Original']['IsCurrent']:
                current_contests = contests['Original']
            else:
                current_contests = contests['Modified']

            # precinctId for this ballot
            precinctPortion = precinctPortion_manifest[current_contests['PrecinctPortionId']]['Portion']
            precinctId = precinctPortion_manifest[current_contests['PrecinctPortionId']]['PrecinctId']

            precinct = None
            if precinct_manifest:
                precinct = precinct_manifest[precinctId]

            # ballotType for this ballot
            ballotType = ballotType_manifest[current_contests['BallotTypeId']]

            if len(current_contests['Cards']) > 1:
                print('"Cards" has length greater than 1, not prepared for this. debug')
                exit(1)

            ballot_contest_marks = None
            for ballot_contest in current_contests['Cards'][0]['Contests']:
                if ballot_contest['Id'] == current_contest_id:
                    ballot_contest_marks = ballot_contest['Marks']

            # skip ballot if didn't contain contest
            if ballot_contest_marks is None:
                continue

            # check for marks on each rank expected for this contest
            currentRank = 1
            current_ballot_ranks = []
            while currentRank <= current_contest_rank_limit:

                # find any marks that have the currentRank and aren't Ambiguous
                currentRank_marks = [i for i in ballot_contest_marks
                                     if i['Rank'] == currentRank and i['IsAmbiguous'] is False]

                currentCandidate = '**error**'

                if len(currentRank_marks) == 0:
                    currentCandidate = util.BallotMarks.SKIPPEDRANK
                elif len(currentRank_marks) > 1:
                    currentCandidate = util.BallotMarks.OVERVOTE
                else:
                    currentCandidate = candidate_manifest[currentRank_marks[0]['CandidateId']]

                if currentCandidate == '**error**':
                    raise RuntimeError('error in filtering marks. debug')

                current_ballot_ranks.append(currentCandidate)
                currentRank += 1

            ballot_ranks.append(current_ballot_ranks)
            ballot_precinctPortions.append(precinctPortion)
            ballot_precincts.append(precinct)
            ballot_IDs.append(ballotID)
            ballot_types.append(ballotType)
            ballot_countingGroups.append(countingGroup)

    ballot_dict = {'ranks': ballot_ranks,
                   'weight': [decimal.Decimal('1')] * len(ballot_ranks),
                   'ballotID': ballot_IDs,
                   'precinctPortion': ballot_precinctPortions,
                   'ballot_type': ballot_types,
                   'countingGroup': ballot_countingGroups}

    # make sure precinctManifest was part of CVR, otherwise exclude precinct column
    if len(ballot_precincts) != sum(i is None for i in ballot_precincts):
        ballot_dict['precinct'] = ballot_precincts

    # check ballotIDs are unique
    if len(set(ballot_dict['ballotID'])) != len(ballot_dict['ballotID']):
        print("some non-unique ballot IDs")
        exit(1)

    return ballot_dict

def dominion5_10(ctx):

    path = ctx['cvr_path']

    # load manifests, with ids as keys
    with open(path / 'ContestManifest.json', encoding="utf8") as f:
        for i in json.load(f)['List']:
            if i['Description'] == ctx['office']:
                current_contest_id = i['Id']
                current_contest_rank_limit = i['NumOfRanks']

    candidate_manifest = {}
    with open(path / 'CandidateManifest.json', encoding="utf8") as f:
        for i in json.load(f)['List']:
            candidate_manifest[i['Id']] = i['Description']

    precinctPortion_manifest = {}
    with open(path / 'PrecinctPortionManifest.json', encoding="utf8") as f:
        for i in json.load(f)['List']:
            precinctPortion_manifest[i['Id']] = {'Portion': i['Description'], 'PrecinctId': i['PrecinctId']}

    precinct_manifest = {}
    if os.path.isfile(path / 'PrecinctManifest.json'):
        with open(path / 'PrecinctManifest.json', encoding="utf8") as f:
            for i in json.load(f)['List']:
                precinct_manifest[i['Id']] = i['Description']

    district_manifest = {}
    with open(path / 'DistrictManifest.json', encoding="utf8") as f:
        for i in json.load(f)['List']:
            district_manifest[i['Id']] = {'District': i['Description'], 'DistrictTypeId': i['DistrictTypeId']}

    districtType_manifest = {}
    with open(path / 'DistrictTypeManifest.json', encoding="utf8") as f:
        for i in json.load(f)['List']:
            districtType_manifest[i['Id']] = i['Description']

    districtPrecinctPortion_manifest = {}
    with open(path / 'DistrictPrecinctPortionManifest.json', encoding="utf8") as f:
        for i in json.load(f)['List']:
            districtPrecinctPortion_manifest[i['PrecinctPortionId']] = i['DistrictId']

    ballotType_manifest = {}
    with open(path / 'BallotTypeManifest.json', encoding="utf8") as f:
        for i in json.load(f)['List']:
            ballotType_manifest[i['Id']] = i['Description']

    countingGroup_manifest = {}
    with open(path / 'CountingGroupManifest.json', encoding="utf8") as f:
        for i in json.load(f)['List']:
            countingGroup_manifest[i['Id']] = i['Description']

    ballotTypeContest_manifest = {}
    with open(path / 'BallotTypeContestManifest.json', encoding="utf8") as f:
        for i in json.load(f)['List']:

            if i['ContestId'] not in ballotTypeContest_manifest.keys():
                ballotTypeContest_manifest[i['ContestId']] = []

            ballotTypeContest_manifest[i['ContestId']].append(i['BallotTypeId'])

    tabulator_manifest = {}
    with open(path / 'TabulatorManifest.json', encoding="utf8") as f:
        for i in json.load(f)['List']:
            tabulator_manifest[i['Id']] = i['VotingLocationName']

    # read in ballots
    ballot_ranks = []
    ballot_IDs = []
    ballot_precinctPortions = []
    ballot_precincts = []
    ballot_types = []
    ballot_countingGroups = []
    ballot_votingLocation = []
    ballot_district = []
    ballot_districtType = []

    for cvr_export in path.glob("CvrExport*.json"):
        with open(cvr_export, encoding="utf8") as f:
            for contests in json.load(f)['Sessions']:

                # ballotID
                ballotID_search = re.search('Images\\\\(.*)\*\.\*', contests['ImageMask'])
                if ballotID_search:
                    ballotID = ballotID_search.group(1)
                else:
                    raise RuntimeError('regex is not working correctly. debug')

                countingGroup = countingGroup_manifest[contests['CountingGroupId']]

                # voting location for ballots
                ballotVotingLocation = tabulator_manifest[contests['TabulatorId']]

                # for each session use original, or if isCurrent is False,
                # use modified
                if contests['Original']['IsCurrent']:
                    current_contests = contests['Original']
                else:
                    current_contests = contests['Modified']

                # precinctId for this ballot
                precinctPortion = precinctPortion_manifest[current_contests['PrecinctPortionId']]['Portion']
                precinctId = precinctPortion_manifest[current_contests['PrecinctPortionId']]['PrecinctId']

                precinct = None
                if precinct_manifest:
                    precinct = precinct_manifest[precinctId]

                # ballotType for this ballot
                ballotType = ballotType_manifest[current_contests['BallotTypeId']]

                # district for ballot
                ballotDistrictId = districtPrecinctPortion_manifest[current_contests['PrecinctPortionId']]
                ballotDistrict = district_manifest[ballotDistrictId]['District']
                ballotDistrictType = districtType_manifest[district_manifest[ballotDistrictId]['DistrictTypeId']]

                ballot_contest_marks = None
                for cards in current_contests['Cards']:
                    for ballot_contest in cards['Contests']:
                        if ballot_contest['Id'] == current_contest_id:
                            if ballot_contest_marks is not None:
                                raise (RuntimeError(
                                    "Contest Id appears twice across a single set of cards. Not expected."))
                            ballot_contest_marks = ballot_contest['Marks']

                # skip ballot if didn't contain contest
                if ballot_contest_marks is None:
                    continue

                # check for marks on each rank expected for this contest
                currentRank = 1
                current_ballot_ranks = []
                while currentRank <= current_contest_rank_limit:

                    # find any marks that have the currentRank and aren't Ambiguous
                    currentRank_marks = [i for i in ballot_contest_marks
                                         if i['Rank'] == currentRank and i['IsAmbiguous'] is False]

                    currentCandidate = '**error**'

                    if len(currentRank_marks) == 0:
                        currentCandidate = util.BallotMarks.SKIPPEDRANK
                    elif len(currentRank_marks) > 1:
                        currentCandidate = util.BallotMarks.OVERVOTE
                    else:
                        currentCandidate = candidate_manifest[currentRank_marks[0]['CandidateId']]

                    if currentCandidate == '**error**':
                        raise RuntimeError('error in filtering marks. debug')

                    current_ballot_ranks.append(currentCandidate)
                    currentRank += 1

                ballot_ranks.append(current_ballot_ranks)
                ballot_precinctPortions.append(precinctPortion)
                ballot_precincts.append(precinct)
                ballot_IDs.append(ballotID)
                ballot_types.append(ballotType)
                ballot_countingGroups.append(countingGroup)
                ballot_votingLocation.append(ballotVotingLocation)
                ballot_district.append(ballotDistrict)
                ballot_districtType.append(ballotDistrictType)

    ballot_dict = {'ranks': ballot_ranks,
                   'weight': [decimal.Decimal('1')] * len(ballot_ranks),
                   'ballotID': ballot_IDs,
                   'precinct': ballot_precincts,
                   'precinctPortion': ballot_precinctPortions,
                   'ballot_type': ballot_types,
                   'countingGroup': ballot_countingGroups,
                   'votingLocation': ballot_votingLocation,
                   'district': ballot_district,
                   'districtType': ballot_districtType}

    # make sure precinctManifest was part of CVR, otherwise exclude precinct column
    if len(ballot_precincts) != sum(i is None for i in ballot_precincts):
        ballot_dict['precinct'] = ballot_precincts

    # check ballotIDs are unique
    if len(set(ballot_dict['ballotID'])) != len(ballot_dict['ballotID']):
        raise RuntimeError("some non-unique ballot IDs")

    return ballot_dict

def chp_names(ctx):
    """
    Read chp file and return candidate code map
    """
    mapping = {}
    with open(ctx['cvr_path'], encoding='utf8') as f:
        for i in f:
            split = i.split()
            if len(split) >= 3 and split[0] == '.CANDIDATE':
                mapping[split[1].strip(',')] = i.split('"')[1].split('"')[0]
    return mapping

def chp_order(ctx):
    """
    Read chp file and return prm file paths in order listed. Order is important for cambridge elections.
    """
    path_dir = ctx['cvr_path'].parent
    prm_filepaths = []
    with open(ctx['cvr_path'], encoding='utf8') as f:
        for i in f:
            split = i.split()
            if len(split) == 2 and split[0] == '.INCLUDE':
                prm_filepaths.append(path_dir / split[1])
    return prm_filepaths

# TODO: add functionality to allow resolvalbe overvotes
#       i.e. overvotes that are tabulated after all but
#       one of the candidates in the overvote is eliminated
#       burlington, and possibly cambridge will still count
#       this vote
def prm(ctx):
    """
    Parser based on CHP and PRM files. CHP file contains contest meta-info and candidate code maps.
    PRM file contains ballot info. PRM files may appear separated out by precinct.
    """
    # get candidate code map
    name_map = chp_names(ctx)
    # get prm file list
    prm_filepaths = chp_order(ctx)

    ballots = []
    for prm_filepath in prm_filepaths:
        with open(prm_filepath, 'r', encoding='utf8') as f:
            for i in f:
                if any(map(str.isalnum, i)) and i.strip()[0] != '#':
                    b = []
                    s = i.split()
                    choices = [] if len(s) == 1 else s[1].split(',')
                    for choice in filter(None, choices):
                        can, rank = choice.split(']')[0].split('[')
                        b.extend([util.BallotMarks.SKIPPEDRANK] * (int(rank) - len(b) - 1))
                        b.append(util.BallotMarks.OVERVOTE if '=' in choice else name_map[can])
                    ballots.append(b)

    # add in tail skipped ranks
    maxlen = max(map(len, ballots))
    for b in ballots:
        b.extend([util.BallotMarks.SKIPPEDRANK] * (maxlen - len(b)))

    return {'ranks': ballots, 'weight': [decimal.Decimal('1')] * len(ballots)}

def burlington2006(ctx):
    """Function to parse file format used in 2006 Burlington Mayoral Election.

    Args:
        ctx (dictionary): A dictionary containing key "path" which points to the cvr file containing ranking information of each ballot. If a file called "candidate_codes.csv" exists in the same directory, it will be read and values from the "code" column that are found in the cvr file ranks will be replaced values in the "candidate" columns.

    Returns:
        dictionary: Dictionary with a single key, "ranks", containing parsed ballots as a list of lists. Overvotes and skipped rankings are represented by constants.
    """
    path = ctx['cvr_path']

    # read in lines
    ballots = []
    with open(path, "r", encoding='utf8') as f:
        for line in f:
            ballots.append([util.BallotMarks.OVERVOTE if '=' in i else i for i in line.split()[3:]])

    # fill in skipped ranks with constant
    maxlen = max(map(len, ballots))
    for b in ballots:
        b.extend([util.BallotMarks.SKIPPEDRANK] * (maxlen - len(b)))

    # read candidate codes
    candidate_codes_fname = path.parent / "candidate_codes.csv"
    if os.path.exists(candidate_codes_fname):

        cand_codes = pd.read_csv(candidate_codes_fname, encoding="utf8")
        cand_codes_dict = {str(code): cand for code, cand in zip(cand_codes['code'], cand_codes['candidate'])}

        # replace candidate codes with candidate names
        new_ballots = []
        for b in ballots:
            new_ballots.append([cand_codes_dict[cand] if cand in cand_codes_dict else cand for cand in b])

    return {'ranks': new_ballots}

def optech(ctx):

    cvr_path = ctx['cvr_path']

    # FIND THE FILES
    ballot_image_files = [f for f in cvr_path.glob('*allot*.txt')]
    master_lookup_files = [f for f in cvr_path.glob('*aster*.txt')]

    ballot_image_path = None
    if not ballot_image_files:
        raise RuntimeError(f'parser error - no ballot image file found in {cvr_path}')
    elif len(ballot_image_files) > 1:
        raise RuntimeError(f'too many ballot image files in directory {cvr_path}. Should only be one.')
    else:
        ballot_image_path = ballot_image_files[0]

    master_lookup_path = None
    if not master_lookup_files:
        raise RuntimeError(f'parser error - no master lookup file found in {cvr_path}')
    elif len(master_lookup_files) > 1:
        raise RuntimeError(f'too many master lookup files in directory {cvr_path}. Should only be one.')
    else:
        master_lookup_path = master_lookup_files[0]

    # READ MASTER LOOKUP
    master_lookup = collections.defaultdict(dict)
    candidate_contest_map = {}
    with open(master_lookup_path, encoding='utf8') as f:
        for i in f:
            mapping = i[:10].strip()
            key = i[10:17].strip()
            value = i[17:67].strip()

            master_lookup[mapping][key] = value

            if mapping == "Candidate":
                candidate_contest_id = i[74:81].strip()
                candidate_contest_map.update({key: candidate_contest_id})

    # find contest id
    contest_reverse_map = {v: k for k, v in master_lookup['Contest'].items()}
    if ctx['office'] not in contest_reverse_map:
        raise RuntimeError(f'contest set office value ({ctx["office"]}) not present in master lookup file {master_lookup_path}')
    contest_id = contest_reverse_map[ctx['office']]

    # remove candidates from master lookup if they are from another contest
    master_lookup['Candidate'] = {candidate_id: candidate_val for candidate_id, candidate_val
                                  in master_lookup['Candidate'].items()
                                  if candidate_contest_map[candidate_id] == contest_id}

    # tally types are stored in master lookup with 7 chars but only recorded in ballot image with 3
    # trim off the first 4 char from the master lookup strings
    tally_type_map = {k[4:]: v for k, v in master_lookup['Tally Type'].items()}

    # separate out other maps
    precinct_map = master_lookup['Precinct']
    name_map = {k: {'WRITEIN': util.BallotMarks.WRITEIN}.get(v.upper().replace('-', ''), v)
                for k, v in master_lookup['Candidate'].items()}

    # READ BALLOT FILE
    voter_info_collected = collections.defaultdict(list)
    max_rank_num = 0
    with open(ballot_image_path, "r", encoding='utf8') as f:

        for line in f:

            line_contest_id = line[:7].strip()
            line_voter_id = line[7:16].strip()
            line_tally_type = line[23:26].strip()
            line_precinct_id = line[26:33].strip()
            line_candidate_id = line[36:43].strip()
            line_rank = line[33:36].strip()
            line_skipped = line[43].strip()
            line_overvote = line[44].strip()

            # skip line if not for contest
            if line_contest_id != contest_id:
                continue

            max_rank_num = int(line_rank) if int(line_rank) > max_rank_num else max_rank_num

            voter_info_collected[line_voter_id].append({
                'voter_id': line_voter_id,
                'tally_type': tally_type_map[line_tally_type],
                'precinct': precinct_map[line_precinct_id],
                # 0 candidate id plus a skipped or overvote mark, indicate skip or overvote
                'candidate': name_map[line_candidate_id] if int(line_candidate_id) else 0,
                'rank': int(line_rank),
                'skipped': int(line_skipped),
                'overvote': int(line_overvote)
                })

            # debug check to see if ballot marks with valid candidate name stored sometimes also get paired,
            # with overvote or skipped marks?
            if int(line_candidate_id) and (int(line_skipped) or int(line_overvote)):
                raise RuntimeError('both a skip and overvote mark for this rank. unexpected')

    # for each voter, assemble the ballot
    dct = {
        'ranks': [],
        'precinct': [],
        'tally_type': [],
        'ballotID': []
    }
    for voter_id in voter_info_collected:

        voter_ballot_info = voter_info_collected[voter_id]

        # debug checks
        voter_tally_type_set = set([b['tally_type'] for b in voter_ballot_info])
        voter_precinct_set = set([b['precinct'] for b in voter_ballot_info])

        if len(voter_tally_type_set) > 1:
            raise RuntimeError("Marks for this voter contain multiple tally type values. Unexpected.")

        if len(voter_precinct_set) > 1:
            raise RuntimeError("Marks for this voter contain multiple precinct values. Unexpected.")

        voter_tally_type = list(voter_tally_type_set)[0]
        voter_precinct = list(voter_precinct_set)[0]

        voter_ranks = [None] * max_rank_num
        for rank in range(1, max_rank_num + 1):

            rank_info_filter = [b for b in voter_ballot_info if b['rank'] == rank]

            if len(rank_info_filter) > 1:
                raise RuntimeError('unexpected')
                # an overvote marker is stored in the file, but do overvoted ranks still get all their marks stored ?
            elif len(rank_info_filter) == 0:
                raise RuntimeError('unexpected')
                # this would be unexpected since there is a skipped rank mark in the file
            else:
                rank_info = rank_info_filter[0]

            rank_candidate = rank_info['candidate']

            if rank_candidate == 0 and rank_info['skipped'] and rank_info['overvote']:
                raise RuntimeError('this shouldnt be reached')
            elif rank_candidate == 0 and rank_info['skipped']:
                voter_ranks[rank-1] = util.BallotMarks.SKIPPEDRANK
            elif rank_candidate == 0 and rank_info['overvote']:
                voter_ranks[rank-1] = util.BallotMarks.OVERVOTE
            else:
                voter_ranks[rank-1] = rank_candidate

        if any(r is None for r in voter_ranks):
            raise RuntimeError('not all ranks for this voter had data stored in the file. unexpected.')

        dct['ranks'].append(voter_ranks)
        dct['ballotID'].append(voter_id)
        dct['tally_type'].append(voter_tally_type)
        dct['precinct'].append(voter_precinct)

    # add weights
    dct.update({'weight': [decimal.Decimal('1')] * len(dct['ranks'])})
    return dct


# def sf_precinct_map(ctx):
#     path = ctx['path']
#     master_lookup_path = ctx.get('master_lookup')
#     if master_lookup_path is None:
#         master_lookup_path = path.replace('ballot_image', 'master_lookup') \
#                                  .replace('BallotImage', 'MasterLookup') \
#                                  .replace('ballotimage', 'masterlookup') \
#                                  .replace('Ballot Image', 'Master Lookup')

#     precinct_map = {}
#     with open(master_lookup_path, encoding='utf8') as f:
#         for i in f:
#             if i.startswith('Precinct'):
#                 kv = i.split()[1]
#                 precinct_map[kv[:7]] = kv[7:]
#                 if ctx['place'] == 'San Francisco':
#                     precinct_map[kv[:7]] = i.split()[2]
#     return precinct_map

# def parse_master_lookup(ctx):
#     path = ctx['path']
#     master_lookup_path = ctx.get('master_lookup')
#     if master_lookup_path is None:
#         master_lookup_path = path.replace('ballot_image', 'master_lookup') \
#                                  .replace('BallotImage', 'MasterLookup') \
#                                  .replace('ballotimage', 'masterlookup') \
#                                  .replace('Ballot Image', 'Master Lookup')

#     master_lookup = defaultdict(dict)
#     with open(master_lookup_path, encoding='utf8') as f:
#         for i in f:
#             mapping = i[:10].strip()
#             key = i[10:17].strip()
#             value = i[17:67].strip()
#             master_lookup[mapping][key] = value
#     return dict(master_lookup)

# def sf_name_map(ctx):
#     return dict((k, {'WRITEIN': util.BallotMarks.WRITEIN}.get(v.upper().replace('-', ''), v))
#                 for k, v in parse_master_lookup(ctx)['Candidate'].items())

# def sf_tally_type_map(ctx):
#     path = ctx['path']
#     master_lookup_path = ctx.get('master_lookup')
#     if master_lookup_path is None:
#         master_lookup_path = path.replace('ballot_image', 'master_lookup') \
#             .replace('BallotImage', 'MasterLookup') \
#             .replace('ballotimage', 'masterlookup') \
#             .replace('Ballot Image', 'Master Lookup')

#     tally_type_map = {}
#     with open(master_lookup_path, encoding='utf8') as f:
#         for i in f:
#             if i.startswith('Tally Type'):
#                 splited = i.split("  ")[0].split("Type")[1]
#                 k = splited[4:7]
#                 v = splited[7:]
#                 tally_type_map[k] = v

#     return tally_type_map

# def sf(contest_id, ctx):

#     path = ctx['path']

#     # parse "config" file
#     precinct_map = sf_precinct_map(ctx)
#     name_map = sf_name_map(ctx)
#     tally_type_map = sf_tally_type_map(ctx)

#     # read ballot info into lists
#     ballots = []
#     precincts = []
#     tally_types = []
#     voterID = []
#     with open(path, "r", encoding='utf8') as f:

#         b = []
#         ballot_precincts = []
#         ballot_tally_types = []
#         voter_id = None

#         for line in f:

#             # skip line if not for contest
#             if line[:7] != contest_id:
#                 continue

#             # when reach new ballot, store the accumulated previous one
#             if line[7:16] != voter_id:

#                 if len(set(ballot_precincts)) > 1:
#                     print("this ballot contains several precincts. weird")
#                     raise RuntimeError
#                 if ballot_precincts:
#                     precincts.append(ballot_precincts[0])
#                 else:
#                     precincts.append([])

#                 if len(set(ballot_tally_types)) > 1:
#                     print("this ballot contains several tally types. weird")
#                     raise RuntimeError
#                 if ballot_tally_types:
#                     tally_types.append(ballot_tally_types[0])
#                 else:
#                     tally_types.append([])

#                 ballots.append(b)
#                 voterID.append(voter_id)

#                 voter_id = line[7:16]
#                 b = []
#                 ballot_precincts = []
#                 ballot_tally_types = []

#             # read current line

#             # precinct
#             precinct_id = line[26:33]
#             ballot_precincts.append(precinct_map[precinct_id])

#             # tally type - vote by mail
#             tally_type = line[23:26]
#             ballot_tally_types.append(tally_type_map[tally_type])

#             # candidate and rank
#             candidate_id = int(line[36:43]) and name_map[line[36:43]]
#             undervote = util.BallotMarks.SKIPPEDRANK if int(line[44]) else 0
#             overvote = util.BallotMarks.OVERVOTE if int(line[43]) else 0
#             b.append(candidate_id or undervote or overvote)
#             if b[-1] == 0 or len(b) != int(line[33:36]):
#                 raise Exception("Invalid Choice or Rank")

#         # store last ballot
#         if b:

#             if len(set(ballot_precincts)) > 1:
#                 print("this ballot contains several precincts. weird")
#                 raise RuntimeError
#             precincts.append(ballot_precincts[0])

#             if len(set(ballot_tally_types)) > 1:
#                 print("this ballot contains several tally types. weird")
#                 raise RuntimeError
#             tally_types.append(ballot_tally_types[0])

#             ballots.append(b)
#             voterID.append(voter_id)

#     if len(set(voterID[1:])) != len(voterID[1:]):
#         raise Exception("non-unique voter IDs")

#     d = {
#         'ranks': ballots[1:],
#         'weight': [Fraction('1') for b in ballots[1:]],
#         'precincts': precincts[1:],
#         'tally_type': tally_types[1:],
#         'ballotID': voterID[1:]
#     }

#     return d

# def sfnoid(ctx):

#     path = ctx['path']

#     # parse "config" file
#     precinct_map = sf_precinct_map(ctx)
#     name_map = sf_name_map(ctx)
#     tally_type_map = sf_tally_type_map(ctx)

#     # read ballot info into lists
#     ballots = []
#     precincts = []
#     tally_types = []
#     voterID = []
#     with open(path, "r", encoding='utf8') as f:

#         b = []
#         ballot_precincts = []
#         ballot_tally_types = []
#         voter_id = None

#         for line in f:

#             # when reach new ballot, store the accumulated previous one
#             if line[7:16] != voter_id:

#                 if len(set(ballot_precincts)) > 1:
#                     print("this ballot contains several precincts. weird")
#                     raise RuntimeError
#                 if ballot_precincts:
#                     precincts.append(ballot_precincts[0])
#                 else:
#                     precincts.append([])

#                 if len(set(ballot_tally_types)) > 1:
#                     print("this ballot contains several tally types. weird")
#                     raise RuntimeError
#                 if ballot_tally_types:
#                     tally_types.append(ballot_tally_types[0])
#                 else:
#                     tally_types.append([])

#                 ballots.append(b)
#                 voterID.append(voter_id)

#                 voter_id = line[7:16]
#                 b = []
#                 ballot_precincts = []
#                 ballot_tally_types = []

#             # read current line

#             # precinct
#             precinct_id = line[26:33]
#             ballot_precincts.append(precinct_map[precinct_id])

#             # tally type - vote by mail
#             tally_type = line[23:26]
#             ballot_tally_types.append(tally_type_map[tally_type])

#             # candidate and rank
#             candidate_id = int(line[36:43]) and name_map[line[36:43]]
#             undervote = util.BallotMarks.SKIPPEDRANK if int(line[44]) else 0
#             overvote = util.BallotMarks.OVERVOTE if int(line[43]) else 0

#             #Alameda County incorrectly reported 0 for write in candidates for
#             #races in 2012 and treated write-ins as undervotes in their reports
#             #for city attorney, the undervote ID was 92. This snippit was used to validate rcv results
#             #with the counties official report here:
#             #https://www.acvote.org/acvote-assets/pdf/elections/2012/11062012/results/rcv/oakland/city_attorney/nov-6-2012-pass-report-oakland-city-attorney.pdf
#             #if candidate_id == 92:
#             #    b.append(UNDERVOTE)
#             #    continue

#             b.append(candidate_id or undervote or overvote)
#             if b[-1] == 0 or len(b) != int(line[33:36]):
#                 raise Exception("Invalid Choice or Rank")

#         # store last ballot
#         if b:

#             if len(set(ballot_precincts)) > 1:
#                 print("this ballot contains several precincts. weird")
#                 raise RuntimeError
#             precincts.append(ballot_precincts[0])

#             if len(set(ballot_tally_types)) > 1:
#                 print("this ballot contains several tally types. weird")
#                 raise RuntimeError
#             tally_types.append(ballot_tally_types[0])

#             ballots.append(b)
#             voterID.append(voter_id)

#     if len(set(voterID[1:])) != len(voterID[1:]):
#         raise Exception("non-unique voter IDs")

#     d = {
#         'ranks': ballots[1:],
#         'weight': [Fraction('1') for b in ballots[1:]],
#         'precincts': precincts[1:],
#         'tally_type': tally_types[1:],
#         'ballotID': voterID[1:]
#     }

#     return d

def old(ctx):
    path = ctx['cvr_path']
    candidate_map = {}
    with open(ctx['candidate_map'], encoding='utf8') as f:
        for i in f:
            line = [j.strip() for j in i.split(':')]
            if line and line[0] == 'Candidate':
                candidate_map[line[1]] = line[2]
    candidate_map['--'] = util.BallotMarks.SKIPPEDRANK
    candidate_map['++'] = util.BallotMarks.OVERVOTE
    ballots = []
    with open(path, "r", encoding='utf8') as f:
        line = f.readline()
        while line:
            ballots.append([candidate_map[i] for i in line.split()[-1].split('>')])
            line = f.readline()
    return ballots

def minneapolis(ctx):
    choice_map = {}
    default = None
    if ctx['year'] == '2009':
        with open(ctx['cvr_path'].parent / 'convert.csv', encoding='utf8') as f:
            for i in f:
                split = i.strip().split('\t')
                if len(split) >= 3 and split[0] == ctx['office']:
                    choice_map[split[2]] = split[1]
        if choice_map == {}:
            raise RuntimeError('No candidates found. Ensure "office" field in contest_set matches CVR.')
        choice_map['XXX'] = util.BallotMarks.SKIPPEDRANK
        default = util.BallotMarks.WRITEIN
    else:
        choice_map = {
            'UWI': util.BallotMarks.WRITEIN,
            'undervote': util.BallotMarks.SKIPPEDRANK,
            'overvote': util.BallotMarks.OVERVOTE
        }
    path = ctx['cvr_path']
    precincts = []
    ballots = []
    with open(path, "r", encoding='utf8') as f:
        f.readline()
        for line in csv.reader(f):
            choices = [choice_map.get(i.strip(), i if default is None else default)
                          for i in line[1:-1]]
            if choices != ['','','']:
                ballots.extend([choices] * int(float(line[-1])))
                for p in range(int(float(line[-1]))):
                    precincts.append(line[0])

    bs = {'ranks': ballots,
          'weight': [decimal.Decimal('1')] * len(ballots),
          'precinct': precincts}

    return bs

def maine(n, ctx):
    path = ctx['cvr_path']
    ballots = []
    with open(path, "r", encoding='utf8') as f:
        f.readline()
        for line in csv.reader(f):
            choices = [{'undervote': util.BallotMarks.SKIPPEDRANK,
                        'overvote': util.BallotMarks.OVERVOTE,
                        'Write-in': util.BallotMarks.WRITEIN}.get(i,i)
                         for i in line[3:3+n]]
            if '' not in choices and choices:
                ballots.append(choices)
    return ballots

def santafe(column_id, contest_id, ctx):
    path = ctx['cvr_path']
    candidate_map = {}
    with open(ctx['cvr_path'].replace('CvrExport','CandidateManifest'), encoding='utf8') as f:
        for i in f:
            row = i.split(',')
            if row:
                candidate_map[row[1]] = row[0]
    ballots = []
    ballot_length = 0
    with open(path, "r", encoding='utf8') as f:
        reader = csv.reader(f)
        header = next(reader)
        s = 'Original/Cards/0/Contests/{}/Marks/{}/{}'
        rinds = []
        cinds = []
        for i in range(len(header)):
            try:
                rinds.append(header.index(s.format(column_id, i, 'Rank')))
            except ValueError:
                break
            cinds.append(header.index(s.format(column_id, i, 'CandidateId')))
        col = header.index('Original/Cards/0/Contests/{}/Id'.format(column_id))
        for line in reader:
            if line[col] == str(contest_id):
                choices = []
                ranks = [int(line[i]) for i in rinds if line[i] != '']
                ballot_length = max(ranks + [ballot_length])
                candidates = iter(cinds)
                for i in range(len(rinds)):
                    c = ranks.count(i+1)
                    if c == 0:
                        choices.append(util.BallotMarks.SKIPPEDRANK)
                    elif c == 1:
                        next_candidate = line[next(candidates)]
                        choices.append(candidate_map[next_candidate])
                    else:
                        choices.append(util.BallotMarks.OVERVOTE)
                ballots.append(choices)
    return [b[:ballot_length] for b in ballots]

def santafe_id(column_id, contest_id, ctx):
    path = ctx['cvr_path']
    ballots = []
    ballot_length = 0
    with open(path, "r", encoding='utf8') as f:
        reader = csv.reader(f)
        header = next(reader)
        s = 'Original/Cards/0/Contests/{}/Marks/{}/{}'
        rinds = []
        cinds = []
        for i in range(len(header)):
            try:
                rinds.append(header.index(s.format(column_id, i, 'Rank')))
            except ValueError:
                break
            cinds.append(header.index(s.format(column_id, i, 'CandidateId')))
        col = header.index('Original/Cards/0/Contests/{}/Id'.format(column_id))
        for i, line in enumerate(reader):
            if line[col] == str(contest_id):
                choices = collections.UserList([])
                choices.voter_id = i
                ranks = [int(line[i]) for i in rinds if line[i] != '']
                ballot_length = max(ranks + [ballot_length])
                candidates = iter(cinds)
                for i in range(len(rinds)):
                    c = ranks.count(i+1)
                    if c == 0:
                        choices.append(util.BallotMarks.SKIPPEDRANK)
                    elif c == 1:
                        choices.append(line[next(candidates)])
                    else:
                        choices.append(util.BallotMarks.OVERVOTE)
                ballots.append(choices)
    for b in ballots:
        b.data = b.data[:ballot_length]
    return ballots

def sf2005(contest_ids, over, under, sep, ctx):
    path = ctx['cvr_path']
    ballots = []
    with open(path, 'r', encoding='utf8') as f:
        for i in f:
            if sep is None:
                s = [rc.split('-') for rc in i.split()[1:] if '-' in i.strip()]
            else:
                s = [rc.strip().split('-') for rc in i.split(sep)[1:] if '-' in i]
            if s == [] or len(s[0]) != 2:
                continue
            raw = [c for r, c in s if r in contest_ids]
            if raw:
                ballots.append([{over: util.BallotMarks.OVERVOTE, under: util.BallotMarks.SKIPPEDRANK}.get(i, i)
                                for i in raw])
    return ballots

def dominion5_2(ctx):

    with open(ctx['cvr_path'] / 'ContestManifest.json', encoding='utf8') as f:
        for i in json.load(f)['List']:
            if i['Description'] == ctx['office'].upper():
                contest_id = i['Id']
                ranks = i['NumOfRanks']
                if ranks == 0:
                    ranks = 1

    candidates = {}
    with open(ctx['cvr_path'] / 'CandidateManifest.json', encoding='utf8') as f:
        for i in json.load(f)['List']:
            if i['ContestId'] == contest_id:
                candidates[i['Id']] = i['Description']

    precincts = {}
    with open(ctx['cvr_path'] / 'PrecinctPortionManifest.json', encoding='utf8') as f:
        for i in json.load(f)['List']:
            precincts[i['Id']] = i['Description'].split()[1]

    ballotType_manifest = {}
    with open(ctx['cvr_path'] / 'BallotTypeManifest.json', encoding='utf8') as f:
        for i in json.load(f)['List']:
            ballotType_manifest[i['Id']] = i['Description']

    countingGroup_manifest = {}
    with open(ctx['cvr_path'] / 'CountingGroupManifest.json', encoding='utf8') as f:
        for i in json.load(f)['List']:
            countingGroup_manifest[i['Id']] = i['Description']

    ballots = {'ranks': [], 'ballotID': [], 'precinct': [], 'ballotType': [], 'countingGroup': [], 'weight': []}
    with open(ctx['cvr_path'] / 'CvrExport.json', encoding='utf8') as f:

        for contests in json.load(f)['Sessions']:

            # ballotID
            ballotID_search = re.search('Images\\\\(.*)\*\.\*', contests['ImageMask'])
            if ballotID_search:
                ballotID = ballotID_search.group(1)
            else:
                raise RuntimeError('regex is not working correctly. debug')

            countingGroup = countingGroup_manifest[contests['CountingGroupId']]

            if contests['Original']['IsCurrent']:
                current_contests = contests['Original']
            else:
                current_contests = contests['Modified']

            precinct = precincts[current_contests['PrecinctPortionId']]
            ballotType = ballotType_manifest[current_contests['BallotTypeId']]

            for contest in current_contests['Contests']:

                # confirm correct contest
                if contest['Id'] == contest_id:

                    # make empty ballot
                    ballot = [util.BallotMarks.SKIPPEDRANK] * ranks

                    # look through marks
                    for mark in contest['Marks']:
                        candidate = candidates[mark['CandidateId']]
                        if candidate == 'Write-in':
                            candidate = util.BallotMarks.WRITEIN
                        rank = mark['Rank']-1
                        if mark['IsAmbiguous']:
                            pass
                        elif ballot[rank] == util.BallotMarks.OVERVOTE:
                            pass
                        elif ballot[rank] == util.BallotMarks.SKIPPEDRANK:
                            ballot[rank] = candidate
                        elif ballot[rank] != candidate:
                            ballot[rank] = util.BallotMarks.OVERVOTE

                    ballots['countingGroup'].append(countingGroup)
                    ballots['ballotType'].append(ballotType)
                    ballots['precinct'].append(precinct)
                    ballots['ranks'].append(ballot)
                    ballots['ballotID'].append(ballotID)

    ballots['weight'] = [decimal.Decimal('1')] * len(ballots['ranks'])

    # check ballotIDs are unique
    if len(set(ballots['ballotID'])) != len(ballots['ballotID']):
        print("some non-unique ballot IDs")
        exit(1)

    return ballots

def utah(ctx):
    ballots = []
    with open(ctx['cvr_path'], encoding='utf8') as f:
        next(f)
        for b in f:
            ballots.append(
                [{'overvote': util.BallotMarks.OVERVOTE,
                  'undervote': util.BallotMarks.SKIPPEDRANK,
                  '': util.BallotMarks.SKIPPEDRANK}.get(i, i)
                for i in b.strip().split(',')[2:]]
            )
    return ballots

def ep(ctx):
    ballots = []
    with open(ctx['cvr_path'], encoding='utf8') as f:
        next(f)
        for b in csv.reader(f):
            ballots.append(
                [{'overvote': util.BallotMarks.OVERVOTE,
                  'undervote': util.BallotMarks.SKIPPEDRANK,
                  'UWI': util.BallotMarks.WRITEIN}.get(i, i)
                for i in b[3:]]
            )

    return ballots

def unisyn(ctx):
    """
    This parser was developed for the unisyn 2020 Hawaii Dem Primary CVR which only contained the
    ranked choice votes for a single election. Unisyn uses the common data format in xml, however the
    parser currently is not a complete common data format parser.

    For more information on common data format, see:
    https://pages.nist.gov/CastVoteRecords/
    https://github.com/hiltonroscoe/cdfprototype
    """

    glob_str = ctx['cvr_path'].glob('/*.xml')

    contestIDdicts = {}
    for f in glob_str:

        with open(f) as fd:
            xml_dict = xmltodict.parse(fd.read())

        # get candidates
        candidatesIDs = {}
        for cand_dict in xml_dict['CastVoteRecordReport']['Election']['Candidate']:
            candidatesIDs[cand_dict['@ObjectId']] = cand_dict['Name']

        # loop through CVR snapshots
        for cvr_dict in xml_dict['CastVoteRecordReport']['CVR']:

            cvr_contest = cvr_dict['CVRSnapshot']['CVRContest']

            if cvr_contest['ContestId'] not in contestIDdicts:
                contestIDdicts.update({cvr_contest['ContestId']: []})
            contestIDdicts[cvr_contest['ContestId']].append(cvr_contest['CVRContestSelection'])

    # check that all rank lists are equal
    first_rank = list(contestIDdicts.keys())[0]
    rank_length_equal = [len(contestIDdicts[k]) == len(contestIDdicts[first_rank]) for k in contestIDdicts]
    if not all(rank_length_equal):
        print("not all rank lists are equal.")
        raise RuntimeError

    # combine ranks into lists
    ballot_lists = []
    for idx in range(len(contestIDdicts[first_rank])):

        idx_ranks = [int(contestIDdicts[rank_key][idx]['Rank']) for rank_key in contestIDdicts]

        idx_candidates = []
        for rank_key in contestIDdicts:
            contest_dict = contestIDdicts[rank_key][idx]
            if 'SelectionPosition' in contest_dict:
                if isinstance(contest_dict['SelectionPosition'], list):
                    idx_candidates.append(util.BallotMarks.OVERVOTE)
                else:
                    idx_candidates.append(candidatesIDs[contest_dict['SelectionPosition']['Position']])
            elif contest_dict['TotalNumberVotes'] == '0':
                idx_candidates.append(util.BallotMarks.SKIPPEDRANK)

        ordered_ranks = sorted(zip(idx_candidates, idx_ranks), key=lambda x: x[1])
        ballot_lists.append([t[0] for t in ordered_ranks])

    # assemble dict
    dct = {'ranks': ballot_lists}
    dct['weight'] = [decimal.Decimal('1')] * len(dct['ranks'])

    return dct

def surveyUSA(ctx):
    """
    Survey USA files usually include all respondents and should be pre-filtered for any columns
    prior to cruncher use (such as filtering likely democratic voters). Rank columns and ballotID columns
    should also be renamed prior to parsing.

    Rank columns can contain candidate codes or NaN. NaN is treated as a skipped rank.

    Required files:
    cvr.csv - contains ballots, ranks, weights
    candidate_codes.csv - contains two columns ("code" and "candidate") that map cvr code numbers to candidate names.
    """

    csv_df = pd.read_csv(ctx['cvr_path'] / 'cvr.csv')
    candidate_codes_df = pd.read_csv(ctx['cvr_path'] / 'candidate_codes.csv')

    # candidate code dict
    candidate_map = {row['code']: row['candidate'] for index, row in candidate_codes_df.iterrows()}

    # find rank columns
    rank_columns = [col for col in csv_df.columns if 'rank' in col.lower()]

    ballots = []
    for index, row in csv_df.iterrows():

        b_ranks = [util.BallotMarks.SKIPPEDRANK] * len(rank_columns)

        saw_undecided = False
        since_undecided = []

        for idx, rank in enumerate(rank_columns):

            # nan marks end of ranks
            if math.isnan(row[rank]):
                if since_undecided:
                    print('some candidates appeared after an undecided vote! debug')
                    raise RuntimeError
                break

            candidate = candidate_map[row[rank]]

            if saw_undecided:
                since_undecided.append(candidate)

            if candidate == 'Undecided':
                saw_undecided = True

            if candidate != 'Undecided':
                b_ranks[idx] = candidate

        ballots.append(b_ranks)

    ballot_dict = {'ranks': ballots, 'weight': csv_df['weight'], 'ballotID': csv_df['ballotID']}
    return ballot_dict
