from functools import wraps
from collections import Counter
from argparse import ArgumentParser
from pprint import pprint
from fractions import Fraction
import manifest
from math import floor
from collections import defaultdict
from contextlib import suppress
from glob import glob

from hashlib import sha256
from inspect import getsource
import pickle
from re import sub

def stv(ctx):
    rounds = []
    bs = [(b,Fraction(1,1)) for b in cleaned(ctx) if b]
    threshold = int(len(bs)/(number(ctx)+1)) + 1 
    winners = []
    while len(winners) != number(ctx):
        totals = defaultdict(int)
        for c,v in bs:
            totals[c[0]] += v
        ordered = sorted(totals.items(), key=lambda x:-x[1])
        rounds.append(ordered)
        names, tallies = zip(*ordered)
        if len(names) + len(winners) == number(ctx):
            winners.extend(names)
            break
        if threshold < tallies[0]:
            winners.append(names[0])
            bs = ((keep(names[1:], c), 
                    v*(names[0] != c[0] or (tallies[0]-threshold)/tallies[0]))
                   for c,v in bs)
        else:
            bs = ((keep(names[:-1], c), v) for c,v in bs)
        bs = [b for b in bs if b[0]]
    return winners, rounds

def rcv_stack(ballots):
    stack = [ballots]
    results = []
    while stack:
        ballots = stack.pop()
        finalists, tallies = map(list, zip(*Counter(b[0] for b in ballots if b).most_common()))
        if tallies[0]*2 > sum(tallies):
            results.append((finalists, tallies))
        else:
            losers = finalists[tallies.index(min(tallies)):]
            for loser in losers:
                stack.append([keep(set(finalists)-set([loser]), b) for b in ballots])
            if len(losers) > 1:
                stack.append([keep(set(finalists)-set(losers), b) for b in ballots])
    return results

UNDERVOTE = -1
OVERVOTE = -2
WRITEIN = -3

def save(f):
    @wraps(f)
    def fun(ctx):
        if f.__name__ in ctx:
            return ctx[f.__name__]
        h = hasher(ctx).copy()
        h.update(bytes(getsource(f), 'utf-8'))
        file_name = '.pickled/.{}.pickle'.format(h.hexdigest())
        with suppress(IOError, EOFError), open(file_name, 'rb') as file_object:
            return ctx.setdefault(f.__name__, pickle.load(file_object))
        with open(file_name, 'wb') as file_object:
            pickle.dump(ctx.setdefault(f.__name__, f(ctx)), file_object)
        return ctx[f.__name__]
    return fun

def tmpsave(f):
    @wraps(f)
    def fun(ctx):
        if f.__name__ in ctx:
            return ctx[f.__name__]
        return ctx.setdefault(f.__name__, f(ctx))
    return fun

def remove(x,l): 
    return [i for i in l if i != x]

def keep(x,l): 
    return [i for i in l if i in x]

@save #d
def cleaned(ctx):
    new = []
    for b in ballots(ctx):
        result = []
        for a,b in zip(b,b[1:]+[None]):
            if break_on_repeated_undervotes(ctx) and {a,b} == {UNDERVOTE}:
                break
            if break_on_overvote(ctx) and a == OVERVOTE:
                break
            if a not in (result + [OVERVOTE,UNDERVOTE]):
                result.append(a)
        new.append(result)
    return new

@save #d
def minneapolis_undervote(ctx):
    return effective_ballot_length(ctx).get(0,0)

@save #d
def minneapolis_total(ctx):
    return total(ctx) - minneapolis_undervote(ctx)  

@save
def naive_tally(ctx):
    """ Sometimes reported if only one round, only nominal 1st place rankings count"""
    return Counter(b[0] if b else None for b in ballots(ctx))

@save #d
def winner_ranking(ctx):
    return Counter(b.index(winner(ctx))+1 if winner(ctx) in b else None
                    for b in cleaned(ctx))

@save #d
def winner_in_top_3(ctx):
    return sum(v for k,v in winner_ranking(ctx).items() if k is not None and k<4)

@save #d
def consensus(ctx):
    return winner_in_top_3(ctx) / (total(ctx) - undervote(ctx)) 

       
@save #d 
def rcv(ctx):
    rounds = []
    ballots = remove([], (remove(UNDERVOTE, b) for b in cleaned(ctx)))
    while True:
        rounds.append(list(zip(*Counter(b[0] for b in ballots).most_common())))
        finalists, tallies = rounds[-1] 
        if tallies[0]*2 > sum(tallies):
            return rounds
        ballots = remove([], (keep(finalists[:-1], b) for b in ballots))

@save #d
def winner(ctx):
    return rcv(ctx)[-1][0][0]

@save #d
def finalists(ctx):
    return rcv(ctx)[-1][0]

@save #should be dependant
def first_round(ctx):
    return [next((c for c in b if c != UNDERVOTE), UNDERVOTE)
            for b in ballots(ctx)]

@save #should be dependant
def undervote(ctx):
    return sum(c == UNDERVOTE for c in first_round(ctx))


@save #d
def ranked2(ctx):
    return sum(len(b) == 2 for b in cleaned(ctx))

@save #d
def ranked_multiple(ctx): 
    return sum(len(b) > 1 for b in cleaned(ctx))

@save #d
def effective_ballot_length(ctx):
    return Counter(len(b) for b in cleaned(ctx))

@save #d
def exhausted(ctx):
    return [not set(finalists(ctx)) & set(b) for b in cleaned(ctx)]

@save #d
def total_exhausted(ctx):
    return sum(exhausted(ctx))

@save #d fixme
def involuntarily_exhausted(ctx):
    return [a and b for a,b in zip(fully_ranked(ctx), exhausted(ctx))]

@save #d
def total_involuntarily_exhausted(ctx):
    return sum(involuntarily_exhausted(ctx))

@save #d
def voluntarily_exhausted(ctx):
    return [a and not b 
            for a,b in zip(exhausted(ctx),involuntarily_exhausted(ctx))]

@save #d
def total_voluntarily_exhausted(ctx):
    return sum(voluntarily_exhausted(ctx))

@save #d
def exhausted_by_repeated_choices(ctx):
    return total_exhausted(ctx) - sum([exhausted_by_undervote(ctx), 
                                        total_exhausted_by_overvote(ctx),
                                        total_involuntarily_exhausted(ctx)])

@save #d
def exhausted_by_undervote(ctx):
    if break_on_repeated_undervotes(ctx):
        return sum(all([ex, not ex_over, has_under]) for ex,ex_over,has_under in 
                  zip(exhausted(ctx),exhausted_by_overvote(ctx), has_undervote(ctx)))
    return 0

@save #d
def exhausted_by_overvote(ctx):
    if break_on_repeated_undervotes(ctx):
        return [ex and over<under for ex,over,under in 
                    zip(exhausted(ctx),overvote_ind(ctx), repeated_undervote_ind(ctx))]
    return [ex and over for ex,over in zip(exhausted(ctx),overvote(ctx))]

@save #d
def total_exhausted_by_overvote(ctx):
    return sum(exhausted_by_overvote(ctx))

@save #d
def total_exhausted_not_by_overvote(ctx):
    return sum(ex and not ov 
                for ex,ov in zip(exhausted(ctx), exhausted_by_overvote(ctx)))

@save #d
def ranked_winner(ctx):
    return sum(winner(ctx) in b for b in cleaned(ctx))

def before(x, y, l):
    for i in l:
        if i == x:
            return 1
        if i == y:
            return -1
    return 0

@save #d
def losers(ctx):
    return set(finalists(ctx)) - {winner(ctx)}

@save #d
def condorcet(ctx):
    net = Counter()
    for b in ballots(ctx):
        for loser in losers(ctx):
            net.update({loser: before(winner(ctx), loser, b)})
    return net.most_common()[-1][1] > 0
        
@save #d
def combinations(ctx):
    return Counter(tuple(sorted(b) for b in cleaned(ctx)))

@save #d
def orderings(ctx):
    return Counter(map(tuple,cleaned(ctx)))

@save
def repeated_undervote_ind(ctx):
    rs = []
    for b in ballots(ctx):
        rs.append(float('inf'))
        with suppress(ValueError):
            rs[-1] = list(zip(b, b[1:])).index((UNDERVOTE,)*2)
    return rs

@save
def overvote_ind(ctx):
    return [b.index(OVERVOTE) if OVERVOTE in b else float('inf')
            for b in ballots(ctx)]

@save
def has_undervote(ctx):
    return [UNDERVOTE in b #[:len(b)-write_ins(ctx)+b.count(WRITEIN)] 
            for b in ballots(ctx)]

@save
def max_repeats(ctx):
    return [max(0,0,*map(b.count,set(b)-{UNDERVOTE,OVERVOTE}))
            for b in ballots(ctx)]

@save
def count_duplicates(ctx):
    return Counter(max_repeats(ctx))

@save
def duplicates(ctx):
    return [v > 1 for v in max_repeats(ctx)]

@save
def two_repeated(ctx):
    return count_duplicates(ctx)[2]

@save
def three_repeated(ctx):
    return count_duplicates(ctx)[3]

@save
def overvote(ctx):
    return [OVERVOTE in b for b in ballots(ctx)]

@save
def total_overvote(ctx):
    return sum(overvote(ctx))

@save
def skipped(ctx):
    return [any({UNDERVOTE} & {x} - {y} for x,y in zip(b, b[1:]))
            for b in ballots(ctx)]

@save
def total_skipped(ctx):
    return sum(skipped(ctx))

@save
def irregular(ctx):
    return sum(map(any, zip(duplicates(ctx), overvote(ctx), skipped(ctx)))) 

@save
def first_round_overvote(ctx):
    return sum(c == OVERVOTE for c in first_round(ctx))

@save
def fully_ranked(ctx):
    return [len(a) <= len(b)+write_ins(ctx)
            for a,b in zip(ballots(ctx), cleaned(ctx))]

@save
def total_fully_ranked(ctx):
    return sum(fully_ranked(ctx))

@save
def candidates(ctx):
    cans = set()
    for b in ballots(ctx):
        cans.update(b) 
    return cans - {OVERVOTE, UNDERVOTE}

@save
def total(ctx):
    return len(ballots(ctx))

@save
def ballots(ctx):
    return ctx['parser'](ctx['path'])

@tmpsave
def break_on_repeated_undervotes(ctx):
    return False

@tmpsave
def break_on_overvote(ctx):
    return True

@tmpsave
def write_ins(ctx):
    return 0

@tmpsave
def number(ctx):
    return 1

@save
def ballot_length(ctx):
    return len(ballots(ctx)[0])

@save 
def number_of_candidates(ctx):
    return len(candidates(ctx)) 

@tmpsave
def hasher(ctx):
    h = sha256(bytes(sub(r'0x[0-9a-f]+','',str(ctx)),'utf-8')) #stripping pointer addrs
    for path in glob(ctx['path']):
        with open(path, 'rb') as f:
            for i in f:
                h.update(i)
    return h

FUNCTIONS = [
    total, undervote, total_overvote, first_round_overvote, 
    total_exhausted_by_overvote, total_fully_ranked, ranked2, ranked_winner, 
    two_repeated, three_repeated, total_skipped, irregular, total_exhausted, 
    total_exhausted_not_by_overvote, total_involuntarily_exhausted, 
    total_voluntarily_exhausted, condorcet, effective_ballot_length,rcv,
    finalists,winner,exhausted_by_undervote, exhausted_by_repeated_choices,
    minneapolis_undervote, minneapolis_total, naive_tally, candidates]

def calc(competition, functions):
    ctx = dict(manifest.competitions[competition])
    hasher(ctx) 
    return {f.__name__: f(ctx) for f in functions}

def main():
    p = ArgumentParser()
    p.add_argument('-e', '--elections', nargs='*')
    p.add_argument('-s', '--stats', nargs='*')
    p.add_argument('-ef', '--election_file', nargs='?')
    p.add_argument('-es', '--stats_file', nargs='?')
    a = p.parse_args()
    possible_elections = list(a.elections or [])
    if a.election_file:
        with open(a.election_file) as f:
            possible_elections.extend([i.strip() for i in f])
    elections = [(election, manifest.competitions[election]) for election in possible_elections] or manifest.competitions.items()
    possible_stats = list(a.stats or [])
    if a.stats_file:
        with open(a.stats_file) as f:
            possible_stats.extend([i.strip() for i in f])
    stats = [globals()[i] for i in possible_stats] or FUNCTIONS
    pprint(stats)
    print('\t'.join(['name'] + possible_stats))
    for k,v in elections:
        result = calc(k, stats)
        print('\t'.join([k] + [str(result[s.__name__]) for s in stats]))
    
if __name__== '__main__':
    main()
 
