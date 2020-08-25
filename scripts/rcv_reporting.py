
# package imports
import os
from collections import Counter, defaultdict
import time
from copy import deepcopy
from functools import wraps
from csv import writer
from inspect import signature
import pandas as pd

# cruncher imports
from .definitions import SKIPPEDRANK, OVERVOTE, isInf, WRITEIN, NOT_EXHAUSTED, POSTTALLY_EXHAUSTED_BY_OVERVOTE, \
    POSTTALLY_EXHAUSTED_BY_REPEATED_SKIPVOTE, POSTTALLY_EXHAUSTED_BY_RANK_LIMIT, POSTTALLY_EXHAUSTED_BY_ABSTENTION, UNDERVOTE, PRETALLY_EXHAUST, \
    replace, remove
from .ballots import ballots, cleaned, candidates, candidates_no_writeIns

global RECORD_FUNCTION_TIMES, USE_TEMP_DICT
RECORD_FUNCTION_TIMES = True
USE_TEMP_DICT = True

def use_timekeeping():
    global RECORD_FUNCTION_TIMES
    return RECORD_FUNCTION_TIMES

def use_temp_dict():
    global USE_TEMP_DICT
    return USE_TEMP_DICT

def allow_list_args(f):
    """
    Wrapper for reporting functions. Assumes args: self (positional) and (keyword) tabulation_num.
    Allows the decorated function to take as tabulation_num single numbers and lists of numbers, and return
    a single value or list accordingly
    """
    @wraps(f)
    def wrapper(*args, **kwargs):

        # ensure there is a kwarg
        if 'tabulation_num' not in f.__kwdefaults__:
            print("you must have tabulation_num as a keyword argument 'f(tabulation_num=1)'")
            raise RuntimeError

        # Used passed in arg or default if not passed
        if 'tabulation_num' in kwargs:
            tabulation_num = kwargs['tabulation_num']
        else:
            tabulation_num = f.__kwdefaults__['tabulation_num']

        # if list, return result of list comprehension over all elements as inputs
        # otherwise simply call the function
        if isinstance(tabulation_num, list):
            return "; ".join([str(f(*args, tabulation_num=i)) for i in tabulation_num])
        else:
            return f(*args, tabulation_num=tabulation_num)

    return wrapper

def check_temp_dict(f):

    @wraps(f)
    def wrapper(self, *args, **kwargs):

        fname = f.__name__

        tabulation_num = 'no_tabulation'
        if 'tabulation_num' in kwargs:
            tabulation_num = kwargs['tabulation_num']

        cache_key = fname + '_' + str(tabulation_num)

        if cache_key in self.cache_dict:
            res = self.cache_dict[cache_key]
        else:
            res = f(self, *args, **kwargs)
            self.cache_dict[cache_key] = res

        return res

    return wrapper


def write_func_time(id, fname, t):
    time_fpath = "contest_sets/reporting_time.csv"
    with open(time_fpath, 'a+', newline='') as write_obj:
        csv_writer = writer(write_obj)
        if os.path.exists(time_fpath) and os.stat(time_fpath).st_size == 0:
            csv_writer.writerow(['id', 'function', 'time'])
        csv_writer.writerow([id, fname, t])

def timer(f):

    if use_timekeeping():
        @wraps(f)
        def timed(self, *args, **kwargs):

            ts = time.time()
            result = f(self, *args, **kwargs)
            te = time.time()

            write_func_time(self.ctx['unique_id'], f.__name__, te - ts)
            return result

        return timed
    else:
        return f

def class_decorators(cls):
    for attr in cls.__dict__: # there's probably a better way to do this
        if callable(getattr(cls, attr)):
            if use_temp_dict():
                setattr(cls, attr, check_temp_dict(getattr(cls, attr)))
            if use_timekeeping(): # add timer decorator
                setattr(cls, attr, timer(getattr(cls, attr)))
    return cls

@class_decorators
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
            self.year,
            self.date,
            self.office,
            self.rcv_type,
            self.number_of_winners,
            self.tabulation_num,
            self.unique_id,
            self.winner,
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
            self.ranked_3_or_more,
            self.total_fully_ranked,
            self.ranked_winner,
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
            self.total_posttally_exhausted_by_rank_limit]

    def multi_winner_stats(self):
        return [
            self.contest_name,
            self.place,
            self.state,
            self.year,
            self.date,
            self.office,
            self.rcv_type,
            self.number_of_winners,
            self.tabulation_num,
            self.winner,
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
            self.ranked_3_or_more,
            self.total_undervote,
            self.first_round_overvote,
            self.total_ballots_with_overvote,
            self.total_pretally_exhausted,
            self.total_posttally_exhausted,
            self.total_posttally_exhausted_by_overvote,
            self.total_posttally_exhausted_by_skipped_rankings,
            self.total_posttally_exhausted_by_abstention,
            self.total_posttally_exhausted_by_rank_limit,
            self.includes_duplicate_ranking,
            self.includes_skipped_ranking,
            self.total_irregular]

    def ballot_debug_df(self, *, tabulation_num=1):
        """
        Return pandas data frame with ranks as well stats on exhaustion, ranked_multiple ...
        """

        # compute ballot stats
        func_list = [self.duplicates,
                     self.posttally_exhausted,
                     self.posttally_exhausted_by_abstention,
                     self.posttally_exhausted_by_overvote,
                     self.posttally_exhausted_by_rank_limit,
                     self.posttally_exhausted_by_skipvote,
                     self.first_round_overvote_bool,
                     self.fully_ranked,
                     self.used_last_rank,
                     self.overvote,
                     self.ranked_multiple_bool,
                     self.ranked_single_bool,
                     self.skipped,
                     self.undervote,
                     self.irregular_bool]

        dct = {f.__name__: f(tabulation_num=tabulation_num) if 'tabulation_num' in signature(f).parameters else f()
               for f in func_list}

        # get ballot info
        ballot_dict = deepcopy(ballots(self.ctx))
        bs = ballot_dict['ranks']

        # ballotIDs?
        if 'ballotID' not in ballot_dict:
            ballotIDs = {'ballotID': [i for i in range(1, len(bs) + 1)]}
        else:
            ballotIDs = {'ballotID': ballot_dict['ballotID']}

        # how many ranks?
        num_ranks = max(len(i) for i in bs)

        # replace constants with strings
        bs = [replace(SKIPPEDRANK, 'skipped', b) for b in bs]
        bs = [replace(WRITEIN, 'writein', b) for b in bs]
        bs = [replace(OVERVOTE, 'overvote', b) for b in bs]

        # make sure all ballots are lists of equal length, adding trailing 'skipped' if necessary
        bs = [b + (['skipped'] * (num_ranks - len(b))) for b in bs]

        # add in rank columns
        ranks = {}
        for i in range(1, num_ranks + 1):
            ranks['rank' + str(i)] = [b[i-1] for b in bs]

        # assemble output_table, start with extras
        return pd.DataFrame.from_dict({**ballotIDs, **ranks, **dct})

    ####################
    # CONTEST INFO

    def contest_name(self):
        return self.ctx['contest']

    def place(self):
        return self.ctx['place']

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

    @allow_list_args
    def unique_id(self, *, tabulation_num=1):
        return self.ctx['unique_id'] + '_tab' + str(tabulation_num)

    ####################
    # OUTCOME STATS

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

    @allow_list_args
    def condorcet(self, *, tabulation_num=1):
        '''
        Is the winner the condorcet winner?
        The condorcet winner is the candidate that would win a 1-on-1 election versus
        any other candidate in the election. Note that this calculation depends on
        jurisdiction dependant rule variations.

        In the case of multi-winner elections, this result will only pertain to the first candidate elected.
        '''

        if len(candidates(self.ctx)) == 1:
            return "yes"

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
            return "yes"
        else:
            return "no"

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

    @allow_list_args
    def final_round_active_votes(self, *, tabulation_num=1):
        '''
        The number of votes that were awarded to any candidate in the final round. (weighted)
        '''
        n_rounds = self.n_rounds(tabulation_num=tabulation_num)
        tally_dict = self.get_round_tally_dict(n_rounds, tabulation_num=tabulation_num)
        return float(sum(tally_dict.values()))

    @allow_list_args
    def first_round_active_votes(self, *, tabulation_num=1):
        '''
        The number of votes that were awarded to any candidate in the first round. (weighted)
        '''
        tally_dict = self.get_round_tally_dict(1, tabulation_num=tabulation_num)
        return float(sum(tally_dict.values()))

    @allow_list_args
    def final_round_winner_percent(self, *, tabulation_num=1):
        '''
        The percent of votes for the winner in the final round.
        If more than one winner, return the final round count for the first winner elected. (weighted)
        '''
        n_rounds = self.n_rounds(tabulation_num=tabulation_num)
        tally_dict = self.get_round_tally_dict(n_rounds, tabulation_num=tabulation_num)
        winner = self.tabulation_winner(tabulation_num=tabulation_num)
        return float(tally_dict[winner[0]] / sum(tally_dict.values())) * 100

    @allow_list_args
    def final_round_winner_vote(self, *, tabulation_num=1):
        '''
        The percent of votes for the winner in the final round.
        If more than one winner, return the final round count for the first winner elected. (weighted)
        '''
        n_rounds = self.n_rounds(tabulation_num=tabulation_num)
        tally_dict = self.get_round_tally_dict(n_rounds, tabulation_num=tabulation_num)
        winner = self.tabulation_winner(tabulation_num=tabulation_num)
        return float(tally_dict[winner[0]])

    @allow_list_args
    def final_round_winner_votes_over_first_round_valid(self, *, tabulation_num=1):
        '''
        The number of votes the winner receives in the final round divided by the
        number of valid votes in the first round. Reported as percentage.

        If more than one winner, return the final round count for the first winner elected. (weighted)
        '''
        return float(self.final_round_winner_vote(tabulation_num=tabulation_num) /
                     self.first_round_active_votes(tabulation_num=tabulation_num)) * 100

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

    @allow_list_args
    def first_round_winner_percent(self, *, tabulation_num=1):
        '''
        The percent of votes for the winner in the first round.
        In the case of multi-winner elections, this result will only pertain to the first candidate elected. (weighted)
        '''
        winner = self.tabulation_winner(tabulation_num=tabulation_num)
        tally_dict = self.get_round_tally_dict(1, tabulation_num=tabulation_num, only_round_active_candidates=True)
        return float(tally_dict[winner[0]] / sum(tally_dict.values())) * 100

    @allow_list_args
    def first_round_winner_vote(self, *, tabulation_num=1):
        '''
        The number of votes for the winner in the first round.
        In the case of multi-winner elections, this result will only pertain to the first candidate elected. (weighted)
        '''
        winner = self.tabulation_winner(tabulation_num=tabulation_num)
        tally_dict = self.get_round_tally_dict(1, tabulation_num=tabulation_num, only_round_active_candidates=True)
        return float(tally_dict[winner[0]])

    def number_of_winners(self):
        """
        Number of winners a contest had.
        """
        return len(self.all_winner())

    @allow_list_args
    def number_of_rounds(self, *, tabulation_num=1):
        """
        Number of rounds in the tabulation.
        """
        return self.n_rounds(tabulation_num=tabulation_num)

    def number_of_candidates(self):
        '''
        The number of candidates on the ballot, not including write-ins.
        '''
        return len(candidates_no_writeIns(self.ctx))

    @allow_list_args
    def ranked_winner(self, *, tabulation_num=1):
        """
        Number of ballots with a non-overvote mark for the winner
        """
        winners = self.tabulation_winner(tabulation_num=tabulation_num)
        return sum(bool(set(winners).intersection(b)) for b in ballots(self.ctx)['ranks'])

    @allow_list_args
    def win_threshold(self, *, tabulation_num=1):
        """
        Election threshold, if static, otherwise NA
        """
        thresh = self.get_win_threshold(tabulation_num=tabulation_num)
        if thresh == 'NA':
            return thresh
        else:
            return float(thresh)

    def all_winner(self):
        """
        Return contest winner names in order of election.
        """
        # accumulate winners across tabulations
        winners = []
        for i in range(1, self.n_tabulations()+1):
            winners += self.tabulation_winner(tabulation_num=i)
        return winners

    def tabulation_winner(self, *, tabulation_num=1):
        """
        Return winners from tabulation.
        """
        elected_candidates = [d for d in self.get_candidate_outcomes(tabulation_num=tabulation_num)
                              if d['round_elected'] is not None]
        return [d['name'] for d in sorted(elected_candidates, key=lambda x: x['round_elected'])]

    @allow_list_args
    def winners_consensus_value(self, *, tabulation_num=1):
        '''
        The percentage of valid first round votes that rank any winner in the top 3.
        '''
        return float(self.winner_in_top_3(tabulation_num=tabulation_num) /
                     self.first_round_active_votes(tabulation_num=tabulation_num)) * 100

    def winner_ranking(self):
        """
        Returns a dictionary with ranking-count key-values, with count
        indicating the number of ballots in which the winner received each
        ranking.
        If more than one winner is elected in the contest, the value returned for this function refers to the
        first winner elected.
        """
        return Counter(b.index(self.all_winner()[0]) + 1 if self.all_winner()[0] in b else None
                       for b in cleaned(self.ctx)['ranks']
        )

    @allow_list_args
    def winner_in_top_3(self, *, tabulation_num=1):
        """
        Number of ballots that ranked any winner in the top 3 ranks. (weighted)
        """
        winner = self.tabulation_winner(tabulation_num=tabulation_num)
        top3 = [b[:min(3, len(b))] for b in ballots(self.ctx)['ranks']]
        top3_check = [set(winner).intersection(b) for b in top3]
        return sum([weight * bool(top3) for weight, top3 in zip(ballots(self.ctx)['weight'], top3_check)])

    def duplicates(self):
        """
        Returns boolean list with elements set to True if ballot has at least one
        duplicate ranking.
        """
        # remove overvotes and undervotes
        bs = [remove(SKIPPEDRANK, b) for b in ballots(self.ctx)['ranks']]
        bs = [remove(OVERVOTE, b) for b in bs]
        # count all ranks for candidates
        counters = [Counter(b) for b in bs]
        # check if any candidates were ranked more than once
        bools = [max(counter.values()) > 1 if counter else False for counter in counters]
        return bools

    def effective_ballot_length(self):
        """
        A list of validly ranked choices, and how many ballots had that number of
        valid choices. (weighted)
        """
        counts = defaultdict(int)
        for ranks, weight in zip(cleaned(self.ctx)['ranks'], cleaned(self.ctx)['weight']):
            counts[len(ranks)] += weight
        return '; '.join('{}: {}'.format(a, b) for a, b in sorted(counts.items()))

    def posttally_exhausted(self, *, tabulation_num=1):
        """
        Returns a boolean list indicating which ballots were exhausted.
        """
        return [True if x != NOT_EXHAUSTED and x != UNDERVOTE
                else False for x in self.exhaustion_check(tabulation_num=tabulation_num)]

    def posttally_exhausted_by_abstention(self, *, tabulation_num=1):
        """
        Returns bool list with elements corresponding to ballots.
        """
        return [True if i == POSTTALLY_EXHAUSTED_BY_ABSTENTION else False
                for i in self.exhaustion_check(tabulation_num=tabulation_num)]

    def posttally_exhausted_by_overvote(self, *, tabulation_num=1):
        """
        Returns bool list with elements corresponding to ballots.
        """
        return [True if i == POSTTALLY_EXHAUSTED_BY_OVERVOTE else False
                for i in self.exhaustion_check(tabulation_num=tabulation_num)]

    def posttally_exhausted_by_rank_limit(self, *, tabulation_num=1):
        """
        Returns bool list with elements corresponding to ballots.
        """
        return [True if i == POSTTALLY_EXHAUSTED_BY_RANK_LIMIT else False
                for i in self.exhaustion_check(tabulation_num=tabulation_num)]

    def posttally_exhausted_by_skipvote(self, *, tabulation_num=1):
        """
        Returns bool list with elements corresponding to ballots.
        """
        return [True if i == POSTTALLY_EXHAUSTED_BY_REPEATED_SKIPVOTE else False
                for i in self.exhaustion_check(tabulation_num=tabulation_num)]

    def pretally_exhaust(self, *, tabulation_num=1):
        """
        Returns bool list with elements corresponding to ballots.
        """
        return [True if i == PRETALLY_EXHAUST else False
                for i in self.exhaustion_check(tabulation_num=tabulation_num)]

    def contest_rank_limit(self):
        """
        The number of rankings allowed on the ballot.
        """
        bs = ballots(self.ctx)['ranks']

        if len(set(len(b) for b in bs)) > 1:
            raise RuntimeError("contest has ballots with varying rank limits.")
        return len(bs[0])

    def restrictive_rank_limit(self):
        """
        True if the contest allowed less than n-1 rankings, where n in the number of candidates.
        """
        if self.contest_rank_limit() < (self.number_of_candidates() - 1):
            return True
        else:
            return False

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
                      self.pretally_exhaust(),  # True if exhausted before the first round
                      self.overvote_ind(),  # Inf if no overvote
                      self.repeated_skipvote_ind(),  # Inf if no repeated skipvotes
                      self.get_final_ranks(tabulation_num=tabulation_num),
                      self.undervote())  # True if ballot is undervote

        why_exhaust = []

        # loop through each ballot
        for last_rank_used, is_pre_tally_exhaust, over_idx, repskip_idx, final_ranks, is_under in ziplist:

            # if the ballot is an undervote,
            # nothing else to check
            if is_under:
                why_exhaust.append(UNDERVOTE)
                continue

            # if the ballot was exhausted before the first round
            # no further categorization needed
            if is_pre_tally_exhaust:
                why_exhaust.append(PRETALLY_EXHAUST)

            # if the ballot still had some ranks at the end of tabulation
            # then it wasnt exhausted
            if final_ranks:
                why_exhaust.append(NOT_EXHAUSTED)
                continue

            # determine exhaustion cause
            idx_dictlist = []
            # check if overvote can cause exhaust
            if self.ctx['break_on_overvote'] and not isInf(over_idx):
                idx_dictlist.append({'exhaust_cause': POSTTALLY_EXHAUSTED_BY_OVERVOTE, 'idx': over_idx})

            # check if skipvotes can cause exhaustion
            if self.ctx['break_on_repeated_skipvotes'] and not isInf(repskip_idx):
                idx_dictlist.append({'exhaust_cause': POSTTALLY_EXHAUSTED_BY_REPEATED_SKIPVOTE, 'idx': repskip_idx})

            if idx_dictlist:

                # what comes first on ballot: overvote, skipvotes
                min_dict = sorted(idx_dictlist, key=lambda x: x['idx'])[0]
                exhaust_cause = min_dict['exhaust_cause']

            else:

                # means this ballot contained neither skipped ranks or overvote, it will be exhausted
                # either for rank limit or abstention
                if restrictive_rank_limit and last_rank_used:
                    exhaust_cause = POSTTALLY_EXHAUSTED_BY_RANK_LIMIT
                else:
                    exhaust_cause = POSTTALLY_EXHAUSTED_BY_ABSTENTION

            why_exhaust.append(exhaust_cause)

        return why_exhaust

    def first_round(self):
        """
        Returns a list of first non-skipvote for each ballot OR
        if the ballot is empty, can also return None
        """
        return [next((c for c in b if c != SKIPPEDRANK), None)
                for b in ballots(self.ctx)['ranks']]

    def first_round_overvote_bool(self):
        return [c == OVERVOTE for c in self.first_round()]

    def first_round_overvote(self):
        '''
        The number of ballots with an overvote before any valid ranking. (weighted)

        Note that this is not the same as "exhausted by overvote". This is because
        some jurisdictions (Maine) discard any ballot beginning with two
        skipped rankings, and call this ballot as exhausted by skipped rankings, even if the
        skipped rankings are followed by an overvote.

        Other jursidictions (Minneapolis) simply skip over overvotes in a ballot.
        '''
        return float(sum([weight * flag for weight, flag
                          in zip(ballots(self.ctx)['weight'], self.first_round_overvote_bool())]))

    def used_last_rank(self):
        """
        Returns boolean list, corresponding to ballots.
        Returns True if the ballot used the final rank.
        """
        return [b[-1] != SKIPPEDRANK for b in ballots(self.ctx)['ranks']]

    def fully_ranked(self):
        """
            Returns a list of bools with each item corresponding to a ballot.
            True indicates a fully ranked ballot.

            Fully ranked here means all the candidates were ranked or all the rankings were used validly
        """
        return [(set(b) & candidates_no_writeIns(self.ctx)) == candidates_no_writeIns(self.ctx) or
                # voters ranked every possible candidate
                len(a) == len(b)
                # or did not, had no skipped ranks, overvotes, or duplicates
                for a, b in zip(ballots(self.ctx)['ranks'], cleaned(self.ctx)['ranks'])]

    def includes_duplicate_ranking(self):
        '''
        The number of ballots that rank the same candidate more than once. (weighted)
        '''
        # return weighted sum
        return float(sum([weight * flag for weight, flag in zip(ballots(self.ctx)['weight'], self.duplicates())]))

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

    def ranked_single_bool(self):
        return [len(set(b) - {OVERVOTE, SKIPPEDRANK}) == 1 for b in ballots(self.ctx)['ranks']]

    def ranked_single(self):
        """
        The number of voters that validly used only a single ranking. (weighted)
        """
        return float(sum([weight * flag for weight, flag
                          in zip(ballots(self.ctx)['weight'], self.ranked_single_bool())]))

    def ranked_3_or_more(self):
        """
        The number of voters that validly used 3 or more rankings. (weighted)
        """
        bools = [len(set(b) - {OVERVOTE, SKIPPEDRANK}) >= 3 for b in ballots(self.ctx)['ranks']]
        return float(sum([weight * flag for weight, flag
                          in zip(ballots(self.ctx)['weight'], bools)]))

    def ranked_multiple_bool(self):
        return [len(set(b) - {OVERVOTE, SKIPPEDRANK}) > 1 for b in ballots(self.ctx)['ranks']]

    def ranked_multiple(self):
        """
        The number of voters that validly use more than one ranking. (weighted)
        """
        return float(sum([weight * flag for weight, flag
                          in zip(ballots(self.ctx)['weight'], self.ranked_multiple_bool())]))

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

    @allow_list_args
    def total_posttally_exhausted(self, *, tabulation_num=1):
        """
        Number of ballots (excluding undervotes) that do not rank a finalist or
        were exhausted from overvotes/skipped ranks rules after being active in the first round. (weighted)
        """
        return float(sum([weight * flag for weight, flag
                          in zip(self.get_final_weights(tabulation_num=tabulation_num),
                                 self.posttally_exhausted(tabulation_num=tabulation_num))]))

    @allow_list_args
    def total_pretally_exhausted(self, *, tabulation_num=1):
        """
        Number of ballots that were exhausted prior to the first round count. (weighted)
        """
        return float(sum([weight * flag for weight, flag
                          in zip(self.get_final_weights(tabulation_num=tabulation_num),
                                 self.pretally_exhaust(tabulation_num=tabulation_num))]))

    @allow_list_args
    def total_posttally_exhausted_by_abstention(self, *, tabulation_num=1):
        """
        Number of initially (reached first round count) active ballots exhausted after all marked rankings used and
        no finalists are present on the ballot. (weighted)
        """
        return float(sum([weight * flag for weight, flag in
                          zip(self.get_final_weights(tabulation_num=tabulation_num),
                              self.posttally_exhausted_by_abstention(tabulation_num=tabulation_num))]))

    @allow_list_args
    def total_posttally_exhausted_by_overvote(self, *, tabulation_num=1):
        """
        Number of ballots exhausted due to overvote that were initially active in the first round.
        Only applicable to certain contests. (weighted)
        """
        return float(sum([weight * flag for weight, flag in
                          zip(self.get_final_weights(tabulation_num=tabulation_num),
                              self.posttally_exhausted_by_overvote(tabulation_num=tabulation_num))]))

    @allow_list_args
    def total_posttally_exhausted_by_rank_limit(self, *, tabulation_num=1):
        """
        Number of initially (reached first round count) active ballots exhausted after all marked rankings used and
        no finalists are present on the ballot. Ballots are only considered as exhausted by rank limit if the final rank
        on the ballot was marked and the contest imposed a restrictive rank limit on voters. (weighted)
        """
        return float(sum([weight * flag for weight, flag in
                          zip(self.get_final_weights(tabulation_num=tabulation_num),
                              self.posttally_exhausted_by_rank_limit(tabulation_num=tabulation_num))]))

    @allow_list_args
    def total_posttally_exhausted_by_skipped_rankings(self, *, tabulation_num=1):
        """
        Number of ballots exhausted due to repeated skipped rankings. Only applicable to certain contests.(weighted)
        """
        return float(sum([weight * flag for weight, flag in
                          zip(self.get_final_weights(tabulation_num=tabulation_num),
                              self.posttally_exhausted_by_skipvote(tabulation_num=tabulation_num))]))

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

    def irregular_bool(self):
        return [True if a or b or c else False for a, b, c in zip(self.duplicates(), self.overvote(), self.skipped())]

    def total_irregular(self):
        """
        Number of ballots that either had a multiple ranking, overvote,
        or a skipped ranking. This includes ballots even where the irregularity was not
        the cause of exhaustion. (weighted)
        """
        return float(sum([weight * flag for weight, flag in zip(ballots(self.ctx)['weight'], self.irregular_bool())]))

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
