"""
Contains BallotMarks class
"""

from __future__ import annotations
from typing import Callable, Dict, Union, Set, List


class BallotMarks:
    """Wrap up ranking list of a ballot with useful methods."""

    # special non-candidate marks
    SKIPPED = "skipped"
    OVERVOTE = "overvote"
    WRITEIN = "writein"

    writein_partial_match_words = ["write"]
    writein_anycase_exact_match_words = ["uwi"]

    # ballot inactive type possibilities
    UNDERVOTE = "undervote"
    PRETALLY_EXHAUST = "pretally_exhaust"

    MAYBE_EXHAUSTED = "maybe_exhausted"
    MAYBE_EXHAUSTED_BY_OVERVOTE = "maybe_exhausted_by_overvote"
    MAYBE_EXHAUSTED_BY_REPEATED_SKIPPED_RANKING = "maybe_exhausted_by_repeated_skipped_ranking"
    MAYBE_EXHAUSTED_BY_DUPLICATE_RANKING = "maybe_exhausted_by_duplicate_ranking"

    NOT_EXHAUSTED = "not_exhausted"
    POSTTALLY_EXHAUSTED_BY_RANK_LIMIT = "posttally_exhausted_by_rank_limit"
    POSTTALLY_EXHAUSTED_BY_ABSTENTION = "posttally_exhausted_by_abstention"
    POSTTALLY_EXHAUSTED_BY_OVERVOTE = "posttally_exhausted_by_overvote"
    POSTTALLY_EXHAUSTED_BY_REPEATED_SKIPPED_RANKING = "posttally_exhausted_by_repeated_skipped_ranking"
    POSTTALLY_EXHAUSTED_BY_DUPLICATE_RANKING = "posttally_exhausted_by_duplicate_ranking"

    @staticmethod
    def new_rule_set(
        combine_writein_marks: bool = False,
        exclude_writein_marks: bool = False,
        exclude_duplicate_candidate_marks: bool = False,
        exclude_overvote_marks: bool = False,
        exclude_skipped_marks: bool = False,
        treat_combined_writeins_as_exhaustable_duplicates: bool = False,
        exhaust_on_duplicate_candidate_marks: bool = False,
        exhaust_on_overvote_marks: bool = False,
        exhaust_on_repeated_skipped_marks: bool = False,
    ) -> Dict:
        """A constructor of sorts. Returns passed and default parameters as a dictionary.

        :param combine_writein_marks: combine writein marks that match writein patterns, defaults to False
        :type combine_writein_marks: bool, optional
        :param exclude_writein_marks: treat writein marks, defaults to False
        :type exclude_writein_marks: bool, optional
        :param exclude_duplicate_candidate_marks: [description], defaults to False
        :type exclude_duplicate_candidate_marks: bool, optional
        :param exclude_overvote_marks: [description], defaults to False
        :type exclude_overvote_marks: bool, optional
        :param exclude_skipped_marks: [description], defaults to False
        :type exclude_skipped_marks: bool, optional
        :param treat_combined_writeins_as_exhaustable_duplicates: [description], defaults to False
        :type treat_combined_writeins_as_exhaustable_duplicates: bool, optional
        :param exhaust_on_duplicate_candidate_marks: [description], defaults to False
        :type exhaust_on_duplicate_candidate_marks: bool, optional
        :param exhaust_on_overvote_marks: [description], defaults to False
        :type exhaust_on_overvote_marks: bool, optional
        :param exhaust_on_repeated_skipped_marks: [description], defaults to False
        :type exhaust_on_repeated_skipped_marks: bool, optional
        :return: [description]
        :rtype: Dict
        """
        return {
            "combine_writein_marks": combine_writein_marks,
            "exclude_writein_marks": exclude_writein_marks,
            "exclude_duplicate_candidate_marks": exclude_duplicate_candidate_marks,
            "exclude_overvote_marks": exclude_overvote_marks,
            "exclude_skipped_marks": exclude_skipped_marks,
            "treat_combined_writeins_as_exhaustable_duplicates": treat_combined_writeins_as_exhaustable_duplicates,
            "exhaust_on_duplicate_candidate_marks": exhaust_on_duplicate_candidate_marks,
            "exhaust_on_overvote_marks": exhaust_on_overvote_marks,
            "exhaust_on_repeated_skipped_marks": exhaust_on_repeated_skipped_marks,
        }

    @staticmethod
    def check_writein_match(candidate_name: str) -> bool:
        """Returns true if the mark name matches partial or exact writein matching rules.
        Exact matching strings specified in :attr:`BallotMarks.writein_anycase_exact_match_words`.
        Partial matching strings specified in :attr:`BallotMarks.writein_partial_match_words`.

        :param mark: mark name to be checked for writein match
        :type mark: str
        :return: True if mark name is a match to writein conditions, else False.
        :rtype: bool
        """
        matched = False

        if not matched:
            for writein_mark in BallotMarks.writein_partial_match_words:
                if writein_mark in candidate_name.lower():
                    matched = True
                    break

        if not matched:
            for writein_mark in BallotMarks.writein_anycase_exact_match_words:
                if writein_mark == candidate_name.lower():
                    matched = True
                    break

        return matched

    @staticmethod
    def combine_writein_marks(ballot_marks: BallotMarks) -> BallotMarks:
        """Return copied BallotMarks object with any ballot marks that meet
        writein match criteria changed into WRITEIN constant.

        :param ballot_marks: BallotMarks object to copy and combine the writein marks of.
        :type ballot_marks: BallotMarks
        :return: Copied BallotMarks object with matching marks converted to writein constant.
        :rtype: BallotMarks
        """
        copy_ballot_marks = ballot_marks.copy()
        new_marks = [
            BallotMarks.WRITEIN if BallotMarks.check_writein_match(mark) else mark for mark in copy_ballot_marks.marks
        ]
        copy_ballot_marks.update_marks(new_marks)
        return copy_ballot_marks

    @staticmethod
    def remove_mark(ballot_marks: BallotMarks, remove_mark_names: Union[List, Set]) -> BallotMarks:
        """Return a copied BallotMarks object with any ballot marks present in `remove_mark_names` removed.

        :param ballot_marks: Object to copy and remove marks from.
        :type ballot_marks: BallotMarks
        :param remove_mark_names: List or Set of mark names to be removed.
        :type remove_mark_names: List or Set
        :return: Copied object with specified marks removed.
        :rtype: BallotMarks
        """
        remove_set = set(mark for mark in remove_mark_names)
        copy_ballot_marks = ballot_marks.copy()
        new_marks = [mark for mark in copy_ballot_marks.marks if mark not in remove_set]
        copy_ballot_marks.update_marks(new_marks)
        return copy_ballot_marks

    @staticmethod
    def remove_duplicate_candidate_marks(ballot_marks: BallotMarks) -> BallotMarks:
        """Return copied BallotMarks object with duplicated candidate marks removed, including WRITEIN constant.

        :param ballot_marks: Object to copy and from which to remove duplicates.
        :type ballot_marks: BallotMarks
        :return: Copied object with duplicate candidates removed.
        :rtype: BallotMarks
        """
        copy_ballot_marks = ballot_marks.copy()
        new_marks_list = []
        new_marks_set = set()
        for mark in copy_ballot_marks.marks:
            if mark not in new_marks_set.difference({BallotMarks.OVERVOTE, BallotMarks.SKIPPED}):
                new_marks_list.append(mark)
                new_marks_set = new_marks_set.union({mark})
        copy_ballot_marks.update_marks(new_marks_list)
        return copy_ballot_marks

    def __init__(self, marks: List = []) -> None:
        """Constructor

        :param marks: List of mark names, including candidates and special marks, representing ranked choices on a ballot. Defaults to empty list.
        :type marks: List, optional
        """
        self.input_marks = marks

        self.marks = []
        self.unique_marks = {}
        self.unique_candidates = {}

        if marks:
            self.update_marks(marks)

        self.rules = {}
        self.inactive_type = None

        # in the future, add functionality to handle overvotes that can be conditionally resolved
        # if all but one of the overvoted candidates is eliminated before the overvote is reached

    def copy(self) -> BallotMarks:
        """Make a copy.

        :return: Returns a copy of BallotMarks object
        :rtype: BallotMarks
        """
        copy_obj = BallotMarks(self.marks)

        copy_obj.input_marks = [i for i in self.input_marks]
        copy_obj.rules = {k: v for k, v in self.rules.items()}
        copy_obj.inactive_type = self.inactive_type

        return copy_obj

    def update_marks(self, new_marks: List[str]) -> None:
        """Update `marks` property along with `unique_marks` and `unique_candidates`
        based on a new list of marks names.

        :param new_marks: List of new ordered mark names to replace old ones.
        :type new_marks: List
        """
        self.marks = [mark for mark in new_marks]
        self.unique_marks = set(self.marks)
        self.unique_candidates = self.unique_marks - {
            BallotMarks.SKIPPED,
            BallotMarks.OVERVOTE,
        }

    def get_marks(self) -> List:
        """
        :return: List of current marks
        :rtype: List
        """
        return self.marks

    def get_unique_marks(self) -> Set:
        """
        :return: Set of unique marks
        :rtype: Set
        """
        return self.unique_marks

    def get_unique_candidates(self) -> Set:
        """
        :return: Set of unique candidate marks
        :rtype: Set
        """
        return self.unique_candidates

    def clear_rules(self):
        """Put object back to its init state."""
        self.rules = {}
        self.inactive_type = None
        self.update_marks(self.input_marks)

    def apply_rules(
        self,
        combine_writein_marks: bool = False,
        exclude_writein_marks: bool = False,
        exclude_duplicate_candidate_marks: bool = False,
        exclude_overvote_marks: bool = False,
        exclude_skipped_marks: bool = False,
        treat_combined_writeins_as_exhaustable_duplicates: bool = False,
        exhaust_on_duplicate_candidate_marks: bool = False,
        exhaust_on_overvote_marks: bool = False,
        exhaust_on_repeated_skipped_marks: bool = False,
    ) -> None:
        """
        Applies rules to ballot, modifying marks as necessary.

        :param combine_writein_marks: If True, any marks which are guessed to be a write-in candidate are replaced with the constant `BallotMarks.WRITEIN`, defaults to False
        :type combine_writein_marks: bool, optional
        :param exclude_writein_marks: If True, all `BallotMarks.WRITEIN` marks are removed, defaults to False
        :type exclude_writein_marks: bool, optional
        :param exclude_duplicate_candidate_marks: If True, duplicated candidate marks are removed, defaults to False
        :type exclude_duplicate_candidate_marks: bool, optional
        :param exclude_overvote_marks: If True, `BallotMarks.OVERVOTE` marks are removed, defaults to False
        :type exclude_overvote_marks: bool, optional
        :param exclude_skipped_marks: If True, `BallotMarks.SKIPPED` marks are removed, defaults to False
        :type exclude_skipped_marks: bool, optional
        :param treat_combined_writeins_as_exhaustable_duplicates: If True and `combine_writein_marks` is True, duplicate writein marks are considered after they have been combined, defaults to False
        :type treat_combined_writeins_as_exhaustable_duplicates: bool, optional
        :param exhaust_on_duplicate_candidate_marks: If True, ballot is truncated following a duplicated candidate mark, defaults to False
        :type exhaust_on_duplicate_candidate_marks: bool, optional
        :param exhaust_on_overvote_marks: If True, ballot is truncated following a `BallotMarks.OVERVOTE` mark, defaults to False, defaults to False
        :type exhaust_on_overvote_marks: bool, optional
        :param exhaust_on_repeated_skipped_marks: If True, ballot is truncated following at least 2 `BallotMarks.SKIPPED` marks which are followed by a non-skipped mark, defaults to False
        :type exhaust_on_repeated_skipped_marks: bool, optional
        :raises RuntimeError: Raised if rules already applied to this object. To apply fresh rules, first execute the `clean_rules` method.
        """

        if self.rules:
            raise RuntimeError("rules have already been applied to this ballot")

        self.rules = {
            "combine_writein_marks": combine_writein_marks,
            "exclude_writein_marks": exclude_writein_marks,
            "exclude_duplicate_candidate_marks": exclude_duplicate_candidate_marks,
            "exclude_overvote_marks": exclude_overvote_marks,
            "exclude_skipped_marks": exclude_skipped_marks,
            "treat_combined_writeins_as_exhaustable_duplicates": treat_combined_writeins_as_exhaustable_duplicates,
            "exhaust_on_duplicate_candidate_marks": exhaust_on_duplicate_candidate_marks,
            "exhaust_on_overvote_marks": exhaust_on_overvote_marks,
            "exhaust_on_repeated_skipped_marks": exhaust_on_repeated_skipped_marks,
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

                remaining_marks = self.marks[mark_idx + 1 :]
                next_mark = remaining_marks[0]

                # check for successive skips
                if mark == BallotMarks.SKIPPED and next_mark == BallotMarks.SKIPPED:
                    repeated_skipped_marks_present = True
                else:
                    repeated_skipped_marks_present = False

                # and check if any non-skip marks remain after skips
                if (
                    repeated_skipped_marks_present
                    and set(remaining_marks)
                    and set(remaining_marks) != {BallotMarks.SKIPPED}
                ):
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
