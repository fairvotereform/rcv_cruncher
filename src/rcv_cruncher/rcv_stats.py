import collections
import copy
import functools
import inspect

import pandas as pd

import rcv_cruncher.ballots as ballots
import rcv_cruncher.util as util


def allow_list_args(f):
    """
    Wrapper for reporting functions. Assumes args: self (positional) and (keyword) tabulation_num.
    Allows the decorated function to take as tabulation_num single numbers and lists of numbers, and return
    a single value or list accordingly
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):

        # ensure there is a kwarg
        if 'tabulation_num' not in f.__kwdefaults__:
            raise RuntimeError("you must have tabulation_num as a keyword argument 'f(*, tabulation_num=1)'")

        # Used passed in arg or default if not passed
        if 'tabulation_num' in kwargs:
            tabulation_num = kwargs['tabulation_num']
        else:
            tabulation_num = f.__kwdefaults__['tabulation_num']

        copy_kwargs = copy.deepcopy(kwargs)
        del copy_kwargs['tabulation_num']

        # if list, return result of list comprehension over all elements as inputs
        # otherwise simply call the function
        if isinstance(tabulation_num, list):
            return "; ".join([str(f(*args, tabulation_num=i, **copy_kwargs)) for i in tabulation_num])
        else:
            return f(*args, tabulation_num=tabulation_num, **copy_kwargs)

    return wrapper


def check_temp_dict(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):

        fname = f.__name__

        tabulation_num = 'no_tabulation'
        if 'tabulation_num' in kwargs:
            tabulation_num = kwargs['tabulation_num']

        cache_key = fname + '_' + str(tabulation_num)

        if 'split' in fname:
            res = f(self, *args, **kwargs)
        elif cache_key in self.cache_dict:
            res = self.cache_dict[cache_key]
        else:
            res = f(self, *args, **kwargs)
            self.cache_dict[cache_key] = res

        return res

    return wrapper


class RCVStats:
    """
    Mixin containing all reporting stats. Can be overriden by any rcv variant.
    """

    ####################
    # COLLECTIONS OF STATS

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

        stat_names = [
            'contains_duplicate',
            f'pretally_exhausted{tabulation_num}',
            f'posttally_exhausted{tabulation_num}',
            f'posttally_exhausted_by_abstention{tabulation_num}',
            f'posttally_exhausted_by_overvote{tabulation_num}',
            f'posttally_exhausted_by_rank_limit{tabulation_num}',
            f'posttally_exhausted_by_skipped_rankings{tabulation_num}',
            f'posttally_exhausted_by_duplicate_rankings{tabulation_num}',
            'first_round_overvote',
            'fully_ranked',
            'contains_overvote',
            'ranked_multiple',
            'ranked_single',
            'undervote',
            'irregular'
        ]

        dct = {stat_name: list(self._stat_table[stat_name]) for stat_name in stat_names}
        dct['used_last_rank'] = self.used_last_rank()

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

    # STATICS

    @staticmethod
    def stat_args(func, *, tabulation_num=None, ballot_filter=None):
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

    @staticmethod
    def get_tabulation_stats_df(rcv_obj):
        """
        Return a pandas data frame with one row per tabulation. Any functions that take
        'tabulation_num' as parameter return the value for each tabulation on that tabulation's row.
        Any functions that do not take 'tabulation_num' just return their single value, repeated on each row.
        """
        tabulation_list = list(range(1, rcv_obj._tab_num+1))
        dct = {f.__name__: [f(**RCVStats.stat_args(f, tabulation_num=i)) for i in tabulation_list]
               for f in rcv_obj._tabulation_stats()()}
        dct = {k: [util.decimal2float(i) for i in v] for k, v in dct.items()}
        return pd.DataFrame.from_dict(dct)

    @staticmethod
    def get_contest_stats_df(rcv_obj):
        """
        Return a pandas data frame with a single row. Any functions that take
        'tabulation_num' as parameter return a concatenating string with the function results for each
        tabulation joined together. Any functions that do not take 'tabulation_num' just return their single value.
        """
        tabulation_list = list(range(1, rcv_obj._tab_num+1))
        dct = {f.__name__: [f(**RCVStats.stat_args(f, tabulation_num=tabulation_list))] for f in rcv_obj._contest_stats()()}
        dct = {k: [util.decimal2float(i) for i in v] for k, v in dct.items()}
        return pd.DataFrame.from_dict(dct)

    @staticmethod
    def get_split_stats(rcv_obj):

        split_info_list = rcv_obj.get_split_info_list()
        n_splits = len(split_info_list)

        splits = []
        error_splits = []
        for split_info in split_info_list:

            try:
                rcv_obj.update_split_info(split_info)
                splits.append({
                    'variant': rcv_obj.get_variant_name(),
                    'variant_group': rcv_obj.get_variant_group(),
                    'contest_stats_df': rcv_obj.get_contest_stats_df(),
                    'tabulation_stats_df': rcv_obj.get_tabulation_stats_df()
                })
            except Exception:
                error_splits.append(split_info['split_id'])

        if error_splits:
            error_str = ",".join(error_splits)
            raise RuntimeError(f'rcv_base.get_split_stats: {len(error_splits)} of {n_splits} splits errored. {error_str}')

        rcv_obj.update_split_info()
        return splits

    ###################
    # USEFUL FUNCTIONS

    def conditional_weighted_sum(self, condition, *, weights=None):
        if weights:
            return sum(weight for weight, cond in zip(weights, condition) if cond)
        else:
            return sum(weight for weight, cond in zip(self._cleaned_dict['weight'], condition) if cond)

    @check_temp_dict
    def repeated_skipvote_ind(self):
        """
            return list with index from each ballot where the skipvotes start repeating,
            if no repeated skipvotes, set list element to inf

            note:
            repeated skipvotes are only counted if non-skipvotes occur after them. this
            prevents incompletely ranked ballots from being counted as having repeated skipvotes
        """

        rs = []

        for b in ballots.input_ballots(self.ctx)['ranks']:

            rs.append(float('inf'))

            # pair up successive rankings on ballot
            z = list(zip(b, b[1:]))
            uu = (util.BallotMarks.SKIPPEDRANK, util.BallotMarks.SKIPPEDRANK)

            # if repeated skipvote on the ballot
            if uu in z:
                occurance = z.index(uu)

                # start at second skipvote in the pair
                # and loop until a non-skipvote is found
                # only then record this ballot as having a
                # repeated skipvote
                for c in b[occurance + 1:]:
                    if c != util.BallotMarks.SKIPPEDRANK:
                        rs[-1] = occurance
                        break
        return rs

    @check_temp_dict
    def duplicate_ranking_ind(self):
        """
        Returns the index of the first repeated candidate on the ballot, if that exists, otherwise Inf.
        This function is only used for exhaustion cause determination and so writeins should be treated as
        duplicates only if that option was set in the contest set file.
        """
        res = []

        for b in ballots.input_ballots(self.ctx,
                                       combine_writeins=self.ctx['combine_writeins'] and
                                       self.ctx['treat_combined_writeins_as_duplicates'])['ranks']:

            seen = []
            rep_idx = float('inf')

            for idx, m in enumerate(b):

                if m == util.BallotMarks.OVERVOTE or m == util.BallotMarks.SKIPPEDRANK:
                    continue

                if m in seen:
                    rep_idx = idx
                    break

                seen.append(m)

            res.append(rep_idx)

        return res

    @check_temp_dict
    def exhaustion_check(self, *, tabulation_num=1):
        """
        Returns a list with constants indicating why each ballot
        was exhausted in a single-winner rcv contest.

        Possible list values are:

        - UNDERVOTE : if the ballot was undervote, and therefore neither active nor exhaustable.

        - NOT_EXHAUSTED: if finalist was present on the ballot and was ranked higher than an exhaust condition
        (overvote or repeated_skipvotes)

        - PRETALLY_EXHAUST: if the ballot was exahusted by overvote or skipped rankings prior to being counted in the first round.

        - POSTTALLY_EXHAUSTED_BY_OVERVOTE: overvote rules apply to contest, and an overvote is encountered prior to a
        final round candidate or another exhaust condition.

        - POSTTALLY_EXHAUSTED_BY_REPEATED_SKIPVOTE: skipped rankings rules apply to contest, and two or more repeated skipped
         rankings are encountered prior to a final round candidate or another exhaust condition. The skipped rankings
          must be followed by a non-skipped ranking for this condition to apply.

        - POSTTALLY_EXHAUSTED_BY_DUPLICATE_RANKING: repeated rankings rules apply to contest, and a candidate that had already appeared
         on the ballot is encountered again prior to a final round candidate or another exhaust condition.

        - POSTTALLY_EXHAUSTED_BY_ABSTENTION: if the ballot is rank restricted, then a ballot receives this label if the final
        rank was skipped. If the ballot is not rank restricted, then all ballots that do not reach another exhaust
        condition and do not rank a final round candidate receive this label.

        - POSTTALLY_EXHAUSTED_BY_RANK_LIMIT: if the ballot is rank restricted, then a ballot recieves this label if the final
        rank was marked. If the ballot is not rank restricted, then no ballots recieve this label.

        rank restricted ballot: less than or equal to n-2 ranks, where n is number of candidates (not counting writeins).
        """

        restrictive_rank_limit = self.restrictive_rank_limit()

        # gather ballot info
        ziplist = zip(self.used_last_rank(),
                      self.pretally_exhausted(tabulation_num=tabulation_num),  # True if exhausted or undervote
                      self.overvote_ind(),  # Inf if no overvote
                      self.repeated_skipvote_ind(),  # Inf if no repeated skipvotes
                      self.duplicate_ranking_ind(),  # Inf if no repeats
                      self.get_final_ranks(tabulation_num=tabulation_num),
                      self.undervote(),  # True if ballot is undervote
                      ballots.input_ballots(self.ctx, combine_writeins=False)['ranks'])  # sanity check)

        why_exhaust = []

        # loop through each ballot
        for last_rank_used, pretally_exhaust, over_idx, repskip_idx, rep_idx, final_ranks, is_under, b in ziplist:

            # if the ballot is an undervote,
            # nothing else to check
            if is_under:
                why_exhaust.append(util.InactiveType.UNDERVOTE)
                continue

            # if not undervote and the ballot was exhausted before the first round
            # no further categorization needed
            if pretally_exhaust:
                why_exhaust.append(util.InactiveType.PRETALLY_EXHAUST)
                continue

            # if the ballot still had some ranks at the end of tabulation
            # then it wasnt exhausted
            if final_ranks:
                why_exhaust.append(util.InactiveType.NOT_EXHAUSTED)
                continue

            # determine exhaustion cause
            idx_dictlist = []
            # check if overvote can cause exhaust
            if self.ctx['exhaust_on_overvote'] and not util.isInf(over_idx):
                idx_dictlist.append({'exhaust_cause': util.InactiveType.POSTTALLY_EXHAUSTED_BY_OVERVOTE,
                                     'idx': over_idx})

            # check if skipvotes can cause exhaustion
            if self.ctx['exhaust_on_repeated_skipped_rankings'] and not util.isInf(repskip_idx):
                idx_dictlist.append({'exhaust_cause': util.InactiveType.POSTTALLY_EXHAUSTED_BY_REPEATED_SKIPVOTE,
                                     'idx': repskip_idx})

            if self.ctx['exhaust_on_duplicate_rankings'] and not util.isInf(rep_idx):
                idx_dictlist.append({'exhaust_cause': util.InactiveType.POSTTALLY_EXHAUSTED_BY_DUPLICATE_RANKING,
                                     'idx': rep_idx})

            if idx_dictlist:

                # what comes first on ballot: overvote, skipvotes
                min_dict = sorted(idx_dictlist, key=lambda x: x['idx'])[0]
                exhaust_cause = min_dict['exhaust_cause']

            else:

                # means this ballot contained neither skipped ranks or overvote, it will be exhausted
                # either for rank limit or abstention
                if restrictive_rank_limit and last_rank_used:
                    exhaust_cause = util.InactiveType.POSTTALLY_EXHAUSTED_BY_RANK_LIMIT
                else:
                    exhaust_cause = util.InactiveType.POSTTALLY_EXHAUSTED_BY_ABSTENTION

            why_exhaust.append(exhaust_cause)

        return why_exhaust

    ####################
    # CONTEST INFO

    def notes(self):
        return self.ctx['notes']

    def jurisdiction(self):
        return self.ctx['jurisdiction']

    def state(self):
        return self.ctx['state']

    def year(self):
        return self.ctx['year']

    def date(self):
        return self.ctx['date']

    def office(self):
        return self.ctx['office']

    def rcv_type(self):
        return self.ctx['rcv_type'].__name__

    def exhaust_on_overvote(self):
        return self.ctx['exhaust_on_overvote']

    def exhaust_on_repeated_skipped_rankings(self):
        return self.ctx['exhaust_on_repeated_skipped_rankings']

    def exhaust_on_duplicate_rankings(self):
        return self.ctx['exhaust_on_duplicate_rankings']

    def skip_writeins(self):
        return self.ctx['skip_writeins']

    def combine_writeins(self):
        return self.ctx['combine_writeins']

    def treat_combined_writeins_as_duplicates(self):
        return self.ctx['treat_combined_writeins_as_duplicates']

    def unique_id(self):
        """
        Unique id for each contest. Combination of jurisdiction, date, and office.
        """
        return self.ctx['uid']

    def split_id(self):
        """
        String describing which field and value the cvr ballots were filtered on. If no filtering done, it is empty.
        """
        return self._split_id

    def split_field(self):
        return self._split_field

    def split_value(self):
        return self._split_value.replace(":", "_").replace("/", "_").replace("\\", "_").replace(" ", "_").replace("-", "_")

    def file_stub(self, *, tabulation_num=None):

        stub = ""
        if not self.split_id():
            stub += self.unique_id()
        else:
            stub += self.split_id()

        if tabulation_num:
            stub += '_tab-' + str(tabulation_num)

        return stub

    ####################
    # OUTCOME STATS

    @check_temp_dict
    @allow_list_args
    def winner(self, *, tabulation_num=1):
        '''
        The winner(s) of the election.
        '''
        return ", ".join([str(w).title() for w in self.tabulation_winner(tabulation_num=tabulation_num)])

    @allow_list_args
    def tabulation_num(self, *, tabulation_num=1):
        """
        Tabulation number
        """
        return tabulation_num

    @check_temp_dict
    @allow_list_args
    def condorcet(self, *, tabulation_num=1):
        '''
        Is the winner the condorcet winner?
        The condorcet winner is the candidate that would win a 1-on-1 election versus
        any other candidate in the election. Note that this calculation depends on
        jurisdiction dependant rule variations.

        In the case of multi-winner elections, this result will only pertain to the first candidate elected.
        '''

        cands = ballots.candidates(self.ctx)
        if len(cands) == 1:
            return "yes"

        winner = self.tabulation_winner(tabulation_num=tabulation_num)[0]
        losers = [cand for cand in cands if cand != winner]

        net = collections.Counter()
        for b in ballots.cleaned_ballots(self.ctx)['ranks']:
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
            return "yes"
        else:
            return "no"

    @check_temp_dict
    @allow_list_args
    def come_from_behind(self, *, tabulation_num=1):
        """
        "yes" if rcv winner is not first round leader, else "no".

        In the case of multi-winner elections, this result will only pertain to the first candidate elected.
        """
        if self.tabulation_winner(tabulation_num=tabulation_num)[0] != \
                self.get_round_tally_tuple(1, tabulation_num=tabulation_num,
                                           only_round_active_candidates=True, desc_sort=True)[0][0]:
            return "yes"
        else:
            return "no"

    @check_temp_dict
    @allow_list_args
    def final_round_active_votes(self, *, tabulation_num=1):
        '''
        The number of votes that were awarded to any candidate in the final round. (weighted)
        '''
        n_rounds = self.n_rounds(tabulation_num=tabulation_num)
        tally_dict = self.get_round_tally_dict(n_rounds, tabulation_num=tabulation_num)
        return sum(tally_dict.values())

    @check_temp_dict
    @allow_list_args
    def first_round_active_votes(self, *, tabulation_num=1):
        '''
        The number of votes that were awarded to any candidate in the first round. (weighted)
        '''
        tally_dict = self.get_round_tally_dict(1, tabulation_num=tabulation_num)
        return sum(tally_dict.values())

    @check_temp_dict
    @allow_list_args
    def final_round_winner_percent(self, *, tabulation_num=1):
        '''
        The percent of votes for the winner in the final round.
        If more than one winner, return the final round count for the first winner elected. (weighted)
        '''
        n_rounds = self.n_rounds(tabulation_num=tabulation_num)
        tally_dict = self.get_round_tally_dict(n_rounds, tabulation_num=tabulation_num)
        winner = self.tabulation_winner(tabulation_num=tabulation_num)
        return (tally_dict[winner[0]] / sum(tally_dict.values())) * 100

    @check_temp_dict
    @allow_list_args
    def final_round_winner_vote(self, *, tabulation_num=1):
        '''
        The percent of votes for the winner in the final round.
        If more than one winner, return the final round count for the first winner elected. (weighted)
        '''
        n_rounds = self.n_rounds(tabulation_num=tabulation_num)
        tally_dict = self.get_round_tally_dict(n_rounds, tabulation_num=tabulation_num)
        winner = self.tabulation_winner(tabulation_num=tabulation_num)
        return tally_dict[winner[0]]

    @check_temp_dict
    @allow_list_args
    def final_round_winner_votes_over_first_round_valid(self, *, tabulation_num=1):
        '''
        The number of votes the winner receives in the final round divided by the
        number of valid votes in the first round. Reported as percentage.

        If more than one winner, return the final round count for the first winner elected. (weighted)
        '''
        return (self.final_round_winner_vote(tabulation_num=tabulation_num) /
                self.first_round_active_votes(tabulation_num=tabulation_num)) * 100

    @check_temp_dict
    @allow_list_args
    def first_round_winner_place(self, *, tabulation_num=1):
        '''
        In terms of first round votes, what place the eventual winner came in.
        In the case of multi-winner elections, this result will only pertain to the first candidate elected.
        '''
        winner = self.tabulation_winner(tabulation_num=tabulation_num)
        tally_tuple = self.get_round_tally_tuple(1, tabulation_num=tabulation_num,
                                                 only_round_active_candidates=True, desc_sort=True)
        return tally_tuple[0].index(winner[0]) + 1

    @check_temp_dict
    @allow_list_args
    def first_round_winner_percent(self, *, tabulation_num=1):
        '''
        The percent of votes for the winner in the first round.
        In the case of multi-winner elections, this result will only pertain to the first candidate elected. (weighted)
        '''
        winner = self.tabulation_winner(tabulation_num=tabulation_num)
        tally_dict = self.get_round_tally_dict(1, tabulation_num=tabulation_num, only_round_active_candidates=True)
        return tally_dict[winner[0]] / sum(tally_dict.values()) * 100

    @check_temp_dict
    @allow_list_args
    def first_round_winner_vote(self, *, tabulation_num=1):
        '''
        The number of votes for the winner in the first round.
        In the case of multi-winner elections, this result will only pertain to the first candidate elected. (weighted)
        '''
        winner = self.tabulation_winner(tabulation_num=tabulation_num)
        tally_dict = self.get_round_tally_dict(1, tabulation_num=tabulation_num, only_round_active_candidates=True)
        return tally_dict[winner[0]]

    def number_of_winners(self):
        """
        Number of winners a contest had.
        """
        return len(self.all_winner())

    @check_temp_dict
    @allow_list_args
    def number_of_rounds(self, *, tabulation_num=1):
        """
        Number of rounds in the tabulation.
        """
        return self.n_rounds(tabulation_num=tabulation_num)

    @check_temp_dict
    def number_of_candidates(self):
        '''
        The number of candidates on the ballot, not including write-ins.
        '''
        return len(ballots.candidates(self.ctx, exclude_writeins=True))

    @check_temp_dict
    @allow_list_args
    def ranked_winner(self, *, tabulation_num=1):
        """
        Number of ballots with a non-overvote mark for the winner. (weighted) (filtered)
        """
        winners = self.tabulation_winner(tabulation_num=tabulation_num)
        winner_marked = [bool(set(winners).intersection(b)) for b in ballots.input_ballots(self.ctx)['ranks']]
        return self.conditional_weighted_sum(winner_marked)

    @check_temp_dict
    @allow_list_args
    def win_threshold(self, *, tabulation_num=1):
        """
        Election threshold, if static, otherwise NA
        """
        thresh = self.get_win_threshold(tabulation_num=tabulation_num)
        if thresh == 'NA':
            return thresh
        else:
            return thresh

    @check_temp_dict
    def all_winner(self):
        """
        Return contest winner names in order of election.
        """
        # accumulate winners across tabulations
        winners = []
        for i in range(1, self.n_tabulations() + 1):
            winners += self.tabulation_winner(tabulation_num=i)
        return winners

    @check_temp_dict
    def tabulation_winner(self, *, tabulation_num=1):
        """
        Return winners from tabulation.
        """
        elected_candidates = [d for d in self.get_candidate_outcomes(tabulation_num=tabulation_num)
                              if d['round_elected'] is not None]
        return [d['name'] for d in sorted(elected_candidates, key=lambda x: x['round_elected'])]

    @check_temp_dict
    @allow_list_args
    def winners_consensus_value(self, *, tabulation_num=1):
        '''
        The percentage of valid first round votes that rank any winner in the top 3.
        '''
        return (self.winner_in_top_3(tabulation_num=tabulation_num) /
                self.first_round_active_votes(tabulation_num=tabulation_num)) * 100

    @check_temp_dict
    @allow_list_args
    def winner_in_top_3(self, *, tabulation_num=1):
        """
        Number of ballots that ranked any winner in the top 3 ranks. (weighted)
        """
        winner = self.tabulation_winner(tabulation_num=tabulation_num)
        top3 = [b[:min(3, len(b))] for b in ballots.input_ballots(self.ctx)['ranks']]
        top3_check = [bool(set(winner).intersection(b)) for b in top3]
        return self.conditional_weighted_sum(top3_check)

    @check_temp_dict
    def effective_ballot_length(self):
        """
        A list of validly ranked choices, and how many ballots had that number of
        valid choices. (weighted)
        """
        ballot_dict = ballots.cleaned_ballots(self.ctx)
        counts = collections.defaultdict(int)
        for ranks, weight in zip(ballot_dict['ranks'], ballot_dict['weight']):
            counts[len(ranks)] += weight
        return '; '.join('{}: {}'.format(a, b) for a, b in sorted(counts.items()))

    @check_temp_dict
    def pretally_exhausted(self, *, tabulation_num=1):
        """
        Returns bool list with elements corresponding to ballots.
        """
        return [True if not a and not b else False for a, b in
                zip(self.get_initial_ranks(tabulation_num=tabulation_num), self.undervote())]

    @check_temp_dict
    def contest_rank_limit(self):
        """
        The number of rankings allowed on the ballot.
        """
        bs = ballots.input_ballots(self.ctx)['ranks']

        if len(set(len(b) for b in bs)) > 1:
            raise RuntimeError("contest has ballots with varying rank limits.")
        return len(bs[0])

    @check_temp_dict
    def restrictive_rank_limit(self):
        """
        True if the contest allowed less than n-1 rankings, where n in the number of candidates.
        """
        if self.contest_rank_limit() < (self.number_of_candidates() - 1):
            return True
        else:
            return False

    @check_temp_dict
    def first_round_overvote(self):
        '''
        The number of ballots with an overvote before any valid ranking. (weighted)

        Note that this is not the same as "exhausted by overvote". This is because
        some jurisdictions (Maine) discard any ballot beginning with two
        skipped rankings, and call this ballot as exhausted by skipped rankings, even if the
        skipped rankings are followed by an overvote.

        Other jursidictions (Minneapolis) simply skip over overvotes in a ballot.
        '''
        return self._stat_table.loc[self._stat_table['first_round_overvote'], 'weight'].sum()

    @check_temp_dict
    def used_last_rank(self):
        """
        Returns boolean list, corresponding to ballots.
        Returns True if the ballot used the final rank.
        """
        return [b[-1] != util.BallotMarks.SKIPPEDRANK for b in ballots.input_ballots(self.ctx)['ranks']]

    @check_temp_dict
    def includes_duplicate_ranking(self):
        '''
        The number of ballots that rank the same candidate more than once. (weighted)
        '''
        return self._stat_table.loc[self._stat_table['contains_duplicate'], 'weight'].sum()

    @check_temp_dict
    def includes_skipped_ranking(self):
        """
        The number of ballots that have an skipped ranking followed by any other marked ranking. (weighted)
        """
        return self._stat_table.loc[self._stat_table['contains_skip'], 'weight'].sum()

    @check_temp_dict
    def overvote_ind(self):
        """
            Returns list of index values for first overvote on each ballot
            If no overvotes on ballots, list element is inf
        """
        return [b.index(util.BallotMarks.OVERVOTE) if util.BallotMarks.OVERVOTE in b else float('inf')
                for b in ballots.input_ballots(self.ctx)['ranks']]

    @check_temp_dict
    def ranked_single(self):
        """
        The number of voters that validly used only a single ranking. (weighted)
        """
        return self._stat_table.loc[self._stat_table['ranked_single'], 'weight'].sum()

    @check_temp_dict
    def ranked_3_or_more(self):
        """
        The number of voters that validly used 3 or more rankings. (weighted)
        """
        return self._stat_table.loc[self._stat_table['ranked_3_or_more'], 'weight'].sum()

    @check_temp_dict
    def ranked_multiple(self):
        """
        The number of voters that validly use more than one ranking. (weighted)
        """
        return self._stat_table.loc[self._stat_table['ranked_multiple'], 'weight'].sum()

    @check_temp_dict
    def mean_rankings_used(self):
        """
        Mean number of validly used rankings across all non-undervote ballots. (weighted)
        """
        return self._stat_table.loc[~self._stat_table['undervote'], 'ranks_used_times_weight'].mean()

    @check_temp_dict
    def median_rankings_used(self):
        """
        Median number of validly used rankings across all non-undervote ballots. (weighted)
        """
        return self._stat_table.loc[~self._stat_table['undervote'], 'ranks_used_times_weight'].median()

    @check_temp_dict
    def total_ballots(self):
        """
        This includes ballots with no marks. (weighted)
        """
        return self._stat_table['weight'].sum()

    @check_temp_dict
    @allow_list_args
    def total_posttally_exhausted(self, *, tabulation_num=1):
        """
        Number of ballots (excluding undervotes) that do not rank a finalist or
        were exhausted from overvotes/skipped ranks rules after being active in the first round. (weighted)
        """
        condition = self._stat_table[f'posttally_exhausted{tabulation_num}']
        return self._stat_table.loc[condition, f'final_weight{tabulation_num}'].sum()

    @check_temp_dict
    @allow_list_args
    def total_pretally_exhausted(self, *, tabulation_num=1):
        """
        Number of ballots that were exhausted prior to the first round count. (weighted)
        """
        condition = self._stat_table[f'pretally_exhausted{tabulation_num}']
        return self._stat_table.loc[condition, 'weight'].sum()

    @check_temp_dict
    @allow_list_args
    def total_posttally_exhausted_by_abstention(self, *, tabulation_num=1):
        """
        Number of initially (reached first round count) active ballots exhausted after all marked rankings used and
        no finalists are present on the ballot. (weighted)
        """
        condition = self._stat_table[f'posttally_exhausted_by_abstention{tabulation_num}']
        return self._stat_table.loc[condition, f'final_weight{tabulation_num}'].sum()

    @check_temp_dict
    @allow_list_args
    def total_posttally_exhausted_by_overvote(self, *, tabulation_num=1):
        """
        Number of ballots exhausted due to overvote that were initially active in the first round.
        Only applicable to certain contests. (weighted)
        """
        condition = self._stat_table[f'posttally_exhausted_by_overvote{tabulation_num}']
        return self._stat_table.loc[condition, f'final_weight{tabulation_num}'].sum()

    @check_temp_dict
    @allow_list_args
    def total_posttally_exhausted_by_rank_limit(self, *, tabulation_num=1):
        """
        Number of initially (reached first round count) active ballots exhausted after all marked rankings used and
        no finalists are present on the ballot. Ballots are only considered as exhausted by rank limit if the final rank
        on the ballot was marked and the contest imposed a restrictive rank limit on voters. (weighted)
        """
        condition = self._stat_table[f'posttally_exhausted_by_rank_limit{tabulation_num}']
        return self._stat_table.loc[condition, f'final_weight{tabulation_num}'].sum()

    @check_temp_dict
    @allow_list_args
    def total_posttally_exhausted_by_duplicate_rankings(self, *, tabulation_num=1):
        """
        Number of ballots exhausted due to duplicate rankings. Only applicable to certain contests.(weighted)
        """
        condition = self._stat_table[f'posttally_exhausted_by_duplicate_rankings{tabulation_num}']
        return self._stat_table.loc[condition, f'final_weight{tabulation_num}'].sum()

    @check_temp_dict
    @allow_list_args
    def total_posttally_exhausted_by_skipped_rankings(self, *, tabulation_num=1):
        """
        Number of ballots exhausted due to repeated skipped rankings. Only applicable to certain contests.(weighted)
        """
        condition = self._stat_table[f'posttally_exhausted_by_skipped_rankings{tabulation_num}']
        return self._stat_table.loc[condition, f'final_weight{tabulation_num}'].sum()

    @check_temp_dict
    def total_ballots_with_overvote(self):
        """
        Number of ballots with at least one overvote. Not necessarily cause of exhaustion. (weighted)
        """
        return self._stat_table.loc[self._stat_table['contains_overvote'], 'weight'].sum()

    @check_temp_dict
    def total_fully_ranked(self):
        """
        The number of voters that have validly used all available rankings on the
        ballot, or that have validly ranked all non-write-in candidates. (weighted)
        """
        return self._stat_table.loc[self._stat_table['fully_ranked'], 'weight'].sum()

    @check_temp_dict
    def total_irregular(self):
        """
        Number of ballots that either had a multiple ranking, overvote,
        or a skipped ranking (only those followed by a mark). This includes ballots even where the irregularity was not
        the cause of exhaustion. (weighted)
        """
        return self._stat_table.loc[self._stat_table['irregular'], 'weight'].sum()

    @check_temp_dict
    def total_undervote(self):
        """
        Ballots completely made up of skipped rankings (no marks). (weighted)
        """
        return self._stat_table.loc[self._stat_table['undervote'], 'weight'].sum()

    @check_temp_dict
    def undervote(self):
        """
        Returns a boolean list with True indicating ballots that were undervotes (left blank)
        """
        return [set(x) == {util.BallotMarks.SKIPPEDRANK} for x in ballots.input_ballots(self.ctx)['ranks']]

    def split_first_round_overvote(self):
        return self._split_stat_table.loc[self._split_stat_table['first_round_overvote'], 'weight'].sum()

    def split_ranked_single(self):
        return self._split_stat_table.loc[self._split_stat_table['ranked_single'], 'weight'].sum()

    def split_ranked_multiple(self):
        return self._split_stat_table.loc[self._split_stat_table['ranked_multiple'], 'weight'].sum()

    def split_ranked_3_or_more(self):
        return self._split_stat_table.loc[self._split_stat_table['ranked_3_or_more'], 'weight'].sum()

    def split_mean_rankings_used(self):
        return self._split_stat_table.loc[~self._split_stat_table['undervote'], 'ranks_used_times_weight'].mean()

    def split_median_rankings_used(self):
        return self._split_stat_table.loc[~self._split_stat_table['undervote'], 'ranks_used_times_weight'].median()

    def split_total_fully_ranked(self):
        return self._split_stat_table.loc[self._split_stat_table['fully_ranked'], 'weight'].sum()

    def split_includes_duplicate_ranking(self):
        return self._split_stat_table.loc[self._split_stat_table['contains_duplicate'], 'weight'].sum()

    def split_includes_skipped_ranking(self):
        return self._split_stat_table.loc[self._split_stat_table['contains_skip'], 'weight'].sum()

    def split_total_irregular(self):
        return self._split_stat_table.loc[self._split_stat_table['irregular'], 'weight'].sum()

    def split_total_ballots(self):
        return self._split_stat_table['weight'].sum()

    def split_total_ballots_with_overvote(self):
        return self._split_stat_table.loc[self._split_stat_table['contains_overvote'], 'weight'].sum()

    def split_total_undervote(self):
        return self._split_stat_table.loc[self._split_stat_table['undervote'], 'weight'].sum()

    @allow_list_args
    def split_total_pretally_exhausted(self, *, tabulation_num=1):
        condition = self._split_stat_table[f'pretally_exhausted{tabulation_num}']
        return self._split_stat_table.loc[condition, 'weight'].sum()

    @allow_list_args
    def split_total_posttally_exhausted(self, *, tabulation_num=1):
        condition = self._split_stat_table[f'posttally_exhausted{tabulation_num}']
        return self._split_stat_table.loc[condition, f'final_weight{tabulation_num}'].sum()

    @allow_list_args
    def split_total_posttally_exhausted_by_overvote(self, *, tabulation_num=1):
        condition = self._split_stat_table[f'posttally_exhausted_by_overvote{tabulation_num}']
        return self._split_stat_table.loc[condition, f'final_weight{tabulation_num}'].sum()

    @allow_list_args
    def split_total_posttally_exhausted_by_skipped_rankings(self, *, tabulation_num=1):
        condition = self._split_stat_table[f'posttally_exhausted_by_skipped_rankings{tabulation_num}']
        return self._split_stat_table.loc[condition, f'final_weight{tabulation_num}'].sum()

    @allow_list_args
    def split_total_posttally_exhausted_by_abstention(self, *, tabulation_num=1):
        condition = self._split_stat_table[f'posttally_exhausted_by_abstention{tabulation_num}']
        return self._split_stat_table.loc[condition, f'final_weight{tabulation_num}'].sum()

    @allow_list_args
    def split_total_posttally_exhausted_by_rank_limit(self, *, tabulation_num=1):
        condition = self._split_stat_table[f'posttally_exhausted_by_rank_limit{tabulation_num}']
        return self._split_stat_table.loc[condition, f'final_weight{tabulation_num}'].sum()

    @allow_list_args
    def split_total_posttally_exhausted_by_duplicate_rankings(self, *, tabulation_num=1):
        condition = self._split_stat_table[f'posttally_exhausted_by_duplicate_rankings{tabulation_num}']
        return self._split_stat_table.loc[condition, f'final_weight{tabulation_num}'].sum()
