from rcv_cruncher import CastVoteRecord, rank_column_csv
import os

cvr_file = f'{os.path.dirname(__file__)}/../example_cvr/minneapolis2017/2017-mayor-cvr.csv'
# initialize the object with optional details about the election (state, date, office, ..)
# along with the parser function and parser function arguments. As described in the
# documentation the only argument for this parser is the path to the CVR file.
cvr = CastVoteRecord(
     jurisdiction='Minneapolis',
     state='MN',
     year='2017',
     office='Mayor',
     parser_func=rank_column_csv,
     parser_args={'cvr_path': cvr_file}
)

# an output directory
out_dir = f'{os.path.dirname(__file__)}/parse_convert/output/rank_format'

# rank column format
CastVoteRecord.write_cvr_table(cvr, out_dir, table_format='rank')

# the file written to out_dir will have an automatically
# generated name following the format {jurisdiction}_{year}_{office}.csv.

# an output directory
out_dir = f'{os.path.dirname(__file__)}/parse_convert/output/candidate_format'

# candidate column format
CastVoteRecord.write_cvr_table(cvr, out_dir, table_format='candidate')

# the file written to out_dir will have an automatically
# generated name following the format {jurisdiction}_{year}_{office}.csv.
