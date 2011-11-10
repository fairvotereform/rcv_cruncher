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

    def __init__(self, election_name):
        self.election_name = election_name
        self.contest_infos = []

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

    def add_text(self, text):
        self.text += "%s\n" % text

    def _add_header(self, text, sep_char, label=None):
        divider = len(text) * sep_char

        if label is not None:
            text = "<a name='%s'>%s</name>" % (label, text)

        self.add_text(text)
        self.add_text(divider)
        self.skip()

    def add_title(self, text, label=None):
        self._add_header(text, "=", label)

    def add_section_title(self, text):
        self.skip()
        self._add_header(text, "-")

    def add_candidate_names(self, header, candidate_ids, candidate_dict):
        self.add_text("%s:" % header)
        for candidate_id in candidate_ids:
            name = candidate_dict[candidate_id]
            self.add_text(3 * " " + name)
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
        self.add_text("")

    def write_header(self):
        s = """\
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    </head>
<body>
<pre>
%s
""" % (self.election_name)

        self.add_text(s)

    def write_contents(self):
        self.add_title("Table of Contents")
        
        index = 0
        for contest_info in self.contest_infos:
            contest_label = contest_info[0]
            contest = contest_info[1]

            index += 1
            self.add_text("<a href='#%s'>(%s) %s</a>" % (contest_label, index, contest.name))

        self.add_divider()

    def write_footer(self):
        s = """\
</pre>
</body>
</html>
"""
        self.add_text(s)

    def add_contest(self, contest_label, contest, stats, download_url, download_time):
        self.contest_infos.append((contest_label, contest, stats, download_url, download_time))

    # TODO: refactor this method to be smaller.
    def _write_contest(self, contest_info):
        contest_label = contest_info[0]
        contest = contest_info[1]
        stats = contest_info[2]
        download_url = contest_info[3]
        download_time = contest_info[4]

        # TODO: eliminate the need to set self.stats.
        self.stats = stats

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


        self.add_title(contest.name + " RCV Stats", contest_label)

        self.add_candidate_names(LABELS['winner'], [contest.winner_id], contest.candidate_dict)
        self.add_candidate_names(LABELS['finalists'], contest.finalist_ids, contest.candidate_dict)

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

        self.add_section_title("Candidate support, in descending order of first round totals")

        self.add_text("[(1) First round, and (2) validly ranked anywhere, as percent of first-round continuing.]")
        self.skip()

        for candidate_id, name, first_round in self.sorted_candidates:
            self.add_data2(name, first_round, stats.first_round_continuing, stats.ranked_anywhere[candidate_id], stats.first_round_continuing)

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

        self.add_text("[Percent represented is relative to first-round continuing.]")
        self.skip()

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

            strings = [label_string, percent_string, self.value_string(win_count), self.value_string(total_count), percent_of_voted_string]

            s = "%s %s (%s / %s) (%s represented)" % tuple(strings)

            self.add_text(s)

        self.add_section_title("Truly exhausted ballots, by first choice")

        self.add_data(LABELS['all'], stats.true_exhaust, total=stats.true_exhaust)
        self.skip()

        true_exhaust_data = []
        for candidate_id, name, first_round in self.sorted_candidates:
            true_exhaust_data.append((stats.true_exhaust_by_first_round[candidate_id], name))
        true_exhaust_data.sort()
        true_exhaust_data.reverse()
        
        for data in true_exhaust_data:
            self.add_data(data[1], data[0], total=stats.true_exhaust)

        self.skip()
        self.add_text("[Data downloaded from %s" % download_url)
        self.add_text(" on %s.]" % download_time)

        self.add_divider()

    def add_divider(self):
        self.skip()
        self.add_text(80 * "*")
        self.add_text(80 * "*")
        self.skip()

    def generate(self):
        self.text = ""
        self.write_header()
        self.write_contents()

        for contest_info in self.contest_infos:
            self._write_contest(contest_info)

        self.write_footer()
        
        return self.text
