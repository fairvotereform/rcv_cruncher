from pprint import pprint
from fractions import Fraction
from collections import defaultdict
from random import choice

def keep(x,l): 
    return [i for i in l if i in x]

def stv(number, ballots):
    rounds = []
    bs = [(b,Fraction(1,1)) for b in ballots]
    threshold = int(len(bs)/(number+1)) + 1
    winners = []
    while True:
        totals = defaultdict(int)
        for c,v in bs: 
            totals[c[0] if c else None] += v
        rounds.append(sorted(totals.items(), key=lambda x:(x[0] is None, -x[1]))
        names, tallies = zip(*[k,v for k,v in rounds[-1] if k is not None])
        if len(names) + len(winners) == number:
            winners.extend(names)
            break
        elif threshold < tallies[0]:
            winners.append(names[0])
            bs = [(keep(names[1:], c), 
                    v*(set(names[:1]) != set(c[:1]) or (tallies[0]-threshold)/tallies[0]))
                    for c,v in bs]
        else:
            keepers = set(names) - {choice(names[tallies.index(min(tallies)):])}
            bs = [(keep(keepers, c), v) for c,v in bs]
    return winners, rounds, threshold

