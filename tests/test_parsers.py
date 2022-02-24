import pytest
import os
import pathlib

from rcv_cruncher.marks import BallotMarks
import rcv_cruncher.parsers as parsers

dir_path = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))


def test_candidate_column():

    expected_ballots = [
        ["A", "B", "C", "D"],
        ["D", "C", "B", "A"],
        [
            BallotMarks.SKIPPED,
            BallotMarks.SKIPPED,
            BallotMarks.SKIPPED,
            BallotMarks.SKIPPED,
        ],
        ["A", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "B"],
        [BallotMarks.SKIPPED, "A", "C", BallotMarks.SKIPPED],
        [BallotMarks.SKIPPED, "C", "D", BallotMarks.SKIPPED],
        [BallotMarks.SKIPPED, "C", "B", BallotMarks.SKIPPED],
        [BallotMarks.SKIPPED, "A", BallotMarks.SKIPPED, BallotMarks.SKIPPED],
        [BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED, "B"],
        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
        [BallotMarks.SKIPPED, "D", BallotMarks.SKIPPED, BallotMarks.SKIPPED],
    ]

    test_cvr_path = dir_path / "parser_test_files/candidate_column/test1"
    calc_ballot_dict = parsers.candidate_column_csv(test_cvr_path)

    assert expected_ballots == calc_ballot_dict["ranks"]
