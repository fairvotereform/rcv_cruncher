from scripts.definitions import project_root, verifyDir
from argparse import ArgumentParser
import os
from glob import glob

def run_comparison(contest_set_path):

    current_file_list = glob(contest_set_path + '/ballot_stats_debug/*')
    old_file_list = glob()

def main():

    ###########################
    # project dir
    dname = project_root()
    os.chdir(dname)

    ###########################
    # parse args
    p = ArgumentParser()
    p.add_argument('--contest_set', default='all_contests')

    args = p.parse_args()
    contest_set_name = args.contest_set

    ##########################
    # confirm contest set
    contest_set_path = dname + '/contest_sets/' + contest_set_name
    verifyDir(contest_set_path, make_if_missing=False, error_msg_tail='is not an existing folder in contest_sets')

    ##########################
    # confirm old cruncher set
    old_cruncher_

    run_comparisons(contest_set_path)

if __name__ == '__main__':
    main()