from functools import wraps
from collections import Counter
from argparse import ArgumentParser
from pprint import pprint
import csv
import shutil
import os
import pickle 

import manifest
from contextlib import suppress

from hashlib import md5
from inspect import getsource

UNDERVOTE = -1
OVERVOTE = -2
WRITEIN = -3

### Persistence ###
def unwrap(function):
    while '__wrapped__' in dir(function):
        function = function.__wrapped__
    return function

def srchash(function):
    visited = set()
    frontier = {function}
    while frontier:
        fun = frontier.pop()
        visited.add(fun)
        code = unwrap(globals()[fun]).__code__
        helpers = list(code.co_names)
        for const in code.co_consts:
            if 'co_names' in dir(const):
                helpers.extend(const.co_names)
        for helper in set(helpers) - visited:
            if '__code__' in dir(globals().get(helper)):
                frontier.add(helper)
    h = md5()
    for f in sorted(visited):
        h.update(bytes(getsource(globals()[f]),'utf-8'))
    return h.hexdigest()

def shelve_key(arg):
    if isinstance(arg, dict):
        return dop(arg)
    if callable(arg):
        return arg.__name__
    return arg

def save(f):
    f.not_called = True
    f.cache = {}

    @wraps(f)
    def fun(*args):
        if f.not_called:
            check = srchash(f.__name__)
            dirname = 'results/' + f.__name__
            checkname = dirname + '.check'
            if os.path.exists(checkname) and check != open(checkname).read().strip():
                shutil.rmtree(dirname)
                os.remove(checkname)
            if not os.path.exists(checkname):
                open(checkname,'w').write(check)
                os.mkdir(dirname)
            f.not_called = False
        
        key = tuple(str(shelve_key(a)) for a in args)
        if next(iter(f.cache),key)[0] != key[0]:
            f.cache = {} #evict cache if first part of key (election id usually) is different
            f.visited_cache = False
        if key in f.cache:
            return f.cache[key]
        file_name = 'results/{}/{}'.format(f.__name__, '.'.join(key).replace('/','.'))
        with suppress(IOError, EOFError), open(file_name, 'rb') as file_object:
            f.cache[key] = pickle.load(file_object)
            return f.cache[key]
        with open(file_name, 'wb') as file_object:
            f.cache[key] = f(*args)
            pickle.dump(f.cache[key], file_object)
            return f.cache[key]
    return fun

def tmpsave(f):
    @wraps(f)
    def fun(ctx):
        if f.__name__ in ctx:
            return ctx[f.__name__]
        return ctx.setdefault(f.__name__, f(ctx))
    return fun

### Headline Statistics ###

@tmpsave
def place(ctx):
    return '????'

def state(ctx):
    if place(ctx) in {'Berkeley', 'Oakland', 'San Francisco', 'San Leandro'}:
        return 'CA'
    if place(ctx) in {'Burlington'}:
        return 'VT'
    if place(ctx) in {'Cambridge'}:
        return 'MA'
    if place(ctx) in {'Maine'}:
        return 'ME'
    if place(ctx) in {'Minneapolis'}:
        return 'MN'
    if place(ctx) in {'Pierce County'}:
        return 'WA'
    if place(ctx) in {'Santa Fe'}:
        return 'NM'

@tmpsave
def date(ctx):
    return '????'

@tmpsave
def office(ctx):
    return '????'

@save
def title_case_winner(ctx):
    '''
    The winner of the election, or, in multiple winner contests, the 
    hypothetical winner if the contest was single winner.
    '''
    # Horrible Hack!
    # no mapping file for the 2006 Burlington Mayoral Race, so hard coded here:
    if place(ctx) == 'Burlington' and date(ctx) == '2006':
        return 'Bob Kiss'
    return str(winner(ctx)).title()

def number_of_candidates(ctx):
    '''
    The number of non-candidates on the ballot, not including write-ins.
    '''
    return len(candidates(ctx))

def number_of_rounds(ctx):
    '''
    The number of rounds it takes for one candidate (the winner) to receive 
    the  majority of the non-exhausted votes. This number includes the 
    round in which the winner receives the majority of the non-exhausted votes.
    This is based on a tabulator that doesn't eliminate more than one declared
    candidate per round.
    '''
    return len(rcv(ctx))

def final_round_vote(ctx):
    '''
    The number of votes for the winner in the final round. The final round is 
    the first round where the winner receives a majority of the non-exhausted
    votes.
    '''
    return rcv(ctx)[-1][1][0]

def final_round_percent(ctx):
    '''
    The percent of votes for the winner in the final round. The final round is 
    the first round where the winner receives a majority of the non-exhausted
    votes.
    '''
    return rcv(ctx)[-1][1][0] / sum(rcv(ctx)[-1][1])

def first_round_vote(ctx):
    '''
    The number of votes for the winner in the first round.
    '''
    wind = rcv(ctx)[0][0].index(winner(ctx))
    return rcv(ctx)[0][1][wind]

def first_round_percent(ctx):
    '''
    The percent of votes for the winner in the first round.
    '''
    wind = rcv(ctx)[0][0].index(winner(ctx))
    return rcv(ctx)[0][1][wind] / sum(rcv(ctx)[0][1])

def first_round_place(ctx):
    '''
    In terms of first round votes, what place the eventual winner came in.
    '''
    return rcv(ctx)[0][0].index(winner(ctx)) + 1

def number_of_first_round_valid_votes(ctx):
    '''
    The number of votes that were awarded to any candidate in the first round.
    '''
    return sum(rcv(ctx)[0][1])

def number_of_final_round_active_votes(ctx):
    '''
    The number of votes that were awarded to any candidate in the final round.
    '''
    return sum(rcv(ctx)[-1][1])

@save
def total(ctx):
    '''
    This includes ballots with no marks.
    '''
    return len(ballots(ctx))

def final_round_inactive(ctx):
    '''
    The difference of first round valid votes and final round valid votes.
    '''
    return number_of_first_round_valid_votes(ctx) - number_of_final_round_active_votes(ctx)

def final_round_winner_votes_over_first_round_valid(ctx):
    '''
    The number of votes the winner receives in the final round divided by the 
    number of valid votes in the first round.
    '''
    return final_round_vote(ctx) / number_of_first_round_valid_votes(ctx)

@save 
def winners_consensus_value(ctx):
    '''
    The percentage of valid first round votes that rank the winner in the top 3.
    '''
    return winner_in_top_3(ctx) / number_of_first_round_valid_votes(ctx) 

@save
def condorcet(ctx):
    '''
    Is the winner the condorcet winner?
    The condorcet winner is the candidate that would win a 1-on-1 election versus
    any other candidate in the election. Note that this calculation depends on 
    jurisdiction dependant rule variations.
    '''
    if len(rcv(ctx)) == 1:
        return True
    net = Counter()
    for b in cleaned(ctx):
        for loser in losers(ctx):
            net.update({loser: before(winner(ctx), loser, b)})
    if not net: #Uncontested Race -> net == {}
        return True
    return min(net.values()) > 0

@save
def total_fully_ranked(ctx):
    '''
    The number of voters that have validly used all available rankings on the
    ballot, or that have validly ranked all non-write-in candidates.
    '''
    return sum(fully_ranked(ctx))

@save 
def ranked_multiple(ctx): 
    '''
    The number of voters that validly use more than one ranking.
    '''
    return sum(len(b) > 1 for b in cleaned(ctx))

@save
def first_round_undervote(ctx):
    '''
    The number of ballots with absolutely no markings at all. 

    Note that this is not the same as "exhausted by undervote". This is because 
    some juristidictions (Maine) discard any ballot begining with two 
    undervotes regardless of the rest of the content of the ballot, and call 
    this ballot as exhausted by undervote.
    '''
    return sum(set(b) == {UNDERVOTE} for b in ballots(ctx))

@save
def first_round_overvote(ctx):
    '''
    The number of ballots with an overvote before any valid ranking. 

    Note that this is not the same as "exhausted by overvote". This is because
    some juristidictions (Maine) discard any ballot begining with two 
    undervotes, and call this ballot as exhausted by undervote, even if the 
    undervotes are followed by an overvote.

    Other jursidictions (Minneapolis) simply skip over overvotes in a ballot.
    '''
    return sum(c == OVERVOTE for c in first_round(ctx))

@save
def later_round_inactive_by_overvote(ctx):
    '''
    The number of ballots that were discarded after the first round due to an
    overvote.

    Note that Minneapolis doesn't discard overvote ballots, it simply skips over
    the overvote.
    '''
    return sum(a and b for a,b in zip(later_round_exhausted(ctx), exhausted_by_overvote(ctx)))

@save
def later_round_inactive_by_abstention(ctx):
    '''
    The number of ballots that were discarded after the first round because not
    all rankings were used and it was not discarded because of an overvote.

    This factor will exclude all ballots with overvotes aside from those in Maine
    where more than one sequential undervote preceeds an overvote.
    '''
    return sum(later_round_exhausted(ctx)) \
            - later_round_inactive_by_overvote(ctx) \
            - later_round_inactive_by_ranking_limit(ctx)

@save
def later_round_inactive_by_ranking_limit(ctx):
    '''
    The number of ballots that validly used every ranking, but didn't rank any
    candidate that appeared in the final round.
    '''
    return sum(a and b for a,b in zip(later_round_exhausted(ctx), fully_ranked(ctx)))

def includes_duplicates(ctx):
    '''
    The number of ballots that rank the same candidate more than once, or
    include more than one write in candidate.
    '''
    return sum(v > 1 for v in max_repeats(ctx))

@save
def includes_skipped(ctx):
    '''
    The number of ballots that have an undervote followed by an overvote or a 
    valid ranking
    '''
    return sum(any({UNDERVOTE} & {x} - {y} for x,y in zip(b, b[1:]))
                for b in ballots(ctx))

@save
def until2rcv(ctx):
    """
    run an rcv election until there are two candidates remaining
    """
    rounds = []
    bs = [list(i) for i in cleaned(ctx)]
    while True:
        rounds.append(list(zip(*Counter(b[0] for b in bs if b).most_common())))
        finalists, tallies = rounds[-1] 
        if len(finalists) < 3: 
            return rounds
        bs = [keep(finalists[:-1], b) for b in bs]

@save  
def top2_winners_margin(ctx):
    """
    winner's votes less runner-up's votes 
    (after running an rcv to two candidates and possibly past the round in
    which the winner receives 50% of the remaining vote)
    """
    last_round = until2rcv(ctx)[-1][1]
    if len(last_round) == 2:
        return last_round[0] - last_round[1]

@save
def top2_winners_vote_increased(ctx):
    """
    If you run an RCV contest until there are two or fewer candidates left,
    does the number of votes the winner receive increase from the first to the
    last round?
    """
    first = until2rcv(ctx)[0]
    start = first[1][first[0].index(winner(ctx))]
    return until2rcv(ctx)[-1][1][0] > start

@save
def top2_winners_fraction(ctx):
    """
    If you run an RCV contest until there are two or fewer candidates left,
    what fraction of the votes that cast validly ranked at least one candidate
    does the winner eventually receive? 
    """
    return until2rcv(ctx)[-1][1][0]/float(sum(until2rcv(ctx)[0][1]))

@save
def top2_majority(ctx):
    """
    If you run an RCV contest until there are two or fewer candidates left,
    Does the winner receive over half the votes that cast validly ranked at
    least one candidate?
    """
    return top2_winners_fraction(ctx) > 0.5

@save
def top2_winner_over_40(ctx):
    """
    If you run an RCV contest until there are two or fewer candidates left,
    Does the winner receive over 40% of the votes that cast validly ranked at
    least one candidate?
    """
    return top2_winners_fraction(ctx) > 0.4

def blank(ctx):
    return None

HEADLINE_STATS = [place, state, date, office, title_case_winner, blank, 
    number_of_candidates, number_of_rounds, final_round_vote, 
    final_round_percent, first_round_vote,
    first_round_percent, first_round_place, number_of_first_round_valid_votes,
    number_of_final_round_active_votes, blank, total, blank,
    final_round_inactive, final_round_winner_votes_over_first_round_valid,
    winners_consensus_value, condorcet, total_fully_ranked,
    ranked_multiple, first_round_undervote, first_round_overvote, 
    later_round_inactive_by_overvote, later_round_inactive_by_abstention,
    later_round_inactive_by_ranking_limit, includes_duplicates, includes_skipped,
    top2_winners_vote_increased, top2_winners_fraction, top2_majority,
    top2_winner_over_40
]

### Tabulation ###
def remove(x,l): 
    return [i for i in l if i != x]

def keep(x,l): 
    return [i for i in l if i in x]

@save
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

@save 
def winner_ranking(ctx):
    return Counter(b.index(winner(ctx))+1 if winner(ctx) in b else None
                    for b in cleaned(ctx))
@save 
def winner_in_top_3(ctx):
    return sum(v for k,v in winner_ranking(ctx).items() if k is not None and k<4)

@save  
def rcv(ctx):
    rounds = []
    bs = [list(i) for i in cleaned(ctx)]
    while True:
        rounds.append(list(zip(*Counter(b[0] for b in bs if b).most_common())))
        finalists, tallies = rounds[-1] 
        if tallies[0]*2 > sum(tallies):
            return rounds
        bs = [keep(finalists[:-1], b) for b in bs]

    
@save
def winner(ctx):
    return rcv(ctx)[-1][0][0]

def finalists(ctx):
    return rcv(ctx)[-1][0]

@save 
def first_round(ctx):
    return [next((c for c in b if c != UNDERVOTE), UNDERVOTE)
            for b in ballots(ctx)]

@save 
def exhausted(ctx):
    return [not set(finalists(ctx)) & set(b) for b in cleaned(ctx)]

@save
def later_round_exhausted(ctx):
    return [not (set(finalists(ctx)) & set(b)) and bool(b) for b in cleaned(ctx)]

@save 
def exhausted_by_overvote(ctx):
    if break_on_repeated_undervotes(ctx):
        return [ex and over<under for ex,over,under in 
                zip(exhausted(ctx),overvote_ind(ctx),repeated_undervote_ind(ctx))]

    return [ex and over for ex,over in zip(exhausted(ctx),overvote(ctx))]

def before(x, y, l):
    for i in l:
        if i == x:
            return 1
        if i == y:
            return -1
    return 0

@save
def losers(ctx):
    return set(candidates(ctx)) - {winner(ctx)}

@save
def repeated_undervote_ind(ctx):
    rs = []
    for b in ballots(ctx):
        rs.append(float('inf'))
        z = list(zip(b,b[1:]))
        uu = (UNDERVOTE,UNDERVOTE)
        if uu in z:
            occurance = z.index(uu)
            for c in b[occurance+1:]:
                if c != UNDERVOTE:
                    rs[-1] = occurance
                    break
    return rs

@save
def overvote_ind(ctx):
    return [b.index(OVERVOTE) if OVERVOTE in b else float('inf')
            for b in ballots(ctx)]

@save
def max_repeats(ctx):
    return [max(0,0,*map(b.count,set(b)-{UNDERVOTE,OVERVOTE}))
            for b in ballots(ctx)]

@save
def overvote(ctx):
    return [OVERVOTE in b for b in ballots(ctx)]

@save
def fully_ranked(ctx):
    return [len(b) == len(a) or set(b) >= candidates(ctx)
            for a,b in zip(ballots(ctx), cleaned(ctx))]

@save
def candidates(ctx):
    cans = set()
    for b in ballots(ctx):
        cans.update(b) 
    return cans - {OVERVOTE, UNDERVOTE, WRITEIN}

@save
def ballots(ctx):
    return ctx['parser'](ctx)

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
def dop(ctx):
    return ','.join(str(f(ctx)) for f in [date, office, place])

def calc(ctx, functions):
    print(dop(ctx))
    results = {}
    for f in functions:
        results[f.__name__] = f(ctx)
    return results

def main():
    p = ArgumentParser()
    p.add_argument('-j', '--json', action='store_true')
    a = p.parse_args()
    if a.json:
        for k in manifest.competitions.values():
            pprint(calc(k, FUNCTIONS))
        return

    with open('headline.csv', 'w') as f:
        w = csv.writer(f)
        w.writerow([fun.__name__ for fun in HEADLINE_STATS])
        w.writerow([' '.join((fun.__doc__ or '').split())
                     for fun in HEADLINE_STATS])
        for k in sorted(manifest.competitions.values(),key=lambda x: x['date']):
            if True: #k['office'] == 'Democratic Primary for Governor': #county(k) in {'075'} and int(date(k)) == 2012:
                result = calc(k, HEADLINE_STATS)
                w.writerow([result[fun.__name__] for fun in HEADLINE_STATS])

if __name__== '__main__':
    main()
 
