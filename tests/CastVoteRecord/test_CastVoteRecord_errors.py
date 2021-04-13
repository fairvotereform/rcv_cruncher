
import pytest

from rcv_cruncher.cvr.base import CastVoteRecord

# public methods, no custom errors reachable
# add_rule_set
# get_cvr_dict
# get_candidates
# get_cvr_stats
# get_cvr_split_stats

params = [
    (ValueError, None),
    (RuntimeError, {'ranks': []}),
    (RuntimeError, {'RANKS': [['A', 'B', 'C']]}),
    (RuntimeError, {'ranks': [['A'], ['A', 'B']]}),
    (RuntimeError, {'ranks': [['A', 'B'], ['A', 'B']], 'weight': [1, 1, 1]})
]


@pytest.mark.parametrize("error_type, inputs", params)
def test_constructor_errors(error_type, inputs):

    with pytest.raises(error_type):
        CastVoteRecord(parsed_cvr=inputs)


def test_get_cvr_table_errors():

    cvr = CastVoteRecord(parsed_cvr={
        'ranks': [["A", "B", "C"]]
    })

    with pytest.raises(RuntimeError):
        cvr.get_cvr_table(table_format=None)
