from pathlib import Path
from glob import glob
from collections import UserList
import os
import csv

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
                        b.append(OVERVOTE if '=' in choice else can)
                    ballots.append(b)
                 
    maxlen = max(map(len,ballots))
    for b in ballots:
        b.extend([UNDERVOTE]*(maxlen-len(b)))
    return ballots
        

def sf(contest_id, ctx):
    path = ctx['path']
    precinct_map = sf_precinct_map(ctx)
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
            candidate_id = int(line[36:43])
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
            candidate_id = int(line[36:43])
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
    ballots = []
    with open(path, "r") as f:
        line = f.readline()
        while line:
            ballots.append([{'--': UNDERVOTE, '++': OVERVOTE}.get(i,i) 
                                    for i in line.split()[-1].split('>')])
            line = f.readline()
    return ballots
    
def minneapolis(ctx):
    path = ctx['path']
    ballots = []
    with open(path, "r") as f:
        f.readline()
        for line in csv.reader(f):
            choices = [{'undervote': UNDERVOTE,
                         'XXX': UNDERVOTE,
                         'overvote': OVERVOTE}.get(i,i)
                          for i in line[1:-1]]
            if choices != ['','','']:
                ballots.extend([choices] * int(float(line[-1])))
    return ballots

def maine(n, ctx):
    path = ctx['path']
    lines = 0
    ballots = []
    with open(path, "r") as f:
        f.readline()
        for line in csv.reader(f):
            lines += 1
            choices = [{'undervote': UNDERVOTE,
                        'overvote': OVERVOTE,
                        'Write-in': WRITEIN}.get(i,i)
                         for i in line[3:3+n]]
            if '' not in choices and choices:
                ballots.append(choices)
    return ballots

def santafe(column_id, contest_id, ctx):
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
                        choices.append(line[next(candidates)])
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


