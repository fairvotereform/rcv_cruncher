.. _statistics_list:

Statistics
==========

:class:`cvr.base.CastVoteRecord` objects and RCV variant objects all have a `get_stats()` function which returns a series of statistics that are computed for each election by default. Those stastistics are described below.

CastVoteRecord stastistics
--------------------------

Function
^^^^^^^^

.. autofunction:: cvr.base.CastVoteRecord_stats.get_stats
   :noindex:

Statistics
^^^^^^^^^^

:code:`n_candidates` - number of candidates excluding WRITEIN marks

:code:`rank_limit` - number of rankings allowed on the CVR.

:code:`restrictive_rank_limit` - True if number of candidates - number of ranks is greater than 1.

**(All stats below are also able to be calcualted by group (e.g. by precinct))**

:code:`first_round_overvote` - number of ballots in which the first non-skipped mark is an overvote.

:code:`ranked_single` - number of ballot which only contained 1 valid rankings.

:code:`ranked_multiple` - number of ballot which only contained more than 1 valid rankings.

:code:`ranked_3_or_more` - number of ballot which only contained more than 2 valid rankings.

:code:`total_fully_ranked` - number of ballots that have EITHER validly used all rankings on the ballot OR validly ranked every non-writein candidate.

:code:`includes_overvote_ranking` - number of ballots with an overvote ranking.

:code:`includes_duplicate_ranking` - number of ballots with a duplicate ranking.

:code:`includes_skipped_ranking` - number of ballots with a skipped ranking (that is then followed by at least 1 non-skipped ranking).

:code:`total_irregular` - total number of ballots with EITHER a duplicate ranking OR skipped ranking OR overvote.

:code:`total_ballots` - total number of ballots

:code:`total_undervote` - total number of ballots that contain all skipped rankings.

:code:`mean_rankings_used` - mean number of non-undervote rankings used.


RCV stastistics
---------------

Function
^^^^^^^^

.. autofunction:: rcv.base.RCV.get_stats
   :noindex:

Statistics
^^^^^^^^^^

:code:`number_of_winners` - number of winners in the contest.

:code:`number_of_rounds` - number of rounds in the tabulation.

:code:`winner` - tabulation winners.

:code:`first_round_winner_vote` - If more than 1 winner in tabulation, then None. Else, the vote total for the tabulation winner in the first round.

:code:`first_round_winner_percent` - If more than 1 winner in tabulation, then None. Else, the vote percent for the tabulation winner in the first round.

:code:`first_round_winner_place` - If more than 1 winner in tabulation, then None. Else, the place the tabulation winner finished in the the first round.

:code:`final_round_winner_vote` - If more than 1 winner in tabulation, then None. Else, the vote total for the tabulation winner in the final round.

:code:`final_round_winner_percent` - If more than 1 winner in tabulation, then None. Else, the vote percent for the tabulation winner in the final round.

:code:`final_round_winner_votes_over_first_round_active` - If more than 1 winner in tabulation, then None. Else, the vote total for the tabulation winner in the final round divided by the number of active ballots in the first round.

:code:`condorcet` - If more than 1 winner in tabulation, then None. Else, True if the winner is the condorcet winner, else False.

:code:`come_from_behind` - If more than 1 winner in tabulation, then None. Else, True if the winner was not in first place in the first round, else False.

:code:`ranked_winner` - If more than 1 winner in tabulation, then None. Else, the number of ballots that ranked the winner.

:code:`win_threshold` - If less than 2 winner in tabulation, then None. Else, the static threshold needed to win.

:code:`ranked_winner` - If more than 1 winner in tabulation, then None. Else, the number of ballots that ranked the winner.

:code:`winners_consensus_value` - The number of ballots that rank any winner in their top 3 (after rules applied).

:code:`first_round_active_votes` - The number of votes active in the first round.

:code:`final_round_active_votes` - The number of votes active in the final round.

**(All stats below are also able to calcualted by group (e.g. by precinct))**

:code:`total_pretally_exhausted` - The number of ballots that were not undervotes, yet were not active in the first round.

:code:`total_posttally_exhausted` - The number of ballots that exhausted after the first round.

:code:`total_posttally_exhausted_by_overvote` - The number of ballots that exhausted due to an overvote after the first round.

:code:`total_posttally_exhausted_by_skipped_rankings` - The number of ballots that exhausted due to repeated skipped rankings after the first round.

:code:`total_posttally_exhausted_by_duplicate_rankings` - The number of ballots that exhausted due to duplicate candidate rankings after the first round.

:code:`total_posttally_exhausted_by_rank_limit` - The number of ballots that exhausted after the first round. Only applied to contest with a restrictive rank limit. The count towards this category ballots must either use all ranks OR at least use the last ranking.

:code:`total_posttally_exhausted_by_rank_limit_fully_ranked` - Subset of total_posttally_exhausted_by_rank_limit which ranked all candidates or used all rankings validly.

:code:`total_posttally_exhausted_by_rank_limit_partially_ranked` - Subset of total_posttally_exhausted_by_rank_limit which used the final ranking on a rank restricted ballot.

:code:`total_posttally_exhausted_by_abstention` - The number of ballots that exhausted after the first round which do not fall into the categories above.
