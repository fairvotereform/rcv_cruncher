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
from scipy.stats import linregress

import manifest
from math import floor, sqrt
from statistics import pvariance
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

def pick(f):
    @wraps(f)
    def fun(*args, **kwargs):
        h = md5(bytes(getsource(f),'utf-8')) 
        for arg in chain(args, kwargs):
            h.update(bytes(str(arg),'utf-8'))
        file_name = '.pickled/.{}.pickle'.format(h.hexdigest())
        with suppress(IOError, EOFError), open(file_name, 'rb') as file_object:
            return pickle.load(file_object)
        res = f(*args, **kwargs)
        with open(file_name, 'wb') as file_object:
            pickle.dump(res, file_object)
        return res
    return fun

def tmpsave(f):
    @wraps(f)
    def fun(ctx):
        if f.__name__ in ctx:
            return ctx[f.__name__]
        return ctx.setdefault(f.__name__, f(ctx))
    return fun

def ci(p, n):
    """adapted from stackoverflow.com/q/10029588/"""
    z = 1.96 
    z2 = z*z 
    v = z * sqrt((p*(1-p)+z2/(4*n))/n)
    return tuple([p, *[max(0, (p + z2/(2*n) + i) / (1+z2/n)) for i in [-v,v]]])

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
        c.update({v:1/i for i,v in enumerate(b,1)})
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
def margin(ctx):
    ballots = remove([], (remove(UNDERVOTE, b) for b in cleaned(ctx)))
    while True:
        finalists, tallies = zip(*Counter(b[0] for b in ballots).most_common())
        if len(tallies) == 1:
            return tallies[0]
        if len(tallies) == 2: 
            return tallies[0] - tallies[-1]
        ballots = remove([], (keep(finalists[:-1], b) for b in ballots))

def rcvreg(ballots):
    rounds = []
    while True:
        rounds.append(list(zip(*Counter(b[0] for b in ballots).most_common())))
        finalists, tallies = rounds[-1] 
        if tallies[0]*2 > sum(tallies):
            return rounds
        ballots = remove([], (keep(finalists[:-1], b) for b in ballots))

@save
def rounds(ctx):
    return len(rcv(ctx))

@save
def last5rcv(ctx):
    return rcv(ctx)[-5:]

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
    # return next(filter(None,map({x:1,y:-1}.get,l)),0)
    for i in l:
        if i == x:
            return 1
        if i == y:
            return -1
    return 0

@save #d
def losers(ctx):
    return set(candidates(ctx)) - {winner(ctx)}

@save #d
def condorcet(ctx):
    net = Counter()
    for b in ballots(ctx):
        for loser in losers(ctx):
            net.update({loser: before(winner(ctx), loser, b)})
    if not net: #Uncontested Race -> net == {}
        return True
    return min(net.values()) > 0

@save
def come_from_behind(ctx):
    return winner(ctx) != rcv(ctx)[0][0][0]
        
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
def precincts(ctx):
    return [i.precinct for i in ctx['parser'](ctx)]

@save
def precinct_totals(ctx):
    return Counter(precincts(ctx))

@save
def precinct_overvotes(ctx):
    return Counter(p for p,o in zip(precincts(ctx), overvote(ctx)) if o)

@save
def precinct_overvote_rate(ctx):
    return {k: precinct_overvotes(ctx)[k]/v for k,v in precinct_totals(ctx).items()}

@save
def precinct_overvote_rate_variance(ctx):
    return pvariance(list(precinct_overvote_rate(ctx).values()))

@save
def unique_precincts(ctx):
    return set(precincts(ctx))

@save
def precinct_overvote_rate_range(ctx):
    return {k: ci(precinct_overvotes(ctx)[k]/v, v) for k, v in precinct_totals(ctx).items()}

@save
def precinct_blockgroups(ctx):
    d = {'2017':'2016', '2015': '2014'}.get(date(ctx), date(ctx))
    path = '/'.join([
                'precinct_block_maps',
                state(ctx), 
                county(ctx), 
                'c{}_{}{}_sr_blk_map.csv'.format(county(ctx),election_type(ctx),d[-2:])
                ])
    info = []
    with open(path) as f:
        next(f)
        for line in f:
            p,t,b,xpop,ppop,_,bpop,_ = line.strip().replace('"','').split(',')
            if p != 'NULL':
                info.append({
                    'precinct': p,
                    'tract': t,
                    'block': b,
                    'xpop': int(xpop),
                    'ppop': int(ppop),
                    'bpop': int(bpop)
                })
    block_totals = {(i['tract'], i['block']): i['bpop'] for i in info}

    blockgroup_totals = defaultdict(int)
    for (tract, block),v in block_totals.items():
        blockgroup_totals[(tract, block[0])] += v

    precincts = defaultdict(int)
    for i in info:
        precincts[(i['precinct'], i['tract'], i['block'][0])] += i['xpop']

    return {(p, state(ctx)+county(ctx)+t+bg) : (v, blockgroup_totals[(t, bg)])
            for (p, t, bg), v in precincts.items()}

def processed_sov(file_name):
    result = {}
    asian_ethnicities = ['kor','jpn','chi', 'ind', 'viet', 'fil']
    with open(file_name) as f:
        reader = csv.DictReader(f)
        for i in reader:
            result[i['srprec']] = {
                'total': int(i['totreg_r']),
                'latinx': sum(int(i[k]) for k in i if k.startswith('hisp')),
                'asian': sum(int(i[k]) for k in i 
                            if any(map(k.startswith, asian_ethnicities)))
            }
    return result

@pick
def processed_cvap(file_name):
    result = defaultdict(dict)
    states = {'06'}
    counties = {'001','075'}
    with open(file_name, encoding='latin-1') as f:
        next(f)
        for line in f:
            demo, block_group,*_,tally,_ = line.split(',')[4:]
            blockgroup = block_group.split('US')[1]
            if blockgroup[:2] in states and blockgroup[2:5] in counties:
                result[blockgroup][demo] = int(tally)
    return result

def cvap(year, blockgroup):
    year = max(min(year,2017),2009)
    file_name = 'CVAP/CVAP_{}-{}_ACS_csv_files/BlockGr.csv'.format(year-4,year)
    return processed_cvap(file_name)[blockgroup]

@pick
def ethnicities():
    s = set()
    with open(glob('CVAP/*/BlockGr.csv')[0],encoding='latin-1') as f:
        for i in f:
            ethnicity = i.split(',')[4]
            if ethnicity in s:
                return s - {'Total','CIT_EST', 'Not Hispanic or Latino'}
            s.add(ethnicity)

def precinct_cvap(ethnicity, est, ctx, precinct):
    block_groups = {bg: v for (p,bg),v in precinct_blockgroups(ctx).items()
                    if p == precinct}

    precinct_total = sum(n for n,_ in block_groups.values())
    ethnicity_total = 0
    for k,(n,_) in block_groups.items():
        demos = cvap(int(date(ctx)), k)
        demos.pop('Total')
        demos.pop('Not Hispanic or Latino')
        ethnicity_total += est(ethnicity, demos, n)

    return ethnicity_total, precinct_total

def high_est(demo, demos, number):
    return min(demos[demo], number)

def mean_est(demo, demos, number):
    return ((demos[demo]/sum(demos.values()) * number) if demos[demo] else 0)

def low_est(demo, demos, number):
    return number - min(sum(v for k,v in demos.items() if k != demo), number)
    
@pick
def precinct_ethnicity(ctx, eth, est):
    d = {}
    for precinct in unique_precincts(ctx):
        part, whole = precinct_cvap(eth, est, ctx, precinct)
        d[precinct] = part/whole if whole else 0
    return d

def overvote_ratio(ctx, eth):
    if state(ctx) is None or int(date(ctx))<2012: return None
    num_over = 0
    num_votes = 0
    denom_over = 0
    denom_votes = 0
    for precinct in unique_precincts(ctx):
        pct_eth = precinct_ethnicity(ctx, eth, mean_est)[precinct]
        over = precinct_overvotes(ctx)[precinct]
        total = precinct_totals(ctx)[precinct]
        num_over += pct_eth*over
        num_votes += pct_eth*total
        denom_over += (1-pct_eth)*over
        denom_votes += (1-pct_eth)*total
    if denom_votes and num_votes:
        return (num_over/num_votes)/(denom_over/denom_votes)
    return 0

@save
def black_overvote_ratio(ctx):
    return overvote_ratio(ctx,'Black or African American Alone')

@save
def white_overvote_ratio(ctx):
    return overvote_ratio(ctx,'White Alone')
        
@save
def high_white_overvote(ctx):
    y = [v for _,v in sorted(precinct_overvote_rate(ctx).items())]
    x = [v for _,v in sorted(precinct_ethnicity(ctx, 'White Alone', high_est).items())]
    slope, _, r, p, _= linregress(x,y)
    return {'slope':slope, 'r': r, 'p': p}
    
@save
def low_white_overvote(ctx):
    y = [v for _,v in sorted(precinct_overvote_rate(ctx).items())]
    x = [v for _,v in sorted(precinct_ethnicity(ctx, 'White Alone', low_est).items())]
    slope, _, r, p, _= linregress(x,y)
    return {'slope':slope, 'r': r, 'p': p}


def state(ctx):
    return {
        'Oakland': '06',
        'San Francisco': '06',
        'San Leandro': '06',
        'Berkeley': '06'
        }.get(place(ctx))

def county(ctx):
    return {
        'Oakland': '001',
        'Berkeley': '001',
        'San Leandro': '001',
        'San Francisco': '075'
        }.get(place(ctx))

def election_type(ctx):
    return 'g'

def tdpo(ctx):
        for i in precinct_overvote_rate(ctx).values():
            print(ctx['date'], i, sep='\t')

@save
def ballots(ctx):
    raw = ctx['parser'](ctx)
    can_set = set()
    for b in raw:
        can_set.update(b)
    special = {UNDERVOTE, OVERVOTE, WRITEIN}
    can_map = sorted(can_set - special)
    return [[c if c in special else hex(can_map.index(c))[1:] for c in b] 
            for b in raw]

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
    total_voluntarily_exhausted, condorcet, come_from_behind, 
    effective_ballot_length,rounds, last5rcv, finalists, winner,exhausted_by_undervote, 
    exhausted_by_repeated_choices, minneapolis_undervote, minneapolis_total, 
    naive_tally, candidates, count_duplicates, any_repeat, validly_ranked_winner,
    margin] # black_overvote_ratio, white_overvote_ratio]

def calc(competition, functions):
    ctx = dict(manifest.competitions[competition])
    hasher(ctx) 
    return {f.__name__: f(ctx) for f in functions}

def main():
    p = ArgumentParser()
    p.add_argument('-e', '--elections', nargs='*', default=manifest.competitions.keys())
    p.add_argument('-s', '--stats', nargs='*', default=[i.__name__ for i in FUNCTIONS])
    p.add_argument('-j', '--json', action='store_true')
    a = p.parse_args()
    stats = [globals()[i] for i in a.stats]
    matched_elections = [] 
    for k,g in product(manifest.competitions.keys(), a.elections):
        if fnmatch(k,g):
            matched_elections.append(k)

    if a.json:
        for k in matched_elections:
            pprint(calc(k, stats))
        return

    with open('results.csv', 'w') as f:
        w = csv.writer(f)
        w.writerow(['name'] + a.stats)
        for k in sorted(set(matched_elections)):
            result = calc(k, stats)
            w.writerow([k.replace(',','')] + [result[s] for s in a.stats])

if __name__== '__main__':
    main()
 
