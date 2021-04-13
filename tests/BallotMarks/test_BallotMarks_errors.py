
import pytest

from rcv_cruncher.marks import BallotMarks

params = [
    (TypeError, 1),
    (TypeError, 1.5),
    (TypeError, 'a'),
    (TypeError, True)
]


@pytest.mark.parametrize("error_type, input", params)
def test_constructor_errors(error_type, input):

    with pytest.raises(error_type):
        BallotMarks(input)


@pytest.mark.parametrize("error_type, input", params)
def test_remove_duplicate_marks_errors(error_type, input):

    with pytest.raises(error_type):
        BallotMarks.remove_duplicate_candidate_marks(input)


@pytest.mark.parametrize("error_type, input", params)
def test_combine_writein_marks_errors(error_type, input):

    with pytest.raises(error_type):
        BallotMarks.combine_writein_marks(input)


params = [
    (TypeError, 1, 1),
    (TypeError, 1, 1.5),
    (TypeError, 1, 'a'),
    (TypeError, 1, False),
    (TypeError, 1.5, 1),
    (TypeError, 1.5, 1.5),
    (TypeError, 1.5, 'a'),
    (TypeError, 1.5, True),
    (TypeError, 'a', 1),
    (TypeError, 'a', 1.5),
    (TypeError, 'a', 'a'),
    (TypeError, 'a', True),
    (TypeError, True, 1),
    (TypeError, True, 1.5),
    (TypeError, True, 'a'),
    (TypeError, True, True)
]


@pytest.mark.parametrize("error_type, input1, input2", params)
def test_remove_mark_errors(error_type, input1, input2):

    with pytest.raises(error_type):
        BallotMarks.remove_mark(input1, input2)


def test_apply_rules_errors():

    with pytest.raises(RuntimeError):
        b = BallotMarks(['A', 'B', 'C'])
        b.apply_rules()
        b.apply_rules()
