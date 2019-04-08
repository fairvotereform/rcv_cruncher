from collections import Counter
from ballot_analyzer import UNDERVOTE, OVERVOTE

def remove(x,l): 
    return [i for i in l if i != x]

def clean(ballots):
    ballots = [(b[:b.index(OVERVOTE)] if OVERVOTE in b else b) for b in ballots]
    return remove([], [remove(UNDERVOTE, b) for b in ballots])

def rcv(ballots):
    i = 1
    while True:
        finalists, tallies = zip(*Counter(b[0] for b in ballots).most_common())
        print i, finalists, tallies, sum(tallies)
        i += 1
        if tallies[0]*2 > sum(tallies):
            return {'winner': finalists[0], 'finalists': finalists}
        if len(tallies)>1 and tallies[-1] == tallies[-2]:
            raise "last place tie"
        ballots = remove([], [remove(finalists[-1], b) for b in ballots])
    
