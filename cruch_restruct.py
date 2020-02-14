
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

    # if using and IDE with a debugger, fill this list with contests to break on
    # and set breakpoint below
    debug_list = ['2012 Mayor - Berkeley Nov 2012']

    # get the path of this file
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)

    STATS = contest_func_list() + stats_func_list() + ethnicity_stats_func_list()

    with open('results_restruct.csv', 'w', newline='\n') as f:

        w = csv.writer(f)

        # write header row
        w.writerow([fun.__name__ for fun in STATS])

        # write notes row
        w.writerow([' '.join((fun.__doc__ or '').split())
                    for fun in STATS])

        # crunch STATS on all contests in manifest
        for k in sorted(load_manifest(dname), key=lambda x: x['date']):

            # useful spot to put a breakpoint for debugging a specific contest
            if k['contest'] in debug_list:
                print('debugging')

            result = calc(k, STATS)
            w.writerow([result[fun.__name__] for fun in STATS])


if __name__ == '__main__':
    main()

