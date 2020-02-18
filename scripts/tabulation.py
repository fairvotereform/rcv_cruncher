from collections import defaultdict
from glob import glob
from gmpy2 import mpq as Fraction
from copy import deepcopy
from itertools import product, combinations
from collections import Counter


# cruncher imports
from .definitions import SKIPVOTE, OVERVOTE, WRITEIN
from .cache_helpers import save


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
    return [i for i in l if i != x]

def keep(x, l):
    return [i for i in l if i in x]

def isInf(x):
    return x == float('inf')


def stats_func_list():

    STATS = [contest_winner,
             number_of_candidates,
             final_round_winner_vote,
             final_round_winner_percent,
             final_round_active_votes,
             first_round_winner_vote,
             first_round_winner_percent,
             first_round_active_votes,
             first_round_winner_place,
             final_round_winner_votes_over_first_round_valid,
             winners_consensus_value,
             condorcet,
             come_from_behind,
             effective_ballot_length,
             first_round_overvote,
             ranked_single,
             ranked_multiple,
             total_fully_ranked,
             ranked_winner,
             includes_duplicate_ranking,
             includes_skipped_ranking,
             total_irregular,
             total_ballots,
             total_ballots_with_overvote,
             total_undervote,
             total_exhausted,
             total_exhausted_by_overvote,
             total_exhausted_by_skipped_rankings,
             total_exhausted_by_abstention,
             total_exhausted_by_rank_limit]

    return STATS


@save
def any_repeat(ctx):
    """
        Number of ballots that included one at least one candidate that
        received more than once ranking
    """
    return sum(v for k, v in count_duplicates(ctx).items() if k > 1)


@save
def ballots(ctx):
    return ctx['parser'](ctx)


@save
def candidates(ctx):
    cans = set()
    for b in ballots(ctx):
        cans.update(b)
    return cans - {OVERVOTE, SKIPVOTE, WRITEIN}


@save
def cleaned(ctx):
    """
        retrieve ballots (list of lists, each containing candidate names in
        rank order, also write-ins marked with WRITEIN constant, and OVERVOTES and
        SKIPVOTES marked with their respective constants)

        For each ballot, return a cleaned version that has pre-skipped
        skipped and overvoted rankings and only includes one ranking
        per candidate (the highest ranking for that candidate).

        Additionally, each ballot may be cut short depending on the
        -break_on_repeated_skipvotes- and -break_on_overvote- settings for
        a contest.

        returns: list of cleaned ballot-lists
    """
    new = []
    for b in ballots(ctx):
        result = []
        # look at successive pairs of rankings - zip list with itself offset by 1
        for elem_a, elem_b in zip(b, b[1:]+[None]):
            if ctx['break_on_repeated_skipvotes'] and {elem_a, elem_b} == {SKIPVOTE}:
                break
            if ctx['break_on_overvote'] and elem_a == OVERVOTE:
                break
            if elem_a not in [*result, OVERVOTE, SKIPVOTE]:
                result.append(elem_a)
        new.append(result)
    return new


def come_from_behind(ctx):
    """
    True if rcv winner is not first round leader
    """
    return winner(ctx) != rcv(ctx)[0][0][0]


@save
def condorcet(ctx):
    '''
    Is the winner the condorcet winner?
    The condorcet winner is the candidate that would win a 1-on-1 election versus
    any other candidate in the election. Note that this calculation depends on
    jurisdiction dependant rule variations.
    '''

    # first round winner is the condorcet winner
    if len(rcv(ctx)) == 1:
        return True

    net = Counter()
    for b in cleaned(ctx):
        for loser in losers(ctx):

            # accumulate difference between the number of ballots ranking
            # the winner before the loser
            net.update({loser: before(winner(ctx), loser, b)})

    if not net:  # Uncontested Race -> net == {}
        return True

    # if all differences are positive, then the winner was the condorcet winner
    return min(net.values()) > 0


@save
def count_duplicates(ctx):
    """
    Returns dictionary counting the number of max repeat ranking from each ballot
    """
    return Counter(max_repeats(ctx))


@save
def duplicates(ctx):
    """
    Returns boolean list with elements set to True if ballot has at least one
    duplicate ranking
    """
    return [v > 1 for v in max_repeats(ctx)]


@save
def effective_ballot_length(ctx):
    """
    A list of validly ranked choices, and how many ballots had that number of
    valid choices.
    """
    return '; '.join('{}: {}'.format(a, b) for a, b in sorted(Counter(map(len, cleaned(ctx))).items()))


@save
def exhausted(ctx):
    """
    Returns a boolean list indicating which ballots were exhausted.
    Does not include undervotes as exhausted.
    """
    return [True if x != 'not_exhausted' and x is not None
            else False for x in exhaustion_check(ctx)]


@save
def exhausted_by_abstention(ctx):
    """
    Returns bool list with elements corresponding to ballots.
    True if ballot was exhausted without being fully ranked and the
    cause of exhaustion was not overvotes or skipped rankings.
    """
    return [True if i == 'abstention' else False for i in exhaustion_check(ctx)]


@save
def exhausted_or_undervote(ctx):
    """
    Returns bool list corresponding to each ballot.
    True when ballot when ballot was exhausted OR left blank (undervote)
    False otherwise
    """
    return [True if x != 'not_exhausted' else False for x in exhaustion_check(ctx)]


@save
def exhausted_by_overvote(ctx):
    """
    Returns bool list with elements corresponding to ballots.
    True if ballot was exhausted due to overvote
    """
    return [True if i == 'overvote' else False for i in exhaustion_check(ctx)]


@save
def exhausted_by_rank_limit(ctx):
    """
    Returns bool list with elements corresponding to ballots.
    True if ballot was exhausted AND fully ranked and the
    cause of exhaustion was not overvotes or skipped rankings.
    """
    return [True if i == 'rank_limit' else False for i in exhaustion_check(ctx)]


@save
def exhausted_by_skipvote(ctx):
    """
    Returns bool list with elements corresponding to ballots.
    True if ballot was exhausted due to repeated_skipvotes
    """
    return [True if i == 'repeated_skipvotes' else False for i in exhaustion_check(ctx)]


@save
def exhaustion_check(ctx):
    """
    Returns a list with string elements indicating why each ballot
    was exhausted in a single-winner rcv contest.

    Possible list values are:
    - overvote: if an overvote was the cause of exhaustion (depends on break_on_overvote manifest value)
    - repeated_skipvotes: if repeated skipvotes were the cause of exhaustion
    (depends on break_on_repeated_skipvotes manifest value)
    - not_exhausted: if finalist was present on the ballot and was ranked higher than an exhaust condition
    (overvote or repeated_skipvotes)
    - rank_limit: if no finalist was present on the ballot and the ballot was fully ranked
    - abstention: if no finalist was present on the ballot and the ballot was NOT fully ranked
    - None (Nonetype): if the ballot was undervote, and therefore neither active nor exhaustable
    """

    # gather ballot info
    ziplist = zip(fully_ranked(ctx),  # True if fully ranked
                  overvote_ind(ctx),  # Inf if no overvote
                  repeated_skipvote_ind(ctx),  # Inf if no repeated skipvotes
                  finalist_ind(ctx),  # Inf if not finalist ranked
                  undervote(ctx))  # True if ballot is undervote

    why_exhaust = []

    # loop through each ballot
    for is_fully_ranked, over_idx, repskip_idx, final_idx, is_under in ziplist:

        exhaust_cause = None

        # if the ballot is an undervote,
        # nothing else to check
        if is_under:
            why_exhaust.append(exhaust_cause)
            continue

        # determine exhaustion cause

        missing_finalist = isInf(final_idx)

        # assemble dictionary of possible exhaustion causes and then remove any
        # that don't apply based on the contest rules
        idx_dictlist = [{'exhaust_cause': 'overvote', 'idx': over_idx},
                        {'exhaust_cause': 'repeated_skipvotes', 'idx': repskip_idx},
                        {'exhaust_cause': 'not_exhausted', 'idx': final_idx}]

        # check if overvote can cause exhaust
        if ctx['break_on_overvote'] is False:
            idx_dictlist = [i for i in idx_dictlist if i['exhaust_cause'] != 'overvote']

        # check if skipvotes can cause exhaustion
        if ctx['break_on_repeated_skipvotes'] is False:
            idx_dictlist = [i for i in idx_dictlist if i['exhaust_cause'] != 'repeated_skipvotes']

        # what comes first on ballot: overvote, skipvotes, or finalist?
        min_dict = sorted(idx_dictlist, key=lambda x: x['idx'])[0]

        if isInf(min_dict['idx']):

            # means this ballot contained none of the three, it will be exhausted
            # either for rank limit or abstention
            if is_fully_ranked:
                exhaust_cause = 'rank_limit'
            elif missing_finalist:
                exhaust_cause = 'abstention'
            else:
                print('if final_idx is inf, then missing_finalist should be true. This should never be reached')
                exit(1)

        else:
            exhaust_cause = min_dict['exhaust_cause']

        why_exhaust.append(exhaust_cause)

    return why_exhaust


@save
def first_round(ctx):
    """
    Returns a list of first non-skipvote for each ballot OR
    if the ballot is empty, can also return None
    """
    return [next((c for c in b if c != SKIPVOTE), None)
            for b in ballots(ctx)]


@save
def first_round_overvote(ctx):
    '''
    The number of ballots with an overvote before any valid ranking.

    Note that this is not the same as "exhausted by overvote". This is because
    some juristidictions (Maine) discard any ballot beginning with two
    skipped rankings, and call this ballot as exhausted by skipped rankings, even if the
    skipped rankings are followed by an overvote.

    Other jursidictions (Minneapolis) simply skip over overvotes in a ballot.
    '''
    return sum(c == OVERVOTE for c in first_round(ctx))


def first_round_winner_place(ctx):
    '''
    In terms of first round votes, what place the eventual winner came in.
    '''
    return rcv(ctx)[0][0].index(winner(ctx)) + 1


def first_round_winner_percent(ctx):
    '''
    The percent of votes for the winner in the first round.
    '''
    wind = rcv(ctx)[0][0].index(winner(ctx))
    return rcv(ctx)[0][1][wind] / sum(rcv(ctx)[0][1])


def first_round_winner_vote(ctx):
    '''
    The number of votes for the winner in the first round.
    '''
    wind = rcv(ctx)[0][0].index(winner(ctx))
    return rcv(ctx)[0][1][wind]


def finalists(ctx):
    return rcv(ctx)[-1][0]


def finalist_ind(ctx):
    """
    Returns a list indicating the first rank on each ballot where a finalist is listed.
    List element is Inf if no finalist is present
    """
    final_candidates = finalists(ctx)
    inds = []

    # loop through each ballot and check for each finalist
    for b in ballots(ctx):
        min_ind = float('inf')
        for c in final_candidates:
            if c in b:
                min_ind = min(b.index(c), min_ind)
        inds.append(min_ind)

    return inds


def final_round_active_votes(ctx):
    '''
    The number of votes that were awarded to any candidate in the final round.
    '''
    return sum(rcv(ctx)[-1][1])


def first_round_active_votes(ctx):
    '''
    The number of votes that were awarded to any candidate in the first round.
    '''
    return sum(rcv(ctx)[0][1])


def final_round_winner_percent(ctx):
    '''
    The percent of votes for the winner in the final round. The final round is
    the first round where the winner receives a majority of the non-exhausted
    votes.
    '''
    return rcv(ctx)[-1][1][0] / sum(rcv(ctx)[-1][1])


def final_round_winner_vote(ctx):
    '''
    The number of votes for the winner in the final round. The final round is
    the first round where the winner receives a majority of the non-exhausted
    votes.
    '''
    return rcv(ctx)[-1][1][0]


def final_round_winner_votes_over_first_round_valid(ctx):
    '''
    The number of votes the winner receives in the final round divided by the
    number of valid votes in the first round.
    '''
    return final_round_winner_vote(ctx) / first_round_active_votes(ctx)


@save
def fully_ranked(ctx):
    """
        Returns a list of bools with each item corresponding to a ballot.
        True indicates a fully ranked ballot.

        Fully ranked here means either the cleaned ballot contains the
        full set of candidates OR the raw and cleaned ballot are of the same length
        (this second condition is to account for limited rank voting systems)

        Note: cleaned ballots already should have skipped rankings, overvotes, and
        repeated rankings given to a single candidate all removed
    """
    return [len(b) == len(a)  # either there is a ranking limit and no exhaust conditions shortened the ballot
                              # (the ballot is effectively fully ranked)
            or (set(b) & candidates(ctx)) == candidates  # or voters ranked every possible candidate
            for a, b in zip(ballots(ctx), cleaned(ctx))]


@save
def has_skipvote(ctx):
    """
    Returns boolean list indicating if ballot contains any skipvotes
    """
    return [SKIPVOTE in b for b in ballots(ctx)]


def includes_duplicate_ranking(ctx):
    '''
    The number of ballots that rank the same candidate more than once, or
    include more than one write in candidate.
    '''
    return any_repeat(ctx)


@save
def includes_skipped_ranking(ctx):
    '''
    The number of ballots that have an skipped ranking followed by any other mark
    valid ranking
    '''
    return sum(skipped(ctx))


@save
def losers(ctx):
    return set(candidates(ctx)) - {winner(ctx)}


@save
def max_repeats(ctx):
    """
        Return a list with each element indicating the max duplicate ranking count
        for any candidate on the ballot

        Note:
        If on a ballot, a candidate received two different rankings, that ballot's
        corresponding list element would be 2. If every candidate included on that
        ballot was only ranked once, that ballot's corresponding list element
        would be 1
    """
    return [max(0, 0, *map(b.count, set(b) - {SKIPVOTE, OVERVOTE}))
            for b in ballots(ctx)]


# fixme
def number_of_candidates(ctx):
    '''
    The number of non-candidates on the ballot, not including write-ins.
    '''
    return len(candidates(ctx))


@save
def overvote(ctx):
    return [OVERVOTE in b for b in ballots(ctx)]


@save
def overvote_ind(ctx):
    """
        Returns list of index values for first overvote on each ballot
        If no overvotes on ballots, list element is inf
    """
    return [b.index(OVERVOTE) if OVERVOTE in b else float('inf')
            for b in ballots(ctx)]


@save
def ranked_single(ctx):
    '''
    The number of voters that validly used only a single ranking
    '''
    return sum(len(b) == 1 for b in cleaned(ctx))


@save
def ranked_multiple(ctx):
    '''
    The number of voters that validly use more than one ranking.
    '''
    return sum(len(b) > 1 for b in cleaned(ctx))


@save
def ranked_winner(ctx):
    """
     Number of ballots with a non-overvote mark for the winner
    """
    return sum(winner(ctx) in b for b in ballots(ctx))


@save
def rcv(ctx):
    """
        Retrieves the cleaned ballots using ctx and
        returns a list of round-by-round vote counts.
        Runs until single winner threshold is reached.

        [[(round 1 candidates), (round 1 tally)],
         [(round 2 candidates), (round 2 tally)],
         ...,
         [(final round candidates), (final round tally)]]
    """
    rounds = []
    bs = [list(i) for i in cleaned(ctx)]

    while True:
        rounds.append(
            list(zip(
                # tally ballots and reorder tallies
                # using active rankings for each ballot,
                # skipping empty ballots
                *Counter(b[0] for b in bs if b).most_common()
                     ))
        )
        finalists, tallies = rounds[-1]

        # check for a winner
        if tallies[0]*2 > sum(tallies):
            return rounds

        # else remove round loser from ballots, all ranking spots.
        # removing the round loser from all ranking spots now is equivalent
        # to waiting and skipping over an already-eliminated candidate
        # once they become the active ranking in a later round.
        bs = [keep(finalists[:-1], b) for b in bs]


@save
def repeated_skipvote_ind(ctx):
    """
        return list with index from each ballot where the skipvotes start repeating,
        if no repeated skipvotes, set list element to inf

        note:
        repeated skipvotes are only counted if non-skipvotes occur after them. this
        prevents incompletely ranked ballots from being counted as having repeated skipvotes
    """

    rs = []

    for b in ballots(ctx):

        rs.append(float('inf'))

        # pair up successive rankings on ballot
        z = list(zip(b, b[1:]))
        uu = (SKIPVOTE, SKIPVOTE)

        # if repeated skipvote on the ballot
        if uu in z:
            occurance = z.index(uu)

            # start at second skipvote in the pair
            # and loop until a non-skipvote is found
            # only then record this ballot as having a
            # repeated skipvote
            for c in b[occurance+1:]:
                if c != SKIPVOTE:
                    rs[-1] = occurance
                    break
    return rs


@save
def skipped(ctx):
    """
    Returns boolean list. True if skipped rank (followed by other marks) is present.
    Otherwise False.

    {SKIPVOTE} & {x} - {y}
    this checks that x == SKIPVOTE and that y then != SKIPVOTE
    (the y check is important to know whether or not the ballot contains marks
    following the skipped rank)
    """
    return [any({SKIPVOTE} & {x} - {y} for x, y in zip(b, b[1:]))
            for b in ballots(ctx)]


@save
def contest_winner(ctx):
    '''
    The winner of the election, or, in multiple winner contests, the
    hypothetical winner if the contest was single winner.
    '''
    # Horrible Hack!
    # no mapping file for the 2006 Burlington Mayoral Race, so hard coded here:
    if ctx['place'] == 'Burlington' and ctx['date'] == '2006':
        return 'Bob Kiss'
    return str(winner(ctx)).title()


@save
def total_ballots(ctx):
    '''
    This includes ballots with no marks.
    '''
    return len(ballots(ctx))


@save
def total_exhausted(ctx):
    '''
    Number of ballots (excluding undervotes) that do not rank a finalist.
    '''
    return sum(exhausted(ctx))


@save
def total_exhausted_by_abstention(ctx):
    """
    Number of ballots exhausted after all marked rankings used and ballot is not fully ranked.
    """
    return sum(exhausted_by_abstention(ctx))


@save
def total_exhausted_by_overvote(ctx):
    """
    Number of ballots exhausted due to overvote. Only applicable to certain contests.
    """
    return sum(exhausted_by_overvote(ctx))


@save
def total_exhausted_by_rank_limit(ctx):
    """
    Number of ballots exhausted after all marked rankings used and ballot is fully ranked.
    """
    return sum(exhausted_by_rank_limit(ctx))


def total_exhausted_by_skipped_rankings(ctx):
    """
    Number of ballots exhausted due to repeated skipped rankings. Only applicable to certain contests.
    """
    return sum(exhausted_by_skipvote(ctx))


@save
def total_ballots_with_overvote(ctx):
    '''
    Number of ballots with at least one overvote. Not necessarily cause of exhaustion.
    '''
    return sum(overvote(ctx))


@save
def total_fully_ranked(ctx):
    '''
    The number of voters that have validly used all available rankings on the
    ballot, or that have validly ranked all non-write-in candidates.
    '''
    return sum(fully_ranked(ctx))


@save
def total_irregular(ctx):
    """
    Number of ballots that either had a multiple ranking, overvote,
    or a skipped ranking. This includes ballots even where the irregularity was not
    the cause of exhaustion.
    """
    return sum(map(any, zip(duplicates(ctx), overvote(ctx), skipped(ctx))))


@save
def total_undervote(ctx):
    '''
    Ballots completely made up of skipped rankings (no marks).
    '''
    return sum(undervote(ctx))


@save
def undervote(ctx):
    """
    Returns a boolean list with True indicating ballots that were undervotes (left blank)
    """
    return [True if len(x) == 0 else False for x in cleaned(ctx)]


@save
def until2rcv(ctx):
    """
    run an rcv election until there are two candidates remaining.
    This is might lead to more rounds than necessary to determine a winner.
    """

    rounds = []
    bs = [list(i) for i in cleaned(ctx)]

    while True:
        rounds.append(
            list(zip(
                # tally ballots and reorder tallies
                # using active rankings for each ballot
                *Counter(b[0] for b in bs if b).most_common()
            ))
        )
        finalists, tallies = rounds[-1]

        # finish condition
        if len(finalists) < 3:
            return rounds

        # else remove round loser from ballots, all ranking spots.
        # removing the round loser from all ranking spots now is equivalent
        # to waiting and skipping over an already-eliminated candidate
        # once they become the active ranking in a later round.
        bs = [keep(finalists[:-1], b) for b in bs]


@save
def winner(ctx):
    return rcv(ctx)[-1][0][0]


@save
def winners_consensus_value(ctx):
    '''
    The percentage of valid first round votes that rank the winner in the top 3.
    '''
    return winner_in_top_3(ctx) / first_round_active_votes(ctx)


@save
def winner_ranking(ctx):
    """
        Returns a dictionary with ranking-count key-values, with count
        indicating the number of ballots in which the winner received each
        ranking.
    """
    return Counter(
        b.index(winner(ctx)) + 1 if winner(ctx) in b else None for b in cleaned(ctx)
    )


@save
def winner_in_top_3(ctx):
    """
        Sum the counts from the ranking-count entries, where the ranking is < 4
    """
    return sum(v for k, v in winner_ranking(ctx).items() if k is not None and k < 4)


