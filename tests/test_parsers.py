import pytest
import os
import pathlib
import decimal
import re

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


# ---------------------------------------------------------------------------
# candidate + rank column format (Clear Ballot: Portland OR, Fort Collins CO)
# ---------------------------------------------------------------------------

crc_dir = dir_path / "parser_test_files/candidate_rank_column"


def _read_csv_rows(path):
    import csv

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        return header, list(reader)


def test_candidate_rank_column_simple():

    parsed = parsers.candidate_rank_column_csv(crc_dir / "simple/cvr.csv")

    S, O = BallotMarks.SKIPPED, BallotMarks.OVERVOTE
    expected = [
        ["Smith", "Doe", S],
        [O, "Write-in Line 1", S],  # Smith + Doe at rank 1 is an overvote
        [S, S, S],
        [O, "Doe", "Doe"],  # two different write-in lines at rank 1 is an overvote
        ["Smith", "Smith", "Smith"],  # duplicate rankings are kept
        ["Doe", "Smith", "Doe"],  # TRUE/true/x are all marks
    ]
    assert parsed["ranks"] == expected

    # non-candidate columns are passed through, candidate columns are not
    assert parsed["BallotID"] == ["b1", "b2", "b3", "b4", "b5", "b6"]
    assert parsed["Precinct"] == ["P1", "P1", "P2", "P2", "P2", "P3"]
    assert "Smith Rank 1" not in parsed
    assert parsed["weight"] == [decimal.Decimal("1")] * 6

    # ignored candidates become skipped marks but still cause overvotes
    parsed = parsers.candidate_rank_column_csv(
        crc_dir / "simple/cvr.csv", ignore_candidates="Write-in Line 1, Write-in Line 2"
    )
    assert parsed["ranks"][1] == [O, S, S]
    assert parsed["ranks"][3] == [O, "Doe", "Doe"]


def test_candidate_rank_column_fort_collins():
    """Excerpt of the Fort Collins 2025 mayoral CVR checked against the RCTab conversion of the same file.
    RCTab writes overvotes as newline-separated candidate lists and skipped ranks as 'undervote'."""

    parsed = parsers.candidate_rank_column_csv(crc_dir / "fort_collins/cvr.csv")

    header, rows = _read_csv_rows(crc_dir / "fort_collins/expected_rctab.csv")
    rank_cols = [i for i, col in enumerate(header) if col.startswith("Rank ")]
    expected = {}
    for row in rows:
        ranks = []
        for i in rank_cols:
            if "\n" in row[i]:
                ranks.append(BallotMarks.OVERVOTE)
            elif row[i] == "undervote":
                ranks.append(BallotMarks.SKIPPED)
            else:
                ranks.append(row[i])
        expected[row[1]] = ranks

    assert len(parsed["ranks"]) == len(expected) == 20
    for cvr_number, ranks in zip(parsed["CvrNumber"], parsed["ranks"]):
        assert ranks == expected[cvr_number]
    assert sum(mark == BallotMarks.OVERVOTE for ranks in parsed["ranks"] for mark in ranks) > 0


def test_candidate_rank_column_portland():
    """Excerpt of the Portland 2024 Council District 1 CVR (3 winners, 3 write-in lines) checked against the
    official rank-format CVR published by the city."""

    header, rows = _read_csv_rows(crc_dir / "portland/expected_rank_cvr.csv")
    rank_cols = [i for i, col in enumerate(header) if col.startswith("rank")]
    # the official rank CVR writes names with dots in place of non-alphanumeric characters
    expected = {row[0]: [re.sub(r"[^A-Za-z0-9]", "", row[i]) for i in rank_cols] for row in rows}
    cvr_path = crc_dir / "portland/cvr.csv"

    # the export contains every ballot style, only style 2 includes this contest
    parsed = parsers.candidate_rank_column_csv(cvr_path)
    assert len(parsed["ranks"]) == 27

    # the official file records lone marks on the "Write-in-1xx" lines as skipped
    parsed = parsers.candidate_rank_column_csv(
        cvr_path,
        filter_column="BallotStyleID",
        filter_values="2",
        ignore_candidates=["Write-in-120", "Write-in-121", "Write-in-122"],
    )
    assert len(parsed["ranks"]) == len(expected) == 22
    for ballot_id, ranks in zip(parsed["BallotID"], parsed["ranks"]):
        assert [re.sub(r"[^A-Za-z0-9]", "", mark) for mark in ranks] == expected[ballot_id]

    marks = [mark for ranks in parsed["ranks"] for mark in ranks]
    assert BallotMarks.OVERVOTE in marks
    assert "Uncertified Write In" in marks
    assert "Michael (Mike) Sands" in marks

    # without ignore_candidates the write-in lines are candidates in their own right
    parsed = parsers.candidate_rank_column_csv(cvr_path, filter_column="BallotStyleID", filter_values=["2"])
    n_diff = 0
    for ballot_id, ranks in zip(parsed["BallotID"], parsed["ranks"]):
        for mark, expected_mark in zip(ranks, expected[ballot_id]):
            if re.sub(r"[^A-Za-z0-9]", "", mark) != expected_mark:
                assert mark.startswith("Write-in-") and expected_mark == BallotMarks.SKIPPED
                n_diff += 1
    assert n_diff > 0

    # the contest can be named explicitly
    parsed = parsers.candidate_rank_column_csv(cvr_path, contest="District 1", filter_column="BallotStyleID", filter_values="2")
    assert len(parsed["ranks"]) == 22
    with pytest.raises(ValueError):
        parsers.candidate_rank_column_csv(cvr_path, contest="District 2")
    with pytest.raises(ValueError):
        parsers.candidate_rank_column_csv(cvr_path, filter_column="NotAColumn", filter_values="2")


def test_candidate_rank_column_two_contests():

    cvr_path = crc_dir / "two_contests/cvr.csv"

    with pytest.raises(ValueError):
        parsers.candidate_rank_column_csv(cvr_path)

    # candidate_codes.csv next to the CVR renames candidates
    parsed = parsers.candidate_rank_column_csv(cvr_path, contest="Mayor")
    assert parsed["ranks"] == [["Ann Adams", "Bob Brown"], ["Bob Brown", "Ann Adams"]]
    assert set(parsed) == {"ranks", "id", "weight"}

    parsed = parsers.candidate_rank_column_csv(cvr_path, contest="Council")
    assert parsed["ranks"] == [["Cat"], ["Dan"]]


def test_candidate_rank_column_unrecognized_headers():
    with pytest.raises(ValueError):
        parsers.candidate_rank_column_csv(crc_dir / "unrecognized/cvr.csv")


def test_candidate_rank_column_registered():
    assert parsers.get_parser_dict()["candidate_rank_column_csv"] is parsers.candidate_rank_column_csv
