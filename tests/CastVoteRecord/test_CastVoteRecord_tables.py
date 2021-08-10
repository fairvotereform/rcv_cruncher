
import pytest
import pandas as pd

from rcv_cruncher.cvr.base import CastVoteRecord
from rcv_cruncher.marks import BallotMarks


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
                ],
                'weight': [2, 2, 3, 3, 3]
            }
        },
        'expected': {
            'tables': [
                pd.DataFrame({
                    'Number of Ballots (excluding undervotes and ballots with first round overvote)': [13, 4, 0, 3, 0, 6],
                    'Mean Valid Rankings Used (excluding duplicates)': [2.769, 3, 0, 3, 0, 2.5],
                }, index=['Any candidate', 'A', 'B', 'C', 'D', BallotMarks.WRITEIN], dtype=float)
            ]
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_rank_usage_table(param):
    rcv = CastVoteRecord(**param['input'])

    df = rcv.rank_usage_table()

    assert df.index.tolist() == param['expected']['tables'][0].index.tolist()
    assert df.fillna('NA').to_dict('records') == param['expected']['tables'][0].fillna('NA').to_dict('records')


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
                ],
                'weight': [2, 2, 3, 3, 3]
            }
        },
        'expected': {
            'tables': [
                pd.DataFrame({
                    'Number of Ballots': [4, 0, 3, 0, 6],
                    'A ranked in top 3': [4, 0, 3, 0, 3],
                    'B ranked in top 3': [2, 0, 3, 0, 3],
                    'C ranked in top 3': [2, 0, 3, 0, 3],
                    'D ranked in top 3': [0, 0, 0, 0, 0],
                    BallotMarks.WRITEIN + ' ranked in top 3': [2, 0, 0, 0, 6]
                }, index=['A', 'B', 'C', 'D', BallotMarks.WRITEIN], dtype=float),
                pd.DataFrame({
                    'Number of Ballots': [4, 0, 3, 0, 6],
                    'A ranked in top 3': [100, 0, 100, 0, 50],
                    'B ranked in top 3': [50, 0, 100, 0, 50],
                    'C ranked in top 3': [50, 0, 100, 0, 50],
                    'D ranked in top 3': [0, 0, 0, 0, 0],
                    BallotMarks.WRITEIN + ' ranked in top 3': [50, 0, 0, 0, 100]
                }, index=['A', 'B', 'C', 'D', BallotMarks.WRITEIN], dtype=float)
            ]
        }
    }),
]


@pytest.mark.parametrize("param", params)
def test_crossover_table(param):
    cvr = CastVoteRecord(**param['input'])

    count_df, percent_df = cvr.crossover_tables()

    assert count_df.index.tolist() == param['expected']['tables'][0].index.tolist()
    assert count_df.fillna('NA').to_dict('records') == param['expected']['tables'][0].fillna('NA').to_dict('records')

    assert percent_df.index.tolist() == param['expected']['tables'][1].index.tolist()
    assert percent_df.fillna('NA').to_dict('records') == param['expected']['tables'][1].fillna('NA').to_dict('records')
