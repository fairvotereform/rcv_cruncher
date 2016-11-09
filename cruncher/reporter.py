# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

import codecs
import logging
import os
import sys

import pystache

from cruncher.common import reverse_dict

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


def make_value_string(value):
    return "%6d" % value


def make_percent_string(part, whole):
    """
    Return a percent string, for example, " 12.5%".
    """
    return "%5.1f%%" % percent(part, whole)


def make_percent_breakdown(value, total):
    percent_string = make_percent_string(value, total)
    value_string = make_value_string(value)
    total_string = make_value_string(total)
    return "%s (%s / %s)" % (percent_string, value_string, total_string)


def make_header_line(preceding_text, symbol):
    return len(preceding_text) * symbol


def make_section_title(text):
    header_line = make_header_line(text, "-")
    return ["", text, header_line, ""]


def get_top_dict_totals(mapping, how_many):
    """
    Return a dict mapping total count to list of elements having that total.

    The return value may include more than `how_many` values if there is
    a tie for last place in terms of totals.

    Arguments:
      mapping: dict of element to integer number of occurrences.
    """
    # Call set() to remove duplicates.
    values = list(set(mapping.values()))
    values.sort()
    values = values[-1 * how_many:]
    # Totals is a dict from integer totals to lists of objects having that total.
    totals = reverse_dict(mapping, values)
    # Now limit to "how_many" values in case of multiple values.
    count = 0
    top_totals = {}
    values.reverse()  # Order largest to smallest.
    for value in values:
        els = totals[value]
        top_totals[value] = els
        count += len(els)
        if count >= how_many:
            break
    return top_totals


class ContestWriter(object):

    def __init__(self, contest):
        self.contest = contest

    def get_candidate_name(self, candidate_id):
        name = self.contest.candidate_dict[candidate_id]
        return name

    def display_ordering(self, candidate_ids):
        to_string = self.get_candidate_name
        text = ", ".join([to_string(id_) for id_ in candidate_ids])
        return text

    def display_combination(self, candidate_ids):
        to_string = self.get_candidate_name
        names = [to_string(id_) for id_ in candidate_ids]
        names.sort()
        return ", ".join(names)

    def add_section(self, lines, func, **kwargs):
        section_lines = []
        title = func(section_lines, **kwargs)
        lines.extend(make_section_title(title))
        lines.extend(section_lines)

    def add_top_totals_section(self, lines, totals, denominator, display, how_many):
        """
        Add a "top totals" section.
        """
        top_totals = get_top_dict_totals(totals, how_many=how_many)

        index = 1
        total_counts = top_totals.keys()
        total_counts.sort()
        total_counts.reverse()
        index_width = len(str(how_many))

        for count in total_counts:
            elements = top_totals[count]
            prefix = "{index:{index_width}}.".format(index=index, index_width=index_width)
            for element in elements:
                numerics = make_percent_breakdown(count, denominator)
                info = display(element)
                # Without making the format string unicode, we got an
                # error like the following if "info" contained a non-ascii
                # character:
                # > UnicodeEncodeError: 'ascii' codec can't encode character
                #  u'\xd1' in position 46: ordinal not in range(128)
                line = u"{0} {1}  {2}".format(prefix, numerics, info)
                lines.append(line)
            # If there was a tie, we might need to jump ahead more than one.
            index += len(elements)

    def make_orderings_section(self, lines, stats):
        title = "Top 10 effective orderings"
        self.add_top_totals_section(lines=lines, totals=stats.orderings,
            denominator=stats.first_round_continuing, display=self.display_ordering,
            how_many=10)
        return title

    def make_combinations_section(self, lines, stats):
        title = "Top 10 effective combinations"
        self.add_top_totals_section(lines=lines, totals=stats.combinations,
            denominator=stats.first_round_continuing, display=self.display_combination,
            how_many=10)
        return title


class Reporter(object):

    line_break = "\n"
    candidate_indent = 12

    def __init__(self, election_name, template_path):
        self.election_name = election_name
        self.template_path = template_path

        self.contest_infos = []

    def add_contest(self, contest_info, download_metadata):
        contest_config = contest_info.config

        contest_label = contest_config.label
        contest = contest_info.contest
        round_by_round_url = contest_config.round_by_round_url
        stats = contest_info.stats

        self.contest_infos.append((contest_label, contest, stats,
                                   download_metadata, round_by_round_url))

    def rounded_percent_string(self, part, whole):
        """
        Return a rounded percent string, for example, " 25%".

        """
        return "%3.0f%%" % percent(part, whole)

    def make_string(self, lines):
        return self.line_break.join(lines)

    # TODO: remove in favor of add_lines().
    def add_text(self, text):
        self.text += text + self.line_break

    def add_lines(self, lines):
        s = self.make_string(lines)
        self.add_text(s)

    def skip(self):
        self.add_text("")

    def add_section_title(self, text):
        lines = make_section_title(text)
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

    def make_percent_line(self, label, value, total, description=None):
        """
        Return a line of the form--

        LABEL .....................  46.4% ( 84666 / 182362) [description]

        """
        label_string = self.label_string(label)
        percent_string = make_percent_breakdown(value, total)
        description = "" if description is None else " [%s]" % description
        return "%s %s%s" % (label_string, percent_string, description)

    def make_value(self, label, value, total=None, total_label=None, description=None):
        """
        Return a line of the form--

        LABEL .....................   9578 (  6.2% of total_label) [description]

        """
        s = "%s %s" % (self.label_string(label), make_value_string(value))

        if total is not None:
            percent_string = make_percent_string(value, total)
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

        value_strings = [make_value_string(value) for value in values]
        percent_strings = [make_percent_string(value, total) for value in values]

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
            value_string = make_value_string(value)
            percent_string = make_percent_string(value, total)

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

        lines = make_section_title("Effective ballot position (1st + 2nd + 3rd = any), as percent of first-round continuing")

        for candidate, name, first_round in self.sorted_candidates:
            line = self.make_three_sum_line(name, stats.ballot_position[candidate], stats.first_round_continuing)
            lines.append(line)

        return lines

    def make_number_valid_rankings(self, contest, stats):

        lines = make_section_title("Number of distinct candidates validly ranked (3 + 2 + 1), by first-round choice")

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

        lines = make_section_title("Overview of final round (%s candidates), as percent of first-round continuing" % len(contest.finalists))

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

        winner_header = "%s (%d candidates)" % (LABELS['winner'], contest.candidate_count)
        self.add_candidate_names(winner_header, [contest.winner_id], contest.candidate_dict)
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
            percent_breakdown = make_percent_breakdown(win_count, total_count)
            percent_of_voted_string = make_percent_string(total_count, stats.first_round_continuing)

            strings = [label_string, percent_breakdown, percent_of_voted_string]

            s = "%s %s (%s represented)" % tuple(strings)

            self.add_text(s)

        condorcet_winner = stats.is_condorcet_winner(contest.winner_id, contest.candidate_ids)
        self.add_text("\n(condorcet_winner=%s)" % "YES" if condorcet_winner else "NO")
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

        lines = []
        contest_writer = ContestWriter(contest=contest)
        contest_writer.add_section(lines, contest_writer.make_orderings_section, stats=stats)
        contest_writer.add_section(lines, contest_writer.make_combinations_section, stats=stats)
        self.add_lines(lines)

        self.skip()
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
            round_by_round_url = info[4]

            contest_name = contest.name

            if contest.elimination_rounds and len(contest.finalists) > 2:
                contest_name += " (%d finalists)" % len(contest.finalists)

            title = contest_name + " RCV Stats"
            header_line = make_header_line(title, "=")

            toc_dict = {'candidate_count': contest.candidate_count,
                        'label': contest_label,
                        'index': index,
                        'text': contest_name,
                        'elimination_rounds': contest.elimination_rounds,
            }

            url = metadata.url
            datetime_string = self.format_metadata_datetime(metadata) if url else ''

            contest_report = self.make_contest(info)
            contest_dict = {'label': contest_label,
                            'title': title,
                            'line': header_line,
                            'round_by_round_url': round_by_round_url,
                            'body': contest_report,
                            'download_urls': url,
                            'download_datetime': datetime_string,
                            'elimination_rounds': contest.elimination_rounds,
            }

            toc_dicts.append(toc_dict)
            contest_dicts.append(contest_dict)

        generated_datetime_string = self.format_datetime_tzname(generated_datetime, generated_tzname)

        metadata = self.get_oldest_contest_metadata()
        data_datetime_string = self.format_metadata_datetime(metadata) if metadata.url else ''

        values = {'file_encoding': ENCODING_TEMPLATE_FILE,
                  'election_name': self.election_name,
                  'generated_datetime': generated_datetime_string,
                  'data_datetime': data_datetime_string,
                  'toc_item': toc_dicts,
                  'contest': contest_dicts,
                  }

        s = render_template(self.template_path, values)

        return s
