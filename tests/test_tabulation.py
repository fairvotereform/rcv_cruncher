
# import json
# import os

# import pandas as pd
# import pytest

# import rcv_cruncher.contests as contests
# import rcv_cruncher.misc_tabulation as misc_tabulation
# import rcv_cruncher.rcv_base as rcv_base
# import rcv_cruncher.write_out as write_out


# def read_test_config(test_config_path):

#     # if not present, skip
#     if not os.path.isfile(test_config_path):
#         return {}

#     with open(test_config_path) as test_config_file:
#         test_config = json.load(test_config_file)

#     return test_config


# def test_tabulation(test_root_path, ballot_path):

#     # check for skips
#     # load test config
#     test_config_path = os.path.normpath(f'{ballot_path}/input/test_config.json')

#     # check for config option
#     if not read_test_config(test_config_path).get('test_tabulation', False):
#         pytest.skip(f'"test_tabulation" not set to "true" in test_config.json at {test_config_path}')

#     # proceed with test
#     contest_set_path = os.path.normpath(f'{ballot_path}/input')
#     computed_output_path = os.path.normpath(f'{ballot_path}/computed')

#     if not os.path.isdir(computed_output_path):
#         os.mkdir(computed_output_path)

#     # generate computed results
#     contest_set, _ = contests.read_contest_set(contest_set_path, override_cvr_root_dir=test_root_path)
#     rcv_obj = rcv_base.RCV.run_rcv(contest_set[0])
#     computed_rbrs = misc_tabulation.round_by_round(rcv_obj)

#     write_out.write_converted_cvr_annotated(rcv_obj, computed_output_path)

#     # compare to expected
#     for iTab, computed_rbr in enumerate(computed_rbrs, start=1):

#         # filter count columns
#         keep_cols = ['candidate'] + [col for col in computed_rbr.columns if 'count' in col]
#         computed_rbr_simple = computed_rbr.loc[:, keep_cols]

#         # write out computed for easier comparison when test fails
#         computed_rbr.to_csv(f'{computed_output_path}/round_by_round_tab{iTab}_complete.csv', index=False)
#         computed_rbr_simple.to_csv(f'{computed_output_path}/round_by_round_tab{iTab}_simplified.csv', index=False)

#         # also write out ballot allocation to help debug tests

#         # read expected tabulation
#         expected_tabulation_path = os.path.normpath(f'{ballot_path}/expected/tabulation{iTab}.csv')
#         if not os.path.isfile(expected_tabulation_path):
#             raise FileNotFoundError('testing error - contest requires multiple tabulations,'
#                                     f' but expected tabulation file {expected_tabulation_path} is not found.')
#         expected_rbr = pd.read_csv(expected_tabulation_path)

#         # tables are weird to compare
#         # convert tables to sets to check for equality
#         computed_compare = set(tuple(i) for i in computed_rbr_simple.values.tolist())
#         expected_compare = set(tuple(i) for i in expected_rbr.values.tolist())

#         assert computed_compare == expected_compare
