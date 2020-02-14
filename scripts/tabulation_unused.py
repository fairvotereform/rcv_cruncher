def first_round_percent(ctx):
    '''
    The percent of votes for the winner in the first round.
    '''
    wind = rcv(ctx)[0][0].index(winner(ctx))
    return rcv(ctx)[0][1][wind] / sum(rcv(ctx)[0][1])






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



