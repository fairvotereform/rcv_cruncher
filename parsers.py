from pathlib import Path
from glob import glob
from collections import UserList, defaultdict
import os
import csv
import json

UNDERVOTE = -1
OVERVOTE = -2
WRITEIN = -3

def sf_precinct_map(ctx):
    path = ctx['path']
    master_lookup_path = ctx.get('master_lookup')
    if master_lookup_path is None:
        master_lookup_path = path.replace('ballot_image', 'master_lookup') \
                                 .replace('BallotImage', 'MasterLookup') \
                                 .replace('ballotimage', 'masterlookup') \
                                 .replace('Ballot Image', 'Master Lookup')
                    
    precinct_map = {}
    with open(master_lookup_path) as f:
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
    with open(master_lookup_path) as f:
        for i in f:
            mapping = i[:10].strip()
            key = i[10:17].strip()
            value = i[17:67].strip()
            master_lookup[mapping][key] = value
    return dict(master_lookup)

def sf_name_map(ctx):
    return dict((k,{'WRITEIN': WRITEIN}.get(v.upper().replace('-',''),v)) 
                for k,v in parse_master_lookup(ctx)['Candidate'].items())

def chp_names(ctx):
    mapping = {}
    with open(glob(ctx['chp'])[0]) as f:
        for i in f:
            split = i.split()
            if len(split) >= 3 and split[0] == '.CANDIDATE':
                mapping[split[1].strip(',')] = i.split('"')[1].split('"')[0]
    return mapping

def burlington(ctx):
    path = ctx['path']
    ballots = []
    with open(path, "r") as f:
        for line in f:
            ballots.append([OVERVOTE if '=' in i else i for i in line.split()[3:]])
    maxlen = max(map(len,ballots))
    for b in ballots:
        b.extend([UNDERVOTE]*(maxlen-len(b)))
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
        with open(path, 'r') as f:
            for i in f:
                if any(map(str.isalnum,i)) and i.strip()[0] != '#':
                    b = []
                    s = i.split()
                    choices = [] if len(s) == 1 else s[1].split(',')
                    for choice in filter(None,choices):
                        can, rank = choice.split(']')[0].split('[')
                        b.extend([UNDERVOTE]*(int(rank)-len(b)-1))
                        b.append(OVERVOTE if '=' in choice else name_map[can])
                    ballots.append(b)
                 
    maxlen = max(map(len,ballots))
    for b in ballots:
        b.extend([UNDERVOTE]*(maxlen-len(b)))
    return ballots
        

def sf(contest_id, ctx):
    path = ctx['path']
    precinct_map = sf_precinct_map(ctx)
    name_map = sf_name_map(ctx)
    ballots = []
    with open(path, "r") as f:
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
            undervote = UNDERVOTE if int(line[44]) else 0
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
    with open(path, "r") as f:
        b = UserList([])
        voter_id = None
        for line in f:
            if line[7:16] != voter_id:
                ballots.append(b)
                voter_id = line[7:16]
                b = UserList([])
            precinct_id = line[26:33]
            candidate_id = int(line[36:43]) and name_map[line[36:43]]
            undervote = UNDERVOTE if int(line[44]) else 0
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
    with open(ctx['candidate_map']) as f:
        for i in f:
            line = [j.strip() for j in i.split(':')]
            if line and line[0] == 'Candidate':
                candidate_map[line[1]] = line[2]
    candidate_map['--'] = UNDERVOTE
    candidate_map['++'] = OVERVOTE
    ballots = []
    with open(path, "r") as f:
        line = f.readline()
        while line:
            ballots.append([candidate_map[i] for i in line.split()[-1].split('>')])
            line = f.readline()
    return ballots
    
def minneapolis(ctx):
    choice_map = {}
    default = None
    if ctx['date'] == '2009':
        with open('/'.join(ctx['path'].split('/')[:-1]+['convert.csv'])) as f:
            for i in f:
                split = i.strip().split('\t')
                if len(split) >= 3:
                    choice_map[split[2]] = split[1]
        choice_map['XXX'] = UNDERVOTE
        default = WRITEIN
    else:
        choice_map = {
            'UWI': WRITEIN,
            'undervote': UNDERVOTE,
            'overvote': OVERVOTE
        }
    path = ctx['path']
    ballots = []
    with open(path, "r") as f:
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
    with open(path, "r") as f:
        f.readline()
        for line in csv.reader(f):
            choices = [{'undervote': UNDERVOTE,
                        'overvote': OVERVOTE,
                        'Write-in': WRITEIN}.get(i,i)
                         for i in line[3:3+n]]
            if '' not in choices and choices:
                ballots.append(choices)
    return ballots

def santafe(column_id, contest_id, ctx):
    path = ctx['path']
    candidate_map = {}
    with open(ctx['path'].replace('CvrExport','CandidateManifest')) as f:
        for i in f:
            row = i.split(',')
            if row:
                candidate_map[row[1]] = row[0]
    ballots = []
    ballot_length = 0
    with open(path, "r") as f:
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
                        choices.append(UNDERVOTE)
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
    with open(path, "r") as f:
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
                        choices.append(UNDERVOTE)
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
    with open(path, 'r') as f:
        for i in f:
            if sep is None:
                s = [rc.split('-') for rc in i.split()[1:] if '-' in i.strip()]
            else:
                s = [rc.strip().split('-') for rc in i.split(sep)[1:] if '-' in i]
            if s == [] or len(s[0]) != 2:
                continue
            raw = [c for r, c in s if r in contest_ids]
            if raw:
                ballots.append([{over: OVERVOTE, under: UNDERVOTE}.get(i,i)
                                for i in raw])
    return ballots

def sf2019(ctx):
    with open(ctx['path'] + '/ContestManifest.json') as f:
        for i in json.load(f)['List']:
            if i['Description'] == ctx['office'].upper():
                contest_id = i['Id']
                ranks = i['NumOfRanks']
    candidates = {}
    with open(ctx['path'] + '/CandidateManifest.json') as f:
        for i in json.load(f)['List']:
            if i['ContestId'] == contest_id:
                candidates[i['Id']] = i['Description']
    precincts = {}
    with open(ctx['path'] + '/PrecinctPortionManifest.json') as f:
        for i in json.load(f)['List']:
            precincts[i['Id']] = i['Description'].split()[1]
    ballots = []
    with open(ctx['path'] + '/CvrExport.json') as f:
        for contests in json.load(f)['Sessions']:
            if contests['Original']['IsCurrent']:
                current_contests = contests['Original']
            else:
                current_contests = contests['Modified'] 
            precinct = precincts[current_contests['PrecinctPortionId']]
            for contest in current_contests['Contests']:
                if contest['Id'] == contest_id:
                    ballot = UserList([UNDERVOTE] * ranks)
                    for mark in contest['Marks']:
                        candidate = candidates[mark['CandidateId']]
                        if candidate == 'Write-in':
                            candidate = WRITEIN
                        rank = mark['Rank']-1
                        if mark['IsAmbiguous']:
                            pass 
                        elif ballot[rank] == OVERVOTE:
                            pass
                        elif ballot[rank] == UNDERVOTE:
                            ballot[rank] = candidate
                        elif ballot[rank] != candidate:
                            ballot[rank] = OVERVOTE
                    ballot.precinct = precinct
                    ballots.append(ballot)
                        
    return ballots
            
def utah(ctx):
    ballots = []
    with open(ctx['path']) as f:
        for b in f:
            ballots.append(
                [{'overvote':OVERVOTE, 'undervote':UNDERVOTE, '': UNDERVOTE}.get(i,i) 
                for i in b.split(',')[2:]]
            )
    return ballots
    
        


