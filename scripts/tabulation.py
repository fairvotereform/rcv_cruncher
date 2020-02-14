from collections import defaultdict
from glob import glob
from gmpy2 import mpq as Fraction
from copy import deepcopy
from itertools import product, combinations
from collections import Counter


# cruncher imports
from definitions import UNDERVOTE, OVERVOTE, WRITEIN
from cache_helpers import save, tmpsave


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

def remove(x,l):
    return [i for i in l if i != x]

def keep(x,l):
    return [i for i in l if i in x]



def stats_func_list():

    STATS = [title_case_winner,                     number_of_candidates,
             number_of_rounds,                      final_round_vote,
             final_round_percent,                   first_round_vote,
             first_round_percent,                   first_round_place,
             number_of_first_round_valid_votes,     number_of_final_round_active_votes,
             total,                                 final_round_winner_votes_over_first_round_valid,
             final_round_inactive,                  winners_consensus_value,
             condorcet,                             total_fully_ranked,
             ranked_multiple,                       first_round_undervote,
             first_round_overvote,                  later_round_inactive_by_overvote,
             later_round_inactive_by_abstention,    later_round_inactive_by_ranking_limit,
             includes_duplicates,                   includes_skipped,
             top2_winners_vote_increased,           top2_winners_fraction,
             top2_majority,                         top2_winner_over_40,
             effective_ballot_length_str,           undervote,
             total_overvote,                        total_exhausted_by_overvote,
             ranked2,                               ranked_winner,
             two_repeated,                          three_repeated,
             total_skipped,                         irregular,
             total_exhausted,                       total_exhausted_not_by_overvote,
             total_involuntarily_exhausted,
             minneapolis_undervote,                 minneapolis_total,
             total_voluntarily_exhausted,           come_from_behind,
             number_of_rounds,                      finalists,
             winner,                                exhausted_by_undervote,
             naive_tally,                           candidates,
             count_duplicates,                      any_repeat,
             validly_ranked_winner,                 margin_when_2_left,
             margin_when_winner_has_majority]

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
    return cans - {OVERVOTE, UNDERVOTE, WRITEIN}


@save
def cleaned(ctx):
    """
        retrieve ballots (list of lists, each containing candidate names in
        rank order, also write-ins marked with WRITEIN constant, and OVERVOTES and
        UNDERVOTES marked with their respective constants)

        For each ballot, return a cleaned version that has pre-skipped
        undervoted and overvoted rankings and only includes one ranking
        per candidate (the highest ranking for that candidate).

        Additionally, each ballot may be cut short depending on the
        -break_on_repeated_undervotes- and -break_on_overvote- settings for
        a contest.

        returns: list of cleaned ballot-lists
    """
    new = []
    for b in ballots(ctx):
        result = []
        # look at successive pairs of rankings - zip list with itself offset by 1
        for elem_a, elem_b in zip(b, b[1:]+[None]):
            if ctx['break_on_repeated_undervotes'] and {elem_a, elem_b} == {UNDERVOTE}:
                break
            if ctx['break_on_overvote'] and elem_a == OVERVOTE:
                break
            if elem_a not in [*result, OVERVOTE, UNDERVOTE]:
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
    return Counter(max_repeats(ctx))


@save
def duplicates(ctx):
    return [v > 1 for v in max_repeats(ctx)]


@save
def effective_ballot_length(ctx):
    return Counter(len(b) for b in cleaned(ctx))


@save
def effective_ballot_length_str(ctx):
    """
    A list of validly ranked choices, and how many ballots had that number of
    valid choices.
    """
    return '; '.join('{}: {}'.format(a, b) for a, b in sorted(Counter(map(len, cleaned(ctx))).items()))


### TODO: exhausted should not include straight undervotes nor
### per Drew
@save
def exhausted(ctx):
    """
        Returns bool list corresponding to each cleaned ballot.
        True when ballot contains none of the finalists
        False otherwise
    """
    return [not set(finalists(ctx)) & set(b) for b in cleaned(ctx)]


@save
def exhausted_by_overvote(ctx):
    """
        Returns bool list with elements corresponding to cleaned ballots.
        True if ballot contains an overvote AND became exhausted

        IF the contest uses rules that exhaust a ballot after a repeated undervote,
        then the list element is only True if the ballot became exhausted AND
        and overvote is present and it occurred before the repeated undervotes
    """
    if ctx['break_on_repeated_undervotes']:
        return [ex and over < under for ex, over, under in
                zip(exhausted(ctx), overvote_ind(ctx), repeated_undervote_ind(ctx))]

    return [ex and over for ex, over in zip(exhausted(ctx), overvote(ctx))]


@save
def exhausted_by_undervote(ctx):
    """

    """
    if ctx['break_on_repeated_undervotes']:
        return sum(ex and not ex_over and has_under for ex, ex_over, has_under in
                zip(exhausted(ctx), exhausted_by_overvote(ctx), has_undervote(ctx)))
    return 0


@save
def first_round(ctx):
    """
        Returns a list of first non-undervote for each ballot OR
        if the ballot is empty, can also return UNDERVOTE
    """
    return [next((c for c in b if c != UNDERVOTE), UNDERVOTE)
            for b in ballots(ctx)]


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


def first_round_place(ctx):
    '''
    In terms of first round votes, what place the eventual winner came in.
    '''
    return rcv(ctx)[0][0].index(winner(ctx)) + 1

def first_round_percent(ctx):
    '''
    The percent of votes for the winner in the first round.
    '''
    wind = rcv(ctx)[0][0].index(winner(ctx))
    return rcv(ctx)[0][1][wind] / sum(rcv(ctx)[0][1])

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


def first_round_vote(ctx):
    '''
    The number of votes for the winner in the first round.
    '''
    wind = rcv(ctx)[0][0].index(winner(ctx))
    return rcv(ctx)[0][1][wind]


def finalists(ctx):
    return rcv(ctx)[-1][0]


def final_round_inactive(ctx):
    '''
    The difference of first round valid votes and final round valid votes.
    '''
    return number_of_first_round_valid_votes(ctx) - number_of_final_round_active_votes(ctx)


def final_round_percent(ctx):
    '''
    The percent of votes for the winner in the final round. The final round is
    the first round where the winner receives a majority of the non-exhausted
    votes.
    '''
    return rcv(ctx)[-1][1][0] / sum(rcv(ctx)[-1][1])


def final_round_vote(ctx):
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
    return final_round_vote(ctx) / number_of_first_round_valid_votes(ctx)


@save
def fully_ranked(ctx):
    """
        Returns a list of bools with each item corresponding to a ballot.
        True indicates a fully ranked ballot.

        Fully ranked here means either the cleaned ballot contains the
        full set of candidates OR the raw and cleaned ballot are of the same length
        (this second condition is likely to account for limited rank voting systems)

        Note: cleaned ballots already should have undervotes, overvotes, and
        repeated rankings given to a single candidate all removed
    """
    return [len(b) == len(a) or set(b) >= candidates(ctx)
            for a, b in zip(ballots(ctx), cleaned(ctx))]


@save
def has_undervote(ctx):
    return [UNDERVOTE in b for b in ballots(ctx)]


def includes_duplicates(ctx):
    '''
    The number of ballots that rank the same candidate more than once, or
    include more than one write in candidate.
    '''
    return any_repeat(ctx)


@save
def includes_skipped(ctx):
    '''
    The number of ballots that have an undervote followed by an overvote or a
    valid ranking
    '''
    return sum(skipped(ctx))


@save
def irregular(ctx):
    """
        Number of ballots that either had a multiple ranking, overvote,
        or a skipped undervote
    """
    return sum(map(any, zip(duplicates(ctx), overvote(ctx), skipped(ctx))))


@save #fixme
def involuntarily_exhausted(ctx):
    return [a and b for a, b in zip(fully_ranked(ctx), exhausted(ctx))]


@save
def later_round_exhausted(ctx):
    """
        Returns bool list corresponding to each cleaned ballot.
        True when ballot contains none of the finalists AND the ballot is non-empty.
        (ensures ballot was not exhausted due to complete undervote)
        False otherwise
    """
    return [not (set(finalists(ctx)) & set(b)) and bool(b) for b in cleaned(ctx)]


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
def later_round_inactive_by_overvote(ctx):
    '''
    The number of ballots that were discarded after the first round due to an
    overvote.

    Note that Minneapolis doesn't discard overvote ballots, it simply skips over
    the overvote.
    '''
    return sum(a and b for a, b in zip(later_round_exhausted(ctx), exhausted_by_overvote(ctx)))


@save
def later_round_inactive_by_ranking_limit(ctx):
    '''
    The number of ballots that validly used every ranking, but didn't rank any
    candidate that appeared in the final round.
    '''
    return sum(a and b for a, b in zip(later_round_exhausted(ctx), fully_ranked(ctx)))


@save
def losers(ctx):
    return set(candidates(ctx)) - {winner(ctx)}


@save
def margin_when_2_left(ctx):
    last_tally = until2rcv(ctx)[-1][1]
    if len(last_tally) < 2:
        return last_tally[0]
    else:
        return last_tally[0] - last_tally[1]


@save
def margin_when_winner_has_majority(ctx):
    last_tally = rcv(ctx)[-1][1]
    if len(last_tally) < 2:
        return last_tally[0]
    else:
        return last_tally[0] - last_tally[1]


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
    return [max(0, 0, *map(b.count, set(b) - {UNDERVOTE, OVERVOTE}))
            for b in ballots(ctx)]


def minneapolis_total(ctx):
    """
    Number of non-blank ballots. Ballots with at least one mark (even overvote)
    """
    return total(ctx) - minneapolis_undervote(ctx)


def minneapolis_undervote(ctx):
    """
    Number of ballots left blank, all ranks undervoted
    """
    return effective_ballot_length(ctx).get(0, 0)


@save
def naive_tally(ctx):
    """ Sometimes reported if only one round, only nominal 1st place rankings count"""
    return Counter(b[0] if b else None for b in ballots(ctx))


# fixme
def number_of_candidates(ctx):
    '''
    The number of non-candidates on the ballot, not including write-ins.
    '''
    return len(candidates(ctx))


def number_of_final_round_active_votes(ctx):
    '''
    The number of votes that were awarded to any candidate in the final round.
    '''
    return sum(rcv(ctx)[-1][1])


def number_of_first_round_valid_votes(ctx):
    '''
    The number of votes that were awarded to any candidate in the first round.
    '''
    return sum(rcv(ctx)[0][1])


def number_of_rounds(ctx):
    '''
    The number of rounds it takes for one candidate (the winner) to receive
    the  majority of the non-exhausted votes. This number includes the
    round in which the winner receives the majority of the non-exhausted votes.
    This is based on a tabulator that doesn't eliminate more than one declared
    candidate per round.
    '''
    return len(rcv(ctx))


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
def ranked2(ctx):
    return sum(len(b) == 2 for b in cleaned(ctx))


@save
def ranked_multiple(ctx):
    '''
    The number of voters that validly use more than one ranking.
    '''
    return sum(len(b) > 1 for b in cleaned(ctx))


@save
def ranked_winner(ctx):
    """
        How many ballots included a non-overvote ranking for the winner
        Contrast with validly_ranked_winner
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
def repeated_undervote_ind(ctx):
    """
        return list with index from each ballot where the undervotes start repeating,
        if no repeated undervotes set list element to inf

        note:
        repeated undervotes are only counted if non-undervotes occur after them. this
        prevents incompletely ranked ballots from being counted as having repeated undervotes
    """

    rs = []

    for b in ballots(ctx):

        rs.append(float('inf'))

        # pair up successive rankings on ballot
        z = list(zip(b, b[1:]))
        uu = (UNDERVOTE, UNDERVOTE)

        # if repeated undervote on the ballot
        if uu in z:
            occurance = z.index(uu)

            # start at second undervote in the pair
            # and loop until a non-undervote is found
            # only then record this ballot as having a
            # repeated undervote
            for c in b[occurance+1:]:
                if c != UNDERVOTE:
                    rs[-1] = occurance
                    break
    return rs


@save
def skipped(ctx):
    """
        {UNDERVOTE} & {x} - {y}
        this checks that x == UNDERVOTE and that y then != UNDERVOTE
        (the y check is important to know whether or not the ballot is not
        fully ranked)
    """
    return [any({UNDERVOTE} & {x} - {y} for x, y in zip(b, b[1:]))
            for b in ballots(ctx)]


def three_repeated(ctx):
    """
        Number of ballots in which the candidate that received the maximum
        number of repeated rankings, received 3 repeated rankings
    """
    return count_duplicates(ctx).get(3,0)


@save
def title_case_winner(ctx):
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
def top2_majority(ctx):
    """
    If you run an RCV contest until there are two or fewer candidates left,
    Does the winner receive over half the votes that cast validly ranked at
    least one candidate?
    """
    return top2_winners_fraction(ctx) > 0.5


@save
def top2_winners_fraction(ctx):
    """
    If you run an RCV contest until there are two or fewer candidates left,
    what fraction of the votes that cast validly ranked at least one candidate
    does the winner eventually receive?
    """
    return until2rcv(ctx)[-1][1][0]/float(sum(until2rcv(ctx)[0][1]))


@save
def top2_winner_over_40(ctx):
    """
    If you run an RCV contest until there are two or fewer candidates left,
    Does the winner receive over 40% of the votes that cast validly ranked at
    least one candidate?
    """
    return top2_winners_fraction(ctx) > 0.4


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
def total(ctx):
    '''
    This includes ballots with no marks.
    '''
    return len(ballots(ctx))


@save
def total_exhausted(ctx):
    '''
    Number of ballots (including ballots made up of only undervotes or
    overvotes) that do not rank a finalist.
    '''
    return sum(exhausted(ctx))


@save
def total_exhausted_by_overvote(ctx):
    return sum(exhausted_by_overvote(ctx))


@save
def total_exhausted_not_by_overvote(ctx):
    return sum(ex and not ov
                for ex, ov in zip(exhausted(ctx), exhausted_by_overvote(ctx)))


@save
def total_fully_ranked(ctx):
    '''
    The number of voters that have validly used all available rankings on the
    ballot, or that have validly ranked all non-write-in candidates.
    '''
    return sum(fully_ranked(ctx))


@save
def total_involuntarily_exhausted(ctx):
    '''
    Number of validly fully ranked ballots that do not rank a finalist.
    '''
    return sum(involuntarily_exhausted(ctx))


@save
def total_overvote(ctx):
    '''
    Number of ballots with at least one overvote.
    '''
    return sum(overvote(ctx))


@save
def total_skipped(ctx):
    return sum(skipped(ctx))


@save
def total_voluntarily_exhausted(ctx):
    '''
    Number of ballots that do not rank a finalists and aren't fully ranked.
    This number includes ballots consisting of only undervotes or overvotes.
    '''
    return sum(voluntarily_exhausted(ctx))


def two_repeated(ctx):
    """
        Number of ballots in which the candidate that received the maximum
        number of repeated rankings, received 2 repeated rankings
    """
    return count_duplicates(ctx).get(2, 0)


@save
def undervote(ctx):
    '''
    Ballots completely made up of undervotes (no marks).
    '''
    return sum(c == UNDERVOTE for c in first_round(ctx))


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
def validly_ranked_winner(ctx):
    """
        How many ballots marked the winner in a reachable rank
        (not a rank occurring after an exhaust condition)
    """
    return sum(winner(ctx) in b for b in cleaned(ctx))


@save
def voluntarily_exhausted(ctx):
    return [a and not b
            for a, b in zip(exhausted(ctx), involuntarily_exhausted(ctx))]


@save
def winner(ctx):
    return rcv(ctx)[-1][0][0]


@save
def winners_consensus_value(ctx):
    '''
    The percentage of valid first round votes that rank the winner in the top 3.
    '''
    return winner_in_top_3(ctx) / number_of_first_round_valid_votes(ctx)


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


