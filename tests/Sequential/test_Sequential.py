import pytest

from rcv_cruncher.marks import BallotMarks
from rcv_cruncher.rcv.variants import Sequential


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {
                "n_tabulation": 1,
                "n_round": [3],
                "rounds": [
                    [
                        {"A": 5, "B": 4, "C": 3, "D": 2, BallotMarks.WRITEIN: 1},
                        {"A": 6, "B": 4, "C": 3, "D": 2, BallotMarks.WRITEIN: 0},
                        {"A": 8, "B": 4, "C": 3, "D": 0, BallotMarks.WRITEIN: 0},
                    ]
                ],
            },
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {
                "n_tabulation": 2,
                "n_round": [3, 3],
                "rounds": [
                    [
                        {"A": 5, "B": 4, "C": 3, "D": 2, BallotMarks.WRITEIN: 1},
                        {"A": 6, "B": 4, "C": 3, "D": 2, BallotMarks.WRITEIN: 0},
                        {"A": 8, "B": 4, "C": 3, "D": 0, BallotMarks.WRITEIN: 0},
                    ],
                    [
                        {
                            "A": 0,
                            "B": 4,
                            "C": 3,
                            "D": 2,
                            BallotMarks.WRITEIN: 1,
                        },
                        {"A": 0, "B": 4, "C": 4, "D": 2, BallotMarks.WRITEIN: 0},
                        {"A": 0, "B": 4, "C": 6, "D": 0, BallotMarks.WRITEIN: 0},
                    ],
                ],
            },
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {
                "n_tabulation": 3,
                "n_round": [3, 3, 1],
                "rounds": [
                    [
                        {"A": 5, "B": 4, "C": 3, "D": 2, BallotMarks.WRITEIN: 1},
                        {"A": 6, "B": 4, "C": 3, "D": 2, BallotMarks.WRITEIN: 0},
                        {"A": 8, "B": 4, "C": 3, "D": 0, BallotMarks.WRITEIN: 0},
                    ],
                    [
                        {
                            "A": 0,
                            "B": 4,
                            "C": 3,
                            "D": 2,
                            BallotMarks.WRITEIN: 1,
                        },
                        {"A": 0, "B": 4, "C": 4, "D": 2, BallotMarks.WRITEIN: 0},
                        {"A": 0, "B": 4, "C": 6, "D": 0, BallotMarks.WRITEIN: 0},
                    ],
                    [{"A": 0, "B": 7, "C": 0, "D": 2, BallotMarks.WRITEIN: 1}],
                ],
            },
        }
    ),
]

# 'exhaust_on_duplicate_candidate_marks': False,
# 'exhaust_on_overvote_marks': False,
# 'exhaust_on_repeated_skipped_marks': False,
# 'treat_combined_writeins_as_exhaustable_duplicates': True,
# 'combine_writein_marks': True,
# 'exclude_writein_marks': False


@pytest.mark.parametrize("param", params)
def test_tabulation(param):
    rcv = Sequential(**param["input"])

    # confirm tabulation num
    n_tabulations = rcv.n_tabulations()
    assert n_tabulations == param["expected"]["n_tabulation"]

    # confirm round num
    for iTab in range(n_tabulations):
        n_round = rcv.n_rounds(tabulation_num=iTab + 1)
        assert n_round == param["expected"]["n_round"][iTab]

        # confirm round tallies
        tally_dict = [rcv.get_round_tally_dict(round_num=i, tabulation_num=iTab + 1) for i in range(1, n_round + 1)]
        tally_dict = [{k: float(v) for k, v in d.items()} for d in tally_dict]
        assert tally_dict == param["expected"]["rounds"][iTab]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [5]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [5, 3]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [5, 3, 7]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_first_round_winner_vote(param):
    rcv = Sequential(**param["input"])
    assert [i["first_round_winner_vote"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [8]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [8, 6]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [8, 6, 7]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_final_round_winner_vote(param):
    rcv = Sequential(**param["input"])
    assert [i["final_round_winner_vote"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [round(100 * 5 / 15, 3)]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [round(100 * 5 / 15, 3), round(100 * 3 / 10, 3)]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {
                "stat": [
                    round(100 * 5 / 15, 3),
                    round(100 * 3 / 10, 3),
                    round(100 * 7 / 10, 3),
                ]
            },
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_first_round_winner_percent(param):
    rcv = Sequential(**param["input"])
    assert [i["first_round_winner_percent"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [round(100 * 8 / 15, 3)]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [round(100 * 8 / 15, 3), 60]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [round(100 * 8 / 15, 3), 60, 70]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_final_round_winner_percent(param):
    rcv = Sequential(**param["input"])
    assert [i["final_round_winner_percent"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [1]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [1, 2]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [1, 2, 1]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_first_round_winner_place(param):
    rcv = Sequential(**param["input"])
    assert [i["first_round_winner_place"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [True]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [True, False]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [True, False, False]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_condorcet(param):
    rcv = Sequential(**param["input"])
    assert [i["condorcet"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [False]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [False, True]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [False, True, False]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_come_from_behind(param):
    rcv = Sequential(**param["input"])
    assert [i["come_from_behind"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [15]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [15, 6]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [15, 6, 7]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_ranked_winner(param):
    rcv = Sequential(**param["input"])
    assert [i["ranked_winner"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [round(100 * 8 / 15, 3)]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [round(100 * 8 / 15, 3), round(100 * 6 / 10, 3)]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {
                "stat": [
                    round(100 * 8 / 15, 3),
                    round(100 * 6 / 10, 3),
                    round(100 * 7 / 10, 3),
                ]
            },
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_final_round_winner_votes_over_first_round_active(param):
    rcv = Sequential(**param["input"])
    assert [i["final_round_winner_votes_over_first_round_active"].item() for i in rcv.get_stats()] == param["expected"][
        "stat"
    ]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [None]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [None, None]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [None, None, None]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_static_win_threshold(param):
    rcv = Sequential(**param["input"])
    assert [i["static_win_threshold"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [1]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [1, 1]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [1, 1, 1]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_number_of_tabulation_winners(param):
    rcv = Sequential(**param["input"])
    assert [i["number_of_tabulation_winners"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [1]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [2, 2]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [3, 3, 3]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_number_of_contest_winners(param):
    rcv = Sequential(**param["input"])
    assert [i["number_of_contest_winners"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": ["A"]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": ["A", "C"]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": ["A", "C", "B"]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_winner(param):
    rcv = Sequential(**param["input"])
    assert [i["winner"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [100]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [100, 60]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [100, 60, 70]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_winners_consensus_value(param):
    rcv = Sequential(**param["input"])
    assert [i["winners_consensus_value"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [15]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [15, 10]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [15, 10, 10]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_first_round_active_votes(param):
    rcv = Sequential(**param["input"])
    assert [i["first_round_active_votes"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [15]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [15, 10]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [15, 10, 10]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_final_round_active_votes(param):
    rcv = Sequential(**param["input"])
    assert [i["final_round_active_votes"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [0, 5]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [0, 5, 5]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_pretally_exhausted(param):
    rcv = Sequential(**param["input"])
    assert [i["total_pretally_exhausted"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [0, 0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [0, 0, 0]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted(param):
    rcv = Sequential(**param["input"])
    assert [i["total_posttally_exhausted"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [0, 0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [0, 0, 0]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_overvote(param):
    rcv = Sequential(**param["input"])
    assert [i["total_posttally_exhausted_by_overvote"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [0, 0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [0, 0, 0]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_skipped_rankings(param):
    rcv = Sequential(**param["input"])
    assert [i["total_posttally_exhausted_by_skipped_rankings"].item() for i in rcv.get_stats()] == param["expected"][
        "stat"
    ]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [0, 0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [0, 0, 0]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_abstention(param):
    rcv = Sequential(**param["input"])
    assert [i["total_posttally_exhausted_by_abstention"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [0, 0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [0, 0, 0]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_rank_limit(param):
    rcv = Sequential(**param["input"])
    assert [i["total_posttally_exhausted_by_rank_limit"].item() for i in rcv.get_stats()] == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [0, 0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [0, 0, 0]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_rank_limit_fully_ranked(param):
    rcv = Sequential(**param["input"])
    assert [i["total_posttally_exhausted_by_rank_limit_fully_ranked"].item() for i in rcv.get_stats()] == param[
        "expected"
    ]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [0, 0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [0, 0, 0]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_rank_limit_partially_ranked(param):
    rcv = Sequential(**param["input"])
    assert [i["total_posttally_exhausted_by_rank_limit_partially_ranked"].item() for i in rcv.get_stats()] == param[
        "expected"
    ]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
            },
            "expected": {"stat": [0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
            },
            "expected": {"stat": [0, 0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [0, 0, 0]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_duplicate_rankings(param):
    rcv = Sequential(**param["input"])
    assert [i["total_posttally_exhausted_by_duplicate_rankings"].item() for i in rcv.get_stats()] == param["expected"][
        "stat"
    ]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "precinct": [1, 1, 2, 2, 2],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 1,
                "split_fields": ["precinct"],
            },
            "expected": {"stat": [[0, 0]]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "precinct": [1, 1, 2, 2, 2],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 2,
                "split_fields": ["precinct"],
            },
            "expected": {"stat": [[0, 0], [5, 0]]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "A"],
                        ["C", "A", "B", "B"],
                        ["D", BallotMarks.OVERVOTE, "A", "C"],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                    ],
                    "precinct": [1, 1, 2, 2, 2],
                    "weight": [5, 4, 3, 2, 1],
                },
                "n_winners": 3,
                "split_fields": ["precinct"],
            },
            "expected": {"stat": [[0, 0], [5, 0], [5, 0]]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_split_total_pretally_exhausted(param):
    rcv = Sequential(**param["input"])
    assert [i["split_total_pretally_exhausted"].tolist() for i in rcv.get_stats(add_split_stats=True)] == param[
        "expected"
    ]["stat"]


# params = [
#     ({
#         'input': {
#             'parsed_cvr': {
#                 'ranks': [
#                     ['A', 'B', 'C', 'D'],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.WRITEIN],
#                     ['write-in', 'A', 'C', BallotMarks.OVERVOTE],
#                     ['write-in', 'B', 'B', BallotMarks.OVERVOTE],
#                     ['C', 'A', 'B', 'B']
#                 ],
#                 'split': [1, 1, 2, 2, 2]
#             },
#             'split_fields': ['split']
#         },
#         'expected': {
#             'stat': [0, 0]
#         }
#     }),
#     ({
#         'input': {
#             'parsed_cvr': {
#                 'ranks': [
#                     ['A', 'B', 'C', 'D'],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.WRITEIN],
#                     ['write-in', 'A', 'C', BallotMarks.OVERVOTE],
#                     ['write-in', 'B', 'B', BallotMarks.OVERVOTE],
#                     ['C', 'D', BallotMarks.WRITEIN, 'B']
#                 ],
#                 'split': [1, 1, 2, 2, 2]
#             },
#             'split_fields': ['split']
#         },
#         'expected': {
#             'stat': [0, 0]
#         }
#     }),
#     ({
#         'input': {
#             'parsed_cvr': {
#                 'ranks': [
#                     ['A', 'B', 'C', 'D'],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.WRITEIN],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
#                     ['write-in', 'A', 'C', BallotMarks.OVERVOTE],
#                     ['write-in', 'B', 'B', BallotMarks.OVERVOTE],
#                     ['C', 'D', BallotMarks.WRITEIN, 'B'],
#                     ['C', 'D', 'D', 'B'],
#                     ['D', 'B', BallotMarks.WRITEIN, 'D'],
#                     [BallotMarks.OVERVOTE, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE]
#                 ],
#                 'split': [1, 1, 1, 1, 2, 2, 2, 2, 2]
#             },
#             'split_fields': ['split']
#         },
#         'expected': {
#             'stat': [0, 1]
#         }
#     }),
#     ({
#         'input': {
#             'parsed_cvr': {
#                 'ranks': [
#                     ['A', 'B', 'C', 'D'],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.WRITEIN],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
#                     ['write-in', 'A', 'C', BallotMarks.OVERVOTE],
#                     ['write-in', 'B', 'B', BallotMarks.OVERVOTE],
#                     ['C', 'D', BallotMarks.WRITEIN, 'B'],
#                     ['C', 'D', 'D', 'B'],
#                     ['D', 'B', BallotMarks.WRITEIN, 'D'],
#                     [BallotMarks.OVERVOTE, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE]
#                 ],
#                 'weight': [1, 1, 1, 2, 2, 1, 1, 1, 5],
#                 'split': [1, 1, 1, 1, 2, 2, 2, 2, 2]
#             },
#             'split_fields': ['split']
#         },
#         'expected': {
#             'stat': [0, 1]
#         }
#     }),
#     ({
#         'input': {
#             'parsed_cvr': {
#                 'ranks': [
#                     ['A', 'B', 'C', 'D'],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.WRITEIN],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
#                     ['A', 'A', 'C', BallotMarks.OVERVOTE],
#                     ['write-in', 'B', 'B', BallotMarks.SKIPPED],
#                     ['C', 'D', BallotMarks.WRITEIN, 'B'],
#                     ['C', 'D', 'D', 'B']
#                 ],
#                 'weight': [2, 2, 2, 2, 1, 1, 1],
#                 'split': [1, 1, 1, 1, 2, 2, 2]
#             },
#             'split_fields': ['split'],
#             'exhaust_on_duplicate_candidate_marks': True
#         },
#         'expected': {
#             'stat': [0, 1]
#         }
#     })
# ]


# @pytest.mark.parametrize("param", params)
# def test_split_total_posttally_exhausted(param):
#     rcv = Until2(**param['input'])
#     assert rcv.stats(add_split_stats=True)[0]['split_total_posttally_exhausted'].tolist() == param['expected']['stat']


# params = [
#     ({
#         'input': {
#             'parsed_cvr': {
#                 'ranks': [
#                     ['A', 'C', 'C', 'D'],
#                     [BallotMarks.OVERVOTE, 'A', 'B', 'C'],
#                     ['B', BallotMarks.OVERVOTE, 'A', 'B'],
#                     ['B', 'A', 'A', 'C'],
#                     ['C', BallotMarks.SKIPPED, BallotMarks.SKIPPED, 'A'],
#                     ['C', 'A', 'B', 'E'],
#                     ['D', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
#                     ['E', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED]
#                 ],
#                 'weight': [1, 1, 1, 1, 1, 1, 5, 5],
#                 'split': [1, 1, 1, 1, 2, 2, 2, 2]
#             },
#             'split_fields': ['split'],
#             'exhaust_on_duplicate_candidate_marks': True,
#             'exhaust_on_overvote_marks': True,
#             'exhaust_on_repeated_skipped_marks': True
#         },
#         'expected': {
#             'stat': [1, 0]
#         }
#     }),
#     ({
#         'input': {
#             'parsed_cvr': {
#                 'ranks': [
#                     ['A', 'B', 'C', 'D'],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.WRITEIN],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
#                     ['A', 'A', 'C', BallotMarks.OVERVOTE],
#                     ['write-in', 'B', 'B', BallotMarks.OVERVOTE],
#                     ['C', 'D', BallotMarks.WRITEIN, 'B'],
#                     ['C', 'D', 'D', 'B']
#                 ],
#                 'weight': [2, 2, 2, 2, 1, 1, 1],
#                 'split': [1, 1, 1, 1, 2, 2, 2]
#             },
#             'split_fields': ['split'],
#             'exhaust_on_overvote_marks': True
#         },
#         'expected': {
#             'stat': [0, 1]
#         }
#     })
# ]


# @pytest.mark.parametrize("param", params)
# def test_split_total_posttally_exhausted_by_overvote(param):
#     rcv = Until2(**param['input'])
#     assert rcv.stats(add_split_stats=True)[0]['split_total_posttally_exhausted_by_overvote'].tolist() == param['expected']['stat']


# params = [
#     ({
#         'input': {
#             'parsed_cvr': {
#                 'ranks': [
#                     ['A', 'C', 'C', 'D'],
#                     [BallotMarks.OVERVOTE, 'A', 'B', 'C'],
#                     ['B', BallotMarks.OVERVOTE, 'A', 'B'],
#                     ['B', 'A', 'A', 'C'],
#                     ['C', BallotMarks.SKIPPED, BallotMarks.SKIPPED, 'A'],
#                     ['C', 'A', 'B', 'E'],
#                     ['D', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
#                     ['E', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED]
#                 ],
#                 'weight': [1, 1, 1, 1, 1, 1, 5, 5],
#                 'split': [1, 1, 1, 1, 2, 2, 2, 2]
#             },
#             'split_fields': ['split'],
#             'exhaust_on_duplicate_candidate_marks': True,
#             'exhaust_on_overvote_marks': True,
#             'exhaust_on_repeated_skipped_marks': True
#         },
#         'expected': {
#             'stat': [0, 1]
#         }
#     }),
#     ({
#         'input': {
#             'parsed_cvr': {
#                 'ranks': [
#                     ['A', 'B', 'C', 'D'],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.WRITEIN],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
#                     ['A', 'A', 'C', BallotMarks.OVERVOTE],
#                     ['write-in', BallotMarks.SKIPPED, BallotMarks.SKIPPED, 'A'],
#                     ['C', 'D', BallotMarks.WRITEIN, 'B'],
#                     ['C', 'D', 'D', 'B']
#                 ],
#                 'weight': [2, 2, 2, 2, 1, 1, 1],
#                 'split': [1, 1, 1, 1, 2, 2, 2]
#             },
#             'split_fields': ['split'],
#             'exhaust_on_repeated_skipped_marks': True
#         },
#         'expected': {
#             'stat': [0, 1]
#         }
#     })
# ]


# @pytest.mark.parametrize("param", params)
# def test_split_total_posttally_exhausted_by_skipped_rankings(param):
#     rcv = Until2(**param['input'])
#     assert rcv.stats(add_split_stats=True)[0]['split_total_posttally_exhausted_by_skipped_rankings'].tolist() == param['expected']['stat']


# params = [
#     ({
#         'input': {
#             'parsed_cvr': {
#                 'ranks': [
#                     ['A', 'C', 'C', 'D'],
#                     [BallotMarks.OVERVOTE, 'A', 'B', 'C'],
#                     ['B', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
#                     ['B', 'A', 'A', 'C'],
#                     ['C', BallotMarks.SKIPPED, BallotMarks.SKIPPED, 'A'],
#                     ['C', 'A', 'B', 'E'],
#                     ['D', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
#                     ['E', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED]
#                 ],
#                 'weight': [1, 1, 1, 1, 1, 1, 5, 5],
#                 'split': [1, 1, 1, 1, 2, 2, 2, 2]
#             },
#             'split_fields': ['split'],
#             'exhaust_on_duplicate_candidate_marks': True,
#             'exhaust_on_overvote_marks': True,
#             'exhaust_on_repeated_skipped_marks': True
#         },
#         'expected': {
#             'stat': [1, 0]
#         }
#     }),
#     ({
#         'input': {
#             'parsed_cvr': {
#                 'ranks': [
#                     ['A', 'B', 'C', 'D'],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.WRITEIN],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
#                     ['A', 'A', 'C', BallotMarks.OVERVOTE],
#                     ['write-in', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
#                     ['C', 'D', BallotMarks.WRITEIN, 'B'],
#                     ['C', 'D', 'D', 'B']
#                 ],
#                 'weight': [2, 2, 2, 2, 1, 1, 1],
#                 'split': [1, 1, 1, 1, 2, 2, 2]
#             },
#             'split_fields': ['split'],
#             'exhaust_on_repeated_skipped_marks': True
#         },
#         'expected': {
#             'stat': [0, 1]
#         }
#     })
# ]


# @pytest.mark.parametrize("param", params)
# def test_split_total_posttally_exhausted_by_abstention(param):
#     rcv = Until2(**param['input'])
#     assert rcv.stats(add_split_stats=True)[0]['split_total_posttally_exhausted_by_abstention'].tolist() == param['expected']['stat']


# params = [
#     ({
#         'input': {
#             'parsed_cvr': {
#                 'ranks': [
#                     ['A', 'C', 'C', 'D'],
#                     [BallotMarks.OVERVOTE, 'A', 'B', 'C'],
#                     ['B', BallotMarks.OVERVOTE, 'A', 'B'],
#                     ['B', 'A', 'A', 'C'],
#                     ['C', BallotMarks.SKIPPED, BallotMarks.SKIPPED, 'A'],
#                     ['C', 'A', 'B', 'E'],
#                     ['D', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
#                     ['E', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED]
#                 ],
#                 'weight': [1, 1, 1, 1, 1, 1, 5, 5],
#                 'split': [1, 1, 1, 1, 2, 2, 2, 3]
#             },
#             'split_fields': ['split'],
#             'exhaust_on_duplicate_candidate_marks': True,
#             'exhaust_on_overvote_marks': True,
#             'exhaust_on_repeated_skipped_marks': True
#         },
#         'expected': {
#             'stat': [0, 0, 0]
#         }
#     }),
#     ({
#         'input': {
#             'parsed_cvr': {
#                 'ranks': [
#                     ['A', 'B', 'C', 'D'],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.WRITEIN],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
#                     ['A', 'A', 'C', BallotMarks.OVERVOTE],
#                     ['write-in', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
#                     ['C', 'D', BallotMarks.WRITEIN, 'B'],
#                     ['C', 'D', 'D', 'B']
#                 ],
#                 'weight': [2, 2, 2, 2, 1, 1, 1],
#                 'split': [1, 1, 1, 1, 2, 2, 2]
#             },
#             'split_fields': ['split'],
#             'exhaust_on_repeated_skipped_marks': True
#         },
#         'expected': {
#             'stat': [0, 0]
#         }
#     })
# ]


# @pytest.mark.parametrize("param", params)
# def test_split_total_posttally_exhausted_by_rank_limit(param):
#     rcv = Until2(**param['input'])
#     assert rcv.stats(add_split_stats=True)[0]['split_total_posttally_exhausted_by_rank_limit'].tolist() == param['expected']['stat']


# params = [
#     ({
#         'input': {
#             'parsed_cvr': {
#                 'ranks': [
#                     ['A', 'C', 'C', 'D'],
#                     [BallotMarks.OVERVOTE, 'A', 'B', 'C'],
#                     ['B', BallotMarks.OVERVOTE, 'A', 'B'],
#                     ['B', 'A', 'A', 'C'],
#                     ['C', BallotMarks.SKIPPED, BallotMarks.SKIPPED, 'A'],
#                     ['C', 'A', 'B', 'E'],
#                     ['D', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
#                     ['E', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED]
#                 ],
#                 'weight': [1, 1, 1, 1, 1, 1, 5, 5],
#                 'split': [1, 1, 1, 1, 2, 2, 2, 2]
#             },
#             'split_fields': ['split'],
#             'exhaust_on_duplicate_candidate_marks': True,
#             'exhaust_on_overvote_marks': True,
#             'exhaust_on_repeated_skipped_marks': True
#         },
#         'expected': {
#             'stat': [2, 0]
#         }
#     }),
#     ({
#         'input': {
#             'parsed_cvr': {
#                 'ranks': [
#                     ['A', 'B', 'C', 'D'],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.WRITEIN],
#                     ['A', BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED],
#                     ['A', 'A', 'C', BallotMarks.OVERVOTE],
#                     ['write-in', 'B', 'B', 'B'],
#                     ['C', 'D', BallotMarks.WRITEIN, 'B'],
#                     ['C', 'D', 'D', 'B']
#                 ],
#                 'weight': [2, 2, 2, 2, 1, 1, 1],
#                 'split': [1, 1, 1, 1, 2, 2, 2]
#             },
#             'split_fields': ['split'],
#             'exhaust_on_duplicate_candidate_marks': True
#         },
#         'expected': {
#             'stat': [0, 1]
#         }
#     })
# ]


# @pytest.mark.parametrize("param", params)
# def test_split_total_posttally_exhausted_by_duplicate_rankings(param):
#     rcv = Until2(**param['input'])
#     assert rcv.stats(add_split_stats=True)[0]['split_total_posttally_exhausted_by_duplicate_rankings'].tolist() == param['expected']['stat']
