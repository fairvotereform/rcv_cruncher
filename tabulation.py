from collections import defaultdict
from glob import glob
from gmpy2 import mpq as Fraction
from copy import deepcopy
from itertools import product, combinations
from collections import Counter


# cruncher imports
from definitions import UNDERVOTE, OVERVOTE, WRITEIN
from cache_helpers import save, tmpsave

####################################################################################################################
####################################################################################################################
####################################################################################################################
####################################################################################################################
####################################################################################################################
####################################################################################################################
####################################################################################################################
####################################################################################################################
# unresolved functions

# from crunch
@tmpsave
def number(ctx):
    return {
        ('Cambridge', 'School Committee'): 6,
        ('Cambridge', 'City Council'): 9,
        ('Minneapolis', 'BOE'): 2,
        ('Minneapolis', 'Park At Large'): 3,
    }.get((ctx['place'],ctx['office']), 1)

# from simple crunch
def number(ctx):
    if 'number' in ctx:
        return ctx['number']
    return {
        ('Cambridge', 'School Committee'): 6,
        ('Cambridge', 'City Council'): 9,
        ('Minneapolis', 'BOE'): 2,
        ('Minneapolis', 'Park At Large'): 3,
    }.get((ctx['place'],ctx['office']), 1)


# crunch
HEADLINE_STATS = [place, state, date, office, title_case_winner, blank,
    number_of_candidates, number_of_rounds, final_round_vote,
    final_round_percent, first_round_vote,
    first_round_percent, first_round_place, number_of_first_round_valid_votes,
    number_of_final_round_active_votes, blank, total, blank,
    final_round_inactive, final_round_winner_votes_over_first_round_valid,
    winners_consensus_value, condorcet, total_fully_ranked,
    ranked_multiple, first_round_undervote, first_round_overvote,
    later_round_inactive_by_overvote, later_round_inactive_by_abstention,
    later_round_inactive_by_ranking_limit, includes_duplicates, includes_skipped
]

# simple crunch
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
    top2_winner_over_40, effective_ballot_lengths
]


# crunch
@save
def seq_stv(ctx):
    ballots = deepcopy(cleaned(ctx))
    winners = []
    for _ in range(number(ctx)):
        winners.append(rcv_ballots(ballots)[-1][0][0])
        ballots = remove([], (remove(winners[-1], b) for b in ballots))
    return winners

# simple crunch
@save
def seq_stv(ctx):
    ballots = deepcopy(cleaned(ctx))
    tallies = []
    winners = []
    winners_votes = []
    last_round_votes = []
    for _ in range(number(ctx)):
        deciding_round = rcv_ballots(ballots)[-1]
        winners.append(deciding_round[0][0])
        winners_votes.append(deciding_round[1][0])
        last_round_votes.append(sum(deciding_round[1]))
        ballots = remove([], (remove(winners[-1], b) for b in ballots))
    for i,(w,v,t) in enumerate(zip(winners,winners_votes,last_round_votes)):
        print('winner {}'.format(i+1),w,str(v/float(t)*100)[:5]+'%', v,'/',t,sep='\t')
    return ''



# crunch
@tmpsave
def break_on_repeated_undervotes(ctx):
    return place(ctx) == 'Maine'

@tmpsave
def break_on_overvote(ctx):
    return place(ctx) != 'Minneapolis'


# simple crunch
@tmpsave
def break_on_repeated_undervotes(ctx):
    return False

@tmpsave
def break_on_overvote(ctx):
    return True

####################################################################################################################
####################################################################################################################
####################################################################################################################
####################################################################################################################
####################################################################################################################
####################################################################################################################
####################################################################################################################
####################################################################################################################




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


# fixme
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
def total_fully_ranked(ctx):
    '''
    The number of voters that have validly used all available rankings on the
    ballot, or that have validly ranked all non-write-in candidates.
    '''
    return sum(fully_ranked(ctx))

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
    return sum(a and b for a, b in zip(later_round_exhausted(ctx), exhausted_by_overvote(ctx)))


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
    return sum(a and b for a, b in zip(later_round_exhausted(ctx), fully_ranked(ctx)))


def includes_duplicates(ctx):
    '''
    The number of ballots that rank the same candidate more than once, or
    include more than one write in candidate.
    '''
    return any_repeat(ctx)


@save
def any_repeat(ctx):
    """
        Number of ballots that included one at least one candidate that
        received more than once ranking
    """
    return sum(v for k, v in count_duplicates(ctx).items() if k > 1)


@save
def count_duplicates(ctx):
    return Counter(max_repeats(ctx))


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

@save
def includes_skipped(ctx):
    '''
    The number of ballots that have an undervote followed by an overvote or a
    valid ranking
    '''
    return sum(skipped(ctx))


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
            if break_on_repeated_undervotes(ctx) and {elem_a, elem_b} == {UNDERVOTE}:
                break
            if break_on_overvote(ctx) and elem_a == OVERVOTE:
                break
            if elem_a not in [*result, OVERVOTE, UNDERVOTE]:
                result.append(elem_a)
        new.append(result)
    return new

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


@save
def head_to_head(ctx):
    tallies = Counter()
    for ballot in cleaned(ctx):
        nowritein = [i for i in ballot if i != WRITEIN]
        tallies.update(combinations(nowritein,2))
        tallies.update(product(set(nowritein), candidates(ctx)-set(nowritein)))
    for key in sorted(tallies):
        k0, k1 = key
        print(date(ctx),office(ctx),place(ctx),k0,k1,tallies[key],tallies[(k1,k0)],sep='\t')

def blank(ctx):
    return None



### Tabulation ###
def remove(x,l):
    return [i for i in l if i != x]

def keep(x,l):
    return [i for i in l if i in x]


# simple crunch
@save
def effective_ballot_length_str(ctx):
    """
    A list of validly ranked choices, and how many ballots had that number of
    valid choices.
    """
    return '; '.join('{}: {}'.format(a, b) for a, b in sorted(Counter(map(len, cleaned(ctx))).items()))

# crunch
@save
def effective_ballot_length(ctx):
    return Counter(len(b) for b in cleaned(ctx))



def rcv_ballots(clean_ballots):
    rounds = []
    ballots = remove([],deepcopy(clean_ballots))
    while True:
        rounds.append(list(zip(*Counter(b[0] for b in ballots).most_common())))
        finalists, tallies = rounds[-1]
        if tallies[0]*2 > sum(tallies):
            return rounds
        ballots = remove([], (keep(finalists[:-1], b) for b in ballots))


@save
def rank_and_add_borda(ctx):
    """https://voterschoose.info/wp-content/uploads/2019/04/Tustin-White-Paper.pdf"""
    c = Counter()
    for b in cleaned(ctx):
        c.update({v:1/i for i,v in enumerate(b,1)})
    return [i for i,_ in c.most_common()[:number(ctx)]]

@save
def bottom_up_stv(ctx):
    ballots = deepcopy(cleaned(ctx))
    rounds = []
    while True:
        rounds.append(list(zip(*Counter(b[0] for b in ballots).most_common())))
        finalists,_ = rounds[-1]
        if len(finalists) == number(ctx):
            return finalists
        ballots = remove([], (keep(finalists[:-1], b) for b in ballots))

@save
def stv(ctx):
    rounds = []
    bs = [(b,Fraction(1)) for b in cleaned(ctx) if b]
    threshold = int(len(bs)/(number(ctx)+1)) + 1
    winners = []
    while len(winners) != number(ctx):
        totals = defaultdict(int)
        for c,v in bs:
            totals[c[0]] += v
        ordered = sorted(totals.items(), key=lambda x:-x[1])
        rounds.append(ordered)
        names, tallies = zip(*ordered)
        if len(names) + len(winners) == number(ctx):
            winners.extend(names)
            break
        if threshold < tallies[0]:
            winners.append(names[0])
            bs = ((keep(names[1:], c),
                    v*(names[0] != c[0] or (tallies[0]-threshold)/tallies[0]))
                   for c,v in bs)
        else:
            bs = ((keep(names[:-1], c), v) for c,v in bs)
        bs = [b for b in bs if b[0]]
    return winners

@save
def in_common(ctx):
    return len(set(stv(ctx)) & set(seq_stv(ctx)))

@save
def not_in_common(ctx):
    return len(set(stv(ctx)) ^ set(seq_stv(ctx)))//2

@save
def only_seq(ctx):
    return [name_map(ctx)(i) for i in set(seq_stv(ctx)) - set(stv(ctx))]

@save
def only_reg(ctx):
    return [name_map(ctx)(i) for i in set(stv(ctx)) - set(seq_stv(ctx))]

def name_map(ctx):
    mapping = {}
    with suppress(KeyError), open(glob(ctx['chp'])[0]) as f:
        for i in f:
            parts = i.split(' ')
            if parts[0] == '.CANDIDATE':
                mapping[parts[1].strip(',')] = ' '.join(parts[2:]).replace('"','').replace('\n', '')
    if mapping:
        return lambda x: mapping[x]
    return lambda x: x

def rcv_stack(ballots):
    stack = [ballots]
    results = []
    while stack:
        ballots = stack.pop()
        finalists, tallies = map(list, zip(*Counter(b[0] for b in ballots if b).most_common()))
        if tallies[0]*2 > sum(tallies):
            results.append((finalists, tallies))
        else:
            losers = finalists[tallies.index(min(tallies)):]
            for loser in losers:
                stack.append([keep(set(finalists)-set([loser]), b) for b in ballots])
            if len(losers) > 1:
                stack.append([keep(set(finalists)-set(losers), b) for b in ballots])
    return results


def minneapolis_undervote(ctx):
    """
    Number of ballots left blank, all ranks undervoted
    """
    return effective_ballot_length(ctx).get(0, 0)

def minneapolis_total(ctx):
    """
    Number of non-blank ballots. Ballots with at least one mark (even overvote)
    """
    return total(ctx) - minneapolis_undervote(ctx)

@save
def naive_tally(ctx):
    """ Sometimes reported if only one round, only nominal 1st place rankings count"""
    return Counter(b[0] if b else None for b in ballots(ctx))


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


@save
def consensus(ctx):
    return winner_in_top_3(ctx) / (total(ctx) - undervote(ctx))

@save
def winners_first_round_share(ctx):
    return rcv(ctx)[0][1][0] / (total(ctx) - undervote(ctx))

@save
def winners_final_round_share(ctx):
    return rcv(ctx)[-1][1][0] / (total(ctx) - undervote(ctx))

@save
def rcv(ctx):
    """
        Retrieves the cleaned ballots using ctx and
        returns a list of round-by-round vote counts

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
def margin_when_2_left(ctx):
    # remove undervotes and empty ballots
    ballots = remove([],
                     (remove(UNDERVOTE, b) for b in cleaned(ctx)))
    while True:
        finalists, tallies = zip(*Counter(b[0] for b in ballots).most_common())
        if len(tallies) == 1:
            return tallies[0]
        if len(tallies) == 2:
            return tallies[0] - tallies[-1]
        ballots = remove([], (keep(finalists[:-1], b) for b in ballots))


@save
def margin_when_2_left_restruct(ctx):
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

def rcvreg(ballots):
    rounds = []
    while True:
        rounds.append(list(zip(*Counter(b[0] for b in ballots).most_common())))
        finalists, tallies = rounds[-1]
        if tallies[0]*2 > sum(tallies):
            return rounds
        ballots = remove([], (keep(finalists[:-1], b) for b in ballots))

def last5rcv(ctx):
    return rcv(ctx)[-5:]


@save
def winner(ctx):
    return rcv(ctx)[-1][0][0]

def finalists(ctx):
    return rcv(ctx)[-1][0]

@save
def first_round(ctx):
    """
        Returns a list of first non-undervote for each ballot OR
        if the ballot is empty, can also return UNDERVOTE
    """
    return [next((c for c in b if c != UNDERVOTE), UNDERVOTE)
            for b in ballots(ctx)]


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
def later_round_exhausted(ctx):
    """
        Returns bool list corresponding to each cleaned ballot.
        True when ballot contains none of the finalists AND the ballot is non-empty.
        (ensures ballot was not exhausted due to complete undervote)
        False otherwise
    """
    return [not (set(finalists(ctx)) & set(b)) and bool(b) for b in cleaned(ctx)]

@save
def total_exhausted(ctx):
    '''
    Number of ballots (including ballots made up of only undervotes or
    overvotes) that do not rank a finalist.
    '''
    return sum(exhausted(ctx))

@save #fixme
def involuntarily_exhausted(ctx):
    return [a and b for a, b in zip(fully_ranked(ctx), exhausted(ctx))]

@save
def total_involuntarily_exhausted(ctx):
    '''
    Number of validly fully ranked ballots that do not rank a finalist.
    '''
    return sum(involuntarily_exhausted(ctx))

@save
def voluntarily_exhausted(ctx):
    return [a and not b
            for a, b in zip(exhausted(ctx), involuntarily_exhausted(ctx))]

@save
def total_voluntarily_exhausted(ctx):
    '''
    Number of ballots that do not rank a finalists and aren't fully ranked.
    This number includes ballots consisting of only undervotes or overvotes.
    '''
    return sum(voluntarily_exhausted(ctx))

def margin_greater_than_all_exhausted(ctx):
    return margin_when_2_left(ctx) > total_exhausted(ctx)

@save
def exhausted_by_undervote(ctx):
    """

    """
    if break_on_repeated_undervotes(ctx):
        return sum(ex and not ex_over and has_under for ex, ex_over, has_under in
                zip(exhausted(ctx), exhausted_by_overvote(ctx), has_undervote(ctx)))
    return 0

@save
def has_undervote(ctx):
    return [UNDERVOTE in b for b in ballots(ctx)]

@save
def exhausted_by_overvote(ctx):
    """
        Returns bool list with elements corresponding to cleaned ballots.
        True if ballot contains an overvote AND became exhausted

        IF the contest uses rules that exhuast a ballot after a repeated undervote,
        then the list element is only True if the ballot became exhausted AND
        and overvote is present and it occurred before the repeated undervotes
    """
    if break_on_repeated_undervotes(ctx):
        return [ex and over < under for ex, over, under in
                zip(exhausted(ctx), overvote_ind(ctx), repeated_undervote_ind(ctx))]

    return [ex and over for ex, over in zip(exhausted(ctx), overvote(ctx))]

@save
def total_exhausted_by_overvote(ctx):
    return sum(exhausted_by_overvote(ctx))

@save
def total_exhausted_not_by_overvote(ctx):
    return sum(ex and not ov
                for ex, ov in zip(exhausted(ctx), exhausted_by_overvote(ctx)))

@save
def validly_ranked_winner(ctx):
    """
        How many ballots marked the winner in a reachable rank
        (not a rank occurring after an exhaust condition)
    """
    return sum(winner(ctx) in b for b in cleaned(ctx))

@save
def ranked_winner(ctx):
    """
        How many ballots included a non-overvote ranking for the winner
        Contrast with validly_ranked_winner
    """
    return sum(winner(ctx) in b for b in ballots(ctx))

@save
def ranked_finalist(ctx):
    return [not ex for ex in exhausted(ctx)]


@save
def losers(ctx):
    return set(candidates(ctx)) - {winner(ctx)}


def come_from_behind(ctx):
    """
    True if rcv winner is not first round leader
    """
    return winner(ctx) != rcv(ctx)[0][0][0]


@save
def candidate_combinations(ctx):
    return Counter(tuple(sorted(b)) for b in cleaned(ctx))


@save
def orderings(ctx):
    return Counter(map(tuple, cleaned(ctx))).most_common()


@save
def top2(ctx):
    return Counter(tuple(i[:2]) for i in cleaned(ctx)).most_common()


@save
def next_choice(ctx):
    c = Counter()
    for b in cleaned(ctx):
        c.update(zip([None, *b], [*b, None]))
    return c.most_common()


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
def overvote_ind(ctx):
    """
        Returns list of index values for first overvote on each ballot
        If no overvotes on ballots, list element is inf
    """
    return [b.index(OVERVOTE) if OVERVOTE in b else float('inf')
            for b in ballots(ctx)]

def two_repeated(ctx):
    """
        Number of ballots in which the candidate that received the maximum
        number of repeated rankings, received 2 repeated rankings
    """
    return count_duplicates(ctx).get(2, 0)

def three_repeated(ctx):
    """
        Number of ballots in which the candidate that received the maximum
        number of repeated rankings, received 3 repeated rankings
    """
    return count_duplicates(ctx).get(3,0)

@save
def overvote(ctx):
    return [OVERVOTE in b for b in ballots(ctx)]

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
def irregular(ctx):
    """
        Number of ballots that either had a multiple ranking, overvote,
        or a skipped undervote
    """
    return sum(map(any, zip(duplicates(ctx), overvote(ctx), skipped(ctx))))

@save
def duplicates(ctx):
    return [v > 1 for v in max_repeats(ctx)]

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
def candidates(ctx):
    cans = set()
    for b in ballots(ctx):
        cans.update(b)
    return cans - {OVERVOTE, UNDERVOTE, WRITEIN}


@save
def effective_subsets(ctx):
    c = Counter()
    for b in cleaned(ctx):
        unranked = candidates(ctx) - set(b)
        c.update((b[0], u) for u in unranked)
        for i in range(2, len(b) + 1):
            c.update(combinations(b, i))
            c.update((*b[:i], u) for u in unranked)
    return c


@save
def preference_pairs(ctx):
    return [set(product(b, candidates(ctx) - set(b))) | set(combinations(b, 2))
            for b in cleaned(ctx)]


@save
def preference_pairs_count(ctx):
    c = Counter()
    for i in preference_pairs(ctx):
        c.update(i)
    return c


@save
def all_pairs(ctx):
    return list(preference_pairs_count(ctx).keys())


@save
def undervote(ctx):
    '''
    Ballots completely made up of undervotes (no marks).
    '''
    return sum(c == UNDERVOTE for c in first_round(ctx))

@save
def ballots(ctx):
    return ctx['parser'](ctx)

@tmpsave
def write_ins(ctx):
    return 0

def ballot_length(ctx):
    return len(ballots(ctx)[0])

@save
def one_pct_cans(ctx):
    return sum(1 for i in rcv(ctx)[0][1] if i/sum(rcv(ctx)[0][1]) >= 0.01)
