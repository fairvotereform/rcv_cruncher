# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

import logging
import os
import sys

_log = logging.getLogger(__name__)


LABELS = {
    'total': "Total",
    'voted': "Voted",
    'under': "Undervoted",
    'has_over': "Has_Overvote",
    'has_skip': "Has_Skipped",
    'has_dupe': "Has_Duplicate",
    'dupe3': "Has_Duplicate_3",
    'dupe2': "Has_Duplicate_2",
    'exhaust': "True_Exhaust",
    'irregular': "Irregular",
    'over': "Overvoted",
    'continuing': "Continuing",
    'valid': "Valid",
    'all': "All",
    'winner': "Winner",
    'finalists': "Finalists",
    'non-finalists': "Non-finalists",
}


def percent(part, whole):
    """
    Return a percent float.

    """
    # Prevent division by zero.
    if whole == 0:
        return 0
    return 100.0 * part / whole

def ljust(s, length, fill_string):
    """
    Right pad a string with a fill string, for example "ALICE . . . .".
    """
    fill_length = len(fill_string)
    while len(s) < length:
        # Rotate through the characters in the fill string.
        s += fill_string[len(s) % fill_length]

    return s

class Reporter(object):

    candidate_indent = 12

    def __init__(self, contest, stats, download_url, download_time):
        self.contest = contest
        self.stats = stats
        self.download_url = download_url
        self.download_time = download_time
        
        self.report = ""

        labels = LABELS.values() + contest.candidate_dict.values()
        max_label_length = max([len(label) for label in labels])
        self.left_indent = max_label_length + 1  # for extra space.

        # Sort candidates in descending order by first-round totals.
        triples = []
        for candidate_id, name in contest.candidate_dict.iteritems():
            first_round = stats.get_first_round(candidate_id)
            triples.append((first_round, candidate_id, name))
        triples.sort()
        triples.reverse()
        self.sorted_candidates = [(triple[1], triple[2], triple[0]) for triple in triples]

    def percent_string(self, part, whole):
        """
        Return a percent string, for example, " 12.5%".

        """
        return "%5.1f%%" % percent(part, whole)

    def rounded_percent_string(self, part, whole):
        """
        Return a rounded percent string, for example, " 25%".

        """
        return "%3.0f%%" % percent(part, whole)

    def get_candidate_name(self, candidate_id):
        return self.contest.candidate_dict[candidate_id]

    def add_text(self, text):
        self.report += "%s\n" % text

    def _add_header(self, text, sep_char):
        self.add_text(text)
        self.add_text(len(text) * sep_char)
        self.skip()

    def add_title(self, text):
        self._add_header(text, "=")

    def add_section_title(self, text):
        self.skip()
        self._add_header(text, "-")

    def _add_candidate_name(self, candidate_id):
        name = self.get_candidate_name(candidate_id)
        self.add_text(3 * " " + name)

    def add_candidate_names(self, header, candidate_ids):
        self.add_text("%s:" % header)
        for candidate_id in candidate_ids:
            self._add_candidate_name(candidate_id)
        self.skip()

    def label_string(self, name):
        s = "%s " % name.upper()
        s = ljust(s, self.left_indent, '.')

        return s

    def value_string(self, value):
        return "%6d" % value

    def add_data(self, name, value, total_label=None, total=None, description=None):
        label_string = self.label_string(name)

        percent = self.percent_string(value, total)
        value_string = self.value_string(value)

        total_string = ("of %s" % total_label) if total_label is not None else ""
        s = "%s %s (%s %s)" % (label_string, value_string, percent, total_string)

        if description is not None:
            s += " [%s]" % description

        self.add_text(s)

    # TODO: find a nicer abstraction of this functionality.
    def add_data2(self, name, value1, total1, value2, total2):
        label_string = self.label_string(name)

        def data_pair_string(value, total):
            value_string = self.value_string(value)
            percent_string = self.percent_string(value, total)

            return "%s ( %s )" % (value_string, percent_string)

        s = "%s %s %s" % (label_string, data_pair_string(value1, total1), data_pair_string(value2, total2))

        self.add_text(s)

    def add_number_ranked(self, name, number_ranked):
        first_round = sum(number_ranked)

        label_string = self.label_string(name)
        percent_strings = [self.rounded_percent_string(value, first_round) for value in number_ranked]
        number_ranked_strings = [str(value) for value in number_ranked]

        strings = [label_string] + percent_strings + [first_round] + number_ranked_strings

        s = "%s %s %s %s (%s = %s + %s + %s)" % tuple(strings)

        self.add_text(s)

    def add_aggregate_number_ranked(self, name, candidate_ids):
        # TODO: make this elegant.
        if candidate_ids:
            number_ranked_list = [self.stats.get_number_ranked(candidate_id) for candidate_id in candidate_ids]
            number_ranked = map(sum, zip(*number_ranked_list))
        else:
            number_ranked = (0, 0, 0)

        self.add_number_ranked(name, number_ranked)

    def add_percent_data(self, name, value, total):
        label_string = self.label_string(name)
        percent_string = self.percent_string(value, total)
        value_string = self.value_string(value)
        total_string = self.value_string(total)

        s = "%s %s (%s / %s)" % (label_string, percent_string, value_string, total_string)

        self.add_text(s)

    def add_first_round_percent_data(self, name, value_dict, candidate_ids):
        value = sum([value_dict[candidate_id] for candidate_id in candidate_ids])
        total = sum([self.stats.get_first_round(candidate_id) for candidate_id in candidate_ids])

        self.add_percent_data(name, value, total)

    def skip(self):
        self.report += "\n"

    def make_report(self):

        contest = self.contest
        stats = self.stats

        self.add_title(contest.name + " RCV Stats")

        self.add_candidate_names(LABELS['winner'], [contest.winner_id])
        self.add_candidate_names(LABELS['finalists'], contest.finalist_ids)

        self.add_data(LABELS['total'], stats.total, 'total', stats.total)
        self.skip()
        self.add_data(LABELS['voted'], stats.voted, 'total', stats.total)
        self.add_data(LABELS['under'], stats.undervotes, 'total', stats.total)

        self.add_section_title("Overview of voted, as percent of voted")

        self.add_data(LABELS['has_dupe'], sum(stats.duplicates.values()), total=stats.voted)
        self.add_data(LABELS['has_over'], stats.has_overvote, total=stats.voted)
        self.add_data(LABELS['has_skip'], stats.has_skipped, total=stats.voted)
        self.add_data(LABELS['irregular'], stats.irregular, total=stats.voted,
                      description="has duplicate, overvote, and/or skip")
        self.skip()

        self.add_data(LABELS['dupe3'], stats.duplicates[3], total=stats.voted)
        self.add_data(LABELS['dupe2'], stats.duplicates[2], total=stats.voted)
        self.skip()

        self.add_data(LABELS['exhaust'], stats.true_exhaust, total=stats.voted,
                      description="3 distinct candidates, none a finalist")

        self.add_section_title("Overview of first round, as percent of voted")

        self.add_data(LABELS['continuing'], stats.first_round_continuing, total=stats.voted)
        self.add_data(LABELS['over'], stats.first_round_overvotes, total=stats.voted)

        self.add_section_title("Candidate support, in descending order of first round total")

        self.add_text("[First round as percent of continuing; ranked anywhere as percent of voted.]")
        self.skip()

        for candidate_id, name, first_round in self.sorted_candidates:
            self.add_data2(name, first_round, stats.first_round_continuing, stats.ranked_anywhere[candidate_id], stats.voted)

        self.add_section_title("Number of candidates validly ranked (3-2-1), by first-round choice")

        self.add_aggregate_number_ranked(LABELS['all'], contest.candidate_ids)
        self.add_aggregate_number_ranked(LABELS['winner'], [contest.winner_id])
        self.add_aggregate_number_ranked(LABELS['finalists'], contest.finalist_ids)
        self.add_aggregate_number_ranked(LABELS['non-finalists'], contest.non_finalist_ids)
        self.skip()

        for candidate_id, name, first_round in self.sorted_candidates:
            number_ranked = stats.get_number_ranked(candidate_id)
            self.add_number_ranked(name, number_ranked)

        self.add_section_title("Ballots validly ranking the winner, by first-round choice")

        self.add_first_round_percent_data(LABELS['all'], stats.ranked_winner, contest.candidate_ids)
        self.skip()

        for candidate_id, name, first_round in self.sorted_candidates:
            self.add_first_round_percent_data(name, stats.ranked_winner, [candidate_id])

        self.add_section_title("Ballots validly ranking a finalist, by first-round choice")

        self.add_first_round_percent_data(LABELS['all'], stats.ranked_finalist, contest.candidate_ids)
        self.skip()

        for candidate_id, name, first_round in self.sorted_candidates:
            self.add_first_round_percent_data(name, stats.ranked_finalist, [candidate_id])

        self.add_section_title("Ballots ranking the same candidate 3 times")

        self.add_first_round_percent_data(LABELS['all'], stats.did_sweep, contest.candidate_ids)
        self.skip()

        for candidate_id, name, first_round in self.sorted_candidates:
            self.add_first_round_percent_data(name, stats.did_sweep, [candidate_id])

        self.add_section_title("Condorcet support for winner against each candidate, in ascending order")

        # TODO: move the condorcet code below into a method.
        condorcet_data = []
        for candidate_id, name, first_round in self.sorted_candidates:
            if candidate_id == contest.winner_id:
                continue
            win_count, total_count = stats.get_condorcet_support(contest.winner_id, candidate_id)
            new_data = (percent(win_count, total_count), win_count, total_count, name)
            condorcet_data.append(new_data)
        condorcet_data.sort()

        for data in condorcet_data:
            # BOB  60% (600 / 1000 = 20% of first-round continuing)
            percent_value, win_count, total_count, name = data
            
            label_string = self.label_string(name)
            percent_string = self.percent_string(win_count, total_count)
            percent_of_voted_string = self.percent_string(total_count, stats.first_round_continuing)

            strings = [label_string, percent_string, win_count, total_count, percent_of_voted_string]

            s = "%s %s (%s / %s) (%s of first-round continuing)" % tuple(strings)

            self.add_text(s)

        

        self.skip()
        self.add_text("[Data downloaded from %s" % self.download_url)
        self.add_text(" on %s.]" % self.download_time)

        self.skip()
        self.add_text(80 * "*")
        self.add_text(80 * "*")
        self.skip()
        self.skip()

        return self.report


