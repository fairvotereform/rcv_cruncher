When the 'cvr_ballot_allocation' option is marked as TRUE in the output_config.csv file, the files described below are written out to the `contest_sets/[your_contest_set_dir]/results/cvr_ballot_allocation` directory.

These output files contain the per-ballot ranking information as well as columns that indicate how the ballot was allocated in the final round (whether for a candidate, exhausted, or undervote).

These new columns are:
*   ballot_split_ID - While some CVR files will give each ballot a unique ID, not all do. The ID contained in this column is unique to each individual input ballot. For non-fractional transfer elections, this column will just contain a unique value on each row. However, for fractional transfer elections, ballot_split_IDs will be repeated across rows to indicate ballot fractions that come from the same input ballot.

*   final_allocation - This column indicates which candidate the ballot counted for in the final round. If the ballot did not count for any candidates (undervote, exhausted), it is marked as 'inactive'.

*   weight - ballot weight. If no ballot weights are specified in the input CVR file, they are all 1 by default. In the case of multi-winner elections with fractional ballot transfer, transferred ballot fractions are represented by duplicated rows with the weight column indicating each ballot fraction's vote contribution.

*   inactive_type - If a ballot counted for a candidate, this column contains 'NA'. Otherwise, this column describes how the ballot became inactive in more detail. The possible values in this column are:
  * undervote
  * pretally_exhaust
  * posttally_exhausted_by_rank_limit
  * posttally_exhausted_by_abstention
  * posttally_exhausted_by_overvote
  * posttally_exhausted_by_repeated_skipped_ranking

More information on the inactive types can be found in other READMEs (fill this in once I write this info in a readme).

The other columns that will appear in this file are repeated from the `common_cvr` directory. These include ranking columns (formatted 'rank1', 'rank2', etc) as well any other fields the parser pulled from the input CVR file.

Last edited on 12/4/2020
