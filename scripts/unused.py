

@save
def margin_when_winner_has_majority(ctx):
    last_tally = rcv(ctx)[-1][1]
    if len(last_tally) < 2:
        return last_tally[0]
    else:
        return last_tally[0] - last_tally[1]


@save
def exhausted_by_overvote(ctx):
    """
    Returns bool list with elements corresponding to cleaned ballots.
    True if ballot contains an overvote AND became exhausted

    If the contest uses rules that exhaust a ballot after a repeated skipvote,
    then the list element is only True if the ballot became exhausted AND
    and overvote is present and it occurred before the repeated skipvotes
    """

    if ctx['break_on_overvote']:

        if ctx['break_on_repeated_skipvotes']:
            ziplist = zip(exhausted(ctx),  # true if cleaned ballot did not contain finalist
                          overvote_ind(ctx),  # index of overvote in ballot, else Inf
                          repeated_skipvote_ind(ctx)  # index of start of repeated skipvote in ballot, else Inf
                          )
            return [ex and over < skip for ex, over, skip in ziplist]

        ziplist = zip(exhausted(ctx),
                      overvote(ctx)
                      )
        return [ex and over for ex, over in ziplist]

    return [False for b in cleaned(ctx)]


@save
def first_round_undervote(ctx):
    '''
    The number of ballots with absolutely no markings at all.

    Note that this is not the same as "exhausted by undervote". This is because
    some juristidictions (Maine) discard any ballot begining with two
    undervotes regardless of the rest of the content of the ballot, and call
    this ballot as exhausted by undervote.
    '''
    return sum(set(b) == {SKIPVOTE} for b in ballots(ctx))



@save
def margin_when_2_left(ctx):
    last_tally = until2rcv(ctx)[-1][1]
    if len(last_tally) < 2:
        return last_tally[0]
    else:
        return last_tally[0] - last_tally[1]


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
def naive_tally(ctx):
    """ Sometimes reported if only one round, only nominal 1st place rankings count"""
    return Counter(b[0] if b else None for b in ballots(ctx))


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
def total_exhausted_not_by_overvote(ctx):
    return sum(ex and not ov
                for ex, ov in zip(exhausted_or_undervote(ctx), exhausted_by_overvote(ctx)))

@save
def exhausted_by_skipvote(ctx):
    """
    Returns bool list with elements corresponding to ballots.
    True if ballot was exhausted due to overvote
    """
    if ctx['break_on_repeated_skipvotes']:
        ziplist = zip(
                    exhausted(ctx),  # true if ballot was not undervote and finalist is not ranked or reachable
                    exhausted_by_overvote(ctx),  # true if cause of exhausted ballot is overvote
                    repeated_skipvote_ind(ctx)  # Inf if ballot has no repeated skipvotes
        )
        return sum(ex and not ex_over and not skip == float('inf') for ex, ex_over, skip in ziplist)

    return 'na'


def first_round_percent(ctx):
    '''
    The percent of votes for the winner in the first round.
    '''
    wind = rcv(ctx)[0][0].index(winner(ctx))
    return rcv(ctx)[0][1][wind] / sum(rcv(ctx)[0][1])


@save
def effective_ballot_length(ctx):
    return Counter(len(b) for b in cleaned(ctx))


def final_round_inactive(ctx):
    '''
    The difference of first round valid votes and final round valid votes.
    '''
    return number_of_first_round_valid_votes(ctx) - number_of_final_round_active_votes(ctx)




@save
def in_common(ctx):
    return len(set(stv(ctx)) & set(seq_stv(ctx)))







@save
def rank_and_add_borda(ctx):
    """https://voterschoose.info/wp-content/uploads/2019/04/Tustin-White-Paper.pdf"""
    c = Counter()
    for b in cleaned(ctx):
        c.update({v:1/i for i,v in enumerate(b,1)})
    return [i for i,_ in c.most_common()[:number(ctx)]]




@save
def ranked_finalist(ctx):
    return [not ex for ex in exhausted(ctx)]

@save
def ranked2(ctx):
    return sum(len(b) == 2 for b in cleaned(ctx))


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
def total_skipped(ctx):
    return sum(skipped(ctx))


@save
def total_involuntarily_exhausted(ctx):
    '''
    Number of validly fully ranked ballots that do not rank a finalist.
    '''
    return sum(involuntarily_exhausted(ctx))


@save
def total_voluntarily_exhausted(ctx):
    '''
    Number of ballots that do not rank a finalists and aren't fully ranked.
    This number includes ballots consisting of only undervotes or overvotes.
    '''
    return sum(voluntarily_exhausted(ctx))


@save
def voluntarily_exhausted(ctx):
    return [a and not b
            for a, b in zip(exhausted_or_undervote(ctx), involuntarily_exhausted(ctx))]


@save
def validly_ranked_winner(ctx):
    """
        How many ballots marked the winner in a reachable rank
        (not a rank occurring after an exhaust condition)
    """
    return sum(winner(ctx) in b for b in cleaned(ctx))



@save
def later_round_exhausted(ctx):
    """
        Returns bool list corresponding to each cleaned ballot.
        True when ballot contains none of the finalists AND the ballot is non-empty.
        (ensures ballot was not exhausted due to complete undervote)
        False otherwise
    """
    return [not (set(finalists(ctx)) & set(b)) and bool(b) for b in cleaned(ctx)]


@save #fixme
def involuntarily_exhausted(ctx):
    return [a and b for a, b in zip(fully_ranked(ctx), exhausted_or_undervote(ctx))]






















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
def head_to_head(ctx):
    tallies = Counter()
    for ballot in cleaned(ctx):
        nowritein = [i for i in ballot if i != WRITEIN]
        tallies.update(combinations(nowritein,2))
        tallies.update(product(set(nowritein), candidates(ctx)-set(nowritein)))
    for key in sorted(tallies):
        k0, k1 = key
        print(date(ctx),office(ctx),place(ctx),k0,k1,tallies[key],tallies[(k1,k0)],sep='\t')



# simple crunh

# crunch








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
def margin_when_2_left_old(ctx):
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




def last5rcv(ctx):
    return rcv(ctx)[-5:]













def margin_greater_than_all_exhausted(ctx):
    return margin_when_2_left(ctx) > total_exhausted(ctx)








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
def all_pairs(ctx):
    return list(preference_pairs_count(ctx).keys())




def ballot_length(ctx):
    return len(ballots(ctx)[0])





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
def one_pct_cans(ctx):
    return sum(1 for i in rcv(ctx)[0][1] if i/sum(rcv(ctx)[0][1]) >= 0.01)



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


@save
def losers(ctx):
    return set(candidates(ctx)) - {winner(ctx)}



@save
def sequential_rcv(ctx):
    pass


@save
def stv_fractional_ballot(ctx):
    """
    Static threshold multi-winner elections with fractional surplus transfer
    """

    ctx['use_multiwinner_rounds'] = True

    rounds = []
    outcomes = []

    # select all non-empty ballots and pair each with Fraction(1)
    bs = [(b, Fraction(1)) for b in cleaned(ctx) if b]

    # set win threshold
    threshold = int(len(bs)/(ctx['num_winners']+1)) + 1

    # run rounds until enough winners are found
    round_num = 0
    num_winners = 0
    while ctx['num_winners'] == num_winners:

        round_num += 1

        # is the number of candidates remaining equal
        # to the number of winner left to elect?
        # If so, they win
        # this is necessary step when using a static threshold
        num_winners = len({i for i in outcomes if i['round_elected']})
        num_remaining = 0


        # accumulate fractional values currently held by
        # first-ranked candidate on each ballot
        totals = defaultdict(int)
        for cand_list, ballot_frac in bs:
            totals[cand_list[0]] += ballot_frac

        # sort totals dict into descending order
        ordered = sorted(totals.items(), key=lambda x: -x[1])
        rounds.append(ordered)


        # split ordered totals into two lists
        names, tallies = zip(*ordered)

        # any candidates over the threshold?
        if any([i > threshold for i in tallies]):

            looking_for_winners = True
            round_winners = []

            while looking_for_winners:

                round_winner = names[0]
                round_others = names[1:]

                # then add to contest winners list
                outcomes.append({'name': round_winner, 'round_elected': round_num,
                                'round_eliminated': None})

                # fractional surplus to transfer from each winner ballot
                surplus_percent = (tallies[0] - threshold) / tallies[0]

                # if surplus to transfer is non-zero
                if surplus_percent:

                    # which ballots had the winner on top
                    # and need to be fractionally split
                    winner_in_active_rank = [cand_list[0] == round_winner for cand_list, ballot_frac in bs]

                    # split out tuples
                    split_cand_lists, split_ballot_fracs = zip(*bs)

                    # adjust ballot fracs for winner ballots
                    new_ballot_fracs = [ballot_frac * surplus_percent if winner_active else ballot_frac
                                        for ballot_frac, winner_active in zip(split_ballot_fracs, winner_in_active_rank)]

                    # stitch cand_lists back with new ballot fracs
                    bs = list(zip(split_cand_lists, new_ballot_fracs))

                # remove winner from ballots
                bs = [(keep(round_others, cand_list), ballot_frac) for cand_list, ballot_frac in bs]

                # remove newly-empty ballots
                bs = [b for b in bs if b[0]]

                # update winner list for round
                round_winners.append(round_winner)

                # identify next round-winner ordering
                filtered_ordering = [(cand, cand_tally)
                                    for cand, cand_tally in ordered if cand not in round_winners]

                # any candidates left?
                if filtered_ordering:

                    names, tallies = zip(*filtered_ordering)

                    # if there are no more candidates over the threshold, then move to the next round
                    if any([i > threshold for i in tallies]) is False:
                        looking_for_winners = False
                else:

                    # no candidates left, exit loop
                    looking_for_winners = False

                # if contest setting specifies only one winner per round, then move to next round
                if ctx['use_multiwinner_rounds'] is False:
                    looking_for_winners = False

        else:  # no winner

            # remove candidate from ballots that received the lowest count
            loser_count = min(tallies)

            # in case of tied losers, randomly choose one to eliminate
            round_loser = choice([cand for cand, cand_tally in ordered if cand_tally == loser_count])
            outcomes.append({'name': round_loser, 'round_elected': None,
                             'round_eliminated': round_num})

            # remove loser from
            bs = ((remove(round_loser, cand_list), ballot_frac) for cand_list, ballot_frac in bs)

            # remove newly-empty ballots
            bs = [b for b in bs if b[0]]

    return rounds, outcomes


@save
def stv_whole_ballot(ctx):
    pass


@save
def rcv_multiWinner_thresh15(ctx):
    """
    Runs a multi winner RCV contest with whole ballot transfer. Cease runoffs when all active candidates
    are above 15% of the rounds tally.

    Return:
        rounds_trimmed (list of lists) - each list represents a counting round and contains two tuples.
        first tuple is candidates names and second is vote counts. Both are sorted to reflect descending vote order.
        Each round only contains candidates that achieved votes in that round.

        rounds_full (list of lists) - each list represents a counting round and contains two tuples.
        first tuple is candidates names and second is vote counts. Both are sorted to reflect descending vote order.
        Each round contains all candidates.

        transfers (list of dicts) - each dict has candidates as keys and round vote transfer counts as values.
        Dicts are in round order.

        cand_outcomes (list of dicts) - each dict is {name: cand, round_eliminated: 1, round_elected: None}
    """

    # just filter results from until2rcv
    rounds_trimmed, rounds_full, transfers, _ = deepcopy(until2rcv(ctx))

    # and create fresh candidate outcomes
    candidate_set = candidates(ctx)
    cand_outcomes = {cand: {'name': cand, 'round_eliminated': None, 'round_elected': None} for cand in candidate_set}

    # find round where a candidate has over 50% of active round votes
    rounds_slice_idx = 0
    done = False
    while not done:

        # get round info
        current_round_trimmed = rounds_trimmed[rounds_slice_idx]
        current_round_transfer = transfers[rounds_slice_idx]
        rounds_slice_idx += 1

        # check for finish condition
        round_finalists, round_tally = current_round_trimmed
        round_total = sum(round_tally)

        # does everyone in the round have at least 15% of round total
        # might need to adjust rounding here
        if all([(i/round_total) >= 0.15 for i in round_tally]):

            # update winner in cand_outcomes
            for cand in round_finalists:
                cand_outcomes[cand]['round_elected'] = rounds_slice_idx

            # update flag
            done = True

        else:
            # who lost this round (should be the only one with negative round transfer)?
            # update in candidate outcomes
            round_loser = [key for key, value in current_round_transfer.items() if value < 0]
            if len(round_loser) > 1:
                print('should only be one round loser with eliminated votes per round in single winner rcv. debug')
                exit(1)
            cand_outcomes[round_loser[0]]['round_eliminated'] = rounds_slice_idx

    # unnest candidate outcomes values
    cand_outcomes = [values for key, values in cand_outcomes.items()]

    return rounds_trimmed[0:rounds_slice_idx], rounds_full[0:rounds_slice_idx], \
           transfers[0:rounds_slice_idx], cand_outcomes



@save
def rcv_single_winner(ctx):
    """
    Runs a single winner RCV contest.

    Return:
        rounds_trimmed (list of lists) - each list represents a counting round and contains two tuples.
        first tuple is candidates names and second is vote counts. Both are sorted to reflect descending vote order.
        Each round only contains candidates that achieved votes in that round.

        rounds_full (list of lists) - each list represents a counting round and contains two tuples.
        first tuple is candidates names and second is vote counts. Both are sorted to reflect descending vote order.
        Each round contains all candidates.

        transfers (list of dicts) - each dict has candidates as keys and round vote transfer counts as values.
        Dicts are in round order.

        cand_outcomes (list of dicts) - each dict is {name: cand, round_eliminated: 1, round_elected: None}
    """

    # just filter results from until2rcv
    rounds_trimmed, rounds_full, transfers, _ = deepcopy(until2rcv(ctx))

    # and create fresh candidate outcomes
    candidate_set = candidates(ctx)
    cand_outcomes = {cand: {'name': cand, 'round_eliminated': None, 'round_elected': None} for cand in candidate_set}

    # find round where a candidate has over 50% of active round votes
    rounds_slice_idx = 0
    done = False
    while not done:

        # get round info
        current_round_trimmed = rounds_trimmed[rounds_slice_idx]
        current_round_transfer = transfers[rounds_slice_idx]
        rounds_slice_idx += 1

        # check for finish condition
        round_finalists, round_tally = current_round_trimmed
        round_leader = round_finalists[0]
        round_total = sum(round_tally)

        # does round leader have the majority?
        # might need to adjust rounding here
        if round_tally[0] * 2 > round_total:
            # update winner in cand_outcomes
            cand_outcomes[round_leader]['round_elected'] = rounds_slice_idx

            # update remaining round candidates as losing in this round
            for cand in cand_outcomes:
                if cand != round_leader and cand_outcomes[cand]['round_eliminated'] is None:
                    cand_outcomes[cand]['round_eliminated'] = rounds_slice_idx

            # update flag
            done = True

        else:
            # who lost this round (should be the only one with negative round transfer)?
            # update in candidate outcomes
            round_loser = [key for key, value in current_round_transfer.items() if value < 0]
            if len(round_loser) > 1:
                print('should only be one round loser with eliminated votes per round in single winner rcv. debug')
                exit(1)
            cand_outcomes[round_loser[0]]['round_eliminated'] = rounds_slice_idx

    # unnest candidate outcomes values
    cand_outcomes = [values for key, values in cand_outcomes.items()]

    return rounds_trimmed[0:rounds_slice_idx], rounds_full[0:rounds_slice_idx], \
           transfers[0:rounds_slice_idx], cand_outcomes


@save
def until2rcv(ctx):
    """
    Run an rcv election until there are two candidates remaining.
    This is might lead to more rounds than necessary to determine a winner.

    Return:
        rounds_trimmed (list of lists) - each list represents a counting round and contains two tuples.
        first tuple is candidates names and second is vote counts. Both are sorted to reflect descending vote order.
        Each round only contains candidates that achieved votes in that round.

        rounds_full (list of lists) - each list represents a counting round and contains two tuples.
        first tuple is candidates names and second is vote counts. Both are sorted to reflect descending vote order.
        Each round contains all candidates.

        transfers (list of dicts) - each dict has candidates as keys and round vote transfer counts as values.
        Dicts are in round order.

        cand_outcomes (list of dicts) - each dict is {name: cand, round_eliminated: 1, round_elected: None}
    """

    # inputs
    candidate_set = candidates(ctx)
    cleaned_dict = deepcopy(cleaned(ctx))
    bs = [{'ranks': ranks, 'weight': weight}
          for ranks, weight in zip(cleaned_dict['ranks'], cleaned_dict['weight'])]

    # outputs
    rounds_trimmed = []
    rounds_full = []
    transfers = []
    cand_outcomes = {cand: {'name': cand, 'round_eliminated': None, 'round_elected': None} for cand in candidate_set}

    # other loop variables
    all_losers = []
    round_num = 0
    n_finalists = float('inf')

    while n_finalists > 2:

        round_num += 1

        # round results
        # tally ballots and reorder tallies
        # using active rankings for each ballot,
        # skipping empty ballots
        active_round_candidates = set([b['ranks'][0] for b in bs if b['ranks']])
        choices = Counter({cand: 0 for cand in active_round_candidates})
        for b in bs:
            if b['ranks']:
                choices[b['ranks'][0]] += b['weight']

        # sort round tallies
        round_results = list(zip(*choices.most_common()))
        # split round results into two tuples (index-matched)
        round_finalists, round_tallies = round_results
        n_finalists = len(round_finalists)

        # one the first round, eliminate any candidates with zero votes right away
        if round_num == 1:
            all_losers += [cand for cand in candidate_set if cand not in round_finalists]
            for cand in all_losers:
                # remove losers from ballots
                bs = [{'ranks': remove(cand, b['ranks']), 'weight': b['weight']} for b in bs]
                # update candidate outcomes
                cand_outcomes[cand]['round_eliminated'] = round_num

        # add in loser/no-vote candidates for full round record
        finalists_full = list(round_finalists) + all_losers
        tallies_full = list(round_tallies) + ([0] * len(all_losers))

        # find round loser
        loser_count = min(round_tallies)
        # in case of tied losers, randomly choose one to eliminate
        round_loser = choice([cand for cand, cand_tally in zip(round_finalists, round_tallies)
                              if cand_tally == loser_count])
        # update candidate outcome
        cand_outcomes[round_loser]['round_eliminated'] = round_num

        # calculate transfer from loser - find loser ballots
        round_loser_ballots = [b for b in bs if b['ranks'] and b['ranks'][0] == round_loser]
        # count distribution from loser to other candidates and exhaustion
        round_transfer = Counter({cand: 0 for cand in candidate_set.union({'exhaust'})})
        for b in round_loser_ballots:
            if len(b['ranks']) > 1:
                round_transfer[b['ranks'][1]] += b['weight']
            else:
                round_transfer['exhaust'] += b['weight']

        # record ballot loss from loser
        round_transfer[round_loser] = sum([b['weight'] for b in round_loser_ballots]) * -1

        # remove round loser from ballots, all ranking spots.
        # removing the round loser from all ranking spots now is equivalent
        # to waiting and skipping over an already-eliminated candidate
        # once they become the active ranking in a later round.
        bs = [{'ranks': remove(round_loser, b['ranks']), 'weight': b['weight']} for b in bs]

        # append round info to list
        transfers.append(round_transfer)
        all_losers.append(round_loser)
        rounds_trimmed.append(round_results)
        rounds_full.append([tuple(finalists_full), tuple(tallies_full)])

    # update winner
    cand_outcomes[round_finalists[0]]['round_elected'] = round_num

    # unnest candidate outcomes values
    cand_outcomes = [values for key, values in cand_outcomes.items()]

    # final_weights
    final_weights = [b['weight'] for b in bs]

    return rounds_trimmed, rounds_full, transfers, cand_outcomes, final_weights

