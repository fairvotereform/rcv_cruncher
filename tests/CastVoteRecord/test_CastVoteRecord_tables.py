import pytest
import pandas as pd
import numpy as np


from rcv_cruncher.cvr.base import CastVoteRecord
from rcv_cruncher.marks import BallotMarks


add_rule_set_ballots = [
    [
        "A",
        BallotMarks.WRITEIN,
        "write-in",
        BallotMarks.SKIPPED,
        BallotMarks.SKIPPED,
        BallotMarks.OVERVOTE,
        "A",
        "B",
    ],
    [
        BallotMarks.OVERVOTE,
        "Tuwi",
        BallotMarks.WRITEIN,
        "A",
        "B",
        "B",
        "C",
        BallotMarks.SKIPPED,
    ],
]


params = [
    (
        {
            "input": {
                "jurisdiction": "testville",
                "state": "teststate",
                "date": "01/05/2021",
                "year": "2021",
                "office": "chief tester",
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "A", "B", "B"],
                    ],
                    "weight": [2, 2, 3, 3, 3],
                },
            },
            "expected": {
                "tables": [
                    pd.DataFrame(
                        {
                            "Number of Ballots (excluding undervotes and ballots with first round overvote)": [
                                13,
                                4,
                                0,
                                3,
                                0,
                                6,
                            ],
                            "Mean Valid Rankings Used (excluding duplicates)": [
                                2.769,
                                3,
                                0,
                                3,
                                0,
                                2.5,
                            ],
                            "1 Valid Rankings Used - Count": [0, 0, 0, 0, 0, 0],
                            "2 Valid Rankings Used - Count": [5, 2, 0, 0, 0, 3],
                            "3 Valid Rankings Used - Count": [6, 0, 0, 3, 0, 3],
                            "4 Valid Rankings Used - Count": [2, 2, 0, 0, 0, 0],
                            "1 Valid Rankings Used - Percent": [0, 0, 0, 0, 0, 0],
                            "2 Valid Rankings Used - Percent": [
                                round(100 * 5 / 13, 3),
                                50,
                                0,
                                0,
                                0,
                                50,
                            ],
                            "3 Valid Rankings Used - Percent": [
                                round(100 * 6 / 13, 3),
                                0,
                                0,
                                100,
                                0,
                                50,
                            ],
                            "4 Valid Rankings Used - Percent": [
                                round(100 * 2 / 13, 3),
                                50,
                                0,
                                0,
                                0,
                                0,
                            ],
                        },
                        index=[
                            "Any candidate",
                            "A",
                            "B",
                            "C",
                            "D",
                            BallotMarks.WRITEIN,
                        ],
                        dtype=float,
                    )
                ]
            },
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_rank_usage_table(param):
    rcv = CastVoteRecord(**param["input"])

    df = rcv.get_rank_usage_table()

    assert df.index.tolist() == param["expected"]["tables"][0].index.tolist()
    assert df.fillna("NA").to_dict("records") == param["expected"]["tables"][0].fillna("NA").to_dict("records")


params = [
    (
        {
            "input": {
                "jurisdiction": "testville",
                "state": "teststate",
                "date": "01/05/2021",
                "year": "2021",
                "office": "chief tester",
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "A", "B", "B"],
                    ],
                    "weight": [2, 2, 3, 3, 3],
                },
            },
            "expected": {
                "tables": [
                    pd.DataFrame(
                        {
                            "Number of Ballots": [4, 0, 3, 0, 6],
                            "A ranked in top 3": [4, 0, 3, 0, 3],
                            "B ranked in top 3": [2, 0, 3, 0, 3],
                            "C ranked in top 3": [2, 0, 3, 0, 3],
                            "D ranked in top 3": [0, 0, 0, 0, 0],
                            BallotMarks.WRITEIN + " ranked in top 3": [2, 0, 0, 0, 6],
                        },
                        index=["A", "B", "C", "D", BallotMarks.WRITEIN],
                        dtype=float,
                    ),
                    pd.DataFrame(
                        {
                            "Number of Ballots": [4, 0, 3, 0, 6],
                            "A ranked in top 3": [100, 0, 100, 0, 50],
                            "B ranked in top 3": [50, 0, 100, 0, 50],
                            "C ranked in top 3": [50, 0, 100, 0, 50],
                            "D ranked in top 3": [0, 0, 0, 0, 0],
                            BallotMarks.WRITEIN + " ranked in top 3": [50, 0, 0, 0, 100],
                        },
                        index=["A", "B", "C", "D", BallotMarks.WRITEIN],
                        dtype=float,
                    ),
                ]
            },
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_crossover_table(param):
    cvr = CastVoteRecord(**param["input"])

    count_df, percent_df = cvr.get_crossover_tables()

    assert count_df.index.tolist() == param["expected"]["tables"][0].index.tolist()
    assert count_df.fillna("NA").to_dict("records") == param["expected"]["tables"][0].fillna("NA").to_dict("records")

    assert percent_df.index.tolist() == param["expected"]["tables"][1].index.tolist()
    assert percent_df.fillna("NA").to_dict("records") == param["expected"]["tables"][1].fillna("NA").to_dict("records")


params = [
    (
        {
            "input": {"cvr": {"ranks": add_rule_set_ballots}, "format": "rank"},
            "expected": {
                "table": pd.DataFrame(
                    {
                        "rank1": ["A", BallotMarks.OVERVOTE],
                        "rank2": [BallotMarks.WRITEIN, "Tuwi"],
                        "rank3": ["write-in", BallotMarks.WRITEIN],
                        "rank4": [BallotMarks.SKIPPED, "A"],
                        "rank5": [BallotMarks.SKIPPED, "B"],
                        "rank6": [BallotMarks.OVERVOTE, "B"],
                        "rank7": ["A", "C"],
                        "rank8": ["B", BallotMarks.SKIPPED],
                    }
                )
            },
        }
    ),
    (
        {
            "input": {"cvr": {"ranks": add_rule_set_ballots}, "format": "candidate"},
            "expected": {
                "table": pd.DataFrame(
                    {
                        "candidate_A": ["1,7", "4"],
                        "candidate_B": ["8", "5,6"],
                        "candidate_C": [np.nan, "7"],
                        "candidate_Tuwi": [np.nan, "2"],
                        "candidate_write-in": ["3", np.nan],
                        f"candidate_{BallotMarks.WRITEIN}": ["2", "3"],
                        f"candidate_{BallotMarks.OVERVOTE}": ["6", "1"],
                        "rank_limit": [8, 8],
                    }
                )
            },
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_get_cvr_table(param):

    cast_vote_record = CastVoteRecord(parsed_cvr=param["input"]["cvr"])
    table = cast_vote_record.get_cvr_table(table_format=param["input"]["format"])

    for col in table.columns:
        assert table[col].equals(param["expected"]["table"][col])
