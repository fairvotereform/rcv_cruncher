
import pytest

from rcv_cruncher.marks import BallotMarks


def test_update_marks():

    marks = ['A', 'B', 'B', BallotMarks.OVERVOTE, BallotMarks.SKIPPED]
    unique_marks = {'A', 'B', BallotMarks.OVERVOTE, BallotMarks.SKIPPED}
    unique_candidates = {'A', 'B'}

    b = BallotMarks()
    b.update_marks(marks)

    assert b.marks == marks
    assert b.unique_marks == unique_marks
    assert b.unique_candidates == unique_candidates


param_dicts = [
    ({
        'input': 'A',
        'expected': False
    }),
    ({
        'input': BallotMarks.WRITEIN,
        'expected': True
    }),
    ({
        'input': 'writein10',
        'expected': True
    }),
    ({
        'input': 'Fuwi',
        'expected': False
    }),
    ({
        'input': 'UwI',
        'expected': True
    })
]


@pytest.mark.parametrize("param_dict", param_dicts)
def test_check_writein_match(param_dict):

    computed = BallotMarks.check_writein_match(param_dict['input'])
    expected = param_dict['expected']
    assert expected == computed


param_dicts = [
    ({
        'input': ['A', 'B', 'WriteIn', 'writein10'],
        'expected': {
            'marks': ['A', 'B', BallotMarks.WRITEIN, BallotMarks.WRITEIN],
            'unique_marks': {'A', 'B', BallotMarks.WRITEIN},
            'unique_candidates': {'A', 'B', BallotMarks.WRITEIN}
        }
    }),
    ({
        'input': ['A', 'B', 'Tuwi', 'UWI', 'uwi'],
        'expected': {
            'marks': ['A', 'B', 'Tuwi', BallotMarks.WRITEIN, BallotMarks.WRITEIN],
            'unique_marks': {'A', 'B', 'Tuwi', BallotMarks.WRITEIN},
            'unique_candidates': {'A', 'B', 'Tuwi', BallotMarks.WRITEIN}
        }
    })
]


@pytest.mark.parametrize("param_dict", param_dicts)
def test_combine_writein_marks(param_dict):

    b = BallotMarks(param_dict['input'])
    computed = BallotMarks.combine_writein_marks(b)

    assert computed.marks == param_dict['expected']['marks']
    assert computed.unique_marks == param_dict['expected']['unique_marks']
    assert computed.unique_candidates == param_dict['expected']['unique_candidates']


param_dicts = [
    ({
        'input': ['A', 'B', BallotMarks.WRITEIN, BallotMarks.WRITEIN],
        'expected': {
            'marks': ['A', 'B', BallotMarks.WRITEIN],
            'unique_marks': {'A', 'B', BallotMarks.WRITEIN},
            'unique_candidates': {'A', 'B', BallotMarks.WRITEIN}
        }
    }),
    ({
        'input': ['A', 'B', 'B', 'C', 'C'],
        'expected': {
            'marks': ['A', 'B', 'C'],
            'unique_marks': {'A', 'B', 'C'},
            'unique_candidates': {'A', 'B', 'C'}
        }
    })
]


@pytest.mark.parametrize("param_dict", param_dicts)
def test_remove_duplicate_marks(param_dict):

    b = BallotMarks(param_dict['input'])
    computed = BallotMarks.remove_duplicate_candidate_marks(b)

    assert computed.marks == param_dict['expected']['marks']
    assert computed.unique_marks == param_dict['expected']['unique_marks']
    assert computed.unique_candidates == param_dict['expected']['unique_candidates']


param_dicts = [
    ({
        'input': {
            'marks': ['A', 'B', BallotMarks.WRITEIN, BallotMarks.WRITEIN],
            'remove_marks': ['A']
        },
        'expected': {
            'marks': ['B', BallotMarks.WRITEIN, BallotMarks.WRITEIN],
            'unique_marks': {'B', BallotMarks.WRITEIN},
            'unique_candidates': {'B', BallotMarks.WRITEIN}
        }
    }),
    ({
        'input': {
            'marks': ['A', 'B', BallotMarks.WRITEIN, BallotMarks.WRITEIN],
            'remove_marks': ['A', 'B']
        },
        'expected': {
            'marks': [BallotMarks.WRITEIN, BallotMarks.WRITEIN],
            'unique_marks': {BallotMarks.WRITEIN},
            'unique_candidates': {BallotMarks.WRITEIN}
        }
    }),
    ({
        'input': {
            'marks': ['A', 'B', BallotMarks.WRITEIN, BallotMarks.WRITEIN],
            'remove_marks': []
        },
        'expected': {
            'marks': ['A', 'B', BallotMarks.WRITEIN, BallotMarks.WRITEIN],
            'unique_marks': {'A', 'B', BallotMarks.WRITEIN},
            'unique_candidates': {'A', 'B', BallotMarks.WRITEIN}
        }
    }),
]


@pytest.mark.parametrize("param_dict", param_dicts)
def test_remove_mark(param_dict):

    b = BallotMarks(param_dict['input']['marks'])
    computed = BallotMarks.remove_mark(b, param_dict['input']['remove_marks'])

    assert computed.marks == param_dict['expected']['marks']
    assert computed.unique_marks == param_dict['expected']['unique_marks']
    assert computed.unique_candidates == param_dict['expected']['unique_candidates']


param_dicts = [
    ({
        'input': {
            'marks': ['A', 'B', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'rules': BallotMarks.new_rule_set()
        },
        'expected': {
            'marks': ['A', 'B', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'unique_marks': {'A', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE},
            'unique_candidates': {'A', 'B', 'writein10', 'Tuwi', 'uwi', BallotMarks.WRITEIN}
        }
    }),
    ({
        'input': {
            'marks': ['A', 'B', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'rules': BallotMarks.new_rule_set(combine_writein_marks=True)
        },
        'expected': {
            'marks': ['A', 'B', 'B', BallotMarks.WRITEIN, 'Tuwi', BallotMarks.WRITEIN, BallotMarks.WRITEIN, BallotMarks.OVERVOTE],
            'unique_marks': {'A', 'B', 'Tuwi', BallotMarks.WRITEIN, BallotMarks.OVERVOTE},
            'unique_candidates': {'A', 'B', 'Tuwi', BallotMarks.WRITEIN}
        }
    }),
    ({
        'input': {
            'marks': ['A', 'B', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'rules': BallotMarks.new_rule_set(exclude_duplicate_candidate_marks=True)
        },
        'expected': {
            'marks': ['A', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'unique_marks': {'A', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE},
            'unique_candidates': {'A', 'B', 'writein10', 'Tuwi', 'uwi', BallotMarks.WRITEIN}
        }
    }),
    ({
        'input': {
            'marks': ['A', 'B', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'rules': BallotMarks.new_rule_set(exclude_duplicate_candidate_marks=True, combine_writein_marks=True)
        },
        'expected': {
            'marks': ['A', 'B', BallotMarks.WRITEIN, 'Tuwi', BallotMarks.OVERVOTE],
            'unique_marks': {'A', 'B', 'Tuwi', BallotMarks.WRITEIN, BallotMarks.OVERVOTE},
            'unique_candidates': {'A', 'B', 'Tuwi', BallotMarks.WRITEIN}
        }
    }),
    ({
        'input': {
            'marks': ['A', 'B', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'rules': BallotMarks.new_rule_set(exclude_writein_marks=True)
        },
        'expected': {
            'marks': ['A', 'B', 'B', 'writein10', 'Tuwi', 'uwi', BallotMarks.OVERVOTE],
            'unique_marks': {'A', 'B', 'writein10', 'Tuwi', 'uwi', BallotMarks.OVERVOTE},
            'unique_candidates': {'A', 'B', 'writein10', 'Tuwi', 'uwi'}
        }
    }),
    ({
        'input': {
            'marks': ['A', 'B', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'rules': BallotMarks.new_rule_set(exclude_writein_marks=True, combine_writein_marks=True)
        },
        'expected': {
            'marks': ['A', 'B', 'B', 'Tuwi', BallotMarks.OVERVOTE],
            'unique_marks': {'A', 'B', 'Tuwi', BallotMarks.OVERVOTE},
            'unique_candidates': {'A', 'B', 'Tuwi'}
        }
    }),
    ({
        'input': {
            'marks': ['A', 'B', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'rules': BallotMarks.new_rule_set(exclude_overvote_marks=True)
        },
        'expected': {
            'marks': ['A', 'B', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi'],
            'unique_marks': {'A', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi'},
            'unique_candidates': {'A', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi'}
        }
    }),
    ({
        'input': {
            'marks': [BallotMarks.SKIPPED, 'A', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'rules': BallotMarks.new_rule_set(exclude_skipped_marks=True)
        },
        'expected': {
            'marks': ['A', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'unique_marks': {'A', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE},
            'unique_candidates': {'A', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi'}
        }
    }),
    ({
        'input': {
            'marks': [BallotMarks.SKIPPED, 'A', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'rules': BallotMarks.new_rule_set(combine_writein_marks=True, exclude_duplicate_candidate_marks=True)
        },
        'expected': {
            'marks': [BallotMarks.SKIPPED, 'A', 'B', BallotMarks.WRITEIN, 'Tuwi', BallotMarks.OVERVOTE],
            'unique_marks': {'A', 'B', 'Tuwi', BallotMarks.WRITEIN, BallotMarks.SKIPPED, BallotMarks.OVERVOTE},
            'unique_candidates': {'A', 'B', 'Tuwi', BallotMarks.WRITEIN}
        }
    }),
    ({
        'input': {
            'marks': [BallotMarks.SKIPPED, 'A', 'B', 'writein10', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'rules': BallotMarks.new_rule_set(combine_writein_marks=True,
                                              exhaust_on_duplicate_candidate_marks=True,
                                              treat_combined_writeins_as_exhaustable_duplicates=True)
        },
        'expected': {
            'marks': [BallotMarks.SKIPPED, 'A', 'B', BallotMarks.WRITEIN, 'Tuwi'],
            'unique_marks': {'A', 'B', 'Tuwi', BallotMarks.WRITEIN, BallotMarks.SKIPPED},
            'unique_candidates': {'A', 'B', 'Tuwi', BallotMarks.WRITEIN}
        }
    }),
    ({
        'input': {
            'marks': [BallotMarks.SKIPPED, 'A', 'B', 'B', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'rules': BallotMarks.new_rule_set(exhaust_on_duplicate_candidate_marks=True)
        },
        'expected': {
            'marks': [BallotMarks.SKIPPED, 'A', 'B'],
            'unique_marks': {'A', 'B', BallotMarks.SKIPPED},
            'unique_candidates': {'A', 'B'}
        }
    }),
    ({
        'input': {
            'marks': [BallotMarks.OVERVOTE, 'A', 'B', 'B', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'rules': BallotMarks.new_rule_set(exhaust_on_overvote_marks=True)
        },
        'expected': {
            'marks': [],
            'unique_marks': set(),
            'unique_candidates': set()
        }
    }),
    ({
        'input': {
            'marks': [BallotMarks.SKIPPED, 'A', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'rules': BallotMarks.new_rule_set(exhaust_on_repeated_skipped_marks=True)
        },
        'expected': {
            'marks': [BallotMarks.SKIPPED, 'A', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE],
            'unique_marks': {BallotMarks.SKIPPED, 'A', 'Tuwi', BallotMarks.WRITEIN, 'uwi', BallotMarks.OVERVOTE},
            'unique_candidates': {'A', 'Tuwi', BallotMarks.WRITEIN, 'uwi'}
        }
    }),
    ({
        'input': {
            'marks': ['A', BallotMarks.SKIPPED, BallotMarks.SKIPPED, 'Tuwi', 'uwi', BallotMarks.OVERVOTE],
            'rules': BallotMarks.new_rule_set(exhaust_on_repeated_skipped_marks=True)
        },
        'expected': {
            'marks': ['A'],
            'unique_marks': {'A'},
            'unique_candidates': {'A'}
        }
    }),
    ({
        'input': {
            'marks': ['uwi', 'A', BallotMarks.SKIPPED, BallotMarks.SKIPPED, 'Tuwi', BallotMarks.OVERVOTE],
            'rules': BallotMarks.new_rule_set(exclude_duplicate_candidate_marks=True,
                                              exclude_overvote_marks=True,
                                              exclude_skipped_marks=True,
                                              exclude_writein_marks=True,
                                              combine_writein_marks=True,
                                              treat_combined_writeins_as_exhaustable_duplicates=True,
                                              exhaust_on_duplicate_candidate_marks=True,
                                              exhaust_on_overvote_marks=True,
                                              exhaust_on_repeated_skipped_marks=True)
        },
        'expected': {
            'marks': ['A'],
            'unique_marks': {'A'},
            'unique_candidates': {'A'}
        }
    })
]


@pytest.mark.parametrize("param_dict", param_dicts)
def test_apply_rules(param_dict):

    b = BallotMarks(param_dict['input']['marks'])
    b.apply_rules(**param_dict['input']['rules'])

    assert b.marks == param_dict['expected']['marks']
    assert b.unique_marks == param_dict['expected']['unique_marks']
    assert b.unique_candidates == param_dict['expected']['unique_candidates']
