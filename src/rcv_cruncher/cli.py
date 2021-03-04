"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mrcv_cruncher` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``rcv_cruncher.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``rcv_cruncher.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import argparse
import os

import rcv_cruncher.contests as contests


def main():

    # argument parse and valid
    p = argparse.ArgumentParser(description='Analyze RCV election data.'
                                'For information on input file preparation, check the documentation at ***docs link here ****')

    p.add_argument('contest_set_path', help="Path to directory containing contest_set.csv and run_config.json.")
    p.add_argument('--fresh', action='store_true',
                   help='Delete existing results/ and converted_cvr/ directories located in contest set directory')
    # p.add_argument('--output_path', help='By default all output will be written to contest_set_path,'
    #                                      'provide this argument to specify an alternative.')

    args = p.parse_args()
    contest_set_path = args.contest_set_path
    fresh = args.fresh
    output_path = contest_set_path  # args.output_path if args.output_path else args.contest_set_path

    if not os.path.isabs(contest_set_path):
        contest_set_path = f'{os.getcwd()}/{contest_set_path}'

    if not os.path.isdir(contest_set_path):
        raise RuntimeError(f'invalid path [contest_set_path]: {contest_set_path}')

    # if not os.path.isabs(output_path):
    #     output_path = f'{os.getcwd()}/{output_path}'

    # if not os.path.isdir(output_path):
    #     raise RuntimeError(f'invalid path [output_path]: {output_path}')

    # read in contest set info
    contest_set, run_config = contests.read_contest_set(contest_set_path)

    # analyze contests
    contests.crunch_contest_set(contest_set, run_config, output_path, fresh_output=fresh)

    return(0)
