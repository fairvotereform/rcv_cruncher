
###############################################################
# constants

SKIPPEDRANK = -1
OVERVOTE = -2
WRITEIN = 'writeIns'

"""
undervote = matching the non-rcv context, an undervote is when no marks are made 
on the ballot for a contest (a blank ballot for that contest)

overvote = when more than one candidate is marked for a given rank

skipvote = when no candidate is assigned to a given rank.
can refer to both a skipped rank with two non-skipped ranks surrounding it 
-- vote, skipvote, vote pattern -- OR 
skipped ranks that result from voluntary limiting of the number of rankings made 
-- vote, vote, skipvote, skipvote, skipvote ... pattern --

exhausted ballot = when all rankings on a ballot have been eliminated. Specifically not 
and undervote.
"""

UNDERVOTE = -98
NOT_EXHAUSTED = -99
EXHAUSTED_BY_RANK_LIMIT = -100
EXHAUSTED_BY_ABSTENTION = -101
EXHAUSTED_BY_OVERVOTE = -102
EXHAUSTED_BY_REPEATED_SKIPVOTE = -103

"""
exhaust by overvote - if rules apply, exhaust ballot when overvote is reached

exhaust by repeated skipped rank - if rules apply, exhaust ballot when two or skipped rankings occur. Only counts
if there are valid marks after the skipped ranks. If not, then the ballot would be considered as exhausted by abstention.

exhaust by abstention - when the final series of marks on the ballot are all skipped.

exhaust by rank limit - an inclusive category. Any exhausted ballot in which the final rank was marked and reached.
Most directly refers to ballots that validly used all ranks before exhausting. Though also refers to ballots
that did have irregular marks (skipped rank, duplicate rank, overvote) that were skipped over due 
to rules prior to reaching the final rank. Any ballot exhausted not by overvote, repeated skipped ranks, or abstention.
"""


########################
# helper funcs

def before(victor, loser, ballot):
    """
        Used to calculate condorcet stats. Each ballot passed through this
        function gets mapped to either
        1 (winner ranked before loser),
        0 (neither appear on ballot),
        or -1 (loser ranked before winner).
    """
    for rank in ballot:
        if rank == victor:
            return 1
        if rank == loser:
            return -1
    return 0

def remove(x, l):
    # removes all x from list l
    return [i for i in l if i != x]

def keep(x, l):
    # keeps only all x in list l
    return [i for i in l if i in x]

def isInf(x):
    # checks if x is inf
    return x == float('inf')

def index_inf(lst, el):
    # return element index if in list, inf otherwise
    if el in lst:
        return lst.index(el)
    else:
        return float('inf')

def replace(target, replacement, l):
    # return a list with all instances of 'target' set to 'replacement'
    return [replacement if i == target else i for i in l]

def merge_writeIns(b):
    return [WRITEIN if isinstance(i, str) and 'writein' in i.lower().replace('-', '')
            else i for i in b]
