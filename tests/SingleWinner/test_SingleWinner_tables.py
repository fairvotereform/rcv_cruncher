import pytest

import pandas as pd

import rcv_cruncher.util as util
from rcv_cruncher.marks import BallotMarks
from rcv_cruncher.rcv.variants import SingleWinner

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
                "condorcet_winner": "A",
                "tables": [
                    pd.DataFrame(
                        {
                            "A": [util.NAN, 3, 3, 0, 6],
                            "B": [10, util.NAN, 6, 0, 8],
                            "C": [7, 5, util.NAN, 0, 8],
                            "D": [10, 8, 8, util.NAN, 8],
                            BallotMarks.WRITEIN: [7, 5, 5, 2, util.NAN],
                        },
                        index=["A", "B", "C", "D", BallotMarks.WRITEIN],
                        dtype=float,
                    ),
                    pd.DataFrame(
                        {
                            "A": [
                                util.NAN,
                                round(100 * 3 / 13, 3),
                                round(100 * 3 / 10, 3),
                                round(100 * 0 / 10, 3),
                                round(100 * 6 / 13, 3),
                            ],
                            "B": [
                                round(100 * 10 / 13, 3),
                                util.NAN,
                                round(100 * 6 / 11, 3),
                                round(100 * 0 / 8, 3),
                                round(100 * 8 / 13, 3),
                            ],
                            "C": [
                                round(100 * 7 / 10, 3),
                                round(100 * 5 / 11, 3),
                                util.NAN,
                                round(100 * 0 / 8, 3),
                                round(100 * 8 / 13, 3),
                            ],
                            "D": [
                                round(100 * 10 / 10, 3),
                                round(100 * 8 / 8, 3),
                                round(100 * 8 / 8, 3),
                                util.NAN,
                                round(100 * 8 / 10, 3),
                            ],
                            BallotMarks.WRITEIN: [
                                round(100 * 7 / 13, 3),
                                round(100 * 5 / 13, 3),
                                round(100 * 5 / 13, 3),
                                round(100 * 2 / 10, 3),
                                util.NAN,
                            ],
                        },
                        index=["A", "B", "C", "D", BallotMarks.WRITEIN],
                        dtype=float,
                    ),
                ],
            },
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_condorcet_tables(param):
    rcv = SingleWinner(**param["input"])

    count_df, percent_df, cwinner = rcv.get_condorcet_tables()

    assert count_df.index.tolist() == param["expected"]["tables"][0].index.tolist()
    assert count_df.fillna("NA").to_dict("records") == param["expected"]["tables"][0].fillna("NA").to_dict("records")

    assert percent_df.index.tolist() == param["expected"]["tables"][1].index.tolist()
    assert percent_df.fillna("NA").to_dict("records") == param["expected"]["tables"][1].fillna("NA").to_dict("records")

    assert cwinner == param["expected"]["condorcet_winner"]


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
                    "weight": [2, 2, 2, 2, 2],
                },
            },
            "expected": {
                "tables": [
                    pd.DataFrame(
                        {
                            "A": [4, util.NAN, 2, 0, 0, 2, 0],
                            "B": [0, 0, util.NAN, 0, 0, 0, 0],
                            "C": [2, 2, 0, util.NAN, 0, 0, 0],
                            "D": [0, 0, 0, 0, util.NAN, 0, 0],
                            BallotMarks.WRITEIN: [4, 2, 2, 0, 0, util.NAN, 0],
                        },
                        index=[
                            "first_choice",
                            "A",
                            "B",
                            "C",
                            "D",
                            BallotMarks.WRITEIN,
                            "exhaust",
                        ],
                        dtype=float,
                    ),
                    pd.DataFrame(
                        {
                            "A": [40, util.NAN, 50, 0, 0, 50, 0],
                            "B": [0, 0, util.NAN, 0, 0, 0, 0],
                            "C": [20, 100, 0, util.NAN, 0, 0, 0],
                            "D": [0, 0, 0, 0, util.NAN, 0, 0],
                            BallotMarks.WRITEIN: [40, 50, 50, 0, 0, util.NAN, 0],
                        },
                        index=[
                            "first_choice",
                            "A",
                            "B",
                            "C",
                            "D",
                            BallotMarks.WRITEIN,
                            "exhaust",
                        ],
                        dtype=float,
                    ),
                    pd.DataFrame(
                        {
                            "A": [40, util.NAN, 50, 0, 0, 50],
                            "B": [0, 0, util.NAN, 0, 0, 0],
                            "C": [20, 100, 0, util.NAN, 0, 0],
                            "D": [0, 0, 0, 0, util.NAN, 0],
                            BallotMarks.WRITEIN: [40, 50, 50, 0, 0, util.NAN],
                        },
                        index=["first_choice", "A", "B", "C", "D", BallotMarks.WRITEIN],
                        dtype=float,
                    ),
                ]
            },
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_first_second_tables(param):
    rcv = SingleWinner(**param["input"])

    count_df, percent_df, percent_no_exhaust_df = rcv.get_first_second_tables()

    assert count_df.index.tolist() == param["expected"]["tables"][0].index.tolist()
    assert count_df.fillna("NA").to_dict("records") == param["expected"]["tables"][0].fillna("NA").to_dict("records")

    assert percent_df.index.tolist() == param["expected"]["tables"][1].index.tolist()
    assert percent_df.fillna("NA").to_dict("records") == param["expected"]["tables"][1].fillna("NA").to_dict("records")

    assert percent_no_exhaust_df.index.tolist() == param["expected"]["tables"][2].index.tolist()
    assert percent_no_exhaust_df.fillna("NA").to_dict("records") == param["expected"]["tables"][2].fillna("NA").to_dict(
        "records"
    )


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
                    "weight": [2, 2, 2, 2, 2],
                },
            },
            "expected": {
                "tables": [
                    pd.DataFrame(
                        {
                            "Rank 1": [4, 0, 2, 0, 4],
                            "Rank 2": [8, 4, 2, 0, 6],
                            "Rank 3": [8, 6, 6, 0, 6],
                            "Rank 4": [8, 6, 6, 2, 6],
                            "Did Not Rank": [2, 4, 4, 8, 4],
                        },
                        index=["A", "B", "C", "D", BallotMarks.WRITEIN],
                        dtype=float,
                    ),
                    pd.DataFrame(
                        {
                            "Rank 1": [40, 0, 20, 0, 40],
                            "Rank 2": [80, 40, 20, 0, 60],
                            "Rank 3": [80, 60, 60, 0, 60],
                            "Rank 4": [80, 60, 60, 20, 60],
                            "Did Not Rank": [20, 40, 40, 80, 40],
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
def test_cumulative_ranking_table(param):
    rcv = SingleWinner(**param["input"])

    count_df, percent_df = rcv.get_cumulative_ranking_tables()

    assert count_df.index.tolist() == param["expected"]["tables"][0].index.tolist()
    assert count_df.to_dict("records") == param["expected"]["tables"][0].to_dict("records")

    assert percent_df.index.tolist() == param["expected"]["tables"][1].index.tolist()
    assert percent_df.to_dict("records") == param["expected"]["tables"][1].to_dict("records")


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
                    ]
                },
            },
            "expected": {
                "table": pd.DataFrame(
                    {
                        "jurisdiction": ["testville"],
                        "state": ["teststate"],
                        "date": ["01/05/2021"],
                        "year": ["2021"],
                        "office": ["chief tester"],
                        "unique_id": ["testville_01052021_chieftester"],
                        "winner": ["A"],
                        "rank_limit": [4],
                        "n_candidates": [4],
                        "n_rounds": [2],
                        "choice1": [66.67],
                        "choice2": [33.33],
                        "choice3": [0],
                        "choice4": [0],
                    }
                )
            },
        }
    ),
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
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                    ]
                },
                "exhaust_on_overvote_marks": True,
            },
            "expected": {
                "table": pd.DataFrame(
                    {
                        "jurisdiction": ["testville"],
                        "state": ["teststate"],
                        "date": ["01/05/2021"],
                        "year": ["2021"],
                        "office": ["chief tester"],
                        "unique_id": ["testville_01052021_chieftester"],
                        "winner": ["A"],
                        "rank_limit": [4],
                        "n_candidates": [4],
                        "n_rounds": [2],
                        "choice1": [66.67],
                        "choice2": [33.33],
                        "choice3": [0],
                        "choice4": [0],
                    }
                )
            },
        }
    ),
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
                        ["C", "B", "A", "B"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                    ]
                },
                "exhaust_on_overvote_marks": True,
            },
            "expected": {
                "table": pd.DataFrame(
                    {
                        "jurisdiction": ["testville"],
                        "state": ["teststate"],
                        "date": ["01/05/2021"],
                        "year": ["2021"],
                        "office": ["chief tester"],
                        "unique_id": ["testville_01052021_chieftester"],
                        "winner": ["A"],
                        "rank_limit": [4],
                        "n_candidates": [4],
                        "n_rounds": [2],
                        "choice1": [66.67],
                        "choice2": [0],
                        "choice3": [33.33],
                        "choice4": [0],
                    }
                )
            },
        }
    ),
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
                        ["C", "B", "D", "A"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                    ]
                },
                "exhaust_on_overvote_marks": True,
            },
            "expected": {
                "table": pd.DataFrame(
                    {
                        "jurisdiction": ["testville"],
                        "state": ["teststate"],
                        "date": ["01/05/2021"],
                        "year": ["2021"],
                        "office": ["chief tester"],
                        "unique_id": ["testville_01052021_chieftester"],
                        "winner": ["A"],
                        "rank_limit": [4],
                        "n_candidates": [4],
                        "n_rounds": [2],
                        "choice1": [66.67],
                        "choice2": [0],
                        "choice3": [0],
                        "choice4": [33.33],
                    }
                )
            },
        }
    ),
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
                        ["C", "A", "B", "B"],
                        ["C", "A", "B", "B"],
                        ["D", "B", "E", "A"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                    ]
                },
                "exhaust_on_overvote_marks": True,
            },
            "expected": {
                "table": pd.DataFrame(
                    {
                        "jurisdiction": ["testville"],
                        "state": ["teststate"],
                        "date": ["01/05/2021"],
                        "year": ["2021"],
                        "office": ["chief tester"],
                        "unique_id": ["testville_01052021_chieftester"],
                        "winner": ["A"],
                        "rank_limit": [4],
                        "n_candidates": [5],
                        "n_rounds": [3],
                        "choice1": [50],
                        "choice2": [25],
                        "choice3": [0],
                        "choice4": [25],
                    }
                )
            },
        }
    ),
]


# @pytest.mark.parametrize("param", params)
# def test_winner_choice_position_distribution_table(param):
#     rcv = SingleWinner(**param["input"])

#     table_df = rcv.get_winner_choice_position_distribution_table()

#     for col in table_df.columns:
#         assert table_df[col].item() == param["expected"]["table"][col].item()


# def test_first_choice_to_finalist_table(param):
#     pass


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
                    "weight": [2, 2, 2, 2, 2],
                },
            },
            "expected": {
                "tables": [
                    pd.DataFrame(
                        {
                            "candidate": [
                                "A",
                                BallotMarks.WRITEIN,
                                "C",
                                "B",
                                "D",
                                "exhaust",
                                "colsum",
                            ],
                            "r1_active_percent": [40, 40, 20, 0, 0, 0, 100],
                            "r1_count": [4, 4, 2, 0, 0, 0, 10],
                            "r1_transfer": [2, 0, -2, 0, 0, 0, 0],
                            "r2_active_percent": [60, 40, 0, 0, 0, 0, 100],
                            "r2_count": [6, 4, 0, 0, 0, 0, 10],
                            "r2_transfer": [
                                util.NAN,
                                util.NAN,
                                util.NAN,
                                util.NAN,
                                util.NAN,
                                util.NAN,
                                util.NAN,
                            ],
                        },
                        dtype=float,
                    )
                ]
            },
        }
    )
]


@pytest.mark.parametrize("param", params)
def test_round_by_round(param):
    rcv = SingleWinner(**param["input"])

    table_df = rcv.get_round_by_round_table(tabulation_num=1)

    assert table_df.index.tolist() == param["expected"]["tables"][0].index.tolist()
    assert table_df.fillna("NA").to_dict("records") == param["expected"]["tables"][0].fillna("NA").to_dict("records")
