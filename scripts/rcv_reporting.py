
# package imports
from collections import Counter, defaultdict

# cruncher imports
from .definitions import SKIPPEDRANK, OVERVOTE, isInf, WRITEIN, NOT_EXHAUSTED, EXHAUSTED_BY_OVERVOTE, \
    EXHAUSTED_BY_REPEATED_SKIPVOTE, EXHAUSTED_BY_RANK_LIMIT, EXHAUSTED_BY_ABSTENTION, UNDERVOTE
from .cache_helpers import save
from .misc_tabulation import ballots, cleaned, candidates_no_writeIns, condorcet_tables, candidates


class RCV_Reporting:
    """
    Mixin containing all reporting stats. Can be overriden by any rcv variant.
    """

    ####################
    # STATS LISTS

    def single_winner_stats(self):
        return [
            self.contest_name,
            self.place,
            self.state,
            self.date,
            self.office,
            self.rcv_type,
            self.num_winners,
            self.unique_id,
            self.contest_winner,
            self.number_of_candidates,
            self.number_of_rounds,
            self.final_round_winner_vote,
            self.final_round_winner_percent,
            self.final_round_active_votes,
            self.first_round_winner_vote,
            self.first_round_winner_percent,
            self.first_round_active_votes,
            self.first_round_winner_place,
            self.final_round_winner_votes_over_first_round_valid,
            self.winners_consensus_value,
            self.condorcet,
            self.come_from_behind,
            self.effective_ballot_length,
            self.first_round_overvote,
            self.ranked_single,
            self.ranked_multiple,
            self.total_fully_ranked,
            self.ranked_winner,
            self.includes_duplicate_ranking,
            self.includes_skipped_ranking,
            self.total_irregular,
            self.total_ballots,
            self.total_ballots_with_overvote,
            self.total_undervote,
            self.total_exhausted,
            self.total_exhausted_by_overvote,
            self.total_exhausted_by_skipped_rankings,
            self.total_exhausted_by_abstention,
            self.total_exhausted_by_rank_limit]

    def multi_winner_stats(self):
        return [
            self.contest_name,
            self.place,
            self.state,
            self.date,
            self.office,
            self.rcv_type,
            self.num_winners,
            self.unique_id,
            self.win_threshold,
            self.number_of_candidates,
            self.number_of_rounds,
            self.winners_consensus_value,
            self.total_ballots,
            self.first_round_active_votes,
            self.final_round_active_votes,
            self.total_fully_ranked,
            self.ranked_single,
            self.ranked_multiple,
            self.total_undervote,
            self.first_round_overvote,
            self.total_ballots_with_overvote,
            self.total_exhausted,
            self.total_exhausted_by_overvote,
            self.total_exhausted_by_skipped_rankings,
            self.total_exhausted_by_abstention,
            self.total_exhausted_by_rank_limit,
            self.includes_duplicate_ranking,
            self.includes_skipped_ranking,
            self.total_irregular]

    ####################
    # CONTEST INFO

    def contest_name(self):
        return self.ctx['contest']

    def place(self):
        return self.ctx['place']

    def state(self):
        return self.ctx['state']

    def date(self):
        return self.ctx['data']

    def office(self):
        return self.ctx['office']

    def rcv_type(self):
        return self.ctx['rcv_type'].__name__

    # def num_winners(self):
    #     return self.ctx['num_winners']

    def unique_id(self):
        return self.ctx['unique_id']

    ####################
    # OUTCOME STATS

    def contest_winner(self):
        '''
        The winner(s) of the election.
        '''
        # Horrible Hack!
        # no mapping file for the 2006 Burlington Mayoral Race, so hard coded here:
        # if ctx['place'] == 'Burlington' and ctx['date'] == '2006':
        #     return 'Bob Kiss'
        return ", ".join([str(w).title() for w in self.winner()])

    def condorcet(self, tabulation_num=1):
        '''
        Is the winner the condorcet winner?
        The condorcet winner is the candidate that would win a 1-on-1 election versus
        any other candidate in the election. Note that this calculation depends on
        jurisdiction dependant rule variations.

        In the case of multi-winner elections, this result will only pertain to the first candidate elected.
        '''

        if len(candidates(self.ctx)) == 1:
            return "Yes"

        winner = self.tabulation_winner(tabulation_num=tabulation_num)[0]
        losers = [cand for cand in candidates(self.ctx) if cand != winner]

        net = Counter()
        for b in cleaned(self.ctx)['ranks']:
            for loser in losers:

                # does winner or loser appear first on this ballot?
                ballot_contrib = 0
                for mark in b:
                    if mark == winner:
                        ballot_contrib = 1
                        break
                    if mark == loser:
                        ballot_contrib = -1
                        break

                # accumulate
                net.update({loser: ballot_contrib})

        # any negative net values indicate a head-to-head where contest winner loses
        if min(net.values()) > 0:
            return "Yes"
        else:
            return "No"

    def come_from_behind(self, tabulation_range=range(1, 2)):
        """
        "yes" if rcv winner is not first round leader, else "no"

        In the case of multi-winner elections, this result will only pertain to the first candidate elected.
        """
        res = []
        for tabulation_num in tabulation_range:
            if self.tabulation_winner(tabulation_num=tabulation_num)[0] != \
                    self.get_round_trimmed_tally_tuple(1, tabulation_num=tabulation_num)[0][0]:
                res.append("Yes")
            else:
                res.append("No")
        return ", ".join(res)

    def _final_round_active_votes(self, tabulation_num=1):
        n_rounds = self.n_rounds(tabulation_num=tabulation_num)
        tally_dict = self.get_round_full_tally_dict(n_rounds, tabulation_num=tabulation_num)
        return float(sum(tally_dict.values()))

    def final_round_active_votes(self, tabulation_range=range(1, 2)):
        '''
        The number of votes that were awarded to any candidate in the final round. (weighted)
        '''
        return ", ".join([str(self._final_round_active_votes(tabulation_num=i)) for i in tabulation_range])

    def _first_round_active_votes(self, tabulation_num=1):
        tally_dict = self.get_round_full_tally_dict(1, tabulation_num=tabulation_num)
        return float(sum(tally_dict.values()))

    def first_round_active_votes(self, tabulation_range=range(1, 2)):
        '''
        The number of votes that were awarded to any candidate in the first round. (weighted)
        '''
        return ", ".join([str(self._first_round_active_votes(tabulation_num=i)) for i in tabulation_range])

    def _final_round_winner_percent(self, tabulation_num=1):
        n_rounds = self.n_rounds(tabulation_num=tabulation_num)
        tally_dict = self.get_round_full_tally_dict(n_rounds, tabulation_num=tabulation_num)
        winner = self.tabulation_winner(tabulation_num=tabulation_num)
        return float(tally_dict[winner[0]] / sum(tally_dict.values()))

    def final_round_winner_percent(self, tabulation_range=range(1, 2)):
        '''
        The percent of votes for the winner in the final round.
        If more than one winner, return the final round count for the first winner elected. (weighted)
        '''
        return ", ".join([str(self._final_round_winner_percent(tabulation_num=i)) for i in tabulation_range])

    def _final_round_winner_vote(self, tabulation_num=1):
        '''
        The number of votes for the winner in the final round.
        If more than one winner, return the final round count for the first winner elected. (weighted)
        '''
        n_rounds = self.n_rounds(tabulation_num=tabulation_num)
        tally_dict = self.get_round_full_tally_dict(n_rounds, tabulation_num=tabulation_num)
        winner = self.tabulation_winner(tabulation_num=tabulation_num)
        return float(tally_dict[winner[0]])

    def final_round_winner_vote(self, tabulation_range=range(1, 2)):
        '''
        The percent of votes for the winner in the final round.
        If more than one winner, return the final round count for the first winner elected. (weighted)
        '''
        return ", ".join([str(self._final_round_winner_vote(tabulation_num=i)) for i in tabulation_range])

    def final_round_winner_votes_over_first_round_valid(self, tabulation_num=1):
        '''
        The number of votes the winner receives in the final round divided by the
        number of valid votes in the first round.

        If more than one winner, return the final round count for the first winner elected. (weighted)
        '''
        return float(self.final_round_winner_vote(tabulation_num=tabulation_num) /
                     self.first_round_active_votes(tabulation_num=tabulation_num))

    def first_round_winner_place(self, tabulation_num=1):
        '''
        In terms of first round votes, what place the eventual winner came in.
        In the case of multi-winner elections, this result will only pertain to the first candidate elected.
        '''
        winner = self.tabulation_winner(tabulation_num=tabulation_num)
        tally_tuple = self.get_round_trimmed_tally_tuple(1, tabulation_num=tabulation_num)
        return tally_tuple[0].index(winner[0]) + 1

    def first_round_winner_percent(self, tabulation_num=1):
        '''
        The percent of votes for the winner in the first round.
        In the case of multi-winner elections, this result will only pertain to the first candidate elected. (weighted)
        '''
        winner = self.tabulation_winner(tabulation_num=tabulation_num)
        tally_tuple = self.get_round_trimmed_tally_tuple(1, tabulation_num=tabulation_num)
        return float(tally_tuple[winner[0]] / sum(tally_tuple.values()))

    def first_round_winner_vote(self, tabulation_num=1):
        '''
        The number of votes for the winner in the first round.
        In the case of multi-winner elections, this result will only pertain to the first candidate elected. (weighted)
        '''
        winner = self.tabulation_winner(tabulation_num=tabulation_num)
        tally_tuple = self.get_round_trimmed_tally_tuple(1, tabulation_num=tabulation_num)
        return float(tally_tuple[winner[0]])

    def finalists(self, tabulation_num=1):
        """
        Any candidate that was active into the final round.
        """
        n_rounds = self.n_rounds(tabulation_num=tabulation_num)
        tally_tuple = self.get_round_trimmed_tally_tuple(n_rounds, tabulation_num=tabulation_num)
        return tally_tuple[0]

    def finalist_ind(self, tabulation_num=1):
        """
        Returns a list indicating the first rank on each ballot where a finalist is listed.
        List element is Inf if no finalist is present
        """
        final_candidates = self.finalists(tabulation_num=tabulation_num)
        inds = []

        # loop through each ballot and check for each finalist
        for b in ballots(self.ctx)['ranks']:
            min_ind = float('inf')
            for c in final_candidates:
                if c in b:
                    min_ind = min(b.index(c), min_ind)
            inds.append(min_ind)

        return inds

    def num_winners(self):
        """
        Count how many winners a contest had.
        """
        return len(self.winner())

    def number_of_rounds(self, tabulation_num=range(1)):
        """
        Count how many rounds a contest had.
        """
        return [self.n_rounds(tabulation_num=i) for i in tabulation_num]

    def number_of_candidates(self):
        '''
        The number of candidates on the ballot, not including write-ins.
        '''
        return len(candidates_no_writeIns(self.ctx))

    def ranked_winner(self, tabulation_num=1):
        """
        Number of ballots with a non-overvote mark for the winner
        """
        winners = self.winner()
        return sum(bool(set(winners).intersection(b)) for b in ballots(self.ctx)['ranks'])

    def win_threshold(self):
        return float(self.win_threshold())

    def winner(self):
        """
        Return contest winner names in order of election.
        """
        # accumulate winners across tabulations
        winners = []
        for i in range(1, self.n_tabulations()):
            winners += self.tabulation_winner(tabulation_num=i)
        return winners

    def tabulation_winner(self, tabulation_num=1):
        """
        Return winners from tabulation.
        """
        elected_candidates = [d for d in
                              self.get_candidate_outcomes(tabulation_num=tabulation_num)['candidate_outcomes']
                              if d['round_elected'] is not None]
        return [d['name'] for d in sorted(elected_candidates, key=lambda x: x['round_elected'])]

    def winners_consensus_value(self, tabulation_num=1):
        '''
        The percentage of valid first round votes that rank any winner in the top 3.
        '''
        return float(self.winner_in_top_3(tabulation_num=tabulation_num) /
                     self.first_round_active_votes(tabulation_num=tabulation_num))

    def winner_ranking(self, tabulation_num=1):
        """
        Returns a dictionary with ranking-count key-values, with count
        indicating the number of ballots in which the winner received each
        ranking.
        If more than one winner is elected in the contest, the value returned for this function refers to the
        first winner elected.
        """
        return Counter(
            b.index(self.winner()[0]) + 1 if self.winner()[0] in b else None for b in cleaned(self.ctx)['ranks']
        )

    def winner_in_top_3(self, tabulation_num=1):
        """
        Number of ballots that ranked any winner in the top 3 ranks. (weighted)
        """
        top3 = [b[:min(3, len(b))] for b in ballots(self.ctx)['ranks']]
        top3_check = [set(self.tabulation_winner(tabulation_num=tabulation_num)).intersection(b) for b in top3]
        return sum([weight * bool(top3) for weight, top3 in zip(ballots(self.ctx)['weight'], top3_check)])

    def any_repeat(self):
        """
        Number of ballots that included one at least one candidate that
        received more than once ranking.
        """
        return sum(v for k, v in self.count_duplicates().items() if k > 1)

    def count_duplicates(self):
        """
        Returns dictionary counting the number of max repeat ranking from each ballot.
        """
        return Counter(self.max_repeats())

    def duplicates(self):
        """
        Returns boolean list with elements set to True if ballot has at least one
        duplicate ranking.
        """
        return [v > 1 for v in self.max_repeats()]

    def max_repeats(self):
        """
            Return a list with each element indicating the max duplicate ranking count
            for any candidate on the ballot
            Note:
            If on a ballot, a candidate received two different rankings, that ballot's
            corresponding list element would be 2. If every candidate included on that
            ballot was only ranked once, that ballot's corresponding list element
            would be 1
        """
        return [max(0, 0, *map(b.count, set(b) - {SKIPPEDRANK, OVERVOTE}))
                for b in ballots(self.ctx)['ranks']]

    def effective_ballot_length(self):
        """
        A list of validly ranked choices, and how many ballots had that number of
        valid choices. (weighted)
        """
        counts = defaultdict(int)
        for ranks, weight in zip(cleaned(self.ctx)['ranks'], cleaned(self.ctx)['weight']):
            counts[len(ranks)] += weight
        return '; '.join('{}: {}'.format(a, b) for a, b in sorted(counts.items()))

    def exhausted(self, tabulation_num=1):
        """
        Returns a boolean list indicating which ballots were exhausted.
        Does not include undervotes as exhausted.
        """
        return [True if x != NOT_EXHAUSTED and x != UNDERVOTE
                else False for x in self.exhaustion_check(tabulation_num=tabulation_num)]

    def exhausted_by_abstention(self, tabulation_num=1):
        """
        Returns bool list with elements corresponding to ballots.
        True if ballot was exhausted without being fully ranked and the
        cause of exhaustion was not overvotes or skipped rankings.
        """
        return [True if i == EXHAUSTED_BY_ABSTENTION else False
                for i in self.exhaustion_check(tabulation_num=tabulation_num)]

    def exhausted_or_undervote(self, tabulation_num=1):
        """
        Returns bool list corresponding to each ballot.
        True when ballot when ballot was exhausted OR left blank (undervote)
        False otherwise
        """
        return [True if x != NOT_EXHAUSTED or x == UNDERVOTE else False
                for x in self.exhaustion_check(tabulation_num=tabulation_num)]

    def exhausted_by_overvote(self, tabulation_num=1):
        """
        Returns bool list with elements corresponding to ballots.
        True if ballot was exhausted due to overvote
        """
        return [True if i == EXHAUSTED_BY_OVERVOTE else False
                for i in self.exhaustion_check(tabulation_num=tabulation_num)]

    def exhausted_by_rank_limit(self, tabulation_num=1):
        """
        Returns bool list with elements corresponding to ballots.
        True if ballot was exhausted AND final rank was used and reached.
        """
        return [True if i == EXHAUSTED_BY_RANK_LIMIT else False
                for i in self.exhaustion_check(tabulation_num=tabulation_num)]

    def exhausted_by_skipvote(self, tabulation_num=1):
        """
        Returns bool list with elements corresponding to ballots.
        True if ballot was exhausted due to repeated_skipvotes
        """
        return [True if i == EXHAUSTED_BY_REPEATED_SKIPVOTE else False
                for i in self.exhaustion_check(tabulation_num=tabulation_num)]

    def exhaustion_check(self, tabulation_num=1):
        """
        Returns a list with string elements indicating why each ballot
        was exhausted in a single-winner rcv contest.

        Possible list values are:
        - EXHAUST_BY_OVERVOTE: if an overvote was the cause of exhaustion (depends on break_on_overvote manifest value)
        - EXHAUSTED_BY_REPEATED_SKIPVOTE: if repeated skipvotes were the cause of exhaustion
        (depends on break_on_repeated_skipvotes manifest value)
        - NOT_EXHAUSTED: if finalist was present on the ballot and was ranked higher than an exhaust condition
        (overvote or repeated_skipvotes)
        - EXHAUSTED_BY_RANK_LIMIT: if no finalist was present on the ballot and all ballot ranks were considered
        - EXHAUSTED_BY_ABSTENTION: if no finalist was present on the ballot and the ballot was NOT fully ranked
        - UNDERVOTE : if the ballot was undervote, and therefore neither active nor exhaustable
        """

        # gather ballot info
        ziplist = zip(self.fully_ranked(),  # True if fully ranked
                      self.overvote_ind(),  # Inf if no overvote
                      self.repeated_skipvote_ind(),  # Inf if no repeated skipvotes
                      self.finalist_ind(tabulation_num=tabulation_num),  # Inf if not finalist ranked
                      self.undervote())  # True if ballot is undervote

        why_exhaust = []

        # loop through each ballot
        for is_fully_ranked, over_idx, repskip_idx, final_idx, is_under in ziplist:

            exhaust_cause = UNDERVOTE

            # if the ballot is an undervote,
            # nothing else to check
            if is_under:
                why_exhaust.append(exhaust_cause)
                continue

            # determine exhaustion cause

            missing_finalist = isInf(final_idx)

            # assemble dictionary of possible exhaustion causes and then remove any
            # that don't apply based on the contest rules
            idx_dictlist = [{'exhaust_cause': EXHAUSTED_BY_OVERVOTE, 'idx': over_idx},
                            {'exhaust_cause': EXHAUSTED_BY_REPEATED_SKIPVOTE, 'idx': repskip_idx},
                            {'exhaust_cause': NOT_EXHAUSTED, 'idx': final_idx}]

            # check if overvote can cause exhaust
            if self.ctx['break_on_overvote'] is False:
                idx_dictlist = [i for i in idx_dictlist if i['exhaust_cause'] != EXHAUSTED_BY_OVERVOTE]

            # check if skipvotes can cause exhaustion
            if self.ctx['break_on_repeated_skipvotes'] is False:
                idx_dictlist = [i for i in idx_dictlist if i['exhaust_cause'] != EXHAUSTED_BY_REPEATED_SKIPVOTE]

            # what comes first on ballot: overvote, skipvotes, or finalist?
            min_dict = sorted(idx_dictlist, key=lambda x: x['idx'])[0]

            if isInf(min_dict['idx']):

                # means this ballot contained none of the three, it will be exhausted
                # either for rank limit or abstention
                if is_fully_ranked:
                    exhaust_cause = EXHAUSTED_BY_RANK_LIMIT
                elif missing_finalist:
                    exhaust_cause = EXHAUSTED_BY_ABSTENTION
                else:
                    print('if final_idx is inf, then missing_finalist should be true. This should never be reached')
                    exit(1)

            else:
                exhaust_cause = min_dict['exhaust_cause']

            why_exhaust.append(exhaust_cause)

        return why_exhaust

    def first_round(self):
        """
        Returns a list of first non-skipvote for each ballot OR
        if the ballot is empty, can also return None
        """
        return [next((c for c in b if c != SKIPPEDRANK), None)
                for b in ballots(self.ctx)['ranks']]

    def first_round_overvote(self):
        '''
        The number of ballots with an overvote before any valid ranking. (weighted)

        Note that this is not the same as "exhausted by overvote". This is because
        some jurisdictions (Maine) discard any ballot beginning with two
        skipped rankings, and call this ballot as exhausted by skipped rankings, even if the
        skipped rankings are followed by an overvote.

        Other jursidictions (Minneapolis) simply skip over overvotes in a ballot.
        '''
        bools = [c == OVERVOTE for c in self.first_round()]
        return float(sum([weight * flag for weight, flag in zip(ballots(self.ctx)['weight'], bools)]))

    def fully_ranked(self):
        """
            Returns a list of bools with each item corresponding to a ballot.
            True indicates a fully ranked ballot.

            Fully ranked here means the last rank was used OR all candidates were ranked
        """
        return [(set(b) & candidates_no_writeIns(self.ctx)) == candidates_no_writeIns(self.ctx) or
                # voters ranked every possible candidate
                a[-1] != SKIPPEDRANK
                # or did not, but at least ranked up until the last rank
                for a, b in zip(ballots(self.ctx)['ranks'], cleaned(self.ctx)['ranks'])]

    def has_skipvote(self):
        """
        Returns boolean list indicating if ballot contains any skipvotes
        """
        return [SKIPPEDRANK in b for b in ballots(self.ctx)['ranks']]

    def includes_duplicate_ranking(self):
        '''
        The number of ballots that rank the same candidate more than once, or
        include more than one write in candidate. (weighted)
        '''
        # count all ranks for candidates
        counters = [Counter(set(b) - {SKIPPEDRANK, OVERVOTE}) for b in ballots(self.ctx)['ranks']]
        # check if any candidates were ranked more than once
        bools = [max(counter.values()) > 1 if counter else False for counter in counters]
        # return weighted sum
        return float(sum([weight * flag for weight, flag in zip(ballots(self.ctx)['weight'], bools)]))

    def includes_skipped_ranking(self):
        """
        The number of ballots that have an skipped ranking followed by any other mark
        valid ranking. (weighted)
        """
        return float(sum([weight * flag for weight, flag in zip(ballots(self.ctx)['weight'], self.skipped())]))

    def overvote(self):
        return [OVERVOTE in b for b in ballots(self.ctx)['ranks']]

    def overvote_ind(self):
        """
            Returns list of index values for first overvote on each ballot
            If no overvotes on ballots, list element is inf
        """
        return [b.index(OVERVOTE) if OVERVOTE in b else float('inf')
                for b in ballots(self.ctx)['ranks']]

    def ranked_single(self):
        """
        The number of voters that validly used only a single ranking. (weighted)
        """
        bools = [len(set(b) - {OVERVOTE, SKIPPEDRANK}) == 1 for b in ballots(self.ctx)['ranks']]
        return float(sum([weight * flag for weight, flag in zip(ballots(self.ctx)['weight'], bools)]))

    def ranked_multiple(self):
        """
        The number of voters that validly use more than one ranking. (weighted)
        """
        bools = [len(set(b) - {OVERVOTE, SKIPPEDRANK}) > 1 for b in ballots(self.ctx)['ranks']]
        return float(sum([weight * flag for weight, flag in zip(ballots(self.ctx)['weight'], bools)]))

    def repeated_skipvote_ind(self):
        """
            return list with index from each ballot where the skipvotes start repeating,
            if no repeated skipvotes, set list element to inf

            note:
            repeated skipvotes are only counted if non-skipvotes occur after them. this
            prevents incompletely ranked ballots from being counted as having repeated skipvotes
        """

        rs = []

        for b in ballots(self.ctx)['ranks']:

            rs.append(float('inf'))

            # pair up successive rankings on ballot
            z = list(zip(b, b[1:]))
            uu = (SKIPPEDRANK, SKIPPEDRANK)

            # if repeated skipvote on the ballot
            if uu in z:
                occurance = z.index(uu)

                # start at second skipvote in the pair
                # and loop until a non-skipvote is found
                # only then record this ballot as having a
                # repeated skipvote
                for c in b[occurance+1:]:
                    if c != SKIPPEDRANK:
                        rs[-1] = occurance
                        break
        return rs

    def skipped(self):
        """
        Returns boolean list. True if skipped rank (followed by other marks) is present.
        Otherwise False.

        {SKIPVOTE} & {x} - {y}
        this checks that x == SKIPVOTE and that y then != SKIPVOTE
        (the y check is important to know whether or not the ballot contains marks
        following the skipped rank)
        """
        return [any({SKIPPEDRANK} & {x} - {y} for x, y in zip(b, b[1:]))
                for b in ballots(self.ctx)['ranks']]

    def total_ballots(self):
        """
        This includes ballots with no marks. (weighted)
        """
        return float(sum(ballots(self.ctx)['weight']))

    def total_exhausted(self, tabulation_num=1):
        """
        Number of ballots (excluding undervotes) that do not rank a finalist. (weighted)
        """
        return float(sum([weight * flag for weight, flag
                          in zip(self.get_final_weights(tabulation_num=tabulation_num),
                                 self.exhausted(tabulation_num=tabulation_num))]))

    def total_exhausted_by_abstention(self, tabulation_num=1):
        """
        Number of ballots exhausted after all marked rankings used and ballot is not fully ranked. (weighted)
        """
        return float(sum([weight * flag for weight, flag in
                          zip(self.get_final_weights(tabulation_num=tabulation_num),
                              self.exhausted_by_abstention(tabulation_num=tabulation_num))]))

    def total_exhausted_by_overvote(self, tabulation_num=1):
        """
        Number of ballots exhausted due to overvote. Only applicable to certain contests. (weighted)
        """
        return float(sum([weight * flag for weight, flag in
                          zip(self.get_final_weights(tabulation_num=tabulation_num),
                              self.exhausted_by_overvote(tabulation_num=tabulation_num))]))

    def total_exhausted_by_rank_limit(self, tabulation_num=1):
        """
        Number of ballots exhausted after all marked rankings used and ballot is fully ranked. (weighted)
        """
        return float(sum([weight * flag for weight, flag in
                          zip(self.get_final_weights(tabulation_num=tabulation_num),
                              self.exhausted_by_rank_limit(tabulation_num=tabulation_num))]))

    def total_exhausted_by_skipped_rankings(self, tabulation_num=1):
        """
        Number of ballots exhausted due to repeated skipped rankings. Only applicable to certain contests. (weighted)
        """
        return float(sum([weight * flag for weight, flag in
                          zip(self.get_final_weights(tabulation_num=tabulation_num),
                              self.exhausted_by_skipvote(tabulation_num=tabulation_num))]))

    def total_ballots_with_overvote(self):
        """
        Number of ballots with at least one overvote. Not necessarily cause of exhaustion. (weighted)
        """
        return float(sum([weight * flag for weight, flag in zip(ballots(self.ctx)['weight'], self.overvote())]))

    def total_fully_ranked(self):
        """
        The number of voters that have validly used all available rankings on the
        ballot, or that have validly ranked all non-write-in candidates. (weighted)
        """
        return float(sum([weight * flag for weight, flag in zip(ballots(self.ctx)['weight'], self.fully_ranked())]))

    def total_irregular(self):
        """
        Number of ballots that either had a multiple ranking, overvote,
        or a skipped ranking. This includes ballots even where the irregularity was not
        the cause of exhaustion. (weighted)
        """
        irregular = map(any, zip(self.duplicates(), self.overvote(), self.skipped()))
        return float(sum([weight * flag for weight, flag in zip(ballots(self.ctx)['weight'], irregular)]))

    def total_undervote(self):
        """
        Ballots completely made up of skipped rankings (no marks). (weighted)
        """
        return float(sum([weight * flag for weight, flag in zip(ballots(self.ctx)['weight'], self.undervote())]))

    def undervote(self):
        """
        Returns a boolean list with True indicating ballots that were undervotes (left blank)
        """
        return [set(x) == {SKIPPEDRANK} for x in ballots(self.ctx)['ranks']]
