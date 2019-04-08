from functools import lru_cache, wraps
from pathlib import Path
import re
import csv
from collections import Counter
from argparse import ArgumentParser
from pprint import pprint
from fractions import Fraction
from parsers import *

CACHE = lru_cache(maxsize=256)
UNDERVOTE = -1
OVERVOTE = -2
PATH = None
WINNER = None
FIRST_ROUND_WINNER = None
FINALISTS = None
CANDIDATES = set()

def remove(x,l): 
    return [i for i in l if i != x]

def keep(x,l): 
    return [i for i in l if i in x]

def clean(ballots):
    ballots = [(b[:b.index(OVERVOTE)] if OVERVOTE in b else b) for b in ballots]
    return [remove(UNDERVOTE, b) for b in ballots]

def stv(number, ballots):
    ballots = [(b,1) for b in ballots]
    winners = []
    while len(winners) != number:
        names, tallies = zip(*sum((Counter({c[0]:v}) for c,v in ballots if c), Counter()).most_common())
        threshold = sum(tallies)/(number+1)/tallies[0]
        if threshold < 1:
            winners.append(names[0])
            ballots = [(keep(names[1:], c), v*(c[0:1]!=names[0:1] or 1-threshold))
                       for c,v in ballots]
        else:
            ballots = [(keep(names[:-1], c), v) for c,v in ballots]
    return winners


def rcv_stack(ballots):
    stack = [ballots]
    results = []
    while stack:
        ballots = stack.pop()
        finalists, tallies = zip(*Counter(b[0] for b in ballots if b).most_common())
        if tallies[0]*2 > sum(tallies):
            results.append((finalists, tallies))
        else:
            losers = finalists[tallies.index(min(tallies)):]
            for loser in losers:
                stack.append([keep(set(finalists)-set([loser]), b) for b in ballots])
            if len(losers) > 1:
                stack.append([keep(set(finalists)-set(losers), b) for b in ballots])
    return results
        

def rcv(ballots):
    ballot_count = len(ballots)
    while True:
        finalists, tallies = zip(*Counter(b[0] for b in ballots if b).most_common())
        global FIRST_ROUND_WINNER
        FIRST_ROUND_WINNER = finalists[0]
        print('finalists', finalists)
        print('tallies', tallies)
        if tallies[0]*2 > sum(tallies):
            global WINNER
            WINNER = finalists[0]
            global FINALISTS 
            FINALISTS = finalists
            return
        ballots = [keep(finalists[:-1], b) for b in ballots]
        ballots = [b for b in ballots if b != []]

def first_round(ballot):
    for choice in ballot:
        if choice != UNDERVOTE:
            return choice
    return UNDERVOTE

def total(ballot):
    return True

def undervote(ballot):
    return first_round(ballot) == UNDERVOTE

def voted(ballot):
    return not undervote(ballot)

@CACHE
def count_duplicates(ballot):
    duplicate_count = 0
    choices = set(ballot)
    for choice in choices:
        if choice == UNDERVOTE or choice == OVERVOTE:
            continue
        count = ballot.count(choice)
        if count > duplicate_count:
            duplicate_count = count
    return duplicate_count

@CACHE
def duplicate(ballot):
    return count_duplicates(ballot) > 1

def two_repeated(ballot):
    return count_duplicates(ballot) == 2

def three_repeated(ballot):
    return count_duplicates(ballot) == 3

@CACHE
def overvote(ballot):
    return OVERVOTE in ballot

def overvote_then_choice(ballot):
    if OVERVOTE in ballot:
        return len(get_effective_choices(ballot[ballot.index(OVERVOTE)+1:])) > 1
    return False

def num_overvote(ballot):
    return [('num_overvote', ballot.count(OVERVOTE))]

def num_undervote(ballot):
    return [('num_undervote', ballot.count(UNDERVOTE))]

@CACHE
def includes_undervote(ballot):
    return UNDERVOTE in ballot

def unders(ballot):
    return [('unders', tuple(i for i,v in enumerate(ballot) if v == UNDERVOTE))]

@CACHE
def skipped(ballot):
    seen_undervote = False
    for choice in ballot:
        if choice == UNDERVOTE:
            seen_undervote = True
            continue
        if seen_undervote:
            return True
    return False

@CACHE
def irregular(ballot):
    return any(f(ballot) for f in [duplicate, overvote, skipped])

def first_round_overvote(ballot):
    return first_round(ballot) == OVERVOTE

def first_round_continuing(ballot):
    return not first_round_overvote(ballot) and voted(ballot)

@CACHE
def get_effective_choices(ballot):
    effective_choices = []
    for choice in ballot:
        if choice == UNDERVOTE or choice in effective_choices:
            continue
        if choice == OVERVOTE:
            break
        effective_choices.append(choice)
    return tuple(effective_choices)

@CACHE
def fully_ranked(ballot):
    return len(get_effective_choices(ballot)) == len(ballot)

@CACHE
    return len(get_effective_choices(ballot)) == 2

@CACHE
def ranked_multiple(ballot):
    return len(get_effective_choices(ballot)) > 1

@CACHE
def effective_ballot_length(ballot):
    return [('effective_ballot_length', len(get_effective_choices(ballot)))]

@CACHE
def ballot_position(ballot):
    return [('ballot_position', candidate, position)
            for position, candidate in enumerate(get_effective_choices(ballot))]

@CACHE
def exhausted(ballot):
    return not set(FINALISTS) & set(get_effective_choices(ballot))

@CACHE
def involuntarily_exhausted(ballot):
    return fully_ranked(ballot) and exhausted(ballot)

@CACHE
def voluntarily_exhausted(ballot):
    return exhausted(ballot) and not involuntarily_exhausted(ballot)

@CACHE
def exhausted_by_overvote(ballot):
    if exhausted(ballot) and overvote(ballot):
        return True

@CACHE
def exhausted_not_by_overvote(ballot):
    if exhausted(ballot) and not overvote(ballot):
        return True

@CACHE
def ranked_winner(ballot):
    if WINNER in get_effective_choices(ballot):
        return True

@CACHE
def ranked_finalist(ballot):
    if set(get_effective_choices(ballot)) & set(FINALISTS):
        return True

@CACHE
def swept(ballot):
    fc = first_round(ballot)
    for choice in ballot:
        if choice != fc:
            return [('swept', fc, False)]
    return [('swept', fc, True)]

@CACHE
def final_round_winner_total(ballot):
    for choice in ballot:
        if choice == OVERVOTE:
            break
        if choice == WINNER:
            return True
        if choice in FINALISTS:
            return False
    return False

def before(x, y, l):
    for i in l:
        if i == x:
            return 1
        if i == y:
            return -1
    return 0

@CACHE
def condorcet(ballot):
    return {('condorcet_net', non_winner): before(WINNER, non_winner, ballot)
                for non_winner in (set(CANDIDATES) - set([WINNER]))}

### Condorcet has many types (12):
### strongest:  [w,l] - [w] - [l,w] - [l] - []
### weakest:    [w,l] + [w] - [l,w] + [l] + []
def all_condorcet(ballot):
    results = []
    ec = get_effective_choices(ballot)
    for i in range(len(ec)-1):
        for j in range(i+1, len(ec)):
            pair = tuple(sorted([ec[i],ec[j]]))
            results.append(('pairs_total', pair, 1))
            results.append(('pairs_net', pair, 1 if pair[0] == ec[i] else -1))
    for not_chosen in set(CANDIDATES) - set(ec):
        for chosen in ec:
            pair = tuple(sorted([chosen, not_chosen]))
            results.append(('implied_pairs_total', pair, 1))
            results.append(('implied_pairs_net', pair, 1 if pair[0] == chosen else -1))
    return results

def combinations(ballot):
    return [('combinations', tuple(sorted(get_effective_choices(ballot))))]

def orderings(ballot):
    return [('orderings', get_effective_choices(ballot))]

def collect_ballots(fmt):
    return {'burlington': burlington,
            'prm': prm,
            'minneapolis': minneapolis, 
            'maine5': (lambda x: maine(5,x)),
            'maine7': (lambda x: maine(7,x)),
            'maine8': (lambda x: maine(8,x)),
            'santafe1': (lambda x: santafe(0,1,x)),
            'santafe2': (lambda x: santafe(1,2,x)),
            'santafe3': (lambda x: santafe(1,3,x)),
            'santafe4': (lambda x: santafe(1,4,x)),
            'santafe5': (lambda x: santafe(1,5,x)),
            'sf2005ar' : (lambda x: sf2005(['0100', '0101', '0102'],'05','06', x)),
            'sf2005ca' : (lambda x: sf2005(['0205', '0206', '0207'],'03','04', x)),
            'sf2007s': (lambda x: sf2005(['0205', '0206', '0207'],'03','04', x)),
            'sf2008bds7': (lambda x: sf('0000008', x)),
            'berk2010ccd7': (lambda x: sf('0000039', x)),
            'noid': sfnoid,
            }[fmt]

FUNCTIONS = [
    total, undervote, overvote, first_round_overvote, exhausted_by_overvote,
    fully_ranked, ranked2, ranked_winner, duplicate, three_repeated,
    two_repeated, skipped, irregular, exhausted, exhausted_not_by_overvote, involuntarily_exhausted,
    voluntarily_exhausted, condorcet, effective_ballot_length, includes_undervote, unders, num_overvote, num_undervote]

ORDER= [
    'winner', 'path', 'undervote', 'overvote', 'first_round_overvote', 'exhausted_by_overvote',
    'fully_ranked', 'ranked2', 'ranked_winner', 'duplicate', 'three_repeated',
    'two_repeated', 'skipped', 'irregular', 'exhausted', 'exhausted_not_by_overvote', 'involuntarily_exhausted',
    'voluntarily_exhausted','condorcet_winner', 'includes_undervote', 'unders', 'num_overvote', 'num_undervote']

#FUNCTIONS = [fully_ranked, ranked2, ranked_multiple]
#ORDER = ['path', 'fully_ranked', 'ranked2', 'ranked_multiple']

def stats(fmt, path, functions):
    ballots = collect_ballots(fmt)(path)
    clean_ballots = clean(ballots)
    for b in clean_ballots:
        CANDIDATES.update(b)
    rcv(clean_ballots)
    aggs = Counter()
    for b in ballots:
        for f in functions:
            if f(b) == True:
                aggs.update([f.__name__])
            elif f(b):
                aggs.update(f(b))
    d = dict(aggs)
    d['condorcet_winner'] = len([v for k,v in aggs.items() if k[0] == 'condorcet_net' and v>0])>0
    d['winner'] = WINNER
    d['finalists'] = FINALISTS
    d['candidates'] = sorted(CANDIDATES)
    d['path'] = path.split('/')[-1].split('.')[0]
    return d


#FUNCTIONS = [total, ranked_multiple, fully_ranked, effective_ballot_length]
#ORDER = ['path', 'total', 'ranked_multiple', 'fully_ranked', 'effective_ballot_length']

def main():
    p = ArgumentParser()
    p.add_argument('-f', '--fmt')
    p.add_argument('-p', '--path')
    p.add_argument('-m', '--metric')
    a = p.parse_args()
    s = stats(a.fmt, a.path, FUNCTIONS)
    pprint(s)
    print(' \t'.join([str(s.get(i,0)) for i in ORDER]))
   
if __name__== '__main__':
    main()
 
