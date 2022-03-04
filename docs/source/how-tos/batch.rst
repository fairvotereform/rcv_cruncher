Analyzing CVRs in a batch
=========================

In the case where you have a set of elections, you can analyze them as a batch. Doing so requires organizing your contest information into a couple of files:

* ``contest_set.csv``: A **csv file** listing the elections, their parsers, tabulation methods, rules, and CVR file path locations.
* ``run_config.json``: A **json file** listing which output statistics and tables to produce.

Both files are explained further below. With both files in the same directory, the batch of elections can be analyzed using the function :meth:`batch.analyze_election_set`. Examples of both files can be downloaded `here <https://github.com/fairvotereform/rcv_cruncher/tree/master/src/rcv_cruncher/example/contest_sets/example>`_.

Contest Set File
^^^^^^^^^^^^^^^^^^

The contest set csv file should contain the following columns:

* ``state``: name of jurisdiction state
* ``jurisdiction``: name of jurisdiction, required
* ``year``: year
* ``date``: date in mm/dd/yyyy format, required
* ``office``: office being elected, required
* ``notes``: arbitrary notes
* ``exhaust_on_overvote_marks``: TRUE or FALSE, default is FALSE
* ``exhaust_on_N_repeated_skipped_marks``: Number of repeated skipped marks after which the ballot is exhausted, default is 0 (no amount of repeated skipped marks exhaust a ballot)
* ``exhaust_on_duplicate_candidate_marks``: TRUE or FALSE, default is FALSE
* ``exclude_writein_marks``: TRUE or FALSE, default is FALSE. Write-in ballot markings are ignored.
* ``combine_writein_marks``: TRUE or FALSE, default is FALSE. Any candidates named 'UWI' or that contain the string 'write' in their name are combined into single write-in candidate.
* ``treat_combined_writeins_as_exhaustable_duplicates``: TRUE or FALSE, default is FALSE. If write-ins are combined, decide whether or not the newly combined writeins count as duplicate rankings for the purpose of ballot exhaustion.
* ``multi_winner_rounds``: TRUE or FALSE, default is TRUE
* ``n_winners``: an integer, defaults to 1. Only applies to RCV variants requiring a set number of winners (multi winner STV and Sequential IRV).
* ``rcv_type``: name of RCV variant class
* ``bottoms_up_threshold``: number between 0 and 1. Only applies to bottoms up RCV variant.
* ``split_fields``: comma-separated list of column names on which to calculate split statistics
* ``parser_func``: name of parser function to use for CVR file
* ``cvr_path``: path to CVR file or CVR directory, relative to value provided in cvr_path_root field in run config.
* ``extra_parser_args``: semicolon-separated list of key-value pairs corresponding to additional arguments required by parser function. Each key-value pair should be separated by '=' sign.
* ``ignore_contest``: TRUE of FALSE, default is FALSE. If TRUE, skip election when running the batch.


Run Config
^^^^^^^^^^

The run config file can include the following fields:

* ``cvr_path_root``: A path to a common parent folder for all CVR files included in the election set


* ``convert_cvr_rank_format``: true or false. If true, each CVR is converted into a rank column format csv file. Uses :meth:`cvr.base.CastVoteRecord.write_cvr_table`. Defaults to false.


* ``convert_cvr_candidate_format``: true or false. If true, each CVR is converted into a candidate column format csv file. Uses :meth:`cvr.base.CastVoteRecord.write_cvr_table`. Defaults to false.


* ``per_rcv_type_stats:``: true or false. If true, statistics calculated using :meth:`rcv.base.RCV.calc_stats` are collected for all elections in the set and written out together. One file is produced per RCV variant included in the election set. Defaults to false.


* ``per_rcv_group_stats``: true or false. If true, statistics calculated using :meth:`rcv.base.RCV.calc_stats` are collected for all elections in the set and written out together. All single winner election statistics are combined into one file, multi winner election statistics in another. Defaults to false.


* ``round_by_round_table``: true or false. If true, a round by round table is produced for every election. Uses :meth:`rcv.base.RCV.write_round_by_round_table`. Defaults to false.


* ``round_by_round_json``: true or false. If true, a round by round json is produced for every election. Uses :meth:`rcv.base.RCV.write_round_by_round_json`. Defaults to false.


* ``first_choice_to_finalist``: true or false. If true, first to finalist tables are produced for every election. Uses :meth:`rcv.base.RCV.write_first_choice_to_finalist_table`. Defaults to false.


* ``condorcet``: true or false. If true, condorcet tables are produced for every election. Uses :meth:`cvr.base.CastVoteRecord.write_condorcet_tables`. Defaults to false.


* ``first_second_choices``: true or false. If true, first and second choices tables are produced for every election. Uses :meth:`cvr.base.CastVoteRecord.write_first_second_tables`. Defaults to false.


* ``cumulative_rankings``: true or false. If true, cumulative ranking tables are produced for every election. Uses :meth:`cvr.base.CastVoteRecord.write_cumulative_ranking_tables`. Defaults to false.


* ``rank_usage``: true or false. If true, rank usage tables are produced for every election. Uses :meth:`cvr.base.CastVoteRecord.write_rank_usage_table`. Defaults to false.


* ``crossover_support``: true or false. If true, crossover support tables are produced for every election. Uses :meth:`cvr.base.CastVoteRecord.write_crossover_tables`. Defaults to false.

* ``annotated_cvr_rank_format``: true or false. If true, an annotated cvr is created for each election containing many internal tracking variables for each ballot. Useful for debugging. Uses :meth:`cvr.base.CastVoteRecord.write_annotated_cvr_table`. Defaults to false.

* ``winner_final_pile_rank_distribution_table``: true or false. If true, an aggregate csv file is created containing the rank distribution of the final ballot pile for the winner of each single winner election. The rank distribution is measured twice, once using the ranks as the voters marked them and a second time using the 'effective' rankings of each ballot after the contest rules are applied. Uses :meth:`rcv.base.RCV.calc_winner_final_pile_rank_distribution_table`. Defaults to false.

* ``split_stats``: true or false. If true, split statistics are produced based on "split_fields" values.
