
###############################################################
# constants

SKIPVOTE = -1
OVERVOTE = -2
WRITEIN = -3

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