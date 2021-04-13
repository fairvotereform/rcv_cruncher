
import glob
import os


# def pytest_generate_tests(metafunc):
#     if "ballot_path" in metafunc.fixturenames:

#         test_contest_set = glob.glob(f'{metafunc.config.rootpath}/tests/contest_sets/tabulation_test/**/input', recursive=True)
#         test_contest_set_dirs = [os.path.dirname(test_path) for test_path in test_contest_set]

#         metafunc.parametrize(["test_root_path", "ballot_path"], [(metafunc.config.rootpath, i) for i in test_contest_set_dirs])
