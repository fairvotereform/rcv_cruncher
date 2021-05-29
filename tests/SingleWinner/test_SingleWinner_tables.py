
import pytest

import pandas as pd

from rcv_cruncher.marks import BallotMarks
from rcv_cruncher.rcv.variants import SingleWinner


params = [
    ({
        'input': {
            'jurisdiction': 'testville',
            'state': 'teststate',
            'date': '01/05/2021',
            'year': '2021',
            'office': 'chief tester',
            'parsed_cvr': {
                'ranks': [
                    ['A', 'B', 'C', 'D'],
                    ['A', BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.WRITEIN],
                    ['write-in', 'A', 'C', BallotMarks.OVERVOTE],
                    ['write-in', 'B', 'B', BallotMarks.OVERVOTE],
                    ['C', 'A', 'B', 'B']
                ]
            }
        },
        'expected': {
            'table': pd.DataFrame({
                'jurisdiction': ['testville'],
                'state': ['teststate'],
                'date': ['01/05/2021'],
                'year': ['2021'],
                'office': ['chief tester'],
                'unique_id': ['testville_01052021_chieftester'],
                'winner': ['A'],
                'rank_limit': [4],
                'n_candidates': [4],
                'n_rounds': [2],
                'choice1': [66.67],
                'choice2': [33.33],
                'choice3': [0],
                'choice4': [0]
            })
        }
    }),
    ({
        'input': {
            'jurisdiction': 'testville',
            'state': 'teststate',
            'date': '01/05/2021',
            'year': '2021',
            'office': 'chief tester',
            'parsed_cvr': {
                'ranks': [
                    ['A', 'B', 'C', 'D'],
                    ['A', BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.WRITEIN],
                    ['write-in', 'A', 'C', BallotMarks.OVERVOTE],
                    ['write-in', 'B', 'B', BallotMarks.OVERVOTE],
                    ['C', 'A', 'B', 'B'],
                    [BallotMarks.OVERVOTE, 'A', 'B', 'C']
                ]
            },
            'exhaust_on_overvote_marks': True
        },
        'expected': {
            'table': pd.DataFrame({
                'jurisdiction': ['testville'],
                'state': ['teststate'],
                'date': ['01/05/2021'],
                'year': ['2021'],
                'office': ['chief tester'],
                'unique_id': ['testville_01052021_chieftester'],
                'winner': ['A'],
                'rank_limit': [4],
                'n_candidates': [4],
                'n_rounds': [2],
                'choice1': [66.67],
                'choice2': [33.33],
                'choice3': [0],
                'choice4': [0]
            })
        }
    }),
    ({
        'input': {
            'jurisdiction': 'testville',
            'state': 'teststate',
            'date': '01/05/2021',
            'year': '2021',
            'office': 'chief tester',
            'parsed_cvr': {
                'ranks': [
                    ['A', 'B', 'C', 'D'],
                    ['A', BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.WRITEIN],
                    ['write-in', 'A', 'C', BallotMarks.OVERVOTE],
                    ['write-in', 'B', 'B', BallotMarks.OVERVOTE],
                    ['C', 'B', 'A', 'B'],
                    [BallotMarks.OVERVOTE, 'A', 'B', 'C']
                ]
            },
            'exhaust_on_overvote_marks': True
        },
        'expected': {
            'table': pd.DataFrame({
                'jurisdiction': ['testville'],
                'state': ['teststate'],
                'date': ['01/05/2021'],
                'year': ['2021'],
                'office': ['chief tester'],
                'unique_id': ['testville_01052021_chieftester'],
                'winner': ['A'],
                'rank_limit': [4],
                'n_candidates': [4],
                'n_rounds': [2],
                'choice1': [66.67],
                'choice2': [0],
                'choice3': [33.33],
                'choice4': [0]
            })
        }
    }),
    ({
        'input': {
            'jurisdiction': 'testville',
            'state': 'teststate',
            'date': '01/05/2021',
            'year': '2021',
            'office': 'chief tester',
            'parsed_cvr': {
                'ranks': [
                    ['A', 'B', 'C', 'D'],
                    ['A', BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.WRITEIN],
                    ['write-in', 'A', 'C', BallotMarks.OVERVOTE],
                    ['write-in', 'B', 'B', BallotMarks.OVERVOTE],
                    ['C', 'B', 'D', 'A'],
                    [BallotMarks.OVERVOTE, 'A', 'B', 'C']
                ]
            },
            'exhaust_on_overvote_marks': True
        },
        'expected': {
            'table': pd.DataFrame({
                'jurisdiction': ['testville'],
                'state': ['teststate'],
                'date': ['01/05/2021'],
                'year': ['2021'],
                'office': ['chief tester'],
                'unique_id': ['testville_01052021_chieftester'],
                'winner': ['A'],
                'rank_limit': [4],
                'n_candidates': [4],
                'n_rounds': [2],
                'choice1': [66.67],
                'choice2': [0],
                'choice3': [0],
                'choice4': [33.33]
            })
        }
    }),
    ({
        'input': {
            'jurisdiction': 'testville',
            'state': 'teststate',
            'date': '01/05/2021',
            'year': '2021',
            'office': 'chief tester',
            'parsed_cvr': {
                'ranks': [
                    ['A', 'B', 'C', 'D'],
                    ['A', BallotMarks.SKIPPED, BallotMarks.OVERVOTE, BallotMarks.WRITEIN],
                    ['write-in', 'A', 'C', BallotMarks.OVERVOTE],
                    ['write-in', 'B', 'B', BallotMarks.OVERVOTE],
                    ['C', 'A', 'B', 'B'],
                    ['C', 'A', 'B', 'B'],
                    ['C', 'A', 'B', 'B'],
                    ['D', 'B', 'E', 'A'],
                    [BallotMarks.OVERVOTE, 'A', 'B', 'C']
                ]
            },
            'exhaust_on_overvote_marks': True
        },
        'expected': {
            'table': pd.DataFrame({
                'jurisdiction': ['testville'],
                'state': ['teststate'],
                'date': ['01/05/2021'],
                'year': ['2021'],
                'office': ['chief tester'],
                'unique_id': ['testville_01052021_chieftester'],
                'winner': ['A'],
                'rank_limit': [4],
                'n_candidates': [5],
                'n_rounds': [3],
                'choice1': [50],
                'choice2': [25],
                'choice3': [0],
                'choice4': [25]
            })
        }
    })
]


@pytest.mark.parametrize("param", params)
def test_winner_choice_position_distribution_table(param):
    rcv = SingleWinner(**param['input'])

    table_df = rcv.winner_choice_position_distribution_table()

    for col in table_df.columns:
        assert table_df[col].item() == param['expected']['table'][col].item()
