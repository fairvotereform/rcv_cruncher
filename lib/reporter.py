# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

import codecs
import logging
import os
import sys

import pystache


_log = logging.getLogger(__name__)

ENCODING_TEMPLATE_FILE = 'utf-8'

LABELS = {
    'total': "Total",
    'voted': "Voted",
    'under': "Undervoted",
    'has_over': "Has_Overvote",
    'has_skip': "Has_Skipped",
    'has_dupe': "Has_Duplicate",
    'dupe3': "Has_Duplicate_3",
    'dupe2': "Has_Duplicate_2",
    'exhaust': "Truly_Exhausted",
    'irregular': "Irregular",
    'over': "Overvoted",
    'continuing': "Continuing",
    'valid': "Valid",
    'all': "All",
    'winner': "Winner",
    'finalists': "Finalists",
    'non-finalists': "Non-finalists",
}


def render_template(template_path, values):
    with codecs.open(template_path, "r", encoding=ENCODING_TEMPLATE_FILE) as f:
        template = f.read()

    rendered = pystache.render(template, values)

    return rendered


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

    def __init__(self, election_name, template_path):
        self.election_name = election_name
        self.template_path = template_path

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

    def make_header_line(self, preceding_text, symbol):
        return len(preceding_text) * symbol

    def _add_header(self, text, sep_char, label=None):

        self.add_text(text)

        header_line = self.make_header_line(text, sep_char)
        self.add_text(header_line)

        self.skip()

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

    def write_value(self, label, value, total=None, total_label=None, description=None):
        """
        Write a line of the form--

        LABEL .....................   9578 (  6.2% of total_label) [description]

        """
        label_string = self.label_string(label)
        percent_string = self.percent_string(value, total)
        value_string = self.value_string(value)
        total_label_string = ("of %s" % total_label) if total_label is not None else ""

        s = "%s %s (%s %s)" % (label_string, value_string, percent_string, total_label_string)

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

    def add_contest(self, contest_label, contest, stats, download_metadata):
        self.contest_infos.append((contest_label, contest, stats, download_metadata))

    # TODO: refactor this method to be smaller.
    def make_contest(self, contest_info):
        self.text = ""

        # TODO: eliminate the need to store the arguments as a tuple.
        contest_label = contest_info[0]
        contest = contest_info[1]
        stats = contest_info[2]

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

        self.add_candidate_names(LABELS['winner'], [contest.winner_id], contest.candidate_dict)
        self.add_candidate_names(LABELS['finalists'], contest.finalist_ids, contest.candidate_dict)

        self.write_value(LABELS['total'], stats.total, total=stats.total, total_label='total')
        self.skip()
        self.write_value(LABELS['voted'], stats.voted, total=stats.total, total_label='total')
        self.write_value(LABELS['under'], stats.undervotes, total=stats.total, total_label='total')

        self.add_section_title("Overview of voted, as percent of voted")

        self.write_value(LABELS['has_dupe'], sum(stats.duplicates.values()), total=stats.voted)
        self.write_value(LABELS['has_over'], stats.has_overvote, total=stats.voted)
        self.write_value(LABELS['has_skip'], stats.has_skipped, total=stats.voted)
        self.write_value(LABELS['irregular'], stats.irregular, total=stats.voted,
                      description="has duplicate, overvote, and/or skip")
        self.skip()

        self.write_value(LABELS['dupe3'], stats.duplicates[3], total=stats.voted)
        self.write_value(LABELS['dupe2'], stats.duplicates[2], total=stats.voted)
        self.skip()

        self.write_value(LABELS['exhaust'], stats.true_exhaust, total=stats.voted,
                      description="3 distinct candidates, none a finalist")

        self.add_section_title("Overview of first round, as percent of voted")

        self.write_value(LABELS['continuing'], stats.first_round_continuing, total=stats.voted)
        self.write_value(LABELS['over'], stats.first_round_overvotes, total=stats.voted)

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

        self.write_value(LABELS['all'], stats.true_exhaust, total=stats.true_exhaust)
        self.skip()

        true_exhaust_data = []
        for candidate_id, name, first_round in self.sorted_candidates:
            true_exhaust_data.append((stats.true_exhaust_by_first_round[candidate_id], name))
        true_exhaust_data.sort()
        true_exhaust_data.reverse()
        
        for data in true_exhaust_data:
            self.write_value(data[1], data[0], total=stats.true_exhaust)

        self.skip()

        return self.text

    def make_divider(self):
        return 2 * ((80 * "*" + "\n"))

    def format_datetime(self, metadata):
        dt = metadata.datetime_local
        tz = metadata.local_tzname
        return "%s %s" % (dt.strftime("%A, %B %d, %Y at %I:%M:%S%p"), tz) 

    def get_oldest_contest_metadata(self):
        contest_infos = list(self.contest_infos)

        def key(info):
            metadata = info[3]
            return metadata.iso_datetime_utc

        contest_infos.sort(key=key)
        oldest_info = contest_infos[0]
        metadata = oldest_info[3]

        return metadata

    def generate(self):

        toc_dicts = []
        contest_dicts = []

        index = 0
        for info in self.contest_infos:
            index += 1

            contest_label = info[0]
            contest = info[1]
            metadata = info[3]

            contest_name = contest.name

            title = contest_name + " RCV Stats"
            header_line = self.make_header_line(title, "=")

            toc_dict = {'label': contest_label,
                        'index': index,
                        'text': contest_name
            }

            url = metadata.url
            datetime_string = self.format_datetime(metadata)

            contest_report = self.make_contest(info)
            contest_dict = {'label': contest_label,
                            'title': title,
                            'line': header_line,
                            'body': contest_report,
                            'download_url': url,
                            'download_datetime': datetime_string,
            }

            toc_dicts.append(toc_dict)
            contest_dicts.append(contest_dict)

        metadata = self.get_oldest_contest_metadata()
        datetime_string = self.format_datetime(metadata)

        values = {'file_encoding': ENCODING_TEMPLATE_FILE,
                  'election_name': self.election_name,
                  'data_datetime': datetime_string,
                  'toc_item': toc_dicts,
                  'contest': contest_dicts,
                  }

        s = render_template(self.template_path, values)

        return s
