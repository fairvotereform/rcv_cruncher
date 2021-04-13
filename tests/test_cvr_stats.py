
# import pytest
# import pandas as pd

# import rcv_cruncher.cvr as cvr

# params = [
#     (
#         {
#             'ranks': [['A', 'B', cvr.BallotMarks.SKIPPEDRANK]],
#             'weight': [1]
#         },
#         pd.DataFrame({
#             'rank_limit': [3],
#             'first_round_overvote': [0],
#             'ranked_single': [0],
#             'ranked_multiple': [1],
#             'ranked_3_or_more': [0],
#             'total_fully_ranked': [1],
#             'includes_duplicate_ranking': [0],
#             'includes_skipped_ranking': [0],
#             'includes_overvote_ranking': [0],
#             'total_ballots': [1],
#             'total_irregular': [0],
#             'total_undervote': [0],
#             'mean_rankings_used': [2],
#             'median_rankings_used': [2]
#         })
#     ),
#     (
#         {
#             'ranks': [
#                 ['A', 'B', cvr.BallotMarks.SKIPPEDRANK],
#                 [cvr.BallotMarks.SKIPPEDRANK, cvr.BallotMarks.OVERVOTE, 'C']
#                 ],
#             'weight': [1, 1]
#         },
#         pd.DataFrame({
#             'rank_limit': [3],
#             'first_round_overvote': [1],
#             'ranked_single': [1],
#             'ranked_multiple': [1],
#             'ranked_3_or_more': [0],
#             'total_fully_ranked': [0],
#             'includes_duplicate_ranking': [0],
#             'includes_skipped_ranking': [1],
#             'includes_overvote_ranking': [1],
#             'total_ballots': [2],
#             'total_irregular': [1],
#             'total_undervote': [0],
#             'mean_rankings_used': [1.5],
#             'median_rankings_used': [1.5]
#         })
#     ),
#     (
#         {
#             'ranks': [
#                 ['A', 'B', 'B'],
#                 ['A', 'B', 'C'],
#                 [cvr.BallotMarks.SKIPPEDRANK, cvr.BallotMarks.SKIPPEDRANK, cvr.BallotMarks.SKIPPEDRANK]
#                 ],
#             'weight': [1, 1, 1]
#         },
#         pd.DataFrame({
#             'rank_limit': [3],
#             'first_round_overvote': [0],
#             'ranked_single': [0],
#             'ranked_multiple': [2],
#             'ranked_3_or_more': [2],
#             'total_fully_ranked': [1],
#             'includes_duplicate_ranking': [1],
#             'includes_skipped_ranking': [0],
#             'includes_overvote_ranking': [0],
#             'total_ballots': [3],
#             'total_irregular': [1],
#             'total_undervote': [1],
#             'mean_rankings_used': [3],
#             'median_rankings_used': [3]
#         })
#     )
# ]


# @pytest.mark.parametrize("cvr_input, stats_expected", params)
# def test_cvr(cvr_input, stats_expected):

#     cast_vote_record = cvr.CastVoteRecord(parsed_cvr=cvr_input,
#                                           jurisdiction="x",
#                                           state="x",
#                                           year="x",
#                                           date="x",
#                                           office="x")

#     computed_stats = cast_vote_record.cvr_stats()

#     for stat in stats_expected.columns:
#         assert stats_expected[stat].item() == computed_stats[stat].item()
