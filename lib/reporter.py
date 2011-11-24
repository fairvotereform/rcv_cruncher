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
    'exhausted': "Exhausted",
    'exhausted_by_overvote': "Exhausted_by_overvote",
    'exhausted_involuntary': "exhausted_involuntary",
    'exhausted_voluntary': "exhausted_voluntary",
    'irregular': "Irregular",
    'over': "Overvoted",
    'continuing': "Continuing",
    'valid': "Valid",
    'all': "All",
    'winner': "Winner",
    'finalists': "Finalists",
    'non-finalists': "Non-finalists",
    'mandate_final_round': "Mandate_Final_Round",
    'mandate_first_round': "Mandate_Valid",
    'mandate_minimum': "Mandate_Minimum",
    'mandate_voted': "Mandate_Voted",
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

    line_break = "\n"
    candidate_indent = 12

    def __init__(self, election_name, template_path):
        self.election_name = election_name
        self.template_path = template_path

        self.contest_infos = []

    def add_contest(self, contest_label, contest, stats, download_metadata):
        self.contest_infos.append((contest_label, contest, stats, download_metadata))

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

    def make_string(self, lines):
        return self.line_break.join(lines)

    # DEPRECATED
    def add_text(self, text):
        self.text += text + self.line_break

    def add_lines(self, lines):
        s = self.make_string(lines)
        self.add_text(s)

    def skip(self):
        self.add_text("")

    def make_header_line(self, preceding_text, symbol):
        return len(preceding_text) * symbol

    def make_section_title(self, text):
        header_line = self.make_header_line(text, "-")
        return ["", text, header_line, ""]

    def add_section_title(self, text):
        lines = self.make_section_title(text)
        self.add_lines(lines)

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

    def make_percent_line(self, label, value, total, description=None):
        """
        Return a line of the form--

        LABEL .....................  46.4% ( 84666 / 182362) [description]

        """
        label_string = self.label_string(label)
        percent_string = self.percent_string(value, total)
        value_string = self.value_string(value)
        total_string = self.value_string(total)

        s = "%s %s (%s / %s)" % (label_string, percent_string, value_string, total_string)

        if description is not None:
            s += " [%s]" % description

        return s

    def make_value(self, label, value, total=None, total_label=None, description=None):
        """
        Return a line of the form--

        LABEL .....................   9578 (  6.2% of total_label) [description]

        """
        s = "%s %s" % (self.label_string(label), self.value_string(value))
        
        if total is not None:
            percent_string = self.percent_string(value, total)
            total_label_string = ("of %s" % total_label) if total_label is not None else ""
            
            s += " (%s %s)" % (percent_string, total_label_string)

        if description is not None:
            s += " [%s]" % description

        return s

    def make_three_sum_line(self, label, values, total=None):
        """
        Return a line of the form--

        TONY HALL .....................   6590 +   4256 +   3911 =  14757    3.6% +   2.3% +   2.1% =   8.1%
        
        """
        values = list(values)  # Some callers pass a tuple.

        leave_off_total_percent = total is None

        if total is None:
            total = sum(values)

        def format(strings):
            if len(strings) > 3:
                last = strings.pop()
            else:
                last = None
            return " + ".join(strings) + (" = " + last if last is not None else "")

        values.append(sum(values))

        value_strings = [self.value_string(value) for value in values]
        percent_strings = [self.percent_string(value, total) for value in values]
        
        if leave_off_total_percent:
            # Then the 100% doesn't say more.
            percent_strings.pop()

        s = "%s %s  %s" % (self.label_string(label), format(value_strings), format(percent_strings))

        return s

    def write_value(self, label, value, total=None, total_label=None, description=None):
        s = self.make_value(label, value, total, total_label, description)
        self.add_text(s)

    # TODO: find a nicer abstraction of this functionality.
    def add_data2(self, name, value1, total1, value2, total2):
        label_string = self.label_string(name)

        def data_pair_string(value, total):
            value_string = self.value_string(value)
            percent_string = self.percent_string(value, total)

            return "%s ( %s )" % (value_string, percent_string)

        s = "%s %s   %s" % (label_string, data_pair_string(value1, total1), data_pair_string(value2, total2))

        self.add_text(s)

    def add_number_ranked(self, name, number_ranked):
        first_round = sum(number_ranked)

        label_string = self.label_string(name)
        percent_strings = [self.rounded_percent_string(value, first_round) for value in number_ranked]
        number_ranked_strings = [str(value) for value in number_ranked]

        strings = [label_string] + percent_strings + [first_round] + number_ranked_strings

        s = "%s %s %s %s (%s = %s + %s + %s)" % tuple(strings)

        self.add_text(s)

    def make_aggregate_number_ranked_line(self, name, candidate_ids):
        # TODO: make this elegant.
        if candidate_ids:
            number_ranked_list = [self.stats.get_number_ranked(candidate_id) for candidate_id in candidate_ids]
            number_ranked = map(sum, zip(*number_ranked_list))
        else:
            number_ranked = (0, 0, 0)

        line = self.make_three_sum_line(name, number_ranked)

        return line

    def add_first_round_percent_data(self, name, value_dict, candidate_ids):
        value = sum([value_dict[candidate_id] for candidate_id in candidate_ids])
        total = sum([self.stats.get_first_round(candidate_id) for candidate_id in candidate_ids])

        s = self.make_percent_line(name, value, total)
        self.add_text(s)

    def make_effective_ballot_position(self, stats):

        lines = self.make_section_title("Effective ballot position (1st + 2nd + 3rd = any), as percent of first-round continuing")

        for candidate, name, first_round in self.sorted_candidates:
            line = self.make_three_sum_line(name, stats.ballot_position[candidate], stats.first_round_continuing)
            lines.append(line)

        return lines

    def make_number_valid_rankings(self, contest, stats):

        lines = self.make_section_title("Number of candidates validly ranked (3 + 2 + 1), by first-round choice")

        lines.extend([self.make_aggregate_number_ranked_line(LABELS['all'], contest.candidate_ids),
                      self.make_aggregate_number_ranked_line(LABELS['winner'], [contest.winner_id]),
                      self.make_aggregate_number_ranked_line(LABELS['finalists'], contest.finalists),
                      self.make_aggregate_number_ranked_line(LABELS['non-finalists'], contest.non_finalist_ids)])
        lines.append("")

        for candidate_id, name, first_round in self.sorted_candidates:
            number_ranked = stats.get_number_ranked(candidate_id)
            line = self.make_three_sum_line(name, number_ranked)
            lines.append(line)

        return lines

    def make_final_round(self, contest, stats):
        """
        Return final-round overview as lines.

        """
        first_round_continuing = stats.first_round_continuing

        final_round_continuing = stats.final_round_continuing
        exhausted_by_overvote = stats.exhausted_by_overvote
        exhausted = stats.exhausted

        exhausted_involuntary = stats.truly_exhausted_total
        exhausted_voluntary = exhausted - exhausted_involuntary

        winner_total = stats.final_round_winner_total

        lines = self.make_section_title("Overview of final round (%s candidates), as percent of first-round continuing" % len(contest.finalists))

        total_label = None
        lines.append(self.make_value(LABELS['continuing'], final_round_continuing, total=first_round_continuing, total_label=total_label))
        lines.append(self.make_value(LABELS['exhausted_by_overvote'], exhausted_by_overvote, total=first_round_continuing, total_label=total_label,
            description="excludes overvoted"))
        lines.append(self.make_value(LABELS['exhausted'], exhausted, total=first_round_continuing, total_label=total_label,
            description='does not include overvoted or exhausted-by-overvote'))
        lines.append("")

        lines.append(self.make_value(LABELS['exhausted_involuntary'], exhausted_involuntary, total=first_round_continuing, total_label=total_label,
            description="3 distinct candidates, no finalists"))
        lines.append(self.make_value(LABELS['exhausted_voluntary'], exhausted_voluntary, total=first_round_continuing, total_label=total_label))
        lines.append("")

        lines.append(self.make_value(LABELS['winner'], winner_total))
        lines.append("")

        lines.append(self.make_percent_line(LABELS['mandate_final_round'], stats.final_round_winner_total, final_round_continuing))
        lines.append(self.make_percent_line(LABELS['mandate_minimum'], stats.final_round_winner_total, final_round_continuing + exhausted_involuntary,
            description='final-round continuing and involuntary exhausted'))
        lines.append(self.make_percent_line(LABELS['mandate_first_round'], stats.final_round_winner_total, first_round_continuing,
            description='first-round continuing'))
        lines.append(self.make_percent_line(LABELS['mandate_voted'], stats.final_round_winner_total, stats.voted))

        return lines

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
        self.add_candidate_names(LABELS['finalists'], contest.finalists, contest.candidate_dict)

        self.write_value(LABELS['total'], stats.total, total=stats.total, total_label='total')
        self.skip()
        self.write_value(LABELS['voted'], stats.voted, total=stats.total, total_label='total')
        self.write_value(LABELS['under'], stats.undervotes, total=stats.total, total_label='total')

        self.add_section_title("Overview of voted, as percent of voted")

        self.write_value(LABELS['has_dupe'], sum(stats.duplicates.values()), total=stats.voted)
        self.write_value(LABELS['has_over'], stats.has_overvote, total=stats.voted)
        self.write_value(LABELS['has_skip'], stats.has_skipped, total=stats.voted)
        self.write_value(LABELS['irregular'], stats.irregular, total=stats.voted,
                         description="duplicate, overvote, and/or skip")
        self.skip()

        self.write_value(LABELS['dupe3'], stats.duplicates[3], total=stats.voted)
        self.write_value(LABELS['dupe2'], stats.duplicates[2], total=stats.voted)

        self.add_section_title("Overview of first round, as percent of voted")

        self.write_value(LABELS['continuing'], stats.first_round_continuing, total=stats.voted)
        self.write_value(LABELS['over'], stats.first_round_overvotes, total=stats.voted)

        lines = self.make_final_round(contest, stats)
        lines.extend(self.make_effective_ballot_position(stats))
        lines.extend(self.make_number_valid_rankings(contest, stats))

        self.add_lines(lines)

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

        self.add_section_title("Involuntary exhausted ballots, by first choice")

        self.write_value(LABELS['all'], stats.truly_exhausted_total, total=stats.truly_exhausted_total)
        self.skip()

        true_exhaust_data = []
        for candidate, name, first_round in self.sorted_candidates:
            true_exhaust_data.append((stats.truly_exhausted[candidate], name))
        true_exhaust_data.sort()
        true_exhaust_data.reverse()
        
        for data in true_exhaust_data:
            self.write_value(data[1], data[0], total=stats.truly_exhausted_total)

        return self.text

    def format_datetime_tzname(self, dt, tzname):
        """
        Return a string to display a datetime and timezone.

        """
        return "%s %s" % (dt.strftime("%A, %B %d, %Y at %I:%M:%S%p"), tzname) 

    def format_metadata_datetime(self, metadata):
        """
        Return the metadata datetime as a string for display.

        """
        dt = metadata.datetime_local
        tz = metadata.local_tzname

        return self.format_datetime_tzname(dt, tz)

    def get_oldest_contest_metadata(self):
        """
        Return the metadata for the earliest downloaded contest.

        """
        # Make a copy because list.sort() sorts in place.
        contest_infos = list(self.contest_infos)

        def key(info):
            metadata = info[3]
            return metadata.iso_datetime_utc

        contest_infos.sort(key=key)
        oldest_info = contest_infos[0]
        metadata = oldest_info[3]

        return metadata

    def generate(self, generated_datetime, generated_tzname):

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
            datetime_string = self.format_metadata_datetime(metadata)

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

        generated_datetime_string = self.format_datetime_tzname(generated_datetime, generated_tzname)

        metadata = self.get_oldest_contest_metadata()
        data_datetime_string = self.format_metadata_datetime(metadata)

        values = {'file_encoding': ENCODING_TEMPLATE_FILE,
                  'election_name': self.election_name,
                  'generated_datetime': generated_datetime_string,
                  'data_datetime': data_datetime_string,
                  'toc_item': toc_dicts,
                  'contest': contest_dicts,
                  }

        s = render_template(self.template_path, values)

        return s
