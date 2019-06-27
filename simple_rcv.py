from collections import Counter

def remove(x,l): 
    return [i for i in l if i != x]

def keep(x,l): 
    return [i for i in l if i in x]

def rcvreg(ballots):
    rounds = []
    while True:
        rounds.append(list(zip(*Counter(b[0] for b in ballots).most_common())))
        finalists, tallies = rounds[-1] 
        if tallies[0]*2 > sum(tallies):
            return rounds
        ballots = remove([], (keep(finalists[:-1], b) for b in ballots))

def cleaned(ballots):
    new_ballots = []
    for b in ballots:
        n = []
        for a,b in zip(b,b[1:]+[None]):
            if a == 'overvote':
                break
            if a != 'undervote':
                n.append(a)
        new_ballots.append(b)
    return new_ballots

