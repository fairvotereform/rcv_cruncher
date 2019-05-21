from functools import wraps
from itertools import product, chain, combinations, count
from collections import Counter
from argparse import ArgumentParser
from pprint import pprint
from copy import deepcopy
import json
import csv

#from fractions import Fraction
from gmpy2 import mpq as Fraction

import manifest
from math import floor
from collections import defaultdict
from contextlib import suppress
from glob import glob
from fnmatch import fnmatch
import readline

from hashlib import sha256, md5
from inspect import getsource
import pickle
from re import sub

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

def rcv_ballots(clean_ballots):
    rounds = []
    ballots = remove([],deepcopy(clean_ballots))
    while True:
        rounds.append(list(zip(*Counter(b[0] for b in ballots).most_common())))
        finalists, tallies = rounds[-1] 
        if tallies[0]*2 > sum(tallies):
            return rounds
        ballots = remove([], (keep(finalists[:-1], b) for b in ballots))

@save
def seq_stv(ctx):
    ballots = deepcopy(cleaned(ctx))
    winners = []
    for i in range(number(ctx)):
        winners.append(rcv_ballots(ballots)[-1][0][0])
        ballots = remove([], (remove(winners[-1], b) for b in ballots))
    return winners

@save
def rank_and_add_borda(ctx):
    """https://voterschoose.info/wp-content/uploads/2019/04/Tustin-White-Paper.pdf"""
    c = Counter()
    for b in cleaned(ctx):
        c.update({v:1/(i+1) for i,v in enumerate(b)})
    return [i for i,_ in c.most_common()[:number(ctx)]]

@save     
def bottom_up_stv(ctx):
    ballots = deepcopy(cleaned(ctx))
    rounds = []
    while True:
        rounds.append(list(zip(*Counter(b[0] for b in ballots).most_common())))
        finalists,_ = rounds[-1]
        if len(finalists) == number(ctx):
            return finalists
        ballots = remove([], (keep(finalists[:-1], b) for b in ballots))

@save
def stv(ctx):
    rounds = []
    bs = [(b,Fraction(1)) for b in cleaned(ctx) if b]
#    bs = [(b,1) for b in cleaned(ctx) if b]
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
    return winners

@save
def in_common(ctx):
    return len(set(stv(ctx)) & set(seq_stv(ctx)))

@save 
def not_in_common(ctx):
    return len(set(stv(ctx)) ^ set(seq_stv(ctx)))//2

@save
def only_seq(ctx):
    return [name_map(ctx)(i) for i in set(seq_stv(ctx)) - set(stv(ctx))]

@save
def only_reg(ctx):
    return [name_map(ctx)(i) for i in set(stv(ctx)) - set(seq_stv(ctx))]

def name_map(ctx):
    mapping = {}
    with suppress(KeyError), open(glob(ctx['chp'])[0]) as f:
        for i in f:
            parts = i.split(' ')
            if parts[0] == '.CANDIDATE':
                mapping[parts[1].strip(',')] = ' '.join(parts[2:]).replace('"','').replace('\n', '')
    if mapping:
        return lambda x: mapping[x]
    return lambda x: x

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
            if a not in [*result,OVERVOTE,UNDERVOTE]:
                result.append(a)
        new.append(result)
    return new

@save #d
def minneapolis_undervote(ctx):
    """Ballots containing only"""
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

@save
def winners_first_round_share(ctx):
    return rcv(ctx)[0][1][0] / (total(ctx) - undervote(ctx))

@save
def winners_final_round_share(ctx):
    return rcv(ctx)[-1][1][0] / (total(ctx) - undervote(ctx))

def foop(ctxs):
    for ctx in ctxs:
        ballots(ctx)
       
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


### TODO: exhausted should not include straight undervotes nor
### per Drew
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
def validly_ranked_winner(ctx):
    return sum(winner(ctx) in b for b in cleaned(ctx))

@save
def ranked_winner(ctx):
    return sum(winner(ctx) in b for b in ballots(ctx))

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
    if not net: #Uncontested Race -> net == {}
        return True
    return net.most_common()[-1][1] > 0
        
@save #d
def candidate_combinations(ctx):
    return Counter(tuple(sorted(b)) for b in cleaned(ctx))

@save #d
def orderings(ctx):
    return Counter(map(tuple,cleaned(ctx))).most_common()

@save
def top2(ctx):
    return Counter(tuple(i[:2]) for i in cleaned(ctx)).most_common()

@save
def next_choice(ctx):
    c = Counter()
    for b in cleaned(ctx):
        c.update(zip([None, *b], [*b, None]))
    return c.most_common()

def ordered_choices(ctx):
    c = Counter()
    for b in cleaned(ctx):
        c.update(zip([None, *b], [*b, None], count()))
    return c

def sankey_ordered_choices(ctx):
    sources = {(str(a),i) for a,_,i in ordered_choices(ctx)}
    targets = {(str(b),i+1) for _,b,i in ordered_choices(ctx) if b is not None}
    nodes = sorted(sources | targets)
    node_map = [{"node": i, "name": k[0]} for i,k in enumerate(nodes)]
    link_map = [{"source": nodes.index((str(s),i)), "target": nodes.index((str(t),i+1)),"value": v}
                for (s,t,i),v in ordered_choices(ctx).items() if t is not None]
    with open('sankey/sankey-formatted.json', 'w') as f:
        json.dump({"nodes": node_map, "links": link_map}, f)
    
def sankey(ctx):
    for (i, (a,b)), v in ordered_choices(ctx):
        if None != b:
            print([str(a) + '_' + str(i), str(b) + '_' + str(i+1), v],',')
    return []

def sankey_next_choice(ctx):
    for (a,b), v in next_choice(ctx):
        print([str(a)+'_a', str(b)+'_b', v],',')
    return []

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
def any_repeat(ctx):
    return sum(v for k,v in count_duplicates(ctx).items() if k>1)

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
def effective_subsets(ctx):
    c = Counter()
    for b in cleaned(ctx):
        unranked = candidates(ctx) - set(b)
        c.update((b[0],u) for u in unranked)
        for i in range(2, len(b)+1):
            c.update(combinations(b,i))
            c.update((*b[:i],u) for u in unranked)
    return c 

@save
def preference_pairs(ctx):
    return [set(product(b, candidates(ctx) - set(b))) | set(combinations(b,2))
            for b in cleaned(ctx)]

@save
def preference_pairs_count(ctx):
    c = Counter()
    for i in preference_pairs(ctx):
        c.update(i)
    return c

@save
def all_pairs(ctx):
    return list(preference_pairs_count(ctx).keys())

@save
def voter_ids(ctx):
    return [getattr(b, 'voter_id', None) for b in ballots(ctx)]

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
    return {
        ('Cambridge', 'School Committee'): 6,
        ('Cambridge', 'City Council'): 9,
        ('Minneapolis', 'BOE'): 2,
        ('Minneapolis', 'Park At Large'): 3,
    }.get((ctx['place'],ctx['office']), 1)

@save
def ballot_length(ctx):
    return len(ballots(ctx)[0])

@save 
def number_of_candidates(ctx):
    return len(candidates(ctx))

@save 
def one_pct_cans(ctx):
    return sum(1 for i in rcv(ctx)[0][1] if i/sum(rcv(ctx)[0][1]) >= 0.01)

@tmpsave
def date(ctx):
    return '????'

@tmpsave
def place(ctx):
    return '????'

@tmpsave
def office(ctx):
    return '????'

@tmpsave
def hasher(ctx):
    h = md5(bytes(sub(r'0x[0-9a-f]+','',str(ctx)),'utf-8')) #stripping pointer addrs
    for path in glob(ctx['path']):
        with open(path, 'rb') as f:
            for i in f:
                h.update(i)
    return h

FUNCTIONS = [office, date, place,
    total, undervote, total_overvote, first_round_overvote, 
    total_exhausted_by_overvote, total_fully_ranked, ranked2, ranked_winner, 
    two_repeated, three_repeated, total_skipped, irregular, total_exhausted, 
    total_exhausted_not_by_overvote, total_involuntarily_exhausted, 
    total_voluntarily_exhausted, condorcet, effective_ballot_length,rcv,
    finalists,winner,exhausted_by_undervote, exhausted_by_repeated_choices,
    minneapolis_undervote, minneapolis_total, naive_tally, candidates, 
    count_duplicates, any_repeat, validly_ranked_winner]

def calc(competition, functions):
    ctx = dict(manifest.competitions[competition])
    hasher(ctx) 
    return {f.__name__: f(ctx) for f in functions}

def inputer():
    old = [False]
    def cmp(text, state):
        old[:] = old if state else [text] + self.old[:2]
        matches = dict(enumerate(w for w in FUNCTIONS if text in w))
        return len(set(old))<2 or matches.get(s)
    readline.set_completer(Comp())
    readline.parse_and_bind("tab: complete")

def main():
    p = ArgumentParser()
    p.add_argument('-e', '--elections', nargs='*', default=manifest.competitions.keys())
    p.add_argument('-s', '--stats', nargs='*', default=[i.__name__ for i in FUNCTIONS])
    p.add_argument('-j', '--json', action='store_true')
    a = p.parse_args()
    stats = [globals()[i] for i in a.stats]
    if a.json:
        for k in a.elections:
            pprint(calc(k, stats))
        return

    matched_elections = [] 
    for k,g in product(manifest.competitions.keys(), a.elections):
        if fnmatch(k,g):
            matched_elections.append(k)

    with open('results.csv', 'w') as f:
        w = csv.writer(f)
        w.writerow(['name'] + a.stats)
        for k in sorted(set(matched_elections)):
            result = calc(k, stats)
            w.writerow([k] + [result[s] for s in a.stats])

if __name__== '__main__':
    main()
 
