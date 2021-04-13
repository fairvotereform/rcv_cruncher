from __future__ import annotations
from typing import (Dict, Iterable, Optional)

import copy


class BallotMarks:

    SKIPPED = 'skipped'
    OVERVOTE = 'overvote'
    WRITEIN = 'writein'

    writein_partial_match_words = ['write']
    writein_anycase_exact_match_words = ['uwi']

    UNDERVOTE = 'undervote'
    PRETALLY_EXHAUST = 'pretally_exhaust'
    MAYBE_EXHAUSTED = 'maybe_exhausted'
    MAYBE_EXHAUSTED_BY_OVERVOTE = 'maybe_exhausted_by_overvote'
    MAYBE_EXHAUSTED_BY_REPEATED_SKIPPED_RANKING = 'maybe_exhausted_by_repeated_skipped_ranking'
    MAYBE_EXHAUSTED_BY_DUPLICATE_RANKING = 'maybe_exhausted_by_duplicate_ranking'

    @staticmethod
    def new_rule_set(combine_writein_marks: bool = False,
                     exclude_writein_marks: bool = False,
                     exclude_duplicate_candidate_marks: bool = False,
                     exclude_overvote_marks: bool = False,
                     exclude_skipped_marks: bool = False,
                     treat_combined_writeins_as_exhaustable_duplicates: bool = False,
                     exhaust_on_duplicate_candidate_marks: bool = False,
                     exhaust_on_overvote_marks: bool = False,
                     exhaust_on_repeated_skipped_marks: bool = False) -> Dict:
        return {
            'combine_writein_marks': combine_writein_marks,
            'exclude_writein_marks': exclude_writein_marks,
            'exclude_duplicate_candidate_marks': exclude_duplicate_candidate_marks,
            'exclude_overvote_marks': exclude_overvote_marks,
            'exclude_skipped_marks': exclude_skipped_marks,
            'treat_combined_writeins_as_exhaustable_duplicates': treat_combined_writeins_as_exhaustable_duplicates,
            'exhaust_on_duplicate_candidate_marks': exhaust_on_duplicate_candidate_marks,
            'exhaust_on_overvote_marks': exhaust_on_overvote_marks,
            'exhaust_on_repeated_skipped_marks': exhaust_on_repeated_skipped_marks
        }

    @staticmethod
    def check_writein_match(mark):
        matched = False

        if not matched:
            for writein_mark in BallotMarks.writein_partial_match_words:
                if writein_mark in mark.lower():
                    matched = True
                    break

        if not matched:
            for writein_mark in BallotMarks.writein_anycase_exact_match_words:
                if writein_mark == mark.lower():
                    matched = True
                    break

        return matched

    @staticmethod
    def combine_writein_marks(ballot_marks: BallotMarks) -> BallotMarks:

        if not isinstance(ballot_marks, BallotMarks):
            raise TypeError('ballot_marks must be BallotMarks object.')

        copy_ballot_marks = copy.deepcopy(ballot_marks)
        new_marks = [BallotMarks.WRITEIN if BallotMarks.check_writein_match(mark) else mark
                     for mark in copy_ballot_marks.marks]
        copy_ballot_marks.update_marks(new_marks)
        return copy_ballot_marks

    @staticmethod
    def remove_mark(ballot_marks: BallotMarks, remove_marks: Iterable) -> BallotMarks:

        if not isinstance(ballot_marks, BallotMarks):
            raise TypeError('ballot_marks must be BallotMarks object.')

        if isinstance(remove_marks, str):
            raise TypeError('remove_marks must be Iterable, but cannot be string.')

        copy_ballot_marks = copy.deepcopy(ballot_marks)
        new_marks = copy_ballot_marks.marks
        for remove_mark in remove_marks:
            new_marks = [mark for mark in new_marks if mark != remove_mark]
        copy_ballot_marks.update_marks(new_marks)
        return copy_ballot_marks

    @staticmethod
    def remove_duplicate_candidate_marks(ballot_marks: BallotMarks) -> BallotMarks:

        if not isinstance(ballot_marks, BallotMarks):
            raise TypeError('ballot_marks must be BallotMarks object.')

        copy_ballot_marks = copy.deepcopy(ballot_marks)
        new_marks_list = []
        new_marks_set = set()
        for mark in copy_ballot_marks.marks:
            if mark not in new_marks_set.difference({BallotMarks.OVERVOTE, BallotMarks.SKIPPED}):
                new_marks_list.append(mark)
                new_marks_set = new_marks_set.union({mark})
        copy_ballot_marks.update_marks(new_marks_list)
        return copy_ballot_marks

    def __init__(self, marks: Optional[Iterable] = None) -> None:

        self.marks = []
        self.unique_marks = {}
        self.unique_candidates = {}

        if marks:
            self.update_marks(marks)

        self.rules = {}
        self.inactive_type = None

        # in the future, add functionality to handle overvotes that can be conditionally resolved
        # if all but one of the overvoted candidates is eliminated before the overvote is reached

    def update_marks(self, new_marks: Iterable) -> None:

        if isinstance(new_marks, str):
            raise TypeError('new_marks must be Iterable, but cannot be string.')

        self.marks = list(new_marks)
        self.unique_marks = set(self.marks)
        self.unique_candidates = self.unique_marks - {BallotMarks.SKIPPED, BallotMarks.OVERVOTE}

    def apply_rules(self,
                    combine_writein_marks: bool = False,
                    exclude_writein_marks: bool = False,
                    exclude_duplicate_candidate_marks: bool = False,
                    exclude_overvote_marks: bool = False,
                    exclude_skipped_marks: bool = False,
                    treat_combined_writeins_as_exhaustable_duplicates: bool = False,
                    exhaust_on_duplicate_candidate_marks: bool = False,
                    exhaust_on_overvote_marks: bool = False,
                    exhaust_on_repeated_skipped_marks: bool = False) -> None:

        if self.rules:
            raise RuntimeError('rules have already been applied to this ballot')

        self.rules = {
            'combine_writein_marks': combine_writein_marks,
            'exclude_writein_marks': exclude_writein_marks,
            'exclude_duplicate_candidate_marks': exclude_duplicate_candidate_marks,
            'exclude_overvote_marks': exclude_overvote_marks,
            'exclude_skipped_marks': exclude_skipped_marks,
            'treat_combined_writeins_as_exhaustable_duplicates': treat_combined_writeins_as_exhaustable_duplicates,
            'exhaust_on_duplicate_candidate_marks': exhaust_on_duplicate_candidate_marks,
            'exhaust_on_overvote_marks': exhaust_on_overvote_marks,
            'exhaust_on_repeated_skipped_marks': exhaust_on_repeated_skipped_marks
        }

        all_skipped = None
        specific_exhaust = None

        if self.unique_marks == {BallotMarks.SKIPPED}:
            all_skipped = True
        else:
            all_skipped = False

        # has to occur before exhaustion by duplicates is computed
        if combine_writein_marks and treat_combined_writeins_as_exhaustable_duplicates:
            self.update_marks(self.combine_writein_marks(self).marks)

        new_marks_list = []
        new_marks_set = set()
        for mark_idx, mark in enumerate(self.marks):

            repeated_skipped_marks_present = False
            if mark_idx + 1 < len(self.marks):

                remaining_marks = self.marks[mark_idx+1:]
                next_mark = remaining_marks[0]

                # check for successive skips
                if mark == BallotMarks.SKIPPED and next_mark == BallotMarks.SKIPPED:
                    repeated_skipped_marks_present = True
                else:
                    repeated_skipped_marks_present = False

                # and check if any non-skip marks remain after skips
                if repeated_skipped_marks_present and set(remaining_marks) and set(remaining_marks) != {BallotMarks.SKIPPED}:
                    repeated_skipped_marks_present = True
                else:
                    repeated_skipped_marks_present = False

            if exhaust_on_repeated_skipped_marks and repeated_skipped_marks_present:
                if not self.inactive_type:
                    specific_exhaust = self.MAYBE_EXHAUSTED_BY_REPEATED_SKIPPED_RANKING
                break

            overvote_mark_present = mark == BallotMarks.OVERVOTE
            if exhaust_on_overvote_marks and overvote_mark_present:
                if not self.inactive_type:
                    specific_exhaust = self.MAYBE_EXHAUSTED_BY_OVERVOTE
                break

            duplicate_candidate_mark = mark in new_marks_set.difference({BallotMarks.OVERVOTE, BallotMarks.SKIPPED})
            if exhaust_on_duplicate_candidate_marks and duplicate_candidate_mark:
                if not self.inactive_type:
                    specific_exhaust = self.MAYBE_EXHAUSTED_BY_DUPLICATE_RANKING
                break

            new_marks_list.append(mark)
            new_marks_set = new_marks_set.union({mark})

        self.update_marks(new_marks_list)

        if combine_writein_marks and not treat_combined_writeins_as_exhaustable_duplicates:
            self.update_marks(self.combine_writein_marks(self).marks)

        if exclude_duplicate_candidate_marks:
            self.update_marks(self.remove_duplicate_candidate_marks(self).marks)

        if exclude_overvote_marks:
            self.update_marks(self.remove_mark(self, [BallotMarks.OVERVOTE]).marks)

        if exclude_skipped_marks:
            self.update_marks(self.remove_mark(self, [BallotMarks.SKIPPED]).marks)

        if exclude_writein_marks:
            self.update_marks(self.remove_mark(self, [BallotMarks.WRITEIN]).marks)

        if all_skipped:
            self.inactive_type = self.UNDERVOTE
        elif not self.marks:
            self.inactive_type = self.PRETALLY_EXHAUST
        elif specific_exhaust:
            self.inactive_type = specific_exhaust
        else:
            self.inactive_type = self.MAYBE_EXHAUSTED
