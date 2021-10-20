import pytest

from rcv_cruncher.marks import BallotMarks
from rcv_cruncher.rcv.variants import SingleWinner

# testing:

# tabulations
# first_round_winner_vote
# final_round_winner_vote
# first_round_winner_percent
# final_round_winner_percent
# first_round_winner_place
# condorcet
# come_from_behind
# ranked_winner
# final_round_winner_votes_over_first_round_valid
# win_threshold
# number_of_winners
# winner
# number_of_rounds
# winners_consensus_value
# first_round_active_votes
# final_round_active_votes
# total_pretally_exhausted
# total_posttally_exhausted
# total_posttally_exhausted_by_overvote
# total_posttally_exhausted_by_skipped_rankings
# total_posttally_exhausted_by_abstention
# total_posttally_exhausted_by_rank_limit
# total_posttally_exhausted_by_duplicate_rankings


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {
                "n_tabulation": 1,
                "n_round": 2,
                "rounds": [
                    {"A": 2, "B": 0, "C": 1, "D": 0, BallotMarks.WRITEIN: 2},
                    {"A": 3, "B": 0, "C": 0, "D": 0, BallotMarks.WRITEIN: 2},
                ],
            },
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {
                "n_tabulation": 1,
                "n_round": 2,
                "rounds": [
                    {"A": 2, "B": 0, "C": 1, "D": 0, BallotMarks.WRITEIN: 2},
                    {"A": 2, "B": 0, "C": 0, "D": 0, BallotMarks.WRITEIN: 3},
                ],
            },
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ]
                }
            },
            "expected": {
                "n_tabulation": 1,
                "n_round": 3,
                "rounds": [
                    {"A": 3, "B": 0, "C": 2, "D": 1, BallotMarks.WRITEIN: 2},
                    {"A": 3, "B": 0, "C": 2, "D": 0, BallotMarks.WRITEIN: 3},
                    {"A": 3, "B": 0, "C": 0, "D": 0, BallotMarks.WRITEIN: 4},
                ],
            },
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "weight": [2, 2, 2, 2, 1, 1, 1, 1],
                }
            },
            "expected": {
                "n_tabulation": 1,
                "n_round": 3,
                "rounds": [
                    {"A": 6, "B": 0, "C": 2, "D": 1, BallotMarks.WRITEIN: 3},
                    {"A": 6, "B": 0, "C": 2, "D": 0, BallotMarks.WRITEIN: 4},
                    {"A": 6, "B": 0, "C": 0, "D": 0, BallotMarks.WRITEIN: 5},
                ],
            },
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "weight": [2, 2, 2, 2, 1, 1, 1, 1],
                },
            },
            "expected": {
                "n_tabulation": 1,
                "n_round": 3,
                "rounds": [
                    {"A": 6, "B": 0, "C": 2, "D": 1, BallotMarks.WRITEIN: 3},
                    {"A": 6, "B": 0, "C": 2, "D": 0, BallotMarks.WRITEIN: 4},
                    {"A": 6, "B": 0, "C": 0, "D": 0, BallotMarks.WRITEIN: 5},
                ],
            },
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        ["B", BallotMarks.OVERVOTE, "A", "B"],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "D",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {
                "n_tabulation": 1,
                "n_round": 4,
                "rounds": [
                    {"A": 1, "B": 2, "C": 2, "D": 5, "E": 5},
                    {"A": 0, "B": 2, "C": 3, "D": 5, "E": 5},
                    {"A": 0, "B": 0, "C": 3, "D": 5, "E": 5},
                    {"A": 0, "B": 0, "C": 0, "D": 5, "E": 6},
                ],
            },
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        ["B", BallotMarks.OVERVOTE, "A", "B"],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {
                "n_tabulation": 1,
                "n_round": 1,
                "rounds": [{"A": 1, "B": 2, "C": 2, "D": 0, "E": 10}],
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
    rcv = SingleWinner(**param["input"])

    # confirm tabulation num
    n_tabulations = rcv.n_tabulations()
    assert n_tabulations == param["expected"]["n_tabulation"]

    # confirm round num
    n_round = rcv.n_rounds(tabulation_num=1)
    assert n_round == param["expected"]["n_round"]

    # confirm round tallies
    tally_dict = [rcv.get_round_tally_dict(round_num=i) for i in range(1, n_round + 1)]
    tally_dict = [{k: float(v) for k, v in d.items()} for d in tally_dict]
    assert tally_dict == param["expected"]["rounds"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": 2},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": 2},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
            },
            "expected": {"stat": 2},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_first_round_winner_vote(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["first_round_winner_vote"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": 3},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": 3},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
            },
            "expected": {"stat": 4},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_final_round_winner_vote(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["final_round_winner_vote"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": 40},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": 40},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
            },
            "expected": {"stat": 25},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_first_round_winner_percent(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["first_round_winner_percent"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": 60},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": 60},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
            },
            "expected": {"stat": round(100 * 4 / 7, 3)},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_final_round_winner_percent(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["final_round_winner_percent"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": 1},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": 1},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
            },
            "expected": {"stat": 2},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_first_round_winner_place(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["first_round_winner_place"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": True},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": True},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
            },
            "expected": {"stat": False},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_condorcet(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["condorcet"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": False},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": False},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
            },
            "expected": {"stat": True},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_come_from_behind(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["come_from_behind"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": 4},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": 4},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
            },
            "expected": {"stat": 5},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_ranked_winner(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["ranked_winner"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": 100 * 3 / 5},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": 60},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
            },
            "expected": {"stat": 50},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_final_round_winner_votes_over_first_round_active(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["final_round_winner_votes_over_first_round_active"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": None},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": None},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
            },
            "expected": {"stat": None},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_static_win_threshold(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["static_win_threshold"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": 1},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": 1},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
            },
            "expected": {"stat": 1},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_number_of_tabulation_winners(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["number_of_tabulation_winners"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": "A"},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": BallotMarks.WRITEIN},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
            },
            "expected": {"stat": BallotMarks.WRITEIN},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_winner(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["winner"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": 80},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": 80},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
            },
            "expected": {"stat": 100 * 5 / 8},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_winners_consensus_value(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["winners_consensus_value"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": 5},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": 5},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ]
                }
            },
            "expected": {"stat": 8},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "weight": [1, 1, 1, 2, 2, 1, 1, 1],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
            },
            "expected": {"stat": 10},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_first_round_active_votes(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["first_round_active_votes"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": 5},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": 5},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ]
                }
            },
            "expected": {"stat": 7},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                    ],
                    "weight": [1, 1, 1, 2, 2, 1, 1, 1],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
            },
            "expected": {"stat": 9},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_final_round_active_votes(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["final_round_active_votes"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": 0},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": 0},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                        [
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                        ],
                    ]
                }
            },
            "expected": {"stat": 1},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                        [
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                        ],
                    ],
                    "weight": [1, 1, 1, 2, 2, 1, 1, 1, 5],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3, 4],
                },
                "split_fields": ["precinct"],
            },
            "expected": {"stat": 5},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_pretally_exhausted(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["total_pretally_exhausted"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                }
            },
            "expected": {"stat": 0},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ]
                }
            },
            "expected": {"stat": 0},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                        [
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                        ],
                    ]
                }
            },
            "expected": {"stat": 1},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        ["B", BallotMarks.OVERVOTE, "A", "B"],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "D",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {"stat": 4},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["total_posttally_exhausted"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        ["B", BallotMarks.OVERVOTE, "A", "B"],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "D",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {"stat": 1},
        }
    )
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_overvote(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["total_posttally_exhausted_by_overvote"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        ["B", BallotMarks.OVERVOTE, "A", "B"],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "D",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {"stat": 1},
        }
    )
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_skipped_rankings(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["total_posttally_exhausted_by_skipped_rankings"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        [
                            "B",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "D",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {"stat": 1},
        }
    )
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_abstention(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["total_posttally_exhausted_by_abstention"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        ["B", BallotMarks.OVERVOTE, "A", "B"],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "D",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {"stat": 0},
        }
    )
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_rank_limit(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["total_posttally_exhausted_by_rank_limit"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        ["B", BallotMarks.OVERVOTE, "A", "B"],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "D",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {"stat": 0},
        }
    )
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_rank_limit_fully_ranked(param):
    rcv = SingleWinner(**param["input"])
    assert (
        rcv.get_stats()[0]["total_posttally_exhausted_by_rank_limit_fully_ranked"].item() == param["expected"]["stat"]
    )


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        ["B", BallotMarks.OVERVOTE, "A", "B"],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "D",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {"stat": 0},
        }
    )
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_rank_limit_partially_ranked(param):
    rcv = SingleWinner(**param["input"])
    assert (
        rcv.get_stats()[0]["total_posttally_exhausted_by_rank_limit_partially_ranked"].item()
        == param["expected"]["stat"]
    )


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        ["B", BallotMarks.OVERVOTE, "A", "B"],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "D",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "precinct": [1, 1, 1, 2, 2, 2, 3, 3],
                },
                "split_fields": ["precinct"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {"stat": 2},
        }
    )
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_duplicate_rankings(param):
    rcv = SingleWinner(**param["input"])
    assert rcv.get_stats()[0]["total_posttally_exhausted_by_duplicate_rankings"].item() == param["expected"]["stat"]


params = [
    (
        {
            "input": {
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
                    "split": [1, 1, 2, 2, 2],
                },
                "split_fields": ["split"],
            },
            "expected": {"stat": [0, 0]},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ],
                    "split": [1, 1, 2, 2, 2],
                },
                "split_fields": ["split"],
            },
            "expected": {"stat": [0, 0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                        [
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                        ],
                    ],
                    "split": [1, 1, 1, 1, 2, 2, 2, 2, 2],
                },
                "split_fields": ["split"],
            },
            "expected": {"stat": [0, 1]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                        [
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                        ],
                    ],
                    "weight": [1, 1, 1, 2, 2, 1, 1, 1, 5],
                    "split": [1, 1, 1, 1, 2, 2, 2, 2, 2],
                },
                "split_fields": ["split"],
            },
            "expected": {"stat": [0, 5]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_split_total_pretally_exhausted(param):
    rcv = SingleWinner(**param["input"])
    assert (
        rcv.get_stats(add_split_stats=True)[0]["split_total_pretally_exhausted"].tolist() == param["expected"]["stat"]
    )


params = [
    (
        {
            "input": {
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
                    "split": [1, 1, 2, 2, 2],
                },
                "split_fields": ["split"],
            },
            "expected": {"stat": [0, 0]},
        }
    ),
    (
        {
            "input": {
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
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                    ],
                    "split": [1, 1, 2, 2, 2],
                },
                "split_fields": ["split"],
            },
            "expected": {"stat": [0, 0]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                        [
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                        ],
                    ],
                    "split": [1, 1, 1, 1, 2, 2, 2, 2, 2],
                },
                "split_fields": ["split"],
            },
            "expected": {"stat": [0, 1]},
        }
    ),
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "B", "C", "D"],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.WRITEIN,
                        ],
                        [
                            "A",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["write-in", "A", "C", BallotMarks.OVERVOTE],
                        ["write-in", "B", "B", BallotMarks.OVERVOTE],
                        ["C", "D", BallotMarks.WRITEIN, "B"],
                        ["C", "D", "D", "B"],
                        ["D", "B", BallotMarks.WRITEIN, "D"],
                        [
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                        ],
                    ],
                    "weight": [1, 1, 1, 2, 2, 1, 1, 1, 5],
                    "split": [1, 1, 1, 1, 2, 2, 2, 2, 2],
                },
                "split_fields": ["split"],
            },
            "expected": {"stat": [0, 1]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_split_total_posttally_exhausted(param):
    rcv = SingleWinner(**param["input"])
    assert (
        rcv.get_stats(add_split_stats=True)[0]["split_total_posttally_exhausted"].tolist() == param["expected"]["stat"]
    )


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        ["B", BallotMarks.OVERVOTE, "A", "B"],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "D",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "split": [1, 1, 1, 1, 2, 2, 2, 2],
                },
                "split_fields": ["split"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {"stat": [1, 0]},
        }
    )
]


@pytest.mark.parametrize("param", params)
def test_split_total_posttally_exhausted_by_overvote(param):
    rcv = SingleWinner(**param["input"])
    assert (
        rcv.get_stats(add_split_stats=True)[0]["split_total_posttally_exhausted_by_overvote"].tolist()
        == param["expected"]["stat"]
    )


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        ["B", BallotMarks.OVERVOTE, "A", "B"],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "D",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "split": [1, 1, 1, 1, 2, 2, 2, 2],
                },
                "split_fields": ["split"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {"stat": [0, 1]},
        }
    )
]


@pytest.mark.parametrize("param", params)
def test_split_total_posttally_exhausted_by_skipped_rankings(param):
    rcv = SingleWinner(**param["input"])
    assert (
        rcv.get_stats(add_split_stats=True)[0]["split_total_posttally_exhausted_by_skipped_rankings"].tolist()
        == param["expected"]["stat"]
    )


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        [
                            "B",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "D",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "split": [1, 1, 1, 1, 2, 2, 2, 2],
                },
                "split_fields": ["split"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {"stat": [1, 0]},
        }
    )
]


@pytest.mark.parametrize("param", params)
def test_split_total_posttally_exhausted_by_abstention(param):
    rcv = SingleWinner(**param["input"])
    assert (
        rcv.get_stats(add_split_stats=True)[0]["split_total_posttally_exhausted_by_abstention"].tolist()
        == param["expected"]["stat"]
    )


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        ["B", BallotMarks.OVERVOTE, "A", "B"],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "D",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "split": [1, 1, 1, 1, 2, 2, 2, 3],
                },
                "split_fields": ["split"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {"stat": [0, 0, 0]},
        }
    )
]


@pytest.mark.parametrize("param", params)
def test_split_total_posttally_exhausted_by_rank_limit(param):
    rcv = SingleWinner(**param["input"])
    assert (
        rcv.get_stats(add_split_stats=True)[0]["split_total_posttally_exhausted_by_rank_limit"].tolist()
        == param["expected"]["stat"]
    )


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        ["B", BallotMarks.OVERVOTE, "A", "B"],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "D",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "split": [1, 1, 1, 1, 2, 2, 2, 3],
                },
                "split_fields": ["split"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {"stat": [0, 0, 0]},
        }
    )
]


@pytest.mark.parametrize("param", params)
def test_split_total_posttally_exhausted_by_rank_limit_fully_ranked(param):
    rcv = SingleWinner(**param["input"])
    assert (
        rcv.get_stats(add_split_stats=True)[0]["split_total_posttally_exhausted_by_rank_limit_fully_ranked"].tolist()
        == param["expected"]["stat"]
    )


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        ["B", BallotMarks.OVERVOTE, "A", "B"],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "D",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "split": [1, 1, 1, 1, 2, 2, 2, 3],
                },
                "split_fields": ["split"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {"stat": [0, 0, 0]},
        }
    )
]


@pytest.mark.parametrize("param", params)
def test_split_total_posttally_exhausted_by_rank_limit_partially_ranked(param):
    rcv = SingleWinner(**param["input"])
    assert (
        rcv.get_stats(add_split_stats=True)[0][
            "split_total_posttally_exhausted_by_rank_limit_partially_ranked"
        ].tolist()
        == param["expected"]["stat"]
    )


params = [
    (
        {
            "input": {
                "parsed_cvr": {
                    "ranks": [
                        ["A", "C", "C", "D"],
                        [BallotMarks.OVERVOTE, "A", "B", "C"],
                        ["B", BallotMarks.OVERVOTE, "A", "B"],
                        ["B", "A", "A", "C"],
                        ["C", BallotMarks.SKIPPED, BallotMarks.SKIPPED, "A"],
                        ["C", "A", "B", "E"],
                        [
                            "D",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 1, 5, 5],
                    "split": [1, 1, 1, 1, 2, 2, 2, 2],
                },
                "split_fields": ["split"],
                "exhaust_on_duplicate_candidate_marks": True,
                "exhaust_on_overvote_marks": True,
                "exhaust_on_repeated_skipped_marks": True,
            },
            "expected": {"stat": [2, 0]},
        }
    )
]


@pytest.mark.parametrize("param", params)
def test_split_total_posttally_exhausted_by_duplicate_rankings(param):
    rcv = SingleWinner(**param["input"])
    assert (
        rcv.get_stats(add_split_stats=True)[0]["split_total_posttally_exhausted_by_duplicate_rankings"].tolist()
        == param["expected"]["stat"]
    )
