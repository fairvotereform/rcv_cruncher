"""
Contains CVR parser functions.
"""

from typing import Union, List, Dict

import csv
import pathlib
import json
import math
import os
import re
import collections
import decimal
import xmltodict
import functools

import pandas as pd

from rcv_cruncher.marks import BallotMarks

decimal.getcontext().prec = 30

global parser_dict


def add_parser(parser_dict) -> None:
    """Add custom parser functions to the module parser dictionary.

    :param parser_dict: A dictionary containing parser functions, with their names as keys.
    :type parser_dict: Dict
    """
    parser_dict.update(parser_dict)


def get_parser_dict():
    """Returns the module parser dictionary. Including both package parsers and
    custom parsers added with :func:`add_parser`.

    :return: A dictionary of parser functions. Keys are parser name strings.
    :rtype: Dict
    """
    return parser_dict


def rank_column_csv(cvr_path: Union[str, pathlib.Path]) -> Dict[str, List]:
    """Reads ballot ranking information stored in csv format.
    One ballot per row, with ranking columns appearing in order and named with the word "rank"
    (e.x. "rank1", "rank2", etc)

    :param cvr_path: The path to the CVR file. If a file called "candidate_codes.csv" exists in the same directory, it will be read and columns named "code" and "candidate" will be used to replace candidate codes with candidate names in the CVR file during readin.
    :type cvr_path: Union[str, pathlib.Path]
    :raises RuntimeError: Error raised if not all parsed rank lists are the same length.
    :return: A dictionary of lists containing all columns in the CVR file. Rank columns are combined into per-ballot lists and stored with the key 'ranks'. A 'weight' key and list of 1's is added to the dictionary if no 'weight' column exists. All weights are of type :class:`decimal.Decimal`.
    :rtype: Dict[str, List]
    """

    cvr_path = pathlib.Path(cvr_path)
    df = pd.read_csv(cvr_path, encoding="utf8")

    # find rank columns
    rank_col = [col for col in df.columns if "rank" in col.lower()]

    # ensure rank columns are strings
    df[rank_col] = df[rank_col].astype(str)

    # if candidate codes file exist, swap in names
    candidate_codes_fpath = cvr_path.parent / "candidate_codes.csv"
    if os.path.isfile(candidate_codes_fpath):

        cand_codes = pd.read_csv(candidate_codes_fpath, encoding="utf8")

        cand_codes_dict = {str(code): cand for code, cand in zip(cand_codes["code"], cand_codes["candidate"])}
        replace_dict = {col: cand_codes_dict for col in rank_col}
        df = df.replace(replace_dict)

        cand_codes_dict = {str(float(code)): cand for code, cand in zip(cand_codes["code"], cand_codes["candidate"])}
        replace_dict = {col: cand_codes_dict for col in rank_col}
        df = df.replace(replace_dict)

    # replace skipped ranks and overvotes with constants
    df = df.replace(
        {
            col: {
                "under": BallotMarks.SKIPPED,
                "skipped": BallotMarks.SKIPPED,
                "nan": BallotMarks.SKIPPED,
                "undervote": BallotMarks.SKIPPED,
                "over": BallotMarks.OVERVOTE,
                "overvote": BallotMarks.OVERVOTE,
                "UWI": BallotMarks.WRITEIN,
            }
            for col in rank_col
        }
    )

    df = df.fillna(BallotMarks.SKIPPED)

    # pull out rank lists
    rank_col_list = [df[col].tolist() for col in rank_col]
    rank_lists = [list(rank_tuple) for rank_tuple in list(zip(*rank_col_list))]

    # double check all ballot ranks are equal length
    if not all([len(i) == len(rank_lists[0]) for i in rank_lists]):
        raise RuntimeError("not all rank lists are same length. debug")

    # assemble dict
    dct = {"ranks": rank_lists}

    # add in non-rank columns
    for col in df.columns:
        if col not in rank_col:
            dct[col] = df[col].tolist()

    # add weight if not present in csv
    if "weight" not in dct:
        dct["weight"] = [decimal.Decimal("1") for _ in dct["ranks"]]
    else:
        dct["weight"] = [decimal.Decimal(str(w)) for w in dct["weight"]]

    return dct


def candidate_column_csv(cvr_path: Union[str, pathlib.Path]) -> Dict[str, List]:
    """
    Reads ballot ranking information stored in csv file called "cvr.csv".
    Candidate column names. One ballot per row, with ranks given to candidates in cell rows.

    Candidate columns are identified by reading a "candidate_codes.csv" file. Columns present in the CVR file that are not listed in the candidate codes are parsed as auxillary ballot information (precinct ID, etc).

    :param cvr_path: The path to the directory containing the CVR and candidate codes files.
    :type cvr_path: Union[str, pathlib.Path]
    :raises RuntimeError: Error raised if not all parsed rank lists are the same length.
    :return: A dictionary of lists containing all columns in the CVR file. Rank columns are combined into per-ballot lists and stored with the key 'ranks'. A 'weight' key and list of 1's is added to the dictionary if no 'weight' column exists. All weights are of type :class:`decimal.Decimal`.
    :rtype: Dict[str, List]
    """

    cvr_path = pathlib.Path(cvr_path)

    cvr = pd.read_csv(cvr_path / "cvr.csv", encoding="utf8")
    candidate_codes = pd.read_csv(cvr_path / "candidate_codes.csv", encoding="utf8")

    candidate_dict = {str(code): cand for code, cand in zip(candidate_codes["code"], candidate_codes["candidate"])}

    max_rank_num = int(cvr[candidate_dict.keys()].max().max())

    ballots = []
    for _, row in cvr.iterrows():
        row_ranks = {
            int(row[code]): candidate_dict[code]
            for code, value in candidate_dict.items()
            if value and not pd.isna(row[code])
        }

        ballot = []
        for rank_num in range(1, max_rank_num + 1):
            if rank_num in row_ranks:
                ballot.append(row_ranks[rank_num])
            else:
                ballot.append(BallotMarks.SKIPPED)

        ballots.append(ballot)

    ballot_dict = {"ranks": ballots}
    for col in cvr.columns:
        if col not in candidate_dict:
            ballot_dict[col] = cvr[col]

    return ballot_dict


def dominion5_2(cvr_path: Union[str, pathlib.Path], office: str) -> Dict[str, List]:
    """
    Reads ballot data from Dominion V5.2 CVRs for a single contest.

    Files expected in cvr_path:
        - ContestManifest.json
        - CandidateManifest.json
        - PrecinctPortionManifest.json
        - BallotTypeManifest.json
        - CountingGroupManifest.json
        - CvrExport.json

    :param cvr_path: Path where CVR files are located.
    :type cvr_path: Union[str, pathlib.Path]
    :param office: Names which contest's ballots should be read. Must match a contest name in ContestManifest.json.
    :type office: str
    :raises RuntimeError: If ballotIDs pulled from ImageMask field are not unique. Or if regex used to pull ballotID from ImageMask field malfunctions.
    :return: A dictionary of lists containing informtion in the CVR file. Ranks are combined into per-ballot lists and stored with the key 'ranks'. A 'weight' key and list of 1's is added to the dictionary if no 'weight' column exists. All weights are of type :class:`decimal.Decimal`.
    :rtype: Dict[str, List]
    """

    path = pathlib.Path(cvr_path)

    with open(path / "ContestManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            if i["Description"].strip() == office.upper():
                contest_id = i["Id"]
                ranks = i["NumOfRanks"]
                if ranks == 0:
                    ranks = 1

    candidates = {}
    with open(path / "CandidateManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            if i["ContestId"] == contest_id:
                candidates[i["Id"]] = i["Description"]

    precincts = {}
    with open(path / "PrecinctPortionManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            precincts[i["Id"]] = i["Description"].split()[1]

    ballotType_manifest = {}
    with open(path / "BallotTypeManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            ballotType_manifest[i["Id"]] = i["Description"]

    countingGroup_manifest = {}
    with open(path / "CountingGroupManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            countingGroup_manifest[i["Id"]] = i["Description"]

    ballots = {
        "ranks": [],
        "ballotID": [],
        "precinct": [],
        "ballotType": [],
        "countingGroup": [],
        "weight": [],
    }
    with open(path / "CvrExport.json", encoding="utf8") as f:

        for contests in json.load(f)["Sessions"]:

            # ballotID
            ballotID_search = re.search("Images\\\\(.*)\*\.\*", contests["ImageMask"])
            if ballotID_search:
                ballotID = ballotID_search.group(1)
            else:
                raise RuntimeError("regex is not working correctly. debug")

            countingGroup = countingGroup_manifest[contests["CountingGroupId"]]

            if contests["Original"]["IsCurrent"]:
                current_contests = contests["Original"]
            else:
                current_contests = contests["Modified"]

            precinct = precincts[current_contests["PrecinctPortionId"]]
            ballotType = ballotType_manifest[current_contests["BallotTypeId"]]

            for contest in current_contests["Contests"]:

                # confirm correct contest
                if contest["Id"] == contest_id:

                    # make empty ballot
                    ballot = [BallotMarks.SKIPPED] * ranks

                    # look through marks
                    for mark in contest["Marks"]:
                        candidate = candidates[mark["CandidateId"]]
                        if candidate == "Write-in":
                            candidate = BallotMarks.WRITEIN
                        rank = mark["Rank"] - 1
                        if mark["IsAmbiguous"]:
                            pass
                        elif ballot[rank] == BallotMarks.OVERVOTE:
                            pass
                        elif ballot[rank] == BallotMarks.SKIPPED:
                            ballot[rank] = candidate
                        elif ballot[rank] != candidate:
                            ballot[rank] = BallotMarks.OVERVOTE

                    ballots["countingGroup"].append(countingGroup)
                    ballots["ballotType"].append(ballotType)
                    ballots["precinct"].append(precinct)
                    ballots["ranks"].append(ballot)
                    ballots["ballotID"].append(ballotID)

    ballots["weight"] = [decimal.Decimal("1")] * len(ballots["ranks"])

    # check ballotIDs are unique
    if len(set(ballots["ballotID"])) != len(ballots["ballotID"]):
        raise RuntimeError("some non-unique ballot IDs")

    return ballots


def dominion5_4(cvr_path: Union[str, pathlib.Path], office: str) -> Dict[str, List]:
    """
    Reads ballot data from Dominion V5.4 CVRs for a single contest.

    Files expected in cvr_path:
        - ContestManifest.json
        - CandidateManifest.json
        - PrecinctPortionManifest.json
        - (optional) PrecinctManifest.json
        - BallotTypeManifest.json
        - CountingGroupManifest.json
        - BallotTypeContestManifest.json
        - CvrExport.json

    :param cvr_path: Path where CVR files are located.
    :type cvr_path: Union[str, pathlib.Path]
    :param office: Names which contest's ballots should be read. Must match a contest name in ContestManifest.json.
    :type office: str
    :raises RuntimeError: If ballotIDs pulled from ImageMask field are not unique. Or if regex used to pull ballotID from ImageMask field malfunctions.
    :return: A dictionary of lists containing informtion in the CVR file. Ranks are combined into per-ballot lists and stored with the key 'ranks'. A 'weight' key and list of 1's is added to the dictionary if no 'weight' column exists. All weights are of type :class:`decimal.Decimal`.
    :rtype: Dict[str, List]
    """

    path = pathlib.Path(cvr_path)

    # load manifests, with ids as keys
    with open(path / "ContestManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            if i["Description"].strip() == office:
                current_contest_id = i["Id"]
                current_contest_rank_limit = i["NumOfRanks"]

    candidate_manifest = {}
    with open(path / "CandidateManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            candidate_manifest[i["Id"]] = i["Description"]

    precinctPortion_manifest = {}
    with open(path / "PrecinctPortionManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            precinctPortion_manifest[i["Id"]] = {
                "Portion": i["Description"],
                "PrecinctId": i["PrecinctId"],
            }

    precinct_manifest = {}
    if os.path.isfile(path / "PrecinctManifest.json"):
        with open(path / "PrecinctManifest.json", encoding="utf8") as f:
            for i in json.load(f)["List"]:
                precinct_manifest[i["Id"]] = i["Description"]

    ballotType_manifest = {}
    with open(path / "BallotTypeManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            ballotType_manifest[i["Id"]] = i["Description"]

    countingGroup_manifest = {}
    with open(path / "CountingGroupManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            countingGroup_manifest[i["Id"]] = i["Description"]

    ballotTypeContest_manifest = {}
    with open(path / "BallotTypeContestManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:

            if i["ContestId"] not in ballotTypeContest_manifest.keys():
                ballotTypeContest_manifest[i["ContestId"]] = []

            ballotTypeContest_manifest[i["ContestId"]].append(i["BallotTypeId"])

    # read in ballots
    ballot_ranks = []
    ballot_IDs = []
    ballot_precinctPortions = []
    ballot_precincts = []
    ballot_types = []
    ballot_countingGroups = []
    with open(path / "CvrExport.json", encoding="utf8") as f:
        for contests in json.load(f)["Sessions"]:

            # ballotID
            ballotID_search = re.search("Images\\\\(.*)\*\.\*", contests["ImageMask"])
            if ballotID_search:
                ballotID = ballotID_search.group(1)
            else:
                raise RuntimeError("regex is not working correctly. debug")

            countingGroup = countingGroup_manifest[contests["CountingGroupId"]]

            # for each session use original, or if isCurrent is False,
            # use modified
            if contests["Original"]["IsCurrent"]:
                current_contests = contests["Original"]
            else:
                current_contests = contests["Modified"]

            # precinctId for this ballot
            precinctPortion = precinctPortion_manifest[current_contests["PrecinctPortionId"]]["Portion"]
            precinctId = precinctPortion_manifest[current_contests["PrecinctPortionId"]]["PrecinctId"]

            precinct = None
            if precinct_manifest:
                precinct = precinct_manifest[precinctId]

            # ballotType for this ballot
            ballotType = ballotType_manifest[current_contests["BallotTypeId"]]

            if len(current_contests["Cards"]) > 1:
                print('"Cards" has length greater than 1, not prepared for this. debug')
                exit(1)

            ballot_contest_marks = None
            for ballot_contest in current_contests["Cards"][0]["Contests"]:
                if ballot_contest["Id"] == current_contest_id:
                    ballot_contest_marks = ballot_contest["Marks"]

            # skip ballot if didn't contain contest
            if ballot_contest_marks is None:
                continue

            # check for marks on each rank expected for this contest
            currentRank = 1
            current_ballot_ranks = []
            while currentRank <= current_contest_rank_limit:

                # find any marks that have the currentRank and aren't Ambiguous
                currentRank_marks = [
                    i for i in ballot_contest_marks if i["Rank"] == currentRank and i["IsAmbiguous"] is False
                ]

                if len(currentRank_marks) == 0:
                    currentCandidate = BallotMarks.SKIPPED
                elif len(currentRank_marks) > 1:
                    currentCandidate = BallotMarks.OVERVOTE
                else:
                    currentCandidate = candidate_manifest[currentRank_marks[0]["CandidateId"]]

                current_ballot_ranks.append(currentCandidate)
                currentRank += 1

            ballot_ranks.append(current_ballot_ranks)
            ballot_precinctPortions.append(precinctPortion)
            ballot_precincts.append(precinct)
            ballot_IDs.append(ballotID)
            ballot_types.append(ballotType)
            ballot_countingGroups.append(countingGroup)

    ballot_dict = {
        "ranks": ballot_ranks,
        "weight": [decimal.Decimal("1")] * len(ballot_ranks),
        "ballotID": ballot_IDs,
        "precinctPortion": ballot_precinctPortions,
        "ballot_type": ballot_types,
        "countingGroup": ballot_countingGroups,
    }

    # make sure precinctManifest was part of CVR, otherwise exclude precinct column
    if len(ballot_precincts) != sum(i is None for i in ballot_precincts):
        ballot_dict["precinct"] = ballot_precincts

    # check ballotIDs are unique
    if len(set(ballot_dict["ballotID"])) != len(ballot_dict["ballotID"]):
        raise RuntimeError("some non-unique ballot IDs")

    return ballot_dict


def dominion5_10(cvr_path: Union[str, pathlib.Path], office: str) -> Dict[str, List]:
    """
    Reads ballot data from Dominion V5.10 CVRs for a single contest.

    Files expected in cvr_path:
        - ContestManifest.json
        - CandidateManifest.json
        - PrecinctPortionManifest.json
        - (optional) PrecinctManifest.json
        - DistrictManifest.json
        - DistrictTypeManifest.json
        - DistrictPrecinctPortionManifest.json
        - BallotTypeManifest.json
        - CountingGroupManifest.json
        - BallotTypeContestManifest.json
        - TabulatorManifest.json
        - CvrExport*.json (multiple possible)

    :param cvr_path: Path where CVR files are located.
    :type cvr_path: Union[str, pathlib.Path]
    :param office: Names which contest's ballots should be read. Must match a contest name in ContestManifest.json.
    :type office: str
    :raises RuntimeError: If ballotIDs pulled from ImageMask field are not unique. Or if regex used to pull ballotID from ImageMask field malfunctions.
    :return: A dictionary of lists containing informtion in the CVR file. Ranks are combined into per-ballot lists and stored with the key 'ranks'. A 'weight' key and list of 1's is added to the dictionary if no 'weight' column exists. All weights are of type :class:`decimal.Decimal`.
    :rtype: Dict[str, List]
    """

    path = pathlib.Path(cvr_path)

    # load manifests, with ids as keys
    with open(path / "ContestManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            if i["Description"].strip() == office:
                current_contest_id = i["Id"]
                current_contest_rank_limit = i["NumOfRanks"]

    candidate_manifest = {}
    with open(path / "CandidateManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            candidate_manifest[i["Id"]] = i["Description"]

    precinctPortion_manifest = {}
    with open(path / "PrecinctPortionManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            precinctPortion_manifest[i["Id"]] = {
                "Portion": i["Description"],
                "PrecinctId": i["PrecinctId"],
            }

    precinct_manifest = {}
    if os.path.isfile(path / "PrecinctManifest.json"):
        with open(path / "PrecinctManifest.json", encoding="utf8") as f:
            for i in json.load(f)["List"]:
                precinct_manifest[i["Id"]] = i["Description"]

    district_manifest = {}
    with open(path / "DistrictManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            district_manifest[i["Id"]] = {
                "District": i["Description"],
                "DistrictTypeId": i["DistrictTypeId"],
            }

    districtType_manifest = {}
    with open(path / "DistrictTypeManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            districtType_manifest[i["Id"]] = i["Description"]

    districtPrecinctPortion_manifest = {}
    with open(path / "DistrictPrecinctPortionManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            districtPrecinctPortion_manifest[i["PrecinctPortionId"]] = i["DistrictId"]

    ballotType_manifest = {}
    with open(path / "BallotTypeManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            ballotType_manifest[i["Id"]] = i["Description"]

    countingGroup_manifest = {}
    with open(path / "CountingGroupManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            countingGroup_manifest[i["Id"]] = i["Description"]

    ballotTypeContest_manifest = {}
    with open(path / "BallotTypeContestManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:

            if i["ContestId"] not in ballotTypeContest_manifest.keys():
                ballotTypeContest_manifest[i["ContestId"]] = []

            ballotTypeContest_manifest[i["ContestId"]].append(i["BallotTypeId"])

    tabulator_manifest = {}
    with open(path / "TabulatorManifest.json", encoding="utf8") as f:
        for i in json.load(f)["List"]:
            tabulator_manifest[i["Id"]] = i["VotingLocationName"]

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
            for contests in json.load(f)["Sessions"]:

                # ballotID
                ballotID_search = re.search("Images\\\\(.*)\*\.\*", contests["ImageMask"])
                if ballotID_search:
                    ballotID = ballotID_search.group(1)
                else:
                    raise RuntimeError("regex is not working correctly. debug")

                countingGroup = countingGroup_manifest[contests["CountingGroupId"]]

                # voting location for ballots
                ballotVotingLocation = tabulator_manifest[contests["TabulatorId"]]

                # for each session use original, or if isCurrent is False,
                # use modified
                if contests["Original"]["IsCurrent"]:
                    current_contests = contests["Original"]
                else:
                    current_contests = contests["Modified"]

                # precinctId for this ballot
                precinctPortion = precinctPortion_manifest[current_contests["PrecinctPortionId"]]["Portion"]
                precinctId = precinctPortion_manifest[current_contests["PrecinctPortionId"]]["PrecinctId"]

                precinct = None
                if precinct_manifest:
                    precinct = precinct_manifest[precinctId]

                # ballotType for this ballot
                ballotType = ballotType_manifest[current_contests["BallotTypeId"]]

                # district for ballot
                ballotDistrictId = districtPrecinctPortion_manifest[current_contests["PrecinctPortionId"]]
                ballotDistrict = district_manifest[ballotDistrictId]["District"]
                ballotDistrictType = districtType_manifest[district_manifest[ballotDistrictId]["DistrictTypeId"]]

                ballot_contest_marks = None
                for cards in current_contests["Cards"]:
                    for ballot_contest in cards["Contests"]:
                        if ballot_contest["Id"] == current_contest_id:
                            if ballot_contest_marks is not None:
                                raise (
                                    RuntimeError("Contest Id appears twice across a single set of cards. Not expected.")
                                )
                            ballot_contest_marks = ballot_contest["Marks"]

                # skip ballot if didn't contain contest
                if ballot_contest_marks is None:
                    continue

                # check for marks on each rank expected for this contest
                currentRank = 1
                current_ballot_ranks = []
                while currentRank <= current_contest_rank_limit:

                    # find any marks that have the currentRank and aren't Ambiguous
                    currentRank_marks = [
                        i for i in ballot_contest_marks if i["Rank"] == currentRank and i["IsAmbiguous"] is False
                    ]

                    currentCandidate = "**error**"

                    if len(currentRank_marks) == 0:
                        currentCandidate = BallotMarks.SKIPPED
                    elif len(currentRank_marks) > 1:
                        currentCandidate = BallotMarks.OVERVOTE
                    else:
                        currentCandidate = candidate_manifest[currentRank_marks[0]["CandidateId"]]

                    if currentCandidate == "**error**":
                        raise RuntimeError("error in filtering marks. debug")

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

    ballot_dict = {
        "ranks": ballot_ranks,
        "weight": [decimal.Decimal("1")] * len(ballot_ranks),
        "ballotID": ballot_IDs,
        "precinct": ballot_precincts,
        "precinctPortion": ballot_precinctPortions,
        "ballot_type": ballot_types,
        "countingGroup": ballot_countingGroups,
        "votingLocation": ballot_votingLocation,
        "district": ballot_district,
        "districtType": ballot_districtType,
    }

    # make sure precinctManifest was part of CVR, otherwise exclude precinct column
    if len(ballot_precincts) != sum(i is None for i in ballot_precincts):
        ballot_dict["precinct"] = ballot_precincts

    # check ballotIDs are unique
    if len(set(ballot_dict["ballotID"])) != len(ballot_dict["ballotID"]):
        raise RuntimeError("some non-unique ballot IDs")

    return ballot_dict


def choice_pro_plus(cvr_path: Union[str, pathlib.Path]) -> Dict[str, List]:
    """Parser for choice pro plus CVR files.

    :param cvr_path: Directory where .chp and .prm files are located.
    :type cvr_path: Union[str, pathlib.Path]
    :raises RuntimeError: Raised if more than 1 .chp file present in directory or .chp contains to no references to .prm files.
    :return: A dictionary of lists containing informtion in the CVR file. Ranks are combined into per-ballot lists and stored with the key 'ranks'. A 'weight' key and list of 1's is added to the dictionary if no 'weight' column exists. All weights are of type :class:`decimal.Decimal`.
    :rtype: Dict[str, List]
    """

    cvr_path = pathlib.Path(cvr_path)

    # read chp file
    chp_glob = [f for f in cvr_path.glob("*.chp")]
    if len(chp_glob) > 1:
        raise RuntimeError(f"more than one .chp file found in directory {str(cvr_path)}")

    candidate_map = {}
    prm_files = []
    with open(chp_glob[0], encoding="utf8") as f:
        for i in f:

            split = i.strip("\n").split()

            if len(split) >= 3 and split[0] == ".CANDIDATE":
                candidate_map[split[1].strip(",")] = i.split('"')[1].split('"')[0]

            if len(split) == 2 and split[0] == ".INCLUDE":
                prm_files.append(cvr_path / split[1])

    # read prm files
    if not prm_files:
        raise RuntimeError(f"no .prm files listed in .chp file {chp_glob[0]}")

    ballots = []
    for prm_file in prm_files:
        with open(prm_file, "r", encoding="utf8") as f:
            for i in f:
                if any(map(str.isalnum, i)) and i.strip()[0] != "#":
                    b = []
                    s = i.split()
                    choices = [] if len(s) == 1 else s[1].split(",")
                    for choice in filter(None, choices):
                        can, rank = choice.split("]")[0].split("[")
                        b.extend([BallotMarks.SKIPPED] * (int(rank) - len(b) - 1))
                        b.append(BallotMarks.OVERVOTE if "=" in choice else candidate_map[can])
                    ballots.append(b)

    # add in tail skipped ranks
    maxlen = max(map(len, ballots))
    for b in ballots:
        b.extend([BallotMarks.SKIPPED] * (maxlen - len(b)))

    return {"ranks": ballots, "weight": [decimal.Decimal("1")] * len(ballots)}


def burlington2006(cvr_path: Union[str, pathlib.Path]) -> Dict[str, List]:
    """Function to parse file format used in 2006 Burlington Mayoral Election.

    :param cvr_path: Path to CVR file. If a file called "candidate_codes.csv" exists in the same directory, it will be read and values from the "code" column that are found in the cvr file ranks will be replaced values in the "candidate" columns.
    :type cvr_path: Union[str, pathlib.Path]
    :return: A dictionary of lists containing informtion in the CVR file. Ranks are combined into per-ballot lists and stored with the key 'ranks'. A 'weight' key and list of 1's is added to the dictionary if no 'weight' column exists. All weights are of type :class:`decimal.Decimal`.
    :rtype: Dict[str, List]
    """

    path = pathlib.Path(cvr_path)

    # read in lines
    ballots = []
    with open(path, "r", encoding="utf8") as f:
        for line in f:
            ballots.append([BallotMarks.OVERVOTE if "=" in i else i for i in line.split()[3:]])

    # fill in skipped ranks with constant
    maxlen = max(map(len, ballots))
    for b in ballots:
        b.extend([BallotMarks.SKIPPED] * (maxlen - len(b)))

    # read candidate codes
    candidate_codes_fname = path.parent / "candidate_codes.csv"
    if os.path.exists(candidate_codes_fname):

        cand_codes = pd.read_csv(candidate_codes_fname, encoding="utf8")
        cand_codes_dict = {str(code): cand for code, cand in zip(cand_codes["code"], cand_codes["candidate"])}

        # replace candidate codes with candidate names
        new_ballots = []
        for b in ballots:
            new_ballots.append([cand_codes_dict[cand] if cand in cand_codes_dict else cand for cand in b])

    return {"ranks": new_ballots}


def ess1(cvr_path: Union[str, pathlib.Path], office: str) -> Dict[str, List]:
    """Parser for one format of ES&S CVR files.

    :param cvr_path: Directory containing "\*allot\*.txt" files and "\*aster\*.txt" files.
    :type cvr_path: Union[str, pathlib.Path]
    :param office: Name of election to parse, as written in master lookup file.
    :type office: str
    :return: A dictionary of lists containing informtion in the CVR file. Ranks are combined into per-ballot lists and stored with the key 'ranks'. A 'weight' key and list of 1's is added to the dictionary if no 'weight' column exists. All weights are of type :class:`decimal.Decimal`.
    :rtype: Dict[str, List]
    """

    cvr_path = pathlib.Path(cvr_path)

    # FIND THE FILES
    ballot_image_files = [f for f in cvr_path.glob("*allot*.txt")]
    master_lookup_files = [f for f in cvr_path.glob("*aster*.txt")]

    ballot_image_path = None
    if not ballot_image_files:
        raise RuntimeError(f"parser error - no ballot image file found in {cvr_path}")
    elif len(ballot_image_files) > 1:
        raise RuntimeError(f"too many ballot image files in directory {cvr_path}. Should only be one.")
    else:
        ballot_image_path = ballot_image_files[0]

    master_lookup_path = None
    if not master_lookup_files:
        raise RuntimeError(f"parser error - no master lookup file found in {cvr_path}")
    elif len(master_lookup_files) > 1:
        raise RuntimeError(f"too many master lookup files in directory {cvr_path}. Should only be one.")
    else:
        master_lookup_path = master_lookup_files[0]

    # READ MASTER LOOKUP
    master_lookup = collections.defaultdict(dict)
    candidate_contest_map = {}
    with open(master_lookup_path, encoding="utf8") as f:
        for i in f:
            mapping = i[:10].strip()
            key = i[10:17].strip()
            value = i[17:67].strip()

            master_lookup[mapping][key] = value

            if mapping == "Candidate":
                candidate_contest_id = i[74:81].strip()
                candidate_contest_map.update({key: candidate_contest_id})

    # find contest id
    contest_reverse_map = {v.strip(): k for k, v in master_lookup["Contest"].items()}
    if office not in contest_reverse_map:
        raise RuntimeError(
            f"contest set office value ({office}) not present in master lookup file {master_lookup_path}"
        )
    contest_id = contest_reverse_map[office]

    # remove candidates from master lookup if they are from another contest
    master_lookup["Candidate"] = {
        candidate_id: candidate_val
        for candidate_id, candidate_val in master_lookup["Candidate"].items()
        if candidate_contest_map[candidate_id] == contest_id
    }

    # tally types are stored in master lookup with 7 chars but only recorded in ballot image with 3
    # trim off the first 4 char from the master lookup strings
    tally_type_map = {k[4:]: v for k, v in master_lookup["Tally Type"].items()}

    # separate out other maps
    precinct_map = master_lookup["Precinct"]
    name_map = {
        k: {"WRITEIN": BallotMarks.WRITEIN}.get(v.upper().replace("-", ""), v)
        for k, v in master_lookup["Candidate"].items()
    }

    # READ BALLOT FILE
    voter_info_collected = collections.defaultdict(list)
    max_rank_num = 0
    with open(ballot_image_path, "r", encoding="utf8") as f:

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

            voter_info_collected[line_voter_id].append(
                {
                    "voter_id": line_voter_id,
                    "tally_type": tally_type_map[line_tally_type],
                    "precinct": precinct_map[line_precinct_id],
                    # 0 candidate id plus a skipped or overvote mark, indicate skip or overvote
                    "candidate": name_map[line_candidate_id] if int(line_candidate_id) else 0,
                    "rank": int(line_rank),
                    "skipped": int(line_skipped),
                    "overvote": int(line_overvote),
                }
            )

            # debug check to see if ballot marks with valid candidate name stored sometimes also get paired,
            # with overvote or skipped marks?
            if int(line_candidate_id) and (int(line_skipped) or int(line_overvote)):
                raise RuntimeError("both a skip and overvote mark for this rank. unexpected")

    # for each voter, assemble the ballot
    dct = {"ranks": [], "precinct": [], "tally_type": [], "ballotID": []}
    for voter_id in voter_info_collected:

        voter_ballot_info = voter_info_collected[voter_id]

        # debug checks
        voter_tally_type_set = set([b["tally_type"] for b in voter_ballot_info])
        voter_precinct_set = set([b["precinct"] for b in voter_ballot_info])

        if len(voter_tally_type_set) > 1:
            raise RuntimeError("Marks for this voter contain multiple tally type values. Unexpected.")

        if len(voter_precinct_set) > 1:
            raise RuntimeError("Marks for this voter contain multiple precinct values. Unexpected.")

        voter_tally_type = list(voter_tally_type_set)[0]
        voter_precinct = list(voter_precinct_set)[0]

        voter_ranks = [None] * max_rank_num
        for rank in range(1, max_rank_num + 1):

            rank_info_filter = [b for b in voter_ballot_info if b["rank"] == rank]

            if len(rank_info_filter) > 1:
                raise RuntimeError("unexpected")
                # an overvote marker is stored in the file, but do overvoted ranks still get all their marks stored ?
            elif len(rank_info_filter) == 0:
                raise RuntimeError("unexpected")
                # this would be unexpected since there is a skipped rank mark in the file
            else:
                rank_info = rank_info_filter[0]

            rank_candidate = rank_info["candidate"]

            if rank_candidate == 0 and rank_info["skipped"] and rank_info["overvote"]:
                raise RuntimeError("this shouldnt be reached")
            elif rank_candidate == 0 and rank_info["skipped"]:
                voter_ranks[rank - 1] = BallotMarks.SKIPPED
            elif rank_candidate == 0 and rank_info["overvote"]:
                voter_ranks[rank - 1] = BallotMarks.OVERVOTE
            else:
                voter_ranks[rank - 1] = rank_candidate

        if any(r is None for r in voter_ranks):
            raise RuntimeError("not all ranks for this voter had data stored in the file. unexpected.")

        dct["ranks"].append(voter_ranks)
        dct["ballotID"].append(voter_id)
        dct["tally_type"].append(voter_tally_type)
        dct["precinct"].append(voter_precinct)

    # add weights
    dct.update({"weight": [decimal.Decimal("1")] * len(dct["ranks"])})
    return dct


def ess2(cvr_path: Union[str, pathlib.Path]) -> Dict[str, List]:
    """Parser for another format of ES&S CVR files.

    :param cvr_path: Directory containing "\*allot\*.txt" files and "\*ntl\*.txt" files.
    :type cvr_path: Union[str, pathlib.Path]
    :return: A dictionary of lists containing informtion in the CVR file. Ranks are combined into per-ballot lists and stored with the key 'ranks'. A 'weight' key and list of 1's is added to the dictionary if no 'weight' column exists. All weights are of type :class:`decimal.Decimal`.
    :rtype: Dict[str, List]
    """

    cvr_path = pathlib.Path(cvr_path)

    ballot_glob = [f for f in cvr_path.glob("*allot*.txt")]
    cntl_glob = [f for f in cvr_path.glob("*ntl*.txt")]

    if len(ballot_glob) > 1:
        raise RuntimeError(f"more than 1 file with pattern matching *allot*.txt found in directory {str(cvr_path)}")

    if len(cntl_glob) > 1:
        raise RuntimeError(f"more than 1 file with pattern matching *ntl*.txt found in directory {str(cvr_path)}")

    # read in canadidate codes and names
    candidate_map = {}
    with open(cntl_glob[0], encoding="utf8") as f:
        for i in f:
            line = [j.strip() for j in i.split(":")]
            if line and line[0] == "Candidate":
                candidate_map[line[1]] = line[2]

    candidate_map["--"] = BallotMarks.SKIPPED
    candidate_map["++"] = BallotMarks.OVERVOTE

    # read ballots
    ballots = []
    with open(ballot_glob[0], "r", encoding="utf8") as f:
        line = f.readline()
        while line:
            ballots.append([candidate_map[i] for i in line.split()[-1].split(">")])
            line = f.readline()

    return ballots


def minneapolis2009(cvr_path: Union[str, pathlib.Path], office: str) -> Dict[str, List]:
    """
    Parser for 2009 Minneapolis elections.

    :param cvr_path: Path to CVR file. Parent directory should contain a file called "convert.csv" with candidate and office codes.
    :type cvr_path: Union[str, pathlib.Path]
    :param office: Name of election to parse as written in "convert.csv" file.
    :type office: str
    :raises RuntimeError: Raised if no candidates are found with given office argument.
    :return: A dictionary of lists containing informtion in the CVR file. Ranks are combined into per-ballot lists and stored with the key 'ranks'. A 'weight' key and list of 1's is added to the dictionary if no 'weight' column exists. All weights are of type :class:`decimal.Decimal`.
    :rtype: Dict[str, List]
    """

    cvr_path = pathlib.Path(cvr_path)

    # read map file
    map_file = cvr_path.parent / "convert.csv"

    choice_map = {}
    default = None
    with open(map_file, encoding="utf8") as f:
        for i in f:
            split = i.strip().split("\t")
            if len(split) >= 3 and split[0].strip() == office:
                choice_map[split[2]] = split[1]

    if choice_map == {}:
        raise RuntimeError('No candidates found. Ensure "office" field in contest_set matches CVR.')

    choice_map["XXX"] = BallotMarks.SKIPPED
    default = BallotMarks.WRITEIN

    # read ballots
    precincts = []
    ballots = []
    with open(cvr_path, "r", encoding="utf8") as f:
        f.readline()
        for line in csv.reader(f):
            choices = [choice_map.get(i.strip(), i if default is None else default) for i in line[1:-1]]
            if choices != ["", "", ""]:
                ballots.extend([choices] * int(float(line[-1])))
                for p in range(int(float(line[-1]))):
                    precincts.append(line[0])

    bs = {
        "ranks": ballots,
        "weight": [decimal.Decimal("1")] * len(ballots),
        "precinct": precincts,
    }

    return bs


def _santafe(column_id, contest_id, ctx):
    path = ctx["cvr_path"]
    candidate_map = {}
    with open(ctx["cvr_path"].replace("CvrExport", "CandidateManifest"), encoding="utf8") as f:
        for i in f:
            row = i.split(",")
            if row:
                candidate_map[row[1]] = row[0]
    ballots = []
    ballot_length = 0
    with open(path, "r", encoding="utf8") as f:
        reader = csv.reader(f)
        header = next(reader)
        s = "Original/Cards/0/Contests/{}/Marks/{}/{}"
        rinds = []
        cinds = []
        for i in range(len(header)):
            try:
                rinds.append(header.index(s.format(column_id, i, "Rank")))
            except ValueError:
                break
            cinds.append(header.index(s.format(column_id, i, "CandidateId")))
        col = header.index("Original/Cards/0/Contests/{}/Id".format(column_id))
        for line in reader:
            if line[col] == str(contest_id):
                choices = []
                ranks = [int(line[i]) for i in rinds if line[i] != ""]
                ballot_length = max(ranks + [ballot_length])
                candidates = iter(cinds)
                for i in range(len(rinds)):
                    c = ranks.count(i + 1)
                    if c == 0:
                        choices.append(BallotMarks.SKIPPED)
                    elif c == 1:
                        next_candidate = line[next(candidates)]
                        choices.append(candidate_map[next_candidate])
                    else:
                        choices.append(BallotMarks.OVERVOTE)
                ballots.append(choices)
    return [b[:ballot_length] for b in ballots]


def _santafe_id(column_id, contest_id, ctx):
    path = ctx["cvr_path"]
    ballots = []
    ballot_length = 0
    with open(path, "r", encoding="utf8") as f:
        reader = csv.reader(f)
        header = next(reader)
        s = "Original/Cards/0/Contests/{}/Marks/{}/{}"
        rinds = []
        cinds = []
        for i in range(len(header)):
            try:
                rinds.append(header.index(s.format(column_id, i, "Rank")))
            except ValueError:
                break
            cinds.append(header.index(s.format(column_id, i, "CandidateId")))
        col = header.index("Original/Cards/0/Contests/{}/Id".format(column_id))
        for i, line in enumerate(reader):
            if line[col] == str(contest_id):
                choices = collections.UserList([])
                choices.voter_id = i
                ranks = [int(line[i]) for i in rinds if line[i] != ""]
                ballot_length = max(ranks + [ballot_length])
                candidates = iter(cinds)
                for i in range(len(rinds)):
                    c = ranks.count(i + 1)
                    if c == 0:
                        choices.append(BallotMarks.SKIPPED)
                    elif c == 1:
                        choices.append(line[next(candidates)])
                    else:
                        choices.append(BallotMarks.OVERVOTE)
                ballots.append(choices)
    for b in ballots:
        b.data = b.data[:ballot_length]
    return ballots


def unisyn(cvr_path: Union[str, pathlib.Path]) -> Dict[str, List]:
    """
    Parser for CVRs received from unisyn systems.

    Note: This parser was developed for the unisyn 2020 Hawaii Dem Primary CVR which only contained the
    ranked choice votes for a single election. Unisyn uses the common data format in xml, however the
    parser currently is not a complete common data format parser.

    For more information on common data format, see:
    https://pages.nist.gov/CastVoteRecords/
    https://github.com/hiltonroscoe/cdfprototype

    :param cvr_path: Directory containing .xml files
    :type cvr_path: Union[str, pathlib.Path]
    :return: A dictionary of lists containing informtion in the CVR file. Ranks are combined into per-ballot lists and stored with the key 'ranks'. A 'weight' key and list of 1's is added to the dictionary if no 'weight' column exists. All weights are of type :class:`decimal.Decimal`.
    :rtype: Dict[str, List]
    """

    glob_str = pathlib.Path(cvr_path).glob("/*.xml")

    contestIDdicts = {}
    for f in glob_str:

        with open(f) as fd:
            xml_dict = xmltodict.parse(fd.read())

        # get candidates
        candidatesIDs = {}
        for cand_dict in xml_dict["CastVoteRecordReport"]["Election"]["Candidate"]:
            candidatesIDs[cand_dict["@ObjectId"]] = cand_dict["Name"]

        # loop through CVR snapshots
        for cvr_dict in xml_dict["CastVoteRecordReport"]["CVR"]:

            cvr_contest = cvr_dict["CVRSnapshot"]["CVRContest"]

            if cvr_contest["ContestId"] not in contestIDdicts:
                contestIDdicts.update({cvr_contest["ContestId"]: []})
            contestIDdicts[cvr_contest["ContestId"]].append(cvr_contest["CVRContestSelection"])

    # check that all rank lists are equal
    first_rank = list(contestIDdicts.keys())[0]
    rank_length_equal = [len(contestIDdicts[k]) == len(contestIDdicts[first_rank]) for k in contestIDdicts]
    if not all(rank_length_equal):
        RuntimeError("not all rank lists are equal.")

    # combine ranks into lists
    ballot_lists = []
    for idx in range(len(contestIDdicts[first_rank])):

        idx_ranks = [int(contestIDdicts[rank_key][idx]["Rank"]) for rank_key in contestIDdicts]

        idx_candidates = []
        for rank_key in contestIDdicts:
            contest_dict = contestIDdicts[rank_key][idx]
            if "SelectionPosition" in contest_dict:
                if isinstance(contest_dict["SelectionPosition"], list):
                    idx_candidates.append(BallotMarks.OVERVOTE)
                else:
                    idx_candidates.append(candidatesIDs[contest_dict["SelectionPosition"]["Position"]])
            elif contest_dict["TotalNumberVotes"] == "0":
                idx_candidates.append(BallotMarks.SKIPPED)

        ordered_ranks = sorted(zip(idx_candidates, idx_ranks), key=lambda x: x[1])
        ballot_lists.append([t[0] for t in ordered_ranks])

    # assemble dict
    dct = {"ranks": ballot_lists}
    dct["weight"] = [decimal.Decimal("1")] * len(dct["ranks"])

    return dct


def _surveyUSA(cvr_path):
    """
    Survey USA files usually include all respondents and should be pre-filtered for any columns
    prior to cruncher use (such as filtering likely democratic voters). Rank columns and ballotID columns
    should also be renamed prior to parsing.

    Rank columns can contain candidate codes or NaN. NaN is treated as a skipped rank.

    Required files:
    cvr.csv - contains ballots, ranks, weights
    candidate_codes.csv - contains two columns ("code" and "candidate") that map cvr code numbers to candidate names.
    """

    path = pathlib.Path(cvr_path)

    csv_df = pd.read_csv(path / "cvr.csv")
    candidate_codes_df = pd.read_csv(path / "candidate_codes.csv")

    # candidate code dict
    candidate_map = {row["code"]: row["candidate"] for index, row in candidate_codes_df.iterrows()}

    # find rank columns
    rank_columns = [col for col in csv_df.columns if "rank" in col.lower()]

    ballots = []
    for index, row in csv_df.iterrows():

        b_ranks = [BallotMarks.SKIPPED] * len(rank_columns)

        saw_undecided = False
        since_undecided = []

        for idx, rank in enumerate(rank_columns):

            # nan marks end of ranks
            if math.isnan(row[rank]):
                if since_undecided:
                    print("some candidates appeared after an undecided vote! debug")
                    raise RuntimeError
                break

            candidate = candidate_map[row[rank]]

            if saw_undecided:
                since_undecided.append(candidate)

            if candidate == "Undecided":
                saw_undecided = True

            if candidate != "Undecided":
                b_ranks[idx] = candidate

        ballots.append(b_ranks)

    ballot_dict = {
        "ranks": ballots,
        "weight": csv_df["weight"],
        "ballotID": csv_df["ballotID"],
    }
    return ballot_dict


def _nyc2021(cvr_path, other_data_cols, aggregate=False):

    # read candidate codes
    candidate_code_df = pd.read_csv(cvr_path / "candidate_codes.csv")
    candidate_code_dict = {
        str(code): candidate for code, candidate in zip(candidate_code_df["code"], candidate_code_df["candidate"])
    }
    candidate_code_dict["undervote"] = BallotMarks.SKIPPED
    candidate_code_dict["overvote"] = BallotMarks.OVERVOTE
    candidate_code_dict["Write-in"] = BallotMarks.WRITEIN

    # read election names
    rcv_election_list = []
    with open(cvr_path / "rcv_elections.txt") as rcv_elections:
        for line in rcv_elections:
            rcv_election_list.append(line.strip("\n"))

    # gather subset dataframe for each election
    election_dfs = {election_name: [] for election_name in rcv_election_list}
    for f in cvr_path.glob("*.csv"):

        # read cvr
        df = pd.read_csv(f, skip_blank_lines=False, dtype=object)
        df["source_file"] = str(f.stem)

        added_ballot_style = False
        if "Ballot Style" not in df.columns.tolist():
            df["Ballot Style"] = ""
            added_ballot_style = True

        # which elections are in this file
        incl_elections = []
        for elec in rcv_election_list:
            if any(all(elec_piece in col.split(" ") for elec_piece in elec.split(" ")) for col in df.columns.tolist()):
                incl_elections.append(elec)

        for elec in incl_elections:

            party_abbr = elec.split(" ")[0]

            # subset on party
            which_rows = [True for _ in range(df.shape[0])]
            sub_df = df.loc[:, :]
            if not added_ballot_style:
                which_rows = [True if party_abbr in i else False for i in df["Ballot Style"]]
                sub_df = df.iloc[which_rows, :]

            # find relevant rank columns
            election_cols = [
                col
                for col in sub_df.columns.tolist()
                if all(elec_piece in col.split(" ") for elec_piece in elec.split(" "))
            ]

            # make sure columns are in order
            election_col_order = [(col, int(re.search(".*Choice (\d\d?).*", col).group(1))) for col in election_cols]
            election_col_order = [i[0] for i in sorted(election_col_order, key=lambda x: x[1])]

            sub_cols = list(other_data_cols) + ["Ballot Style", "source_file"] + election_col_order
            election_dfs[elec].append(sub_df.loc[:, sub_cols])

    # aggregate election data frames
    election_ballots = {
        election_name: {i: [] for i in list(other_data_cols) + ["ranks", "Ballot Style", "source_file"]}
        for election_name in rcv_election_list
    }

    for elec in rcv_election_list:

        concat_df = pd.concat(election_dfs[elec])

        if aggregate:
            agg_df = concat_df.groupby(concat_df.columns.tolist()).size().reset_index(name="weight")
            agg_df["weight"] = [decimal.Decimal(i) for i in agg_df["weight"]]
            label_cols = list(other_data_cols) + [
                "Ballot Style",
                "source_file",
                "weight",
            ]

        else:
            agg_df = concat_df
            label_cols = list(other_data_cols) + ["Ballot Style", "source_file"]

        rank_cols = [col for col in agg_df.columns if col not in label_cols]

        for col in label_cols:
            election_ballots[elec][col] = agg_df[col].tolist()

        election_ballots[elec]["ranks"] = [
            [candidate_code_dict[code] if code in candidate_code_dict else str(code) for code in list(i)]
            for i in zip(*[agg_df[col].tolist() for col in rank_cols])
        ]

    return election_ballots


def nyc2021(cvr_path: Union[str, pathlib.Path], office: str, other_data_cols: List = ["Precinct"]) -> Dict[str, List]:
    """Parser for NYC 2021 Primary Elections. One election at a time.

    :param cvr_path: CVR directory containing "candidate_codes.csv", "rcv_elections.txt", and many csv CVR files.
    :type cvr_path: Union[str, pathlib.Path]
    :param office: Name of election listed in "rcv_elections.txt" to parse from CVR.
    :type office: str
    :return: A dictionary of lists containing informtion in the CVR file. Ranks are combined into per-ballot lists and stored with the key 'ranks'. A 'weight' key and list of 1's is added to the dictionary if no 'weight' column exists. All weights are of type :class:`decimal.Decimal`.
    :rtype: Dict[str, List]
    """
    election_ballots = _nyc2021(cvr_path, tuple(other_data_cols), aggregate=False)
    return election_ballots[office]


parser_dict = {
    "burlington2006": burlington2006,
    "rank_column_csv": rank_column_csv,
    "dominion5_2": dominion5_2,
    "dominion5_4": dominion5_4,
    "dominion5_10": dominion5_10,
    "ess1": ess1,
    "ess2": ess2,
    "choice_pro_plus": choice_pro_plus,
    "unisyn": unisyn,
    # "surveyUSA": surveyUSA,
    "minneapolis2009": minneapolis2009,
    "candidate_column_csv": candidate_column_csv,
    "nyc2021": nyc2021
    # "santafe": santafe, still need to figure out this parser
    # "santafe_id": santafe_id,
}
