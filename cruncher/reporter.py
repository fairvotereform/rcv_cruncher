# encoding: utf-8
#
# Copyright (C) 2011 Chris Jerdonek.  All rights reserved.
#

import codecs
import logging
from datetime import datetime

import pystache

from cruncher.common import reverse_dict, utc_datetime_to_local_datetime_tzname

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

    return pystache.render(template, values)

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

def make_section_title(text):
    return ["", text, len(text) * '-', ""]

def get_top_dict_totals(mapping, how_many):
    """
    Return a dict mapping total count to list of elements having that total.

    The return value may include more than `how_many` values if there is
    a tie for last place in terms of totals.

    Arguments:
      mapping: dict of element to integer number of occurrences.
    """
    values = sorted(list(set(mapping.values())))[-1*how_many:]
    totals = reverse_dict(mapping, values)
    count = 0
    top_totals = {}
    for value in reversed(values):
        els = totals[value]
        top_totals[value] = els
        count += len(els)
        if count >= how_many:
            break
    return top_totals

def add_top_totals_section(totals, denominator, candidate_dict, sort=False):
    """
    Add a "top totals" section.
    """
    top_totals = get_top_dict_totals(totals, how_many=10)
    lines = []
    index = 1
    for count in reversed(sorted(top_totals.keys())):
        elements = top_totals[count]
        prefix = "{index:{index_width}}.".format(index=index, index_width=len(str(10)))
        for element in elements:
            numerics = make_percent_breakdown(count, denominator)
            names = [candidate_dict[i] for i in element]
            if sort: names.sort()
            lines.append(u"{0} {1}  {2}".format(prefix, numerics, ', '.join(names)))
        # If there was a tie, we might need to jump ahead more than one.
        index += len(elements)
    return lines

def format_datetime_tzname(dt, tzname):
    """
    Return a string to display a datetime and timezone.

    """
    return "%s %s" % (dt.strftime("%A, %B %d, %Y at %I:%M:%S%p"), tzname)

def format_metadata_datetime(metadata):
    """
    Return the metadata datetime as a string for display.

    """
    dt = metadata.datetime_local
    tz = metadata.local_tzname

    return format_datetime_tzname(dt, tz)

class Reporter(object):

    line_break = "\n"

    def __init__(self, election_name, template_path):
        print "initializing...."
        self.election_name = election_name
        self.template_path = template_path
        self.contest_infos = []
        self.text = None
        self.stats = None
        self.left_indent = None
        self.sorted_candidates = None

    def add_text(self, text):
        self.text += text + self.line_break

    def add_lines(self, lines):
        s = self.line_break.join(lines)
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
        return ljust(s, self.left_indent, '.')

    def make_percent_line(self, label, value, total, description=None):
        """
        Return a line of the form--

        LABEL .....................  46.4% ( 84666 / 182362) [description]

        """
        label_string = self.label_string(label)
        percent_string = make_percent_breakdown(value, total)
        description = "" if description is None else " [%s]" % description
        return "%s %s%s" % (label_string, percent_string, description)

    def make_value(self, label, value, total=None,  description=None):
        """
        Return a line of the form--

        LABEL .....................   9578 (  6.2% of total_label) [description]

        """
        s = "%s %s " % (self.label_string(label), make_value_string(value))

        if total is not None:
            s += make_percent_string(value, total)

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

        def equation(strings):
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

        s = "%s %s  %s" % (self.label_string(label), equation(value_strings), equation(percent_strings))

        return s

    def write_value(self, label, value, total=None, description=None):
        self.add_text(self.make_value(label, value, total, description))

    def make_aggregate_number_ranked_line(self, name, candidate_ids):
        if candidate_ids:
            number_ranked_list = [self.stats.get_number_ranked(candidate_id) for candidate_id in candidate_ids]
            number_ranked = map(sum, zip(*number_ranked_list))
        else:
            number_ranked = (0, 0, 0)

        return self.make_three_sum_line(name, number_ranked)

    def add_first_round_percent_data(self, name, value_dict, candidate_ids):
        value = sum([value_dict[candidate_id] for candidate_id in candidate_ids])
        total = sum([self.stats.get_first_round(candidate_id) for candidate_id in candidate_ids])

        self.add_text(self.make_percent_line(name, value, total))

    def make_effective_ballot_position(self, stats):

        lines = make_section_title("Effective ballot position (1st + 2nd + 3rd = any), as percent of first-round continuing")

        for candidate, name in self.sorted_candidates:
            line = self.make_three_sum_line(name, stats.ballot_position[candidate], stats.first_round_continuing)
            lines.append(line)

        return lines

    def make_number_valid_rankings(self, contest, stats):

        lines = make_section_title("Number of distinct candidates validly ranked (3 + 2 + 1), by first-round choice")
        non_finalist_ids = list(set(contest['candidate_ids']) - set(contest['finalists']))
        lines.extend([self.make_aggregate_number_ranked_line(LABELS['all'], contest['candidate_ids']),
                      self.make_aggregate_number_ranked_line(LABELS['winner'], [contest['winner_id']]),
                      self.make_aggregate_number_ranked_line(LABELS['finalists'], contest['finalists']),
                      self.make_aggregate_number_ranked_line(LABELS['non-finalists'], non_finalist_ids)])
        lines.append("")

        for candidate_id, name in self.sorted_candidates:
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

        lines = make_section_title("Overview of final round (%s candidates), as percent of first-round continuing" % len(contest['finalists']))

        lines.append(self.make_value(LABELS['continuing'], final_round_continuing, total=first_round_continuing))
        lines.append(self.make_value(LABELS['exhausted_by_overvote'], exhausted_by_overvote, total=first_round_continuing, description="excludes overvoted"))
        lines.append(self.make_value(LABELS['exhausted'], exhausted, total=first_round_continuing,
            description='does not include overvoted or exhausted-by-overvote'))
        lines.append("")

        lines.append(self.make_value(LABELS['exhausted_involuntary'], exhausted_involuntary, total=first_round_continuing,
            description="3 distinct candidates, no finalists"))
        lines.append(self.make_value(LABELS['exhausted_voluntary'], exhausted_voluntary, total=first_round_continuing))
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


    def make_contest(self, contest_info):
        self.text = ""

        contest = contest_info[0]
        stats = contest_info[0]['stats']

        # TODO: eliminate the need to set self.stats.
        self.stats = stats

        self.left_indent = max(map(len, LABELS.values() + contest['candidate_dict'].values())) + 1
        self.sorted_candidates = sorted(contest['candidate_dict'].items(), 
                                        key=lambda x: -stats.get_first_round(x[0]))

        winner_header = "%s (%d candidates)" % (LABELS['winner'], contest['candidate_count'])
        self.add_candidate_names(winner_header, [contest['winner_id']], contest['candidate_dict'])
        self.add_candidate_names(LABELS['finalists'], contest['finalists'], contest['candidate_dict'])

        self.write_value(LABELS['total'], stats.total, total=stats.total)
        self.skip()
        self.write_value(LABELS['voted'], stats.voted, total=stats.total)
        self.write_value(LABELS['under'], stats.undervotes, total=stats.total)

        self.add_section_title("Overview of voted, as percent of voted")
        self.write_value(LABELS['has_dupe'], stats.has_dup, total=stats.voted)
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

        self.add_lines(self.make_final_round(contest, stats))
        self.add_lines(self.make_effective_ballot_position(stats))
        self.add_lines(self.make_number_valid_rankings(contest, stats))

        self.add_section_title("Ballots validly ranking the winner, by first-round choice")

        self.add_first_round_percent_data(LABELS['all'], stats.ranked_winner, contest['candidate_ids'])
        self.skip()

        for candidate_id, name in self.sorted_candidates:
            self.add_first_round_percent_data(name, stats.ranked_winner, [candidate_id])

        self.add_section_title("Ballots validly ranking a finalist, by first-round choice")

        self.add_first_round_percent_data(LABELS['all'], stats.ranked_finalist, contest['candidate_ids'])
        self.skip()

        for candidate_id, name in self.sorted_candidates:
            self.add_first_round_percent_data(name, stats.ranked_finalist, [candidate_id])

        self.add_section_title("Ballots ranking the same candidate 3 times")

        self.add_first_round_percent_data(LABELS['all'], stats.did_sweep, contest['candidate_ids'])
        self.skip()

        for candidate_id, name in self.sorted_candidates:
            self.add_first_round_percent_data(name, stats.did_sweep, [candidate_id])

        self.add_section_title("Condorcet support for winner against each candidate, in ascending order")

        self.add_text("[Percent represented is relative to first-round continuing.]")
        self.skip()

        # TODO: move the condorcet code below into a method.
        condorcet_data = []
        for candidate_id, name in self.sorted_candidates:
            if candidate_id != contest['winner_id']:
                win_count, total_count = stats.get_condorcet_support(contest['winner_id'], candidate_id)
                condorcet_data.append((win_count, total_count, name))

        print condorcet_data

        for win_count, total_count, name in sorted(condorcet_data):
            # BOB  60% (600 / 1000 = 20% of first-round continuing)
            label_string = self.label_string(name)
            percent_breakdown = make_percent_breakdown(win_count, total_count)
            percent_of_voted_string = make_percent_string(total_count, stats.first_round_continuing)
            self.add_text("{} {} ({} represented)".format(label_string, percent_breakdown, percent_of_voted_string))

        condorcet_winner = stats.is_condorcet_winner(contest['winner_id'], contest['candidate_ids'])
        self.add_text("\n(condorcet_winner=%s)" % "YES" if condorcet_winner else "NO")
        self.add_section_title("Involuntary exhausted ballots, by first choice")

        self.write_value(LABELS['all'], stats.truly_exhausted_total, total=stats.truly_exhausted_total)
        self.skip()

        true_exhaust_data = [(stats.truly_exhausted[candidate], name)
                                for candidate, name in self.sorted_candidates]

        for data in reversed(sorted(true_exhaust_data)):
            self.write_value(data[1], data[0], total=stats.truly_exhausted_total)

        self.add_lines(make_section_title("Top 10 effective orderings"))
        self.add_lines(add_top_totals_section(
                        stats.orderings, 
                        stats.first_round_continuing, 
                        contest['candidate_dict']))
        self.add_lines(make_section_title("Top 10 effective combinations"))
        self.add_lines(add_top_totals_section(
                        stats.combinations, 
                        stats.first_round_continuing, 
                        contest['candidate_dict'],
                        sort=True))
        self.skip()
        return self.text

    def get_oldest_contest_metadata(self):
        """
        Return the metadata for the earliest downloaded contest.

        """
        # Make a copy because list.sort() sorts in place.
        contest_infos = list(self.contest_infos)

        def key(info):
            metadata = info[-1]
            return metadata.iso_datetime_utc

        contest_infos.sort(key=key)
        oldest_info = contest_infos[0]
        return oldest_info[-1]


    #streamline this 
    def generate(self):
        toc_dicts = []
        contest_dicts = []

        for i, info in enumerate(self.contest_infos):

            contest_label = info[0]['label']
            metadata = info[-1]

            contest_name = info[0]['contest_name']
            contest_finalists = info[0]['finalists']
            contest_elimination_rounds = len(info[0]['finalists']) != len(info[0]['candidate_ids'])

            if contest_elimination_rounds and len(contest_finalists) > 2:
                contest_name += " (%d finalists)" % len(contest_finalists)

            title = contest_name + " RCV Stats"

            count = 0
            for name in info[0]['candidate_dict'].values():
                if name.upper() != "WRITE-IN":
                    count += 1

            info[0]['candidate_count'] = count
            toc_dicts.append({
                'candidate_count': count,
                'label': contest_label,
                'index': i+1,
                'text': contest_name,
                'elimination_rounds': contest_elimination_rounds,
            })

            url = metadata.url
            datetime_string = format_metadata_datetime(metadata) if url else ''
            contest_report = self.make_contest(info)
            contest_dicts.append({
                'label': contest_label,
                'title': title,
                'line': len(title) * "=",
                'round_by_round_url': info[0].get('url'),
                'body': contest_report,
                'download_urls': url,
                'download_datetime': datetime_string,
                'elimination_rounds': contest_elimination_rounds,
            })

        dt, tz = utc_datetime_to_local_datetime_tzname(datetime.utcnow())
        metadata = self.get_oldest_contest_metadata()
        return render_template(self.template_path, {
                'file_encoding': ENCODING_TEMPLATE_FILE,
                'election_name': self.election_name,
                'generated_datetime': format_datetime_tzname(dt, tz),
                'data_datetime': format_metadata_datetime(metadata) if metadata.url else '',
                'toc_item': toc_dicts,
                'contest': contest_dicts,
                })


