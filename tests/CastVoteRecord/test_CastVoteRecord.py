
import pytest
import decimal

import pandas as pd
import numpy as np

from rcv_cruncher.cvr.base import CastVoteRecord
from rcv_cruncher.marks import BallotMarks


add_rule_set_ballots = [
    [
        'A',
        BallotMarks.WRITEIN,
        'write-in',
        BallotMarks.SKIPPED,
        BallotMarks.SKIPPED,
        BallotMarks.OVERVOTE,
        'A',
        'B'
    ],
    [
        BallotMarks.OVERVOTE,
        'Tuwi',
        BallotMarks.WRITEIN,
        'A',
        'B',
        'B',
        'C',
        BallotMarks.SKIPPED
    ]
]

params = [
    ({
        'input': {
            'cvr': {
                'weight': [1, 1],
                'ranks': add_rule_set_ballots
            },
            'rule_set': BallotMarks.new_rule_set(
                combine_writein_marks=True
            )
        },
        'expected': {
            'cvr': {
                'weight': [decimal.Decimal('1'), decimal.Decimal('1')],
                'ranks': [
                    [
                        'A',
                        BallotMarks.WRITEIN,
                        BallotMarks.WRITEIN,  # 'write-in',
                        BallotMarks.SKIPPED,
                        BallotMarks.SKIPPED,
                        BallotMarks.OVERVOTE,
                        'A',
                        'B'
                    ],
                    [
                        BallotMarks.OVERVOTE,
                        'Tuwi',
                        BallotMarks.WRITEIN,
                        'A',
                        'B',
                        'B',
                        'C',
                        BallotMarks.SKIPPED
                    ]
                ]
            },
            'candidate_set': {
                'A',
                'B',
                'C',
                'Tuwi',
                # 'write-in',
                BallotMarks.WRITEIN
            }
        }
    }),
    ({
        'input': {
            'cvr': {
                'weight': [1, 1],
                'ranks': add_rule_set_ballots
            },
            'rule_set': BallotMarks.new_rule_set(
                combine_writein_marks=True,
                exclude_writein_marks=True
            )
        },
        'expected': {
            'cvr': {
                'weight': [decimal.Decimal('1'), decimal.Decimal('1')],
                'ranks': [
                    [
                        'A',
                        # BallotMarks.WRITEIN,
                        # 'write-in',
                        BallotMarks.SKIPPED,
                        BallotMarks.SKIPPED,
                        BallotMarks.OVERVOTE,
                        'A',
                        'B'
                    ],
                    [
                        BallotMarks.OVERVOTE,
                        'Tuwi',
                        # BallotMarks.WRITEIN,
                        'A',
                        'B',
                        'B',
                        'C',
                        BallotMarks.SKIPPED
                    ]
                ]
            },
            'candidate_set': {
                'A',
                'B',
                'C',
                'Tuwi'
                # 'write-in',
                # BallotMarks.WRITEIN
            }
        }
    }),
    ({
        'input': {
            'cvr': {
                'weight': [1, 1],
                'ranks': add_rule_set_ballots
            },
            'rule_set': BallotMarks.new_rule_set(
                combine_writein_marks=False,
                exclude_writein_marks=True
            )
        },
        'expected': {
            'cvr': {
                'weight': [decimal.Decimal('1'), decimal.Decimal('1')],
                'ranks': [
                    [
                        'A',
                        # BallotMarks.WRITEIN,
                        'write-in',
                        BallotMarks.SKIPPED,
                        BallotMarks.SKIPPED,
                        BallotMarks.OVERVOTE,
                        'A',
                        'B'
                    ],
                    [
                        BallotMarks.OVERVOTE,
                        'Tuwi',
                        # BallotMarks.WRITEIN,
                        'A',
                        'B',
                        'B',
                        'C',
                        BallotMarks.SKIPPED
                    ]
                ]
            },
            'candidate_set': {
                'A',
                'B',
                'C',
                'Tuwi',
                'write-in',
                # BallotMarks.WRITEIN
            }
        }
    }),
    ({
        'input': {
            'cvr': {
                'weight': [1, 1],
                'ranks': add_rule_set_ballots
            },
            'rule_set': BallotMarks.new_rule_set(
                exclude_duplicate_candidate_marks=True
            )
        },
        'expected': {
            'cvr': {
                'weight': [decimal.Decimal('1'), decimal.Decimal('1')],
                'ranks': [
                    [
                        'A',
                        BallotMarks.WRITEIN,
                        'write-in',
                        BallotMarks.SKIPPED,
                        BallotMarks.SKIPPED,
                        BallotMarks.OVERVOTE,
                        # 'A',
                        'B'
                    ],
                    [
                        BallotMarks.OVERVOTE,
                        'Tuwi',
                        BallotMarks.WRITEIN,
                        'A',
                        'B',
                        # 'B',
                        'C',
                        BallotMarks.SKIPPED
                    ]
                ]
            },
            'candidate_set': {
                'A',
                'B',
                'C',
                'Tuwi',
                'write-in',
                BallotMarks.WRITEIN
            }
        }
    }),
    ({
        'input': {
            'cvr': {
                'weight': [1, 1],
                'ranks': add_rule_set_ballots
            },
            'rule_set': BallotMarks.new_rule_set(
                exclude_overvote_marks=True
            )
        },
        'expected': {
            'cvr': {
                'weight': [decimal.Decimal('1'), decimal.Decimal('1')],
                'ranks': [
                    [
                        'A',
                        BallotMarks.WRITEIN,
                        'write-in',
                        BallotMarks.SKIPPED,
                        BallotMarks.SKIPPED,
                        # BallotMarks.OVERVOTE,
                        'A',
                        'B'
                    ],
                    [
                        # BallotMarks.OVERVOTE,
                        'Tuwi',
                        BallotMarks.WRITEIN,
                        'A',
                        'B',
                        'B',
                        'C',
                        BallotMarks.SKIPPED
                    ]
                ]
            },
            'candidate_set': {
                'A',
                'B',
                'C',
                'Tuwi',
                'write-in',
                BallotMarks.WRITEIN
            }
        }
    }),
    ({
        'input': {
            'cvr': {
                'weight': [1, 1],
                'ranks': add_rule_set_ballots
            },
            'rule_set': BallotMarks.new_rule_set(
                exclude_skipped_marks=True
            )
        },
        'expected': {
            'cvr': {
                'weight': [decimal.Decimal('1'), decimal.Decimal('1')],
                'ranks': [
                    [
                        'A',
                        BallotMarks.WRITEIN,
                        'write-in',
                        # BallotMarks.SKIPPED,
                        # BallotMarks.SKIPPED,
                        BallotMarks.OVERVOTE,
                        'A',
                        'B'
                    ],
                    [
                        BallotMarks.OVERVOTE,
                        'Tuwi',
                        BallotMarks.WRITEIN,
                        'A',
                        'B',
                        'B',
                        'C',
                        # BallotMarks.SKIPPED
                    ]
                ]
            },
            'candidate_set': {
                'A',
                'B',
                'C',
                'Tuwi',
                'write-in',
                BallotMarks.WRITEIN
            }
        }
    }),
    ({
        'input': {
            'cvr': {
                'weight': [1, 1],
                'ranks': add_rule_set_ballots
            },
            'rule_set': BallotMarks.new_rule_set(
                exhaust_on_overvote_marks=True
            )
        },
        'expected': {
            'cvr': {
                'weight': [decimal.Decimal('1'), decimal.Decimal('1')],
                'ranks': [
                    [
                        'A',
                        BallotMarks.WRITEIN,
                        'write-in',
                        BallotMarks.SKIPPED,
                        BallotMarks.SKIPPED,
                        # BallotMarks.OVERVOTE,
                        # 'A',
                        # 'B'
                    ],
                    [
                        # BallotMarks.OVERVOTE,
                        # 'Tuwi',
                        # BallotMarks.WRITEIN,
                        # 'A',
                        # 'B',
                        # 'B',
                        # 'C',
                        # BallotMarks.SKIPPED
                    ]
                ]
            },
            'candidate_set': {
                'A',
                'B',
                'C',
                'Tuwi',
                'write-in',
                BallotMarks.WRITEIN
            }
        }
    }),
    ({
        'input': {
            'cvr': {
                'weight': [1, 1],
                'ranks': add_rule_set_ballots
            },
            'rule_set': BallotMarks.new_rule_set(
                exhaust_on_repeated_skipped_marks=True
            )
        },
        'expected': {
            'cvr': {
                'weight': [decimal.Decimal('1'), decimal.Decimal('1')],
                'ranks': [
                    [
                        'A',
                        BallotMarks.WRITEIN,
                        'write-in',
                        # BallotMarks.SKIPPED,
                        # BallotMarks.SKIPPED,
                        # BallotMarks.OVERVOTE,
                        # 'A',
                        # 'B'
                    ],
                    [
                        BallotMarks.OVERVOTE,
                        'Tuwi',
                        BallotMarks.WRITEIN,
                        'A',
                        'B',
                        'B',
                        'C',
                        BallotMarks.SKIPPED
                    ]
                ]
            },
            'candidate_set': {
                'A',
                'B',
                'C',
                'Tuwi',
                'write-in',
                BallotMarks.WRITEIN
            }
        }
    }),
    ({
        'input': {
            'cvr': {
                'weight': [1, 1],
                'ranks': add_rule_set_ballots
            },
            'rule_set': BallotMarks.new_rule_set(
                exhaust_on_duplicate_candidate_marks=True
            )
        },
        'expected': {
            'cvr': {
                'weight': [decimal.Decimal('1'), decimal.Decimal('1')],
                'ranks': [
                    [
                        'A',
                        BallotMarks.WRITEIN,
                        'write-in',
                        BallotMarks.SKIPPED,
                        BallotMarks.SKIPPED,
                        BallotMarks.OVERVOTE,
                        # 'A',
                        # 'B'
                    ],
                    [
                        BallotMarks.OVERVOTE,
                        'Tuwi',
                        BallotMarks.WRITEIN,
                        'A',
                        'B',
                        # 'B',
                        # 'C',
                        # BallotMarks.SKIPPED
                    ]
                ]
            },
            'candidate_set': {
                'A',
                'B',
                'C',
                'Tuwi',
                'write-in',
                BallotMarks.WRITEIN
            }
        }
    }),
    ({
        'input': {
            'cvr': {
                'weight': [1, 1],
                'ranks': add_rule_set_ballots
            },
            'rule_set': BallotMarks.new_rule_set(
                exhaust_on_duplicate_candidate_marks=True,
                treat_combined_writeins_as_exhaustable_duplicates=True,
                combine_writein_marks=True
            )
        },
        'expected': {
            'cvr': {
                'weight': [decimal.Decimal('1'), decimal.Decimal('1')],
                'ranks': [
                    [
                        'A',
                        BallotMarks.WRITEIN,
                        # 'write-in',
                        # BallotMarks.SKIPPED,
                        # BallotMarks.SKIPPED,
                        # BallotMarks.OVERVOTE,
                        # 'A',
                        # 'B'
                    ],
                    [
                        BallotMarks.OVERVOTE,
                        'Tuwi',
                        BallotMarks.WRITEIN,
                        'A',
                        'B',
                        # 'B',
                        # 'C',
                        # BallotMarks.SKIPPED
                    ]
                ]
            },
            'candidate_set': {
                'A',
                'B',
                'C',
                'Tuwi',
                # 'write-in',
                BallotMarks.WRITEIN
            }
        }
    })
]


@pytest.mark.parametrize("param", params)
def test_add_rule_set(param):

    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    cast_vote_record.add_rule_set('test', param['input']['rule_set'])

    cvr_dict = cast_vote_record.get_cvr_dict('test')
    cvr_dict['ranks'] = [b.marks for b in cvr_dict['ballot_marks']]
    del cvr_dict['ballot_marks']

    candidate_set = set(cast_vote_record.get_candidates('test').marks)

    assert cvr_dict == param['expected']['cvr']
    assert candidate_set == param['expected']['candidate_set']


params = [
    ({
        'input': {
            'cvr': {
                'ranks': add_rule_set_ballots
            },
            'format': 'rank'
        },
        'expected': {
            'table': pd.DataFrame({
                'rank1': ['A', BallotMarks.OVERVOTE],
                'rank2': [BallotMarks.WRITEIN, 'Tuwi'],
                'rank3': ['write-in', BallotMarks.WRITEIN],
                'rank4': [BallotMarks.SKIPPED, 'A'],
                'rank5': [BallotMarks.SKIPPED, 'B'],
                'rank6': [BallotMarks.OVERVOTE, 'B'],
                'rank7': ['A', 'C'],
                'rank8': ['B', BallotMarks.SKIPPED]
            })
        }
    }),
    ({
        'input': {
            'cvr': {
                'ranks': add_rule_set_ballots
            },
            'format': 'candidate'
        },
        'expected': {
            'table': pd.DataFrame({
                'candidate_A': ['1,7', '4'],
                'candidate_B': ['8', '5,6'],
                'candidate_C': [np.nan, '7'],
                'candidate_Tuwi': [np.nan, '2'],
                'candidate_write-in': ['3', np.nan],
                f'candidate_{BallotMarks.WRITEIN}': ['2', '3'],
                f'candidate_{BallotMarks.OVERVOTE}': ['6', '1'],
                'rank_limit': [8, 8]
            })
        }
    })
]


@pytest.mark.parametrize("param", params)
def test_get_cvr_table(param):

    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    table = cast_vote_record.get_cvr_table(table_format=param['input']['format'])

    for col in table.columns:
        assert table[col].equals(param['expected']['table'][col])


params = [
    ({
        'expected': {
            'stat': 1,
            'split_stat': [1]
        },
        'input': {
            'cvr': {
                'ranks': [['A']],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 2
        },
        'input': {
            'cvr': {
                'ranks': [['A', 'B']],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 3
        },
        'input': {
            'cvr': {
                'ranks': [['A', 'B', 'C']],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['A'],
                    [BallotMarks.SKIPPED]
                ],
                'weight': [1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 2
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['A', 'B'],
                    [BallotMarks.OVERVOTE, 'C']
                ],
                'weight': [1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 3
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['A', 'B', 'C'],
                    [BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED]
                ],
                'weight': [1, 1]
            }
        }
    })
]


@pytest.mark.parametrize("param", params)
def test_rank_limit(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])

    computed_stat = cast_vote_record.stats()['rank_limit'].item()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': False
        },
        'input': {
            'cvr': {
                'ranks': [['A', 'B', 'C']],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': False
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['A', 'B', 'C'],
                    [BallotMarks.SKIPPED, BallotMarks.SKIPPED, 'D']
                    ],
                'weight': [1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': True
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['A', 'B', 'C'],
                    [BallotMarks.SKIPPED, 'E', 'D']
                    ],
                'weight': [1, 1]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_restrictive_rank_limit(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    computed_stat = cast_vote_record.stats()['restrictive_rank_limit'].item()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': 0
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.OVERVOTE]],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 0
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, BallotMarks.WRITEIN, BallotMarks.SKIPPED]
                    ],
                'weight': [1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, BallotMarks.WRITEIN, BallotMarks.SKIPPED]
                    ],
                'weight': [1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 2
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, BallotMarks.WRITEIN, 'B']
                    ],
                'weight': [1, 1]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_n_candidates(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    computed_stat = cast_vote_record.stats()['n_candidates'].item()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': 0
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE]],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.OVERVOTE]],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 2
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.OVERVOTE],
                    [BallotMarks.OVERVOTE, 'A', BallotMarks.OVERVOTE]
                    ],
                'weight': [1, 1]
            }
        }
    })
]


@pytest.mark.parametrize("param", params)
def test_first_round_overvote(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    computed_stat = cast_vote_record.stats()['first_round_overvote'].item()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': [0]
        },
        'input': {
            'cvr': {
                'ranks': [['A']],
                'weight': [1],
                'split': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': [0, 0]
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['A', 'B'],
                    [BallotMarks.SKIPPED, 'A']
                ],
                'weight': [1, 1],
                'split': [1, 2]
            }
        }
    }),
    ({
        'expected': {
            'stat': [0, 2]
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['A', 'B'],
                    [BallotMarks.SKIPPED, BallotMarks.OVERVOTE],
                    [BallotMarks.OVERVOTE, 'A']
                ],
                'weight': [1, 1, 1],
                'split': [1, 2, 2]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_split_first_round_overvote(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'], split_fields=['split'])
    computed_stat = cast_vote_record.stats(add_split_stats=True)['split_first_round_overvote'].tolist()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE]],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 0
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE]],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 0
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, BallotMarks.WRITEIN, 'B']
                ],
                'weight': [1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 5
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, BallotMarks.SKIPPED, 'B']
                ],
                'weight': [1, 5]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_ranked_single(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    computed_stat = cast_vote_record.stats()['ranked_single'].item()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': [1]
        },
        'input': {
            'cvr': {
                'ranks': [['A']],
                'weight': [1],
                'split': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': [0, 1]
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['A', 'B'],
                    [BallotMarks.SKIPPED, 'A']
                ],
                'weight': [1, 1],
                'split': [1, 2]
            }
        }
    }),
    ({
        'expected': {
            'stat': [0, 1]
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['A', 'B'],
                    [BallotMarks.SKIPPED, BallotMarks.OVERVOTE],
                    [BallotMarks.OVERVOTE, 'A']
                ],
                'weight': [1, 1, 1],
                'split': [1, 2, 2]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_split_ranked_single(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'], split_fields=['split'])
    computed_stat = cast_vote_record.stats(add_split_stats=True)['split_ranked_single'].tolist()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': 0
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE]],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 0
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE]],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, BallotMarks.WRITEIN, 'B']
                ],
                'weight': [1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 5
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.WRITEIN, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE],
                    [BallotMarks.WRITEIN, BallotMarks.SKIPPED, 'B']
                ],
                'weight': [1, 5]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_ranked_multiple(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    computed_stat = cast_vote_record.stats()['ranked_multiple'].item()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': [0]
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE]],
                'weight': [1],
                'split': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': [0, 1]
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    ['A', 'B', 'C']
                    ],
                'weight': [1, 1],
                'split': [1, 2]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_split_ranked_multiple(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'], split_fields=['split'])
    computed_stat = cast_vote_record.stats(add_split_stats=True)['split_ranked_multiple'].tolist()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': 0
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE]],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.WRITEIN, 'A', 'B']],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.WRITEIN, 'A', 'B'],
                    [BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED]
                ],
                'weight': [1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 2
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.WRITEIN, 'A', 'B'],
                    ['A', 'B', 'C']
                ],
                'weight': [1, 1]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_ranked_3_or_more(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    computed_stat = cast_vote_record.stats()['ranked_3_or_more'].item()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': [0]
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE]],
                'weight': [1],
                'split': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': [0, 1]
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    ['A', 'B', 'C']
                    ],
                'weight': [1, 1],
                'split': [1, 2]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_split_ranked_3_or_more(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'], split_fields=['split'])
    computed_stat = cast_vote_record.stats(add_split_stats=True)['split_ranked_3_or_more'].tolist()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE]],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 0
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'B', BallotMarks.OVERVOTE],
                ],
                'weight': [1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', 'B'],
                    [BallotMarks.SKIPPED, 'B', BallotMarks.OVERVOTE],
                ],
                'weight': [1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', 'B'],
                    ['C', 'E', 'D'],
                ],
                'weight': [1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 0
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A'],
                    ['C', BallotMarks.SKIPPED],
                    ['B', BallotMarks.OVERVOTE],
                    ['D', BallotMarks.SKIPPED]
                ],
                'weight': [1, 1, 1, 1]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_total_fully_ranked(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    computed_stat = cast_vote_record.stats()['total_fully_ranked'].item()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': [1, 0]
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', 'B'],
                    [BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE]
                ],
                'weight': [1, 1, 1, 1],
                'split': [1, 1, 2, 2]
            }
        }
    }),
    ({
        'expected': {
            'stat': [2, 0]
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['B', 'A', 'C'],
                    ['D', 'A', 'B'],
                    [BallotMarks.SKIPPED, 'E', 'A'],
                    ['A', 'A', 'D']
                ],
                'weight': [1, 1, 1, 1],
                'split': [1, 1, 2, 2]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_split_total_fully_ranked(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'], split_fields=['split'])
    computed_stat = cast_vote_record.stats(add_split_stats=True)['split_total_fully_ranked'].tolist()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': 0
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE]],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, 'A', 'A']],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, BallotMarks.WRITEIN, BallotMarks.WRITEIN],
                    [BallotMarks.SKIPPED, BallotMarks.WRITEIN, 'write-in']
                    ],
                'weight': [1, 1]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_includes_duplicate_ranking(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    computed_stat = cast_vote_record.stats()['includes_duplicate_ranking'].item()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': [0, 0]
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', 'B'],
                    [BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE]
                ],
                'weight': [1, 1, 1, 1],
                'split': [1, 1, 2, 2]
            }
        }
    }),
    ({
        'expected': {
            'stat': [0, 1]
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['B', 'A', 'C'],
                    ['D', 'A', 'B'],
                    [BallotMarks.SKIPPED, 'E', 'A'],
                    ['A', 'A', 'D']
                ],
                'weight': [1, 1, 1, 1],
                'split': [1, 1, 2, 2]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_split_includes_duplicate_ranking(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'], split_fields=['split'])
    computed_stat = cast_vote_record.stats(add_split_stats=True)['split_includes_duplicate_ranking'].tolist()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE]],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.OVERVOTE]],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, BallotMarks.SKIPPED, 'A'],
                    ['A', BallotMarks.SKIPPED, BallotMarks.SKIPPED]
                    ],
                'weight': [1, 1]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_includes_skipped_ranking(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    computed_stat = cast_vote_record.stats()['includes_skipped_ranking'].item()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': [2, 2]
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', 'B'],
                    [BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE]
                ],
                'weight': [1, 1, 1, 1],
                'split': [1, 1, 2, 2]
            }
        }
    }),
    ({
        'expected': {
            'stat': [0, 1]
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['B', 'A', 'C'],
                    ['D', 'A', 'B'],
                    [BallotMarks.SKIPPED, 'E', 'A'],
                    ['A', 'A', 'D']
                ],
                'weight': [1, 1, 1, 1],
                'split': [1, 1, 2, 2]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_split_includes_skipped_ranking(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'], split_fields=['split'])
    computed_stat = cast_vote_record.stats(add_split_stats=True)['split_includes_skipped_ranking'].tolist()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE]],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 0
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, 'A', BallotMarks.WRITEIN]],
                'weight': [1]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_includes_overvote_ranking(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    computed_stat = cast_vote_record.stats()['includes_overvote_ranking'].item()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': [1, 2]
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', 'B'],
                    [BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE]
                ],
                'weight': [1, 1, 1, 1],
                'split': [1, 1, 2, 2]
            }
        }
    }),
    ({
        'expected': {
            'stat': [0, 0]
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['B', 'A', 'C'],
                    ['D', 'A', 'B'],
                    [BallotMarks.SKIPPED, 'E', 'A'],
                    ['A', 'A', 'D']
                ],
                'weight': [1, 1, 1, 1],
                'split': [1, 1, 2, 2]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_split_includes_overvote_ranking(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'], split_fields=['split'])
    computed_stat = cast_vote_record.stats(add_split_stats=True)['split_includes_overvote_ranking'].tolist()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, 'A', 'A', BallotMarks.OVERVOTE]],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 4
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', 'B', 'C'],
                    ['C', 'A', 'B', BallotMarks.OVERVOTE],
                    ['C', 'A', 'A', BallotMarks.SKIPPED],
                    [BallotMarks.SKIPPED, 'A', 'A', BallotMarks.OVERVOTE]
                    ],
                'weight': [1, 1, 1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 0
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['D', 'A', 'B', 'C'],
                    ['C', 'A', 'B', BallotMarks.WRITEIN],
                    ['C', 'A', 'D', BallotMarks.WRITEIN],
                    [BallotMarks.WRITEIN, 'B', 'A', BallotMarks.SKIPPED]
                    ],
                'weight': [1, 1, 1, 1]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_total_irregular(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    computed_stat = cast_vote_record.stats()['total_irregular'].item()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': [2, 2]
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', 'B'],
                    [BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE]
                ],
                'weight': [1, 1, 1, 1],
                'split': [1, 1, 2, 2]
            }
        }
    }),
    ({
        'expected': {
            'stat': [0, 2]
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['B', 'A', 'C'],
                    ['D', 'A', 'B'],
                    [BallotMarks.SKIPPED, 'E', 'A'],
                    ['A', 'A', 'D']
                ],
                'weight': [1, 1, 1, 1],
                'split': [1, 1, 2, 2]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_split_total_irregular(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'], split_fields=['split'])
    computed_stat = cast_vote_record.stats(add_split_stats=True)['split_total_irregular'].tolist()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [[BallotMarks.SKIPPED, 'A', 'A', BallotMarks.OVERVOTE]],
                'weight': [1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 2
        },
        'input': {
            'cvr': {
                'ranks': [['A'], ['B']],
                'weight': [1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 5
        },
        'input': {
            'cvr': {
                'ranks': [['A'], ['B']],
                'weight': [2.5, 2.5]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_total_ballots(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    computed_stat = cast_vote_record.stats()['total_ballots'].item()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': [2, 2]
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', 'B'],
                    [BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE]
                ],
                'weight': [1, 1, 1, 1],
                'split': [1, 1, 2, 2]
            }
        }
    }),
    ({
        'expected': {
            'stat': [2, 2]
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['B', 'A', 'C'],
                    ['D', 'A', 'B'],
                    [BallotMarks.SKIPPED, 'E', 'A'],
                    ['A', 'A', 'D']
                ],
                'weight': [1, 1, 1, 1],
                'split': [1, 1, 2, 2]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_split_total_ballots(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'], split_fields=['split'])
    computed_stat = cast_vote_record.stats(add_split_stats=True)['split_total_ballots'].tolist()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED]
                    ],
                'weight': [1, 1]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_total_undervote(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    computed_stat = cast_vote_record.stats()['total_undervote'].item()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': [0, 1]
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', 'B'],
                    [BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED]
                ],
                'weight': [1, 1, 1, 1, 1],
                'split': [1, 1, 2, 2, 2]
            }
        }
    }),
    ({
        'expected': {
            'stat': [0, 0]
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['B', 'A', 'C'],
                    ['D', 'A', 'B'],
                    [BallotMarks.SKIPPED, 'E', 'A'],
                    ['A', 'A', 'D']
                ],
                'weight': [1, 1, 1, 1],
                'split': [1, 1, 2, 2]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_split_total_undervote(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'], split_fields=['split'])
    computed_stat = cast_vote_record.stats(add_split_stats=True)['split_total_undervote'].tolist()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED]
                    ],
                'weight': [1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 1.5
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', 'B', BallotMarks.SKIPPED]
                    ],
                'weight': [1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': round(11/6, 3)
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', 'B', BallotMarks.SKIPPED]
                    ],
                'weight': [1, 5]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_mean_rankings_used(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    computed_stat = cast_vote_record.stats()['mean_rankings_used'].item()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': [1.5, 0.5]
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', 'B'],
                    [BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED]
                ],
                'weight': [1, 1, 1, 1, 1],
                'split': [1, 1, 2, 2, 2]
            }
        }
    }),
    ({
        'expected': {
            'stat': [3, 2]
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['B', 'A', 'C'],
                    ['D', 'A', 'B'],
                    [BallotMarks.SKIPPED, 'E', 'A'],
                    ['A', 'A', 'D']
                ],
                'weight': [1, 1, 1, 1],
                'split': [1, 1, 2, 2]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_split_mean_rankings_used(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'], split_fields=['split'])
    computed_stat = cast_vote_record.stats(add_split_stats=True)['split_mean_rankings_used'].tolist()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': 1
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED]
                    ],
                'weight': [1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 1.5
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', 'B', BallotMarks.SKIPPED]
                    ],
                'weight': [1, 1]
            }
        }
    }),
    ({
        'expected': {
            'stat': 2
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', 'B', BallotMarks.SKIPPED]
                    ],
                'weight': [1, 5]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_median_rankings_used(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'])
    computed_stat = cast_vote_record.stats()['median_rankings_used'].item()
    assert param['expected']['stat'] == computed_stat


params = [
    ({
        'expected': {
            'stat': [1.5, 0.5]
        },
        'input': {
            'cvr': {
                'ranks': [
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', 'B'],
                    [BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, 'A', BallotMarks.OVERVOTE],
                    [BallotMarks.SKIPPED, BallotMarks.SKIPPED, BallotMarks.SKIPPED]
                ],
                'weight': [1, 1, 1, 1, 1],
                'split': [1, 1, 2, 2, 2]
            }
        }
    }),
    ({
        'expected': {
            'stat': [3, 2]
        },
        'input': {
            'cvr': {
                'ranks': [
                    ['B', 'A', 'C'],
                    ['D', 'A', 'B'],
                    [BallotMarks.SKIPPED, 'E', 'A'],
                    ['A', 'A', 'D']
                ],
                'weight': [1, 1, 1, 6],
                'split': [1, 1, 2, 2]
            }
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_split_median_rankings_used(param):
    cast_vote_record = CastVoteRecord(parsed_cvr=param['input']['cvr'], split_fields=['split'])
    computed_stat = cast_vote_record.stats(add_split_stats=True)['split_median_rankings_used'].tolist()
    assert param['expected']['stat'] == computed_stat
