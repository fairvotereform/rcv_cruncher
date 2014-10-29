
import argparse
from argparse import ArgumentParser


DESCRIPTION = """\
Analyze RCV contests.

"""

def create_argparser(prog="crunch"):
    """
    Return an ArgumentParser object.

    """
    parser = ArgumentParser(prog=prog, description=DESCRIPTION)
    parser.add_argument('config_path', metavar='CONFIG_PATH',
        help=("path to a cruncher configuration file. Supported file "
              "formats are JSON (*.json) and YAML (*.yaml or *.yml)."))
    parser.add_argument('data_dir', metavar='DATA_DIR')
    parser.add_argument('output_dir', metavar='OUTPUT_DIR')

    return parser
