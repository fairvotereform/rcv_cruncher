"""
how 
"""

import manifest
import crunch
from collections import defaultdict, Counter

comps = [v for v in manifest.competitions.values() if v['place'] == 'Santa Fe' and v['date'] == '2018' and v['office'] in ('Mayor', 'Councilor District 4')]
ballots = [ctx['idparser'](ctx['path']) for ctx in comps]
all_ballots = sum(ballots,[])
voters = defaultdict(list)
for b in all_ballots:
    voters[b.voter_id].append(b)

two_ballots = [i for i in voters.values() if len(i)>1]
double_undervotes = sum(set(a) == set(b) == {-1} for a,b in two_ballots) # 4
total = len(two_ballots) # 5080

common = list(set(crunch.voter_ids(m)) & set(crunch.voter_ids(c4)))
ms = [crunch.preference_pairs(m)[crunch.voter_ids(m).index(i)] for i in common]
cs = [crunch.preference_pairs(c4)[crunch.voter_ids(c4).index(i)] for i in common]
c = Counter()
for a,b in zip(ms,cs):
    c.update(product(a,b))

associations = {}
for k,v in c.items():
    total = v + c[(k[0],k[1][::-1])]
    frac = v/total
    interval = 2*(frac * (1-frac) / total)**.5
    associations[k] = {'lower': frac - interval, 'upper': frac + interval}
    total = v + c[(k[0][::-1],k[1])]
    frac = v/total
    interval = 2*(frac * (1-frac) / total)**.5
    associations[k[::-1]] = {'lower': frac - interval, 'upper': frac + interval}

net_boost = {}
for k,v in associations.items():
    net_boost[k] = v['lower'] - associations[(k[0][::-1],k[1])]['upper']

