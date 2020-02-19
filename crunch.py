
from argparse import ArgumentParser
from pprint import pprint
import csv
import os

# cruncher imports
from scripts.contests import *
from scripts.tabulation import *
from scripts.precincts import *

import scripts.global_dict as global_dict
# initialize global func dict across all cruncher imports
# necessary for cache_helpers
global_dict.set_global_dict(globals())


def calc(ctx, functions):
    """
    Run each function in 'functions' on ctx
    """
    print(ctx['dop'])

    results = {}
    for f in functions:
        results[f.__name__] = f(ctx)

    return results


def main():

    p = ArgumentParser()
    p.add_argument('--precincts', action='store_true')
    run_precinct_funcs = p.parse_args()

    # build func list
    func_list = contest_func_list() + stats_func_list()
    if run_precinct_funcs:
        func_list += ethnicity_stats_func_list()

    # get the path of this file
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    stats_fname = 'results.csv'
    condorcet_path = 'condorcet'

    contest_manifest = load_manifest(dname)

    # with open('results.csv', 'w', newline='\n') as f:
    #
    #     w = csv.writer(f)
    #
    #     # write header row
    #     w.writerow([fun.__name__ for fun in func_list])
    #
    #     # write notes row
    #     w.writerow([' '.join((fun.__doc__ or '').split())
    #                 for fun in func_list])
    #
    #     # on all contests in manifest
    #     for k in sorted(contest_manifest, key=lambda x: x['date']):
    #
    #         # crunch STATS
    #         result = calc(k, func_list)
    #         w.writerow([result[fun.__name__] for fun in func_list])

    for k in sorted(contest_manifest, key=lambda x: x['date']):

        # write condorcet table
        print(k['dop'])
        ct = condorcet_table(k)

        ct.to_csv(condorcet_path + "/" + k["dop"] + ".csv", float_format="%.2f")

if __name__ == '__main__':
    main()

