
import glob
import os


def read_test_config(test_config_path):

    test_config = {}
    with open(test_config_path) as test_config_file:
        for line_num, l in enumerate(test_config_file, start=1):

            l_splits = l.strip('\n').split("=")
            l_splits = [s.strip() for s in l_splits]

            if len(l_splits) < 2:
                continue

            input_option = l_splits[0]
            input_value = l_splits[1]

            if input_value.title() != "True" and input_value.title() != "False":
                raise RuntimeError(f'invalid value ({input_value}) provided in {test_config_path}'
                                   ' on line {line_num} for option "{l_splits[0]}". Must be "true" or "false".')
            input_value = eval(input_value.title())

            test_config.update({input_option: input_value})

    return test_config


def pytest_generate_tests(metafunc):
    if "ballot_path" in metafunc.fixturenames:

        test_contest_set = glob.glob(f'{metafunc.config.rootpath}/tests/contest_sets/tabulation_test/**/input', recursive=True)
        test_contest_set_dirs = [os.path.dirname(test_path) for test_path in test_contest_set]

        metafunc.parametrize("ballot_path", test_contest_set_dirs)
