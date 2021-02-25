import abc
import collections
import inspect
import math
import copy

import pandas as pd

import rcv_cruncher.ballots as ballots
import rcv_cruncher.rcv_reporting as rcv_reporting
import rcv_cruncher.util as util


class RCV(rcv_reporting.RCV_Reporting, abc.ABC):
    """
    Base class for all RCV variants.
    State variables are listed in __init__.
    Tabulation skeleton is in tabulate()/run_contest()
    """

    @staticmethod
    def run_rcv(ctx):
        """
        Pass in a ctx dictionary and run the constructor function stored within it
        """
        return ctx['rcv_type'](ctx)

    @staticmethod
    @abc.abstractmethod
    def variant_group():
        """
        Should return the name of the group this rcv variant belongs to. The groups
        determine which contests are written out together in the same file. The groups and
        their corresponding output files are separate from the per-rcv-variant output file that
        are always generated.
        """
        pass

    @staticmethod
    def get_variant_group(rcv_obj):
        return rcv_obj.variant_group()

    @staticmethod
    def get_variant_name(rcv_obj):
        return rcv_obj.rcv_type()

    single_winner_group = 'single_winner'
    multi_winner_group = 'multi_winner'

    @staticmethod
    def _f_args(func, *, tabulation_num=None, ballot_filter=None):
        """
        Pack arguments for rcv_reporting calls.
        """
        arg_pack = {}
        func_params = inspect.signature(func).parameters

        if 'tabulation_num' in func_params and tabulation_num:
            arg_pack.update({'tabulation_num': tabulation_num})
        if 'ballot_filter' in func_params and ballot_filter:
            arg_pack.update({'ballot_filter': ballot_filter})

        return arg_pack

    # override me
    @abc.abstractmethod
    def _contest_stats(self):
        """
        Every rcv variant must specify which stats list it uses.
        Available lists should be set as rcv base methods or reporting methods.
        """
        pass

    @staticmethod
    def contest_stats_df(rcv_obj):
        """
        Return a pandas data frame with a single row. Any functions that take
        'tabulation_num' as parameter return a concatenating string with the function results for each
        tabulation joined together. Any functions that do not take 'tabulation_num' just return their single value.
        """
        tabulation_list = list(range(1, rcv_obj._tab_num+1))
        dct = {f.__name__: [f(**RCV._f_args(f, tabulation_num=tabulation_list))] for f in rcv_obj._contest_stats()()}
        dct = {k: [util.decimal2float(i) for i in v] for k, v in dct.items()}
        return pd.DataFrame.from_dict(dct)

    # def contest_stats_comments_df(self):
    #     return pd.DataFrame.from_dict({fun.__name__: [' '.join((fun.__doc__ or '').split())]
    #                                    for fun in self._contest_stats()})

    # override me
    @abc.abstractmethod
    def _tabulation_stats(self):
        """
        Every rcv variant must specify which stats list it uses.
        Available lists should be set as rcv base methods or reporting methods.
        """
        pass

    @staticmethod
    def tabulation_stats_df(rcv_obj):
        """
        Return a pandas data frame with one row per tabulation. Any functions that take
        'tabulation_num' as parameter return the value for each tabulation on that tabulation's row.
        Any functions that do not take 'tabulation_num' just return their single value, repeated on each row.
        """
        tabulation_list = list(range(1, rcv_obj._tab_num+1))
        dct = {f.__name__: [f(**RCV._f_args(f, tabulation_num=i)) for i in tabulation_list]
               for f in rcv_obj._tabulation_stats()()}
        dct = {k: [util.decimal2float(i) for i in v] for k, v in dct.items()}
        return pd.DataFrame.from_dict(dct)

    # def tabulation_stats_comments_df(self):
    #     return pd.DataFrame.from_dict({fun.__name__: [' '.join((fun.__doc__ or '').split())]
    #                                    for fun in self._tabulation_stats()})

    # override me
    @abc.abstractmethod
    def _set_round_winners(self):
        """
        This function should set self.round_winners to the list of candidates that won the round
        """
        pass

    # override me
    @abc.abstractmethod
    def _contest_not_complete(self):
        """
        This function should return True if another round should be evaluated and False
        is the contest should complete.
        """
        pass

    # override me
    @abc.abstractmethod
    def _calc_round_transfer(self):
        """
        This function should append a dictionary to self._tabulations[self._tab_num-1]['transfers'] containing:
        candidate names as keys, plus one key for 'exhaust' and any other keys for transfer categories
        values as round transfer flows.
        """
        pass

    # override me
    def _win_threshold(self):
        """
        This function should return the win threshold used in the contest
        OR return 'dynamic' if threshold changes with each round.
        """
        return 'NA'

    # override me, if ballots should be split/re-weighted prior to next round
    # such as in fractional transfer contests
    def _update_weights(self):
        pass

    # override me, if you need to do multiple iterations of rcv, e.x. utah sequential rcv
    def _run_contest(self):
        # run tabulation
        self._new_tabulation()
        self._tabulate()

    #
    def __init__(self, ctx):

        self._init_complete = False

        # STORE CONTEST INFO
        self.ctx = ctx

        # STATE INFO

        # contest-level
        self._tab_num = 0
        self._tabulations = []

        # tabulation-level
        self._inactive_candidates = []
        self._removed_candidates = []
        self._extra_votes = {}

        # round-level
        self._round_num = 0
        self._round_winners = []
        self._round_loser = None

        # ballot filtering info
        self._include_split_stats = False
        self._split_id = None
        self._split_field = None
        self._split_value = None
        self._split_filter = None

        # CONTEST INPUTS
        self._n_winners = ctx['num_winners']
        self._multi_winner_rounds = ctx['multi_winner_rounds']
        self._candidate_set = ballots.candidates(ctx)
        self._cleaned_dict = ballots.cleaned_ballots(ctx)
        self._bs = [{'ranks': ranks, 'weight': weight, 'weight_distrib': []}
                    for ranks, weight in zip(self._cleaned_dict['ranks'], self._cleaned_dict['weight'])]
        self.cache_dict = {}

        # RUN
        self._run_contest()

        #self._precompute_some_stats()
        self._accounting_check()

        self._init_complete = True

    def update_split_info(self, split_info_dict):

        if len(split_info_dict['split_filter']) != len(self._bs):
            raise RuntimeError('rcv_base.update_split_info: ballot split filter length != length of ballots')

        self._split_id = split_info_dict['split_id']
        self._split_field = split_info_dict['split_field']
        self._split_value = split_info_dict['split_value']
        self._split_filter = split_info_dict['split_filter']

        self._include_split_stats = True

    def _pre_check(self):
        """
        Any checks on the input data to make sure tabulation will be possible.

        If all undervotes, raise AllUndervoteError
        """

        # check for all blank ballots, undervote or blank before exhaust
        ballot_sets = [set(b['ranks']) for b in self._bs]
        if not set.union(*ballot_sets):
            raise RuntimeError(f"rcv_base._pre_check: (tabulation={self._tab_num}) all effectively blank ballots")

    def _new_tabulation(self):
        """
        Add a new set of results to edited in the tabulations list
        """
        self._tab_num += 1
        new_outcomes = {cand: {'name': cand, 'round_eliminated': None, 'round_elected': None}
                        for cand in self._candidate_set}
        self._tabulations.append({
            'rounds': [],
            'transfers': [],
            'candidate_outcomes': new_outcomes,
            'final_weights': [],
            'final_weight_distrib': [],
            'final_ranks': [],
            'initial_ranks': [],
            'initial_weights': [],
            'win_threshold': None})

    #
    def _tabulate(self):
        """
        Run the rounds of rcv contest.
        """

        # use to mark first elimination round that occurs
        first_elimination_round = None

        #############################################
        # CLEAN ROUND BALLOTS
        # remove inactive candidates
        self._clean_round()

        # checks to make tabulation can proceed
        self._pre_check()

        self._tabulations[self._tab_num-1]['initial_ranks'] = [b['ranks'] for b in self._bs]
        self._tabulations[self._tab_num-1]['initial_weights'] = [b['weight'] for b in self._bs]

        not_complete = self._contest_not_complete()
        while not_complete:
            self._round_num += 1

            #############################################
            # CLEAR LAST ROUND VALUES
            self._round_winners = []
            self._round_loser = None

            #############################################
            # COUNT ROUND RESULTS
            self._tally_active_ballots()

            #############################################
            # CHECK FOR ROUND WINNERS
            self._set_round_winners()

            # on the first elimination round, mark any candidates with zero votes for elimination
            if first_elimination_round is None and not self._round_winners:
                round_dict = self.get_round_tally_dict(self._round_num, tabulation_num=self._tab_num)
                novote_losers = [cand for cand in self._candidate_set if round_dict[cand] == 0]

                for loser in novote_losers:
                    self._tabulations[self._tab_num-1]['candidate_outcomes'][loser]['round_eliminated'] = self._round_num

                self._inactive_candidates += novote_losers
                first_elimination_round = False

            #############################################
            # IDENTIFY ROUND LOSER
            self._set_round_loser()

            #############################################
            # UPDATE inactive candidate list using round winner/loser
            self._update_candidates()

            # update complete flag
            not_complete = self._contest_not_complete()

            #############################################
            # UPDATE WEIGHTS
            # don't update if contest over
            if not_complete:
                self._update_weights()

            #############################################
            # CALC ROUND TRANSFER
            if not_complete:
                self._calc_round_transfer()
            else:
                self._tabulations[self._tab_num-1]['transfers'].append(
                    {cand: util.NAN for cand in self._candidate_set.union({'exhaust'})})

            #############################################
            # CLEAN ROUND BALLOTS
            # remove inactive candidates
            # don't clean if contest over
            if not_complete:
                self._clean_round()

        # record final ballot weight distributions
        self._tabulations[self._tab_num-1]['final_weight_distrib'] = \
            [b['weight_distrib'] + [(b['ranks'][0], b['weight'])] if b['ranks']
             else b['weight_distrib'] + [('empty', b['weight'])] for b in self._bs]
        # set final weight for each ballot
        self._tabulations[self._tab_num-1]['final_weights'] = [b['weight'] for b in self._bs]
        # set final ranks for each ballot
        self._tabulations[self._tab_num-1]['final_ranks'] = [b['ranks'] for b in self._bs]
        self._tabulations[self._tab_num-1]['win_threshold'] = self._win_threshold()

    #
    def _tally_active_ballots(self):
        """
        tally ballots and reorder tallies
        using active rankings for each ballot,
        skipping empty ballots

        function should:
        - set self.round_results
        - append to self._tabulations[self._tab_num-1]['rounds_trimmed']
        """
        active_round_candidates = set([b['ranks'][0] for b in self._bs if b['ranks']])
        choices = collections.Counter({cand: 0 for cand in active_round_candidates})
        for b in self._bs:
            if b['ranks']:
                choices[b['ranks'][0]] += b['weight']

        round_results = list(zip(*choices.most_common()))

        # update rounds_full
        round_candidates, round_tallies = round_results
        round_candidates = list(round_candidates)
        round_tallies = list(round_tallies)

        # add in any extra votes (such as from threshold candidates)
        for cand in self._extra_votes:
            # add to candidate tally if they are still accumulating new votes (idk when this happens)
            # or append the candidate to the list
            if cand in round_candidates:
                round_tallies[round_candidates.index(cand)] += self._extra_votes[cand]
            else:
                round_candidates.append(cand)
                round_tallies.append(self._extra_votes[cand])

        round_inactive_candidates = [cand for cand in self._candidate_set if cand not in round_candidates]
        round_candidates_full = round_candidates + round_inactive_candidates
        round_tallies_full = round_tallies + [0] * len(round_inactive_candidates)

        tuple_list = [tuple(round_candidates_full), tuple(round_tallies_full)]
        self._tabulations[self._tab_num-1]['rounds'].append(tuple_list)

    #
    def _clean_round(self):
        """
        Remove any newly inactivated candidates from the ballot ranks.
        """
        for inactive_cand in self._inactive_candidates:
            if inactive_cand not in self._removed_candidates:
                self._bs = [{'ranks': util.remove(inactive_cand, b['ranks']),
                             'weight': b['weight'],
                             'weight_distrib': b['weight_distrib']}
                            for b in self._bs]
                self._removed_candidates.append(inactive_cand)

    #
    def _set_round_loser(self):
        """
        Find candidate from round with least votes.
        If more than one, choose randomly
        """

        # split round results into two tuples (index-matched)
        active_candidates, round_tallies = self.get_round_tally_tuple(self._round_num, self._tab_num,
                                                                      only_round_active_candidates=True, desc_sort=True)
        # find round loser
        # ignore zero vote candidates, they will be automtically eliminated with the first non-zero loser
        loser_count = min(i for i in round_tallies if i)

        # haven't implemented any special rules for tied losers. Print a warning if one is reached
        if len([cand for cand, cand_tally
                in zip(active_candidates, round_tallies) if cand_tally == loser_count]) > 1:
            print("reached a round with tied losers....")

        # in case of tied losers, 'randomly' choose one to eliminate (the last one in alpha order)
        round_losers = sorted([cand for cand, cand_tally
                               in zip(active_candidates, round_tallies)
                               if cand_tally == loser_count])
        self._round_loser = round_losers[-1]

    #
    def _update_candidates(self):
        """
        Update candidate outcomes
        Assume winners are to become inactive, otherwise inactivate loser
        """

        # update winner outcomes
        for winner in self._round_winners:
            self._tabulations[self._tab_num-1]['candidate_outcomes'][winner]['round_elected'] = self._round_num
            self._inactive_candidates.append(winner)

        # if contest is not over
        if self._contest_not_complete():

            # if no winner, add loser
            if not self._round_winners:
                self._inactive_candidates.append(self._round_loser)
                self._tabulations[self._tab_num-1]['candidate_outcomes'][self._round_loser]['round_eliminated'] = self._round_num

        # if contest is over
        else:

            # set all remaining non-winners as eliminated
            remaining_candidates = [d['name'] for d in self._tabulations[self._tab_num-1]['candidate_outcomes'].values()
                                    if d['round_elected'] is None and d['round_eliminated'] is None]
            for cand in remaining_candidates:
                self._tabulations[self._tab_num-1]['candidate_outcomes'][cand]['round_eliminated'] = self._round_num
            self._inactive_candidates += remaining_candidates

    #
    def get_round_tally_tuple(self, round_num, tabulation_num=1, only_round_active_candidates=False, desc_sort=False):
        """
        Return a dictionary containing keys as candidates and values as their vote counts in the round.
        """
        cands, tallies = self._tabulations[tabulation_num-1]['rounds'][round_num-1]

        # remove elected or eliminated candidates
        if only_round_active_candidates:

            outcomes = self._tabulations[tabulation_num-1]['candidate_outcomes']

            elected_filter = [(outcomes[cand]['round_elected'] is None or outcomes[cand]['round_elected'] >= round_num)
                              for cand in outcomes]
            eliminated_filter = [(outcomes[cand]['round_eliminated'] is None or outcomes[cand]['round_eliminated'] >= round_num)
                                 for cand in outcomes]

            active_candidates = [cand for cand, elect_filt, elim_filt in zip(outcomes, elected_filter, eliminated_filter)
                                 if elect_filt and elim_filt]
            tallies = [tally for idx, tally in enumerate(tallies) if cands[idx] in active_candidates]
            cands = [cand for cand in cands if cand in active_candidates]

        # sort
        if desc_sort:
            rounds = list(zip(*[(cand, tally) for cand, tally in sorted(zip(cands, tallies), key=lambda x: -x[1])]))
        else:
            rounds = [tuple(cands), tuple(tallies)]

        # pull round tally
        return rounds

    #
    def get_round_tally_dict(self, round_num, tabulation_num=1, only_round_active_candidates=False):
        """
        Return a dictionary containing keys as candidates and values as their vote counts in the round. Includes
        zero vote candidates and those winners remaining at threshold.
        """
        # convert to dict
        return {cand: count for cand, count in
                zip(*self.get_round_tally_tuple(round_num,
                                                tabulation_num,
                                                only_round_active_candidates=only_round_active_candidates))}

    #
    def get_round_transfer_dict(self, round_num, tabulation_num=1):
        """
        Return a dictionary containing keys as candidates + 'exhaust' and values as their round net transfer
        """
        transfers = self._tabulations[tabulation_num-1]['transfers']
        # pull round transfer
        round_transfer = transfers[round_num-1]
        return round_transfer

    #
    def get_candidate_outcomes(self, tabulation_num=1):
        """
        Return a list of dictionaries {keys: name, round_elected, round_eliminated}
        """
        candidate_outcomes = self._tabulations[tabulation_num-1]['candidate_outcomes']
        return list(candidate_outcomes.values())

    #
    def get_final_weights(self, tabulation_num=1):
        """
        Return a list of ballot weights after tabulation, index-matched with ballots
        """
        final_weights = self._tabulations[tabulation_num-1]['final_weights']
        return final_weights

    #
    def get_initial_ranks(self, tabulation_num=1):
        """
        Return a list of ballot ranks prior to tabulation, but after an initial cleaning. Each set of ranks is a list.
        """
        initial_ranks = self._tabulations[tabulation_num-1]['initial_ranks']
        return initial_ranks

    #
    def get_initial_weights(self, tabulation_num=1):
        """
        Return a list of ballot weights prior to tabulation, but after an initial cleaning. Each set of ranks is a list.
        """
        initial_weights = self._tabulations[tabulation_num-1]['initial_weights']
        return initial_weights

    #
    def get_final_ranks(self, tabulation_num=1):
        """
        Return a list of ballot ranks after tabulation. Each set of ranks is a list.
        """
        final_ranks = self._tabulations[tabulation_num-1]['final_ranks']
        return final_ranks

    #
    def get_final_weight_distrib(self, tabulation_num=1):
        """
        Return a list of ballot weight distributions after tabulation. Each set of weight distributions
        is a ranking-weight tuple pair. Ballots that exhausted have the string 'empty' in the ranking position of
        the tuple.
        """
        final_weights = self._tabulations[tabulation_num-1]['final_weight_distrib']
        return final_weights

    #
    def get_win_threshold(self, tabulation_num=1):
        return self._tabulations[tabulation_num-1]['win_threshold']

    #
    def finalist_candidates(self, tabulation_num=1):
        """
        Return list of candidates with any ballot weight allotted to them by the end of tabulation.
        """
        final_weight_distrib = self.get_final_weight_distrib(tabulation_num=tabulation_num)
        final_weight_cands = list(set(t[0] for t in util.flatten_list(final_weight_distrib)).difference({'empty'}))
        return final_weight_cands

    #
    def n_rounds(self, tabulation_num=1):
        """
        Return the number of rounds, for a given tabulation.
        """
        rounds = self._tabulations[tabulation_num-1]['rounds']
        return len(rounds)

    def n_tabulations(self):
        return self._tab_num

    def _accounting_check(self):
        """
        Calculate several totals a second way to make sure some identity equations hold.
        """

        all_candidates = ballots.candidates(self.ctx, exclude_writeins=False, combine_writeins=False)
        ballot_dict = ballots.input_ballots(self.ctx, combine_writeins=False)
        n_ballots = sum(ballot_dict['weight'])

        n_undervote = self.total_undervote()
        n_ranked_single = self.ranked_single()
        n_ranked_multiple = self.ranked_multiple()

        problems = []
        # right now just test first tabulations
        for iTab in range(1, self.n_tabulations()+1):

            ############################
            # calculated outputs

            weight_distribs = self.get_final_weight_distrib(tabulation_num=iTab)
            weight_distrib_sum = sum([sum(i[1] for i in weight_distrib) for weight_distrib in weight_distribs])

            first_round_active = self.first_round_active_votes(tabulation_num=iTab)
            final_round_active = self.final_round_active_votes(tabulation_num=iTab)
            n_exhaust = self.total_posttally_exhausted(tabulation_num=iTab) + self.total_pretally_exhausted(tabulation_num=iTab)

            ############################
            # intermediary recalculations
            # ballots which are only overvotes and skips

            n_first_round_exhausted = self.total_ballots()
            n_first_round_exhausted -= self.total_undervote()
            n_first_round_exhausted -= self.first_round_active_votes(tabulation_num=iTab)

            tab_exhausts = [self.get_round_transfer_dict(iRound, tabulation_num=iTab)['exhaust'] for
                            iRound in range(1, self.n_rounds(tabulation_num=iTab)+1)]
            cumulative_exhaust = sum(i for i in tab_exhausts if not math.isnan(i))

            ############################
            # secondary crosschecks
            # add up numbers a second way to make sure they match

            # The number of exhausted ballots should equal
            # the difference between the first round active ballots and the final round active ballots
            # PLUS any ballot exhausted in the first round due to overvote or repeated skipped ranks
            n_exhaust_crosscheck1 = first_round_active - final_round_active + n_first_round_exhausted
            n_exhaust_crosscheck2 = cumulative_exhaust + n_first_round_exhausted

            # The number of exhausted ballots calculated in the reporting class should match
            # the sum total of exhausted ballots contained in all the round transfers

            # The number of undervote ballots should equal
            # the difference between the total number of ballots and
            # the first round active ballots,
            n_undervote_crosscheck = n_ballots - first_round_active - n_first_round_exhausted

            n_ranked_single_crosscheck = sum([weight for i, weight in zip(ballot_dict['ranks'], ballot_dict['weight'])
                                             if len(set(i) & all_candidates) == 1])

            n_ranked_multiple_crosscheck = sum([weight for i, weight in zip(ballot_dict['ranks'], ballot_dict['weight'])
                                                if len(set(i) & all_candidates) > 1])

            if float(weight_distrib_sum) != float(n_ballots):
                problems.append(f"(tabulation={iTab}) ballot total mismatch")
            if round(n_exhaust_crosscheck1, 3) != round(n_exhaust, 3) or round(n_exhaust_crosscheck2, 3) != round(n_exhaust, 3):
                problems.append(f"(tabulation={iTab}) exhaust total mismatch")
            if round(n_undervote_crosscheck, 3) != round(n_undervote, 3):
                problems.append(f"(tabulation={iTab}) undervote mismatch")
            if round(n_ranked_single_crosscheck, 3) != round(n_ranked_single, 3):
                problems.append(f"(tabulation={iTab}) ranked single mismatch")
            if round(n_ranked_multiple_crosscheck, 3) != round(n_ranked_multiple, 3):
                problems.append(f"(tabulation={iTab}) ranked multiple mismatch")

        if problems:
            raise RuntimeError("rcv_base._accounting_check: " + ",".join(problems))

    def tabulation_complete(self):
        return self._init_complete

    def split_filter(self):
        return self._split_filter

    def conditional_weighted_sum(self, condition, *, weights=None):
        if weights:
            return sum(weight for weight, cond in zip(weights, condition) if cond)
        else:
            return sum(weight for weight, cond in zip(self._cleaned_dict['weight'], condition) if cond)

    ####################
    # STATS LISTS

    def base_stats(self):
        return [
            self.notes,
            self.jurisdiction,
            self.state,
            self.year,
            self.date,
            self.office,
            self.rcv_type,
            self.exhaust_on_overvote,
            self.exhaust_on_repeated_skipped_rankings,
            self.exhaust_on_duplicate_rankings,
            self.combine_writeins,
            self.treat_combined_writeins_as_duplicates,
            self.skip_writeins,
            self.contest_rank_limit,
            self.number_of_winners,
            self.tabulation_num,
            self.unique_id,
            self.winner,
            self.number_of_candidates,
            self.number_of_rounds,
            self.winners_consensus_value,
            self.first_round_active_votes,
            self.final_round_active_votes,
        ]

    def ballot_stats(self):
        return [
            self.first_round_overvote,
            self.ranked_single,
            self.ranked_multiple,
            self.ranked_3_or_more,
            self.mean_rankings_used,
            self.median_rankings_used,
            self.total_fully_ranked,
            self.includes_duplicate_ranking,
            self.includes_skipped_ranking,
            self.total_irregular,
            self.total_ballots,
            self.total_ballots_with_overvote,
            self.total_undervote,
            self.total_pretally_exhausted,
            self.total_posttally_exhausted,
            self.total_posttally_exhausted_by_overvote,
            self.total_posttally_exhausted_by_skipped_rankings,
            self.total_posttally_exhausted_by_abstention,
            self.total_posttally_exhausted_by_rank_limit,
            self.total_posttally_exhausted_by_duplicate_rankings
        ]

    def split_stats(self):
        return [
            self.split_id,
            self.split_field,
            self.split_value,
            self.split_first_round_overvote,
            self.split_ranked_single,
            self.split_ranked_multiple,
            self.split_ranked_3_or_more,
            self.split_mean_rankings_used,
            self.split_median_rankings_used,
            self.split_total_fully_ranked,
            self.split_includes_duplicate_ranking,
            self.split_includes_skipped_ranking,
            self.split_total_irregular,
            self.split_total_ballots,
            self.split_total_ballots_with_overvote,
            self.split_total_undervote,
            self.split_total_pretally_exhausted,
            self.split_total_posttally_exhausted,
            self.split_total_posttally_exhausted_by_overvote,
            self.split_total_posttally_exhausted_by_skipped_rankings,
            self.split_total_posttally_exhausted_by_abstention,
            self.split_total_posttally_exhausted_by_rank_limit,
            self.split_total_posttally_exhausted_by_duplicate_rankings
        ]

    def single_winner_stats(self):
        stat_list = [
            self.first_round_winner_vote,
            self.final_round_winner_vote,
            self.first_round_winner_percent,
            self.final_round_winner_percent,
            self.first_round_winner_place,
            self.final_round_winner_votes_over_first_round_valid,
            self.condorcet,
            self.come_from_behind,
            self.effective_ballot_length,
            self.ranked_winner
        ]

        if self._include_split_stats:
            return self.base_stats() + stat_list + self.ballot_stats() + self.split_stats()
        else:
            return self.base_stats() + stat_list + self.ballot_stats()

    def multi_winner_stats(self):
        stat_list = [self.win_threshold]

        if self._include_split_stats:
            return self.base_stats() + stat_list + self.ballot_stats() + self.split_stats()
        else:
            return self.base_stats() + stat_list + self.ballot_stats()

    def ballot_debug_df(self, *, tabulation_num=1):
        """
        Return pandas data frame with ranks as well stats on exhaustion, ranked_multiple ...
        """

        # compute ballot stats
        func_list = [self.duplicates,
                     self.pretally_exhausted,
                     self.posttally_exhausted,
                     self.posttally_exhausted_by_abstention,
                     self.posttally_exhausted_by_overvote,
                     self.posttally_exhausted_by_rank_limit,
                     self.posttally_exhausted_by_skipvote,
                     self.posttally_exhausted_by_duplicate_rankings,
                     self.first_round_overvote_bool,
                     self.fully_ranked,
                     self.used_last_rank,
                     self.overvote,
                     self.ranked_multiple_bool,
                     self.ranked_single_bool,
                     self.skipped,
                     self.undervote,
                     self.irregular_bool]

        dct = {f.__name__: f(tabulation_num=tabulation_num) if 'tabulation_num' in inspect.signature(f).parameters else f()
               for f in func_list}

        # get ballot info
        ballot_dict = copy.deepcopy(ballots.input_ballots(self.ctx, combine_writeins=False))
        bs = ballot_dict['ranks']

        # how many ranks?
        num_ranks = max(len(i) for i in bs)

        # make sure all ballots are lists of equal length, adding trailing 'skipped' if necessary
        bs = [b + ([util.BallotMarks.SKIPPEDRANK] * (num_ranks - len(b))) for b in bs]

        # add in rank columns
        ranks = {}
        for i in range(1, num_ranks + 1):
            ranks['rank' + str(i)] = [b[i - 1] for b in bs]

        # assemble output_table, start with extras
        return pd.DataFrame.from_dict({**ranks, **dct})
