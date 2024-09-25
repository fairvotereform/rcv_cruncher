from rcv_cruncher import SingleWinner, STVFractionalBallot, rank_column_csv
import os

cvr_file = f'{os.path.dirname(__file__)}/../example_cvr/minneapolis2017/2017-mayor-cvr.csv'
out_dir = f'{os.path.dirname(__file__)}/tabulation'

# the constructor for the election class will run the tabulation
election = SingleWinner(
     jurisdiction='Minneapolis',
     state='MN',
     year='2017',
     office='Mayor',
     parser_func=rank_column_csv,
     parser_args={'cvr_path': cvr_file},
     exhaust_on_duplicate_candidate_marks=False,
     exhaust_on_overvote_marks=False,
     exhaust_on_N_repeated_skipped_marks=2
 )

# save a csv table of the results to out_dir
SingleWinner.write_round_by_round_table(election, out_dir)

# or the json for RCVIS
SingleWinner.write_round_by_round_json(election, out_dir)


cvr_file = f'{os.path.dirname(__file__)}/../example_cvr/minneapolis2017/2017-boe-cvr.csv'

# the constructor for the election class will run the tabulation
election = STVFractionalBallot(
     jurisdiction='Minneapolis',
     state='MN',
     year='2017',
     office='Board of Estimates and Taxation',
     parser_func=rank_column_csv,
     parser_args={'cvr_path': cvr_file},
     exhaust_on_duplicate_candidate_marks=False,
     exhaust_on_overvote_marks=False,
     exhaust_on_N_repeated_skipped_marks=2,
     n_winners=2,
     truncate_to=4
 )

# save a csv table of the results to out_dir
STVFractionalBallot.write_round_by_round_table(election, out_dir)

# or the json for RCVIS
STVFractionalBallot.write_round_by_round_json(election, out_dir)
