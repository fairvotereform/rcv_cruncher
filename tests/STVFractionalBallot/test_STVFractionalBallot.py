import decimal
import pytest

import pandas as pd

from decimal import Decimal

import rcv_cruncher.util as util
from rcv_cruncher.marks import BallotMarks
from rcv_cruncher.rcv.variants import STV, STVFractionalBallot


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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {
                "n_tabulation": 1,
                "n_round": 2,
                "rounds": [
                    {"A": 2, "B": 0, "C": 1, "D": 0, "E": 0.5, BallotMarks.WRITEIN: 2},
                    {"A": 2, "B": 0, "C": 1, "D": 0, "E": 0, BallotMarks.WRITEIN: 2},
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {
                "n_tabulation": 1,
                "n_round": 5,
                "rounds": [
                    {"A": 3, "B": 0, "C": 1, "D": 0, "E": 0.5, BallotMarks.WRITEIN: 3},
                    {
                        "A": 2,
                        "B": Decimal(2) / Decimal(3),
                        "C": 1,
                        "D": 0,
                        "E": 0.5,
                        BallotMarks.WRITEIN: 3 + Decimal(1) / Decimal(3),
                    },
                    {
                        "A": 2,
                        "B": (Decimal(2) / Decimal(3))
                        + (((3 + Decimal(1) / Decimal(3)) - 2) / (3 + Decimal(1) / Decimal(3))),
                        "C": 1 + 2 * (((3 + Decimal(1) / Decimal(3)) - 2) / (3 + Decimal(1) / Decimal(3))),
                        "D": 0,
                        "E": 0.5,
                        BallotMarks.WRITEIN: 2,
                    },
                    {
                        "A": 2,
                        "B": (Decimal(2) / Decimal(3))
                        + (((3 + Decimal(1) / Decimal(3)) - 2) / (3 + Decimal(1) / Decimal(3))),
                        "C": 1 + 2 * (((3 + Decimal(1) / Decimal(3)) - 2) / (3 + Decimal(1) / Decimal(3))),
                        "D": 0,
                        "E": 0,
                        BallotMarks.WRITEIN: 2,
                    },
                    {
                        "A": 2,
                        "B": 0,
                        "C": 1
                        + 2 * (((3 + Decimal(1) / Decimal(3)) - 2) / (3 + Decimal(1) / Decimal(3)))
                        + (Decimal(2) / Decimal(3)),
                        "D": 0,
                        "E": 0,
                        BallotMarks.WRITEIN: 2,
                    },
                ],
            },
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {
                "n_tabulation": 1,
                "n_round": 4,
                "rounds": [
                    {"A": 3, "B": 0, "C": 1, "D": 0, "E": 0.5, BallotMarks.WRITEIN: 3},
                    {
                        "A": 2,
                        "B": 1,
                        "C": 1 + Decimal(2) / Decimal(3),
                        "D": 0,
                        "E": 0.5,
                        BallotMarks.WRITEIN: 2,
                    },
                    {
                        "A": 2,
                        "B": 1,
                        "C": 1 + Decimal(2) / Decimal(3),
                        "D": 0,
                        "E": 0,
                        BallotMarks.WRITEIN: 2,
                    },
                    {
                        "A": 2,
                        "B": 0,
                        "C": 1 + Decimal(2) / Decimal(3) + Decimal(2) / Decimal(3),
                        "D": 0,
                        "E": 0,
                        BallotMarks.WRITEIN: 2,
                    },
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
    rcv = STVFractionalBallot(**param["input"])

    # confirm tabulation num
    n_tabulations = rcv.n_tabulations()
    assert n_tabulations == param["expected"]["n_tabulation"]

    # confirm round num
    n_round = rcv.n_rounds(tabulation_num=1)
    assert n_round == param["expected"]["n_round"]

    # confirm round tallies
    tally_dict = [rcv.get_round_tally_dict(round_num=i) for i in range(1, n_round + 1)]
    tally_dict = [{k: float(v) for k, v in d.items()} for d in tally_dict]
    assert tally_dict == [{k: float(v) for k, v in d.items()} for d in param["expected"]["rounds"]]


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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_first_round_winner_vote(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_final_round_winner_vote(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_first_round_winner_percent(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_final_round_winner_percent(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_first_round_winner_place(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_condorcet(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_come_from_behind(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_ranked_winner(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": None},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_final_round_winner_votes_over_first_round_active(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 2},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 2},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_static_win_threshold(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 3},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 3},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_number_of_tabulation_winners(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": "A, writein, C"},
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": "A, writein, C"},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": "A, writein, C"},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_winner(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": round(100 * 5 / 5.5, 3)},
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": round(100 * 7 / 7.5, 3)},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": round(100 * 7 / 7.5, 3)},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_winners_consensus_value(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 5.5},
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 7.5},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 7.5},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_first_round_active_votes(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {
                "stat": round(
                    float(
                        5
                        + 2 * (((3 + Decimal(1) / Decimal(3)) - 2) / (3 + Decimal(1) / Decimal(3)))
                        + (Decimal(2) / Decimal(3))
                    ),
                    3,
                )
            },
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": round(float(6 + decimal.Decimal(1 / 3)), 3)},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_final_round_active_votes(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 0},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                        [
                            BallotMarks.SKIPPED,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5, 5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 5},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_pretally_exhausted(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 0.5},
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {
                "stat": round(
                    float(
                        Decimal(1) / Decimal(3) * (((3 + Decimal(1) / Decimal(3)) - 2) / (3 + Decimal(1) / Decimal(3)))
                        + Decimal("0.5")
                        + (((3 + Decimal(1) / Decimal(3)) - 2) / (3 + Decimal(1) / Decimal(3)))
                    ),
                    3,
                )
            },
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {
                "stat": round(
                    float(decimal.Decimal(2) / decimal.Decimal(3) + decimal.Decimal(1) / decimal.Decimal(2)),
                    3,
                )
            },
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted(param):
    rcv = STVFractionalBallot(**param["input"])
    assert rcv.get_stats()[0]["total_posttally_exhausted"].item() == param["expected"]["stat"]


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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 0},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 0},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_overvote(param):
    rcv = STVFractionalBallot(**param["input"])
    assert rcv.get_stats()[0]["total_posttally_exhausted_by_overvote"].item() == param["expected"]["stat"]


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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 0},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 0},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_skipped_rankings(param):
    rcv = STVFractionalBallot(**param["input"])
    assert rcv.get_stats()[0]["total_posttally_exhausted_by_skipped_rankings"].item() == param["expected"]["stat"]


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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 0.5},
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
                        ["C", "A", "B", "B"],
                        ["E", "F", BallotMarks.SKIPPED, BallotMarks.SKIPPED],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": round(float(+Decimal("0.5")), 3)},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {
                "stat": round(
                    float(decimal.Decimal(2) / decimal.Decimal(3) + decimal.Decimal(1) / decimal.Decimal(2)),
                    3,
                )
            },
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_abstention(param):
    rcv = STVFractionalBallot(**param["input"])
    assert rcv.get_stats()[0]["total_posttally_exhausted_by_abstention"].item() == param["expected"]["stat"]


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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        ["E", "F", BallotMarks.SKIPPED, BallotMarks.SKIPPED],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {
                "stat": round(
                    float(
                        Decimal(1) / Decimal(3) * (((3 + Decimal(1) / Decimal(3)) - 2) / (3 + Decimal(1) / Decimal(3)))
                        + (((3 + Decimal(1) / Decimal(3)) - 2) / (3 + Decimal(1) / Decimal(3)))
                    ),
                    3,
                )
            },
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 0},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_rank_limit(param):
    rcv = STVFractionalBallot(**param["input"])
    assert rcv.get_stats()[0]["total_posttally_exhausted_by_rank_limit"].item() == param["expected"]["stat"]


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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        ["E", "F", BallotMarks.SKIPPED, BallotMarks.SKIPPED],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 0},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 0},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_rank_limit_fully_ranked(param):
    rcv = STVFractionalBallot(**param["input"])
    assert (
        rcv.get_stats()[0]["total_posttally_exhausted_by_rank_limit_fully_ranked"].item() == param["expected"]["stat"]
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        ["E", "F", BallotMarks.SKIPPED, BallotMarks.SKIPPED],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {
                "stat": round(
                    float(
                        Decimal(1) / Decimal(3) * (((3 + Decimal(1) / Decimal(3)) - 2) / (3 + Decimal(1) / Decimal(3)))
                        + (((3 + Decimal(1) / Decimal(3)) - 2) / (3 + Decimal(1) / Decimal(3)))
                    ),
                    3,
                )
            },
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 0},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_rank_limit_partially_ranked(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                },
                "n_winners": 3,
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
                        ["C", "A", "B", "B"],
                        ["E", "F", BallotMarks.SKIPPED, BallotMarks.SKIPPED],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 0},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
                "exhaust_on_duplicate_candidate_marks": True,
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
                        ["write-in", "B", BallotMarks.SKIPPED, BallotMarks.OVERVOTE],
                        ["C", "A", "B", "B"],
                        ["E", "E", BallotMarks.SKIPPED, BallotMarks.SKIPPED],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                },
                "n_winners": 3,
            },
            "expected": {"stat": 0.5},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_total_posttally_exhausted_by_duplicate_rankings(param):
    rcv = STVFractionalBallot(**param["input"])
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
                        [
                            "E",
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [1, 1, 1, 1, 1, 0.5],
                    "precinct": [1, 1, 1, 2, 2, 2],
                },
                "n_winners": 3,
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
                        ["E", "F", BallotMarks.SKIPPED, BallotMarks.SKIPPED],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                    "precinct": [1, 1, 1, 2, 2, 2],
                },
                "n_winners": 3,
                "split_fields": ["precinct"],
            },
            "expected": {"stat": [[0, 0]]},
        }
    ),
    (
        {
            "input": {
                "multi_winner_rounds": True,
                "exhaust_on_duplicate_candidate_marks": True,
                "split_fields": ["precinct"],
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
                        ["write-in", "B", BallotMarks.SKIPPED, BallotMarks.OVERVOTE],
                        ["C", "A", "B", "B"],
                        [
                            BallotMarks.OVERVOTE,
                            BallotMarks.OVERVOTE,
                            BallotMarks.SKIPPED,
                            BallotMarks.SKIPPED,
                        ],
                    ],
                    "weight": [2, 1, 2, 1, 1, 0.5],
                    "precinct": [1, 1, 1, 2, 2, 2],
                },
                "n_winners": 3,
            },
            "expected": {"stat": [[0, 0.5]]},
        }
    ),
]


@pytest.mark.parametrize("param", params)
def test_split_total_pretally_exhausted(param):
    rcv = STVFractionalBallot(**param["input"])
    assert [i["split_total_pretally_exhausted"].tolist() for i in rcv.get_stats(add_split_stats=True)] == param[
        "expected"
    ]["stat"]


# @pytest.mark.parametrize("param", params)
# def test_split_total_posttally_exhausted(param):
#     rcv = Until2(**param['input'])
#     assert rcv.get_stats(add_split_stats=True)[0]['split_total_posttally_exhausted'].tolist() == param['expected']['stat']


# @pytest.mark.parametrize("param", params)
# def test_split_total_posttally_exhausted_by_overvote(param):
#     rcv = Until2(**param['input'])
#     assert rcv.get_stats(add_split_stats=True)[0]['split_total_posttally_exhausted_by_overvote'].tolist() == param['expected']['stat']


# @pytest.mark.parametrize("param", params)
# def test_split_total_posttally_exhausted_by_skipped_rankings(param):
#     rcv = Until2(**param['input'])
#     assert rcv.get_stats(add_split_stats=True)[0]['split_total_posttally_exhausted_by_skipped_rankings'].tolist() == param['expected']['stat']


# @pytest.mark.parametrize("param", params)
# def test_split_total_posttally_exhausted_by_abstention(param):
#     rcv = Until2(**param['input'])
#     assert rcv.get_stats(add_split_stats=True)[0]['split_total_posttally_exhausted_by_abstention'].tolist() == param['expected']['stat']


# @pytest.mark.parametrize("param", params)
# def test_split_total_posttally_exhausted_by_rank_limit(param):
#     rcv = Until2(**param['input'])
#     assert rcv.get_stats(add_split_stats=True)[0]['split_total_posttally_exhausted_by_rank_limit'].tolist() == param['expected']['stat']


# @pytest.mark.parametrize("param", params)
# def test_split_total_posttally_exhausted_by_duplicate_rankings(param):
#     rcv = Until2(**param['input'])
#     assert rcv.get_stats(add_split_stats=True)[0]['split_total_posttally_exhausted_by_duplicate_rankings'].tolist() == param['expected']['stat']
