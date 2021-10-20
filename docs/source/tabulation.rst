Tabulation Methods
==================

RCV tabulation methods currently supported:

**single winner IRV - until 50% winner reached** (:class:`rcv.variants.SingleWinner`) - Candidates are eliminated until one candidate has more than 50% of active votes in a round.

**single winner IRV - until 2 candidates remain** (:class:`rcv.variants.Until2`) - Candidate are eliminated until only 2 remain. The candidate with more votes is the winner. This will produce the same winner as single winner IRV with a 50% threshold, but will likely add on more rounds of tabulation and more inactivated ballots.

**multi winner STV - fractional ballot transfer** (:class:`rcv.variants.STVFractionalBallot`) - Based on the number to elect and the number of votes active in the first round a static vote threshold is calculated. More information on the threshold formula can be found `here <https://www.opavote.com/methods/single-transferable-vote>`_. In a round with no winner, the candidate with the least votes is eliminated and their votes redistributed similar to the elimination process in a single winner election. When a winner is reached, their surplus votes are redistributed fractionally. The formula used to calculate the fraction follows the `Gregory method <https://en.wikipedia.org/wiki/Counting_single_transferable_votes#Gregory>`_.

**multi winner STV - whole ballot transfer** (:class:`rcv.variants.STVWholeBallot`) - Based on the number to elect and the number of votes active in the first round a static vote threshold is calculated. More information on the threshold formula can be found `here <https://www.opavote.com/methods/single-transferable-vote>`_. In a round with no winner, the candidate with the least votes is eliminated and their votes redistributed similar to the elimination process in a single winner election. When a winner is reached a subset of votes allocated to the winner are chosen as surplus votes. Those selected whole ballots are redistributed. The formula used to calculate which ballots are considered surplus is one used in `Cambridge, Massachusetts <https://www.opavote.com/methods/cambridge-stv-rules>`_.

**multi winner bottoms up** (:class:`rcv.variants.BottomsUpThresh`) - Candidates are eliminated round by round until all candidates active in a round have at least X% of the active votes. All those candidates are winners.

**multi winner sequential IRV** (:class:`rcv.variants.Sequential`) - Multiple winners are elected by repeating the process for a single winner IRV tabulation N times, one for each winner needed. After a candidate a candidate wins in one tabulation, they are excluded from the following ones.
