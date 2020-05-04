from pathlib import Path
from glob import glob
from collections import UserList, defaultdict
from gmpy2 import mpq as Fraction
from inspect import isfunction
import pandas as pd
import os
import csv
import json
import re

from .definitions import SKIPPEDRANK, OVERVOTE, WRITEIN

def get_parser_dict():
    """
    Return dictionary of parsers, parser_name: parser_func_obj
    """
    return {key: value for key, value in globals().items()
            if isfunction(value) and key != "get_parser_dict" and value.__module__ == __name__}

def common_csv(ctx, path=None):

    # if no path passed, get from ctx
    if path is None:
        path = ctx['path']

    # assume contest-specific filename, otherwise revert to default name
    cvr_path = path + '/' + ctx['dop'] + '.csv'
    if os.path.isfile(cvr_path) is False:
        cvr_path = path + '/cvr.csv'

    df = pd.read_csv(cvr_path)

    # find rank columns
    rank_col = [col for col in df.columns if 'rank' in col.lower()]

    # ensure rank columns are strings
    df[rank_col] = df[rank_col].astype(str)

    # if candidate codes file exist, swap in names
    candidate_codes_fpath = path + '/candidate_codes.csv'
    if os.path.isfile(candidate_codes_fpath):

        cand_codes = pd.read_csv(candidate_codes_fpath)

        cand_codes_dict = {str(code): cand for code, cand in zip(cand_codes['code'], cand_codes['candidate'])}
        replace_dict = {col: cand_codes_dict for col in rank_col}

        df = df.replace(replace_dict)

    # replace skipped ranks and overvotes with constants
    df = df.replace({col: {'under': SKIPPEDRANK, 'over': OVERVOTE} for col in rank_col})

    # pull out rank lists
    rank_col_list = [df[col].tolist() for col in rank_col]
    rank_lists = [list(rank_tuple) for rank_tuple in list(zip(*rank_col_list))]

    # double check
    if not all([len(i) == len(rank_lists[0]) for i in rank_lists]):
        print('not all rank lists are same length. debug')
        raise RuntimeError

    # assemble dict
    dct = {'ranks': rank_lists}

    # add in non-rank columns
    for col in df.columns:
        if col not in rank_col:
            dct[col] = df[col].tolist()

    # add weight if not present in csv
    if 'weight' not in dct:
        dct['weight'] = [Fraction(1) for b in dct['ranks']]

    return dct

def dominion5_10(ctx):

    path = ctx['path']

    # load manifests, with ids as keys
    with open(path + '/ContestManifest.json') as f:
        for i in json.load(f)['List']:
            if i['Description'] == ctx['office']:
                current_contest_id = i['Id']
                current_contest_rank_limit = i['NumOfRanks']

    candidate_manifest = {}
    with open(path + '/CandidateManifest.json') as f:
        for i in json.load(f)['List']:
            candidate_manifest[i['Id']] = i['Description']

    precinct_manifest = {}
    with open(path + '/PrecinctPortionManifest.json') as f:
        for i in json.load(f)['List']:
            precinct_manifest[i['Id']] = i['Description']

    ballotType_manifest = {}
    with open(path + '/BallotTypeManifest.json') as f:
        for i in json.load(f)['List']:
            ballotType_manifest[i['Id']] = i['Description']

    countingGroup_manifest = {}
    with open(path + '/CountingGroupManifest.json') as f:
        for i in json.load(f)['List']:
            countingGroup_manifest[i['Id']] = i['Description']

    ballotTypeContest_manifest = {}
    with open(path + '/BallotTypeContestManifest.json') as f:
        for i in json.load(f)['List']:

            if i['ContestId'] not in ballotTypeContest_manifest.keys():
                ballotTypeContest_manifest[i['ContestId']] = []

            ballotTypeContest_manifest[i['ContestId']].append(i['BallotTypeId'])

    # read in ballots
    ballot_ranks = []
    ballot_IDs = []
    ballot_precincts = []
    ballot_types = []
    with open(path + '/CvrExport.json') as f:
        for contests in json.load(f)['Sessions']:

            # ballotID
            ballotID_search = re.search('Images\\\\(.*)\*\.\*', contests['ImageMask'])
            if ballotID_search:
                ballotID = ballotID_search.group(1)
            else:
                print('regex is not working correctly. debug')
                exit(1)

            # for each session use original, or if isCurrent is False,
            # use modified
            if contests['Original']['IsCurrent']:
                current_contests = contests['Original']
            else:
                current_contests = contests['Modified']

            # precinctId for this ballot
            precinct = precinct_manifest[current_contests['PrecinctPortionId']]

            # ballotType for this ballot
            ballotType = ballotType_manifest[current_contests['BallotTypeId']]

            if len(current_contests['Cards']) > 1 or len(current_contests['Cards'][0]['Contests']) > 1:
                print('"Cards" has length greater than 1, not prepared for this. debug')
                exit(1)
            else:
                current_contests = current_contests['Cards'][0]['Contests'][0]

            # skip other contests
            if current_contests['Id'] != current_contest_id:
                continue

            ballot_contest_marks = current_contests['Marks']

            # check for marks on each rank expected for this contest
            currentRank = 1
            current_ballot_ranks = []
            while currentRank <= current_contest_rank_limit:

                # find any marks that have the currentRank and aren't Ambiguous
                currentRank_marks = [i for i in ballot_contest_marks
                                     if i['Rank'] == currentRank and i['IsAmbiguous'] is False]

                currentCandidate = '**error_CZ**'

                if len(currentRank_marks) == 0:
                    currentCandidate = SKIPPEDRANK
                elif len(currentRank_marks) > 1:
                    currentCandidate = OVERVOTE
                else:
                    currentCandidate = candidate_manifest[currentRank_marks[0]['CandidateId']]

                if currentCandidate == '**error_CZ**':
                    print('error in filtering marks. debug')
                    exit(1)

                current_ballot_ranks.append(currentCandidate)
                currentRank += 1

            ballot_ranks.append(current_ballot_ranks)
            ballot_precincts.append(precinct)
            ballot_IDs.append(ballotID)
            ballot_types.append(ballotType)

    ballot_dict = {'ranks': ballot_ranks,
                   'weight': [Fraction(1) for b in ballot_ranks],
                   'ballotID': ballot_IDs,
                   'precinct': ballot_precincts,
                   'ballot_type': ballot_types}

    return ballot_dict


def sf_precinct_map(ctx):
    path = ctx['path']
    master_lookup_path = ctx.get('master_lookup')
    if master_lookup_path is None:
        master_lookup_path = path.replace('ballot_image', 'master_lookup') \
                                 .replace('BallotImage', 'MasterLookup') \
                                 .replace('ballotimage', 'masterlookup') \
                                 .replace('Ballot Image', 'Master Lookup')
                    
    precinct_map = {}
    with open(master_lookup_path, encoding='utf8') as f:
        for i in f:
            if i.startswith('Precinct'):
                kv = i.split()[1]
                precinct_map[kv[:7]] = kv[7:]
                if ctx['place'] == 'San Francisco':
                    precinct_map[kv[:7]] = i.split()[2]
    return precinct_map

def parse_master_lookup(ctx):
    path = ctx['path']
    master_lookup_path = ctx.get('master_lookup')
    if master_lookup_path is None:
        master_lookup_path = path.replace('ballot_image', 'master_lookup') \
                                 .replace('BallotImage', 'MasterLookup') \
                                 .replace('ballotimage', 'masterlookup') \
                                 .replace('Ballot Image', 'Master Lookup')
                    
    master_lookup = defaultdict(dict)
    with open(master_lookup_path, encoding='utf8') as f:
        for i in f:
            mapping = i[:10].strip()
            key = i[10:17].strip()
            value = i[17:67].strip()
            master_lookup[mapping][key] = value
    return dict(master_lookup)

def sf_name_map(ctx):
    return dict((k, {'WRITEIN': WRITEIN}.get(v.upper().replace('-', ''), v))
                for k, v in parse_master_lookup(ctx)['Candidate'].items())

def chp_names(ctx):
    mapping = {}
    with open(glob(ctx['chp'])[0], encoding='utf8') as f:
        for i in f:
            split = i.split()
            if len(split) >= 3 and split[0] == '.CANDIDATE':
                mapping[split[1].strip(',')] = i.split('"')[1].split('"')[0]
    return mapping

def burlington(ctx):
    path = ctx['path']
    ballots = []
    with open(path, "r", encoding='utf8') as f:
        for line in f:
            ballots.append([OVERVOTE if '=' in i else i for i in line.split()[3:]])
    maxlen = max(map(len,ballots))
    for b in ballots:
        b.extend([SKIPPEDRANK] * (maxlen - len(b)))
    return ballots

#TODO: add functionality to allow resolvalbe overvotes
#       i.e. overvotes that are tabulated after all but
#       one of the candidates in the overvote is eliminated
#       burlington, and possibly cambridge will still count
#       this vote
def prm(ctx):
    glob_path = ctx['path']
    name_map = chp_names(ctx)
    ballots = []
    for path in glob(glob_path):
        with open(path, 'r', encoding='utf8') as f:
            for i in f:
                if any(map(str.isalnum,i)) and i.strip()[0] != '#':
                    b = []
                    s = i.split()
                    choices = [] if len(s) == 1 else s[1].split(',')
                    for choice in filter(None,choices):
                        can, rank = choice.split(']')[0].split('[')
                        b.extend([SKIPPEDRANK] * (int(rank) - len(b) - 1))
                        b.append(OVERVOTE if '=' in choice else name_map[can])
                    ballots.append(b)
                 
    maxlen = max(map(len,ballots))
    for b in ballots:
        b.extend([SKIPPEDRANK] * (maxlen - len(b)))
    return ballots
        

def sf(contest_id, ctx):
    path = ctx['path']
    precinct_map = sf_precinct_map(ctx)
    name_map = sf_name_map(ctx)
    ballots = []
    with open(path, "r", encoding='utf8') as f:
        b = UserList([])
        voter_id = None
        for line in f:
            if line[:7] != contest_id:
                continue
            if line[7:16] != voter_id:
                ballots.append(b)
                voter_id = line[7:16]
                b = UserList([])
            precinct_id = line[26:33]
            candidate_id = int(line[36:43]) and name_map[line[36:43]]
            undervote = SKIPPEDRANK if int(line[44]) else 0
            overvote = OVERVOTE if int(line[43]) else 0
            b.append(candidate_id or undervote or overvote)
            if b[-1] == 0 or len(b) != int(line[33:36]):
                raise Exception("Invalid Choice or Rank")
            b.precinct = precinct_map[precinct_id]
        if b != []:
            ballots.append(b)
    return ballots[1:]

def sfnoid(ctx):
    path = ctx['path']
    precinct_map = sf_precinct_map(ctx)
    name_map = sf_name_map(ctx)
    ballots = []
    with open(path, "r", encoding='utf8') as f:
        b = UserList([])
        voter_id = None
        for line in f:
            if line[7:16] != voter_id:
                ballots.append(b)
                voter_id = line[7:16]
                b = UserList([])
            precinct_id = line[26:33]
            candidate_id = int(line[36:43]) and name_map[line[36:43]]
            undervote = SKIPPEDRANK if int(line[44]) else 0
            overvote = OVERVOTE if int(line[43]) else 0
            
            #Alameda County incorrectly reported 0 for write in candidates for 
            #races in 2012 and treated write-ins as undervotes in their reports
            #for city attorney, the undervote ID was 92. This snippit was used to validate rcv results
            #with the counties official report here:
            #https://www.acvote.org/acvote-assets/pdf/elections/2012/11062012/results/rcv/oakland/city_attorney/nov-6-2012-pass-report-oakland-city-attorney.pdf
            #if candidate_id == 92:
            #    b.append(UNDERVOTE)
            #    continue

            b.append(candidate_id or undervote or overvote)
            if b[-1] == 0 or len(b) != int(line[33:36]):
                raise Exception("Invalid Choice or Rank")
            b.precinct = precinct_map[precinct_id]
        if b:
            ballots.append(b)
    return ballots[1:]

def old(ctx):
    path = ctx['path']
    candidate_map = {} 
    with open(ctx['candidate_map'], encoding='utf8') as f:
        for i in f:
            line = [j.strip() for j in i.split(':')]
            if line and line[0] == 'Candidate':
                candidate_map[line[1]] = line[2]
    candidate_map['--'] = SKIPPEDRANK
    candidate_map['++'] = OVERVOTE
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
        with open('/'.join(ctx['path'].split('/')[:-1]+['convert.csv']), encoding='utf8') as f:
            for i in f:
                split = i.strip().split('\t')
                if len(split) >= 3:
                    choice_map[split[2]] = split[1]
        choice_map['XXX'] = SKIPPEDRANK
        default = WRITEIN
    else:
        choice_map = {
            'UWI': WRITEIN,
            'undervote': SKIPPEDRANK,
            'overvote': OVERVOTE
        }
    path = ctx['path']
    ballots = []
    with open(path, "r", encoding='utf8') as f:
        f.readline()
        for line in csv.reader(f):
            choices = [choice_map.get(i.strip(), i if default is None else default)
                          for i in line[1:-1]]
            if choices != ['','','']:
                ballots.extend([choices] * int(float(line[-1])))
    return ballots

def maine(n, ctx):
    path = ctx['path']
    ballots = []
    with open(path, "r", encoding='utf8') as f:
        f.readline()
        for line in csv.reader(f):
            choices = [{'undervote': SKIPPEDRANK,
                        'overvote': OVERVOTE,
                        'Write-in': WRITEIN}.get(i,i)
                         for i in line[3:3+n]]
            if '' not in choices and choices:
                ballots.append(choices)
    return ballots

def santafe(column_id, contest_id, ctx):
    path = ctx['path']
    candidate_map = {}
    with open(ctx['path'].replace('CvrExport','CandidateManifest'), encoding='utf8') as f:
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
                        choices.append(SKIPPEDRANK)
                    elif c == 1:
                        next_candidate = line[next(candidates)]
                        choices.append(candidate_map[next_candidate])
                    else:
                        choices.append(OVERVOTE)
                ballots.append(choices)
    return [b[:ballot_length] for b in ballots]

def santafe_id(column_id, contest_id, ctx):
    path = ctx['path']
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
                choices = UserList([])
                choices.voter_id = i
                ranks = [int(line[i]) for i in rinds if line[i] != '']
                ballot_length = max(ranks + [ballot_length])
                candidates = iter(cinds)
                for i in range(len(rinds)):
                    c = ranks.count(i+1)
                    if c == 0:
                        choices.append(SKIPPEDRANK)
                    elif c == 1:
                        choices.append(line[next(candidates)])
                    else:
                        choices.append(OVERVOTE)
                ballots.append(choices)
    for b in ballots:
        b.data = b.data[:ballot_length]
    return ballots

def sf2005(contest_ids, over, under, sep, ctx):
    path = ctx['path']
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
                ballots.append([{over: OVERVOTE, under: SKIPPEDRANK}.get(i, i)
                                for i in raw])
    return ballots

def sf2019(ctx):
    with open(ctx['path'] + '/ContestManifest.json', encoding='utf8') as f:
        for i in json.load(f)['List']:
            if i['Description'] == ctx['office'].upper():
                contest_id = i['Id']
                ranks = i['NumOfRanks']
    candidates = {}
    with open(ctx['path'] + '/CandidateManifest.json', encoding='utf8') as f:
        for i in json.load(f)['List']:
            if i['ContestId'] == contest_id:
                candidates[i['Id']] = i['Description']
    precincts = {}
    with open(ctx['path'] + '/PrecinctPortionManifest.json', encoding='utf8') as f:
        for i in json.load(f)['List']:
            precincts[i['Id']] = i['Description'].split()[1]
    ballots = []
    with open(ctx['path'] + '/CvrExport.json', encoding='utf8') as f:
        for contests in json.load(f)['Sessions']:
            if contests['Original']['IsCurrent']:
                current_contests = contests['Original']
            else:
                current_contests = contests['Modified'] 
            precinct = precincts[current_contests['PrecinctPortionId']]
            for contest in current_contests['Contests']:
                if contest['Id'] == contest_id:
                    ballot = UserList([SKIPPEDRANK] * ranks)
                    ballot = UserList([SKIPPEDRANK] * ranks)
                    for mark in contest['Marks']:
                        candidate = candidates[mark['CandidateId']]
                        if candidate == 'Write-in':
                            candidate = WRITEIN
                        rank = mark['Rank']-1
                        if mark['IsAmbiguous']:
                            pass 
                        elif ballot[rank] == OVERVOTE:
                            pass
                        elif ballot[rank] == SKIPPEDRANK:
                            ballot[rank] = candidate
                        elif ballot[rank] != candidate:
                            ballot[rank] = OVERVOTE
                    ballot.precinct = precinct
                    ballots.append(ballot)
                        
    return ballots
            
def utah(ctx):
    ballots = []
    with open(ctx['path'], encoding='utf8') as f:
        next(f)
        for b in f:
            ballots.append(
                [{'overvote':OVERVOTE, 'undervote':SKIPPEDRANK, '': SKIPPEDRANK}.get(i, i)
                for i in b.strip().split(',')[2:]]
            )
    return ballots

def ep(ctx):
    ballots = []
    with open(ctx['path'], encoding='utf8') as f:
        next(f)
        for b in csv.reader(f):
            ballots.append(
                [{'overvote':OVERVOTE, 'undervote':SKIPPEDRANK, 'UWI': WRITEIN}.get(i, i)
                for i in b[3:]]
            )
    #print(ballots[:5])
    return ballots
    
        


