from argparse import ArgumentParser
import scripts.cache_helpers as cache
from scripts.ballots import *
from scripts.contests import *
from scripts.definitions import verifyDir, project_root
import pandas as pd

def main():

    ###########################
    # project dir
    dname = project_root()
    os.chdir(dname)

    gbls = globals()
    cache.set_global_dict(gbls)

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

    ########################
    # cache outputs
    cache_dir = contest_set_path + '/cache'
    cache.set_cache_dir(cache_dir)

    # check results dir
    cvr_dir = contest_set_path + '/common_cvr'
    verifyDir(cvr_dir)
    set_cvr_dir(cvr_dir)

    ########################
    # load manifest
    contest_set = load_contest_set(contest_set_path)

    for contest in contest_set:

        print(contest['unique_id'])

        cands = candidates_merged_writeIns(contest)
        df = pd.DataFrame(columns=['candidates', 'final_round_count'])
        df['candidates'] = list(cands) + ['exhaust']

        df.to_csv(dname + '/reported_results/' + contest['unique_id'] + ".csv", index=False)

if __name__ == "__main__":
    main()
