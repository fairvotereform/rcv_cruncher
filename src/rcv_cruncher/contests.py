
import json
import os
import pathlib
import re
import shutil
import copy
import pkg_resources
import collections
import datetime
import csv

import pandas as pd
import tqdm

import rcv_cruncher.parsers as parsers
import rcv_cruncher.rcv_base as rcv_base
import rcv_cruncher.rcv_variants as rcv_variants
import rcv_cruncher.util as util
import rcv_cruncher.write_out as write_out
import rcv_cruncher.ballots as ballots

# read functions in parsers and rcv_variants
rcv_dict = rcv_variants.get_rcv_dict()
parser_dict = parsers.get_parser_dict()


def dummy(*args):
    pass


# typecast functions
def cast_str(s):
    """
    If string-in-string '"0006"', evaluate to '0006'
    If 'None', return None (since this string cannot be evaluated)
    else, return str() result
    """
    if (s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'"):
        return eval(s)
    elif s == 'None':
        return None
    else:
        return str(s)


def cast_int(s):
    if isinstance(s, int):
        return s
    return int(s)


def cast_bool(s):
    if isinstance(s, bool):
        return s
    return eval(s.title())


def cast_list(lst):
    if lst == "":
        return []
    return lst.strip('\n').split(",")


def cast_func(s):

    if s in rcv_dict and s in parser_dict:
        raise RuntimeError('(developer error) An rcv variant class and a parser function share the same name. Make them unique.')

    if s in rcv_dict:
        return rcv_dict[s]

    if s in parser_dict:
        return parser_dict[s]


# other helpers
# def dop(ctx):
#     return '_'.join([ctx['year'], ctx['place'], ctx['office']])

def unique_id(ctx):
    filled_date = "/".join([piece if len(piece) > 1 else "0" + piece for piece in ctx['date'].split("/")])
    pieces = [ctx['jurisdiction'], filled_date, ctx['office']]
    cleaned_pieces = [re.sub('[^0-9a-zA-Z_]+', '', x) for x in pieces]
    return "_".join(cleaned_pieces)


def read_contest_set(contest_set_path, override_cvr_root_dir=None):

    # assemble typecast funcs
    cast_dict = {'str': cast_str, 'int': cast_int,
                 'bool': cast_bool, 'func': cast_func, 'list': cast_list}

    # settings/defaults
    contest_set_settings_fpath = f'{os.path.dirname(__file__)}/contest_set_settings.json'
    if os.path.isfile(contest_set_settings_fpath) is False:
        raise RuntimeError(f'(developer error) not a valid file path: {contest_set_settings_fpath}')

    with open(contest_set_settings_fpath) as contest_set_settings_file:
        contest_set_settings = json.load(contest_set_settings_file)

    run_config_settings_fpath = f'{os.path.dirname(__file__)}/run_config_settings.json'
    if os.path.isfile(run_config_settings_fpath) is False:
        raise RuntimeError(f'(developer error) not a valid file path: {run_config_settings_fpath}')

    with open(run_config_settings_fpath) as run_config_settings_file:
        run_config_settings = json.load(run_config_settings_file)

    # read run_config.txt
    run_config_fpath = f'{contest_set_path}/run_config.txt'
    if os.path.isfile(run_config_fpath) is False:
        raise RuntimeError(f'not a valid file path: {run_config_fpath}')

    run_config = {}
    with open(run_config_fpath) as run_config_file:
        for line_num, l in enumerate(run_config_file, start=1):

            l_splits = l.strip('\n').split("=")
            l_splits = [s.strip() for s in l_splits]

            if len(l_splits) < 2:
                continue

            input_option = l_splits[0]
            input_value = l_splits[1]

            if input_option not in run_config_settings:
                continue

            if run_config_settings[input_option]['type'] == "bool":
                if input_value.title() != "True" and input_value.title() != "False":
                    raise RuntimeError(f'invalid value ({input_value}) provided in run_config.txt'
                                       f'on line {line_num} for option "{l_splits[0]}". Must be "true" or "false".')
                input_value = eval(input_value.title())

            run_config.update({input_option: input_value})

    # add in defaults for missing options
    for field in run_config_settings:
        if field not in run_config:
            run_config.update({field: run_config_settings[field]['default']})

    run_config['cvr_path_root'] = pathlib.Path(run_config['cvr_path_root'])

    # make sure cvr path is provided
    # if not run_config['cvr_path_root']:
    #     raise RuntimeError('No "cvr_path_root" provided in run_config.txt. This is required.')

    # read contest_set.csv
    contest_set_fpath = f'{contest_set_path}/contest_set.csv'
    if os.path.isfile(contest_set_fpath) is False:
        raise RuntimeError(f'not a valid file path: {contest_set_fpath}')

    contest_set_df = pd.read_csv(contest_set_fpath, dtype=object)

    # fill in na values with defaults and evaluate column, if indicated
    for col in contest_set_df:

        if col not in contest_set_settings:
            print(f'info -- "{col}" is an unrecognized column in contest_set.csv, it will be ignored.')
        else:
            contest_set_df[col] = contest_set_df[col].fillna(contest_set_settings[col]['default'])
            contest_set_df[col] = [cast_dict[contest_set_settings[col]['type']](i) for i in contest_set_df[col].tolist()]

    contest_set_df['contest_set_path'] = contest_set_path

    # convert df to listOdicts, one dict per row
    competitions = contest_set_df.to_dict('records')

    # add dop, uid, cvr_path_root
    for d in competitions:
        # d['contest_set_line_df'] = pd.DataFrame([[d[col].__name__ if callable(d[col]) else d[col] for col in cols_in_order]],
        #                                         columns=cols_in_order)

        if override_cvr_root_dir:
            d['cvr_path'] = pathlib.Path(override_cvr_root_dir) / d['cvr_path']
        else:
            d['cvr_path'] = run_config['cvr_path_root'] / d['cvr_path']

        if d['candidate_map']:
            d['candidate_map'] = run_config['cvr_path_root'] / d['candidate_map']

        d['uid'] = unique_id(d)
        d['split_id'] = ""
        d['split_field'] = ""
        d['split_value'] = ""

        # add in defaults if needed
        for setting in contest_set_settings:
            if setting not in d:
                d[setting] = contest_set_settings[setting]['default']

    # remove contest that should be ignored
    competitions = [comp for comp in competitions if not comp.get('ignore_contest', True)]

    # remove contests with invalid parser, print warning.
    no_parser = []
    for comp in competitions:
        if comp['parser'] == dummy:
            no_parser.append(comp)

    no_parser_uniqueID = [comp['uid'] for comp in no_parser]
    valid_competitions = [comp for comp in competitions if comp['uid'] not in no_parser_uniqueID]

    if no_parser:
        print(f'info -- {len(no_parser)} contests in contest_set.csv did not include a valid cvr parser field. They will be ignored.')

    # store file locations
    run_config['contest_set_file_path'] = contest_set_fpath
    run_config['run_config_file_path'] = run_config_fpath

    return valid_competitions, run_config


def write_aggregated_stats(results_dir,
                           output_config,
                           rcv_group_stats_df_dict,
                           rcv_variant_stats_df_dict,
                           candidate_details_dfs,
                           quiet=False):

    if not quiet:
        print("####################")
        print("Write stored results")

    if output_config.get('per_rcv_group_stats', False):

        if not quiet:
            print("write group stats ...")

        for group in rcv_group_stats_df_dict:
            if rcv_group_stats_df_dict[group]:
                df = pd.concat(rcv_group_stats_df_dict[group], axis=0, ignore_index=True, sort=False)
                df.to_csv(util.longname(results_dir / f'group_{group}.csv'), index=False)

    if output_config.get('per_rcv_group_stats_fvDBfmt', False):

        if not quiet:
            print("write group stats in fvDB order ...")

        for group in rcv_group_stats_df_dict:
            format_fpath = f"extra/fv_db_format/{group}_columns.csv"
            if rcv_group_stats_df_dict[group] and os.path.isfile(format_fpath):

                # read in column order
                fmt_df = pd.read_csv(format_fpath)
                fmt_order = fmt_df['cruncher_col'].tolist()

                df = pd.concat(rcv_group_stats_df_dict[group], axis=0, ignore_index=True, sort=False)
                df = df.reindex(fmt_order, axis=1)
                df.to_csv(util.longname(results_dir / f'group_{group}_fvDBfmt.csv'), index=False)

    if output_config.get('per_rcv_type_stats', False):

        if not quiet:
            print("Write tabulation stats ...")

        for variant in rcv_variant_stats_df_dict:
            if rcv_variant_stats_df_dict[variant]:
                df = pd.concat(rcv_variant_stats_df_dict[variant], axis=0, ignore_index=True, sort=False)
                df.to_csv(util.longname(results_dir / f'{variant}.csv'), index=False)

    if output_config.get('candidate_details', False) and candidate_details_dfs:

        if not quiet:
            print("Write candidate details ...")

        df = pd.concat(util.flatten_list(candidate_details_dfs), axis=0, ignore_index=True, sort=False)
        df.to_csv(util.longname(results_dir / 'candidate_details.csv'), index=False)


def split_contest(contest):

    split_contest_sets = []
    split_fields = contest.get('split_fields')

    if split_fields:

        all_ballots_dl = ballots.input_ballots(contest)
        all_ballots_ld = util.DL2LD(all_ballots_dl)

        all_fields = list(all_ballots_dl.keys())
        all_fields_lower_dict = {k.lower(): k for k in all_fields}

        # {split_field: {split_val: [ballot]}}
        split_sets = {all_fields_lower_dict[k]: collections.defaultdict(list)
                      for k in split_fields if k.lower() in all_fields_lower_dict}

        split_set_str = ",".join(list(split_sets.keys()))
        split_fields_str = ",".join(split_fields)

        for b in all_ballots_ld:
            for k in split_sets:
                split_sets[k][b[k]].append(b)

        n_split_contest = sum(len(split_sets[k].keys()) for k in split_sets)
        with tqdm.tqdm(total=n_split_contest, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}{postfix}', colour="#C297DB") as pbar:

            pbar.set_description(f'splitting: split on fields [{split_set_str}] out of input [{split_fields_str}]')

            for k in split_sets:
                ky_clean = str(k).replace(":", "").replace("/", "").replace("\\", "").replace(" ", "")

                for split_val in split_sets[k]:
                    val_clean = str(split_val).replace(":", "").replace("/", "").replace("\\", "").replace(" ", "")
                    split_id = ky_clean + "-" + val_clean

                    pbar.set_postfix_str(split_id)
                    pbar.update(1)

                    split_contest = copy.deepcopy(contest)
                    split_contest['cvr'] = util.LD2DL(split_sets[k][split_val])
                    split_contest['split_field'] = k
                    split_contest['split_value'] = split_val
                    split_contest['split_id'] = split_id

                    split_contest_sets.append(split_contest)

            pbar.set_postfix_str("completed")

        # all_fields = {k.lower(): k for k in all_ballots.keys()}

        # split_sets = {k: {} for k in split_fields}
        # for k in split_sets:
        #     if k.lower() in all_fields:
        #         split_sets[all_fields[ky]] = set(all_ballots[all_fields[ky]])

        # for ky in split_sets:
        #     ky_clean = ky.replace(":", "").replace("/", "").replace("\\", "").replace(" ", "")

        #     for split_val in split_sets[ky]:

        #         split_contest = copy.deepcopy(contest)
        #         val_clean = str(split_val)

        #         split_contest['cvr'] = {k: [x for i, x in enumerate(v) if all_ballots[ky][i] == split_val]
        #                                 for k, v in all_ballots.items()}

        #         val_replaced = val_clean.replace(":", "").replace("/", "").replace("\\", "").replace(" ", "")
        #         split_contest['split_id'] = ky_clean + "-" + val_replaced

        #         split_contest_sets.append(split_contest)

    return split_contest_sets


class CrunchSteps:

    def __init__(self, contest, output_config, converted_cvr_dir, results_dir, pbar_desc,
                 *, error_log_writers=None, skipped_steps=None):

        self.contest = contest
        self.output_config = output_config
        self.converted_cvr_dir = converted_cvr_dir
        self.results_dir = results_dir
        self.pbar_desc = pbar_desc
        self.skipped_steps = skipped_steps if isinstance(skipped_steps, list) else []
        self.error_log_writers = error_log_writers if isinstance(error_log_writers, list) else []

        self.state_data = {
            'n_errors': 0,
            'rcv_obj': None
        }

        self.steps = {}
        self.refresh_steps()

        for step_num, k in enumerate(self.steps, start=1):
            self.steps[k]['success'] = None
            self.steps[k]['order'] = step_num

    def refresh_steps(self):

        cache_keys = ['success', 'order']
        cache = collections.defaultdict(dict)
        for k1 in self.steps:
            for k2 in cache_keys:
                if k2 in self.steps[k1]:
                    cache[k1].update({k2: self.steps[k1][k2]})

        self.steps = collections.OrderedDict([
            ('convert_cvr', {
                'f': write_out.write_converted_cvr,
                'args': [self.contest, self.converted_cvr_dir],
                'condition': self.output_config.get('convert_cvr') and 'convert_cvr' not in self.skipped_steps,
                'fail_with': [],
                'depends_on': [],
                'return_key': None
            }),
            ('tabulate', {
                'f': rcv_base.RCV.run_rcv,
                'args': [self.contest],
                'condition': 'tabulate' not in self.skipped_steps,
                'depends_on': [],
                'fail_with': ['convert_cvr'],
                'return_key': 'rcv_obj'
            }),
            ('tabulation_stats', {
                'f': rcv_base.RCV.tabulation_stats_df,
                'args': [self.state_data['rcv_obj']],
                'condition': self.output_config.get('per_rcv_type_stats') and 'per_rcv_type_stats' not in self.skipped_steps,
                'depends_on': ['tabulate'],
                'fail_with': [],
                'return_key': 'tabulation_stats_df'
            }),
            ('rcv_variant', {
                'f': rcv_base.RCV.get_variant_name,
                'args': [self.state_data['rcv_obj']],
                'condition': 'rcv_variant' not in self.skipped_steps,
                'depends_on': ['tabulate'],
                'fail_with': [],
                'return_key': 'variant'
            }),
            ('contest_stats', {
                'f': rcv_base.RCV.contest_stats_df,
                'args': [self.state_data['rcv_obj']],
                'condition': self.output_config.get('per_rcv_group_stats') and 'per_rcv_group_stats' not in self.skipped_steps,
                'depends_on': ['tabulate'],
                'fail_with': [],
                'return_key': 'contest_stats_df'
            }),
            ('rcv_group', {
                'f': rcv_base.RCV.get_variant_group,
                'args': [self.state_data['rcv_obj']],
                'condition': 'rcv_group' not in self.skipped_steps,
                'depends_on': ['tabulate'],
                'fail_with': [],
                'return_key': 'variant_group'
            }),
            ('candidate_details', {
                'f': write_out.prepare_candidate_details,
                'args': [self.state_data['rcv_obj']],
                'condition': self.output_config.get('candidate_details') and 'candidate_details' not in self.skipped_steps,
                'depends_on': ['tabulate'],
                'fail_with': [],
                'return_key': 'candidate_details'
            }),
            ('round_by_round', {
                'f': write_out.write_rcv_rounds,
                'args': [self.state_data['rcv_obj'], self.results_dir],
                'condition': self.output_config.get('round_by_round') and 'round_by_round' not in self.skipped_steps,
                'depends_on': ['tabulate'],
                'fail_with': [],
                'return_key': None
            }),
            ('ballot_stats_debug', {
                'f': write_out.write_ballot_debug_info,
                'args': [self.state_data['rcv_obj'], self.results_dir],
                'condition': self.output_config.get('ballot_stats_debug') and 'ballot_stats_debug' not in self.skipped_steps,
                'depends_on': ['tabulate'],
                'fail_with': [],
                'return_key': None
            }),
            ('cvr_ballot_allocation', {
                'f': write_out.write_converted_cvr_annotated,
                'args': [self.state_data['rcv_obj'], self.results_dir],
                'condition': self.output_config.get('cvr_ballot_allocation') and 'cvr_ballot_allocation' not in self.skipped_steps,
                'depends_on': ['tabulate'],
                'fail_with': [],
                'return_key': None
            }),
            ('first_choice_to_finalist', {
                'f': write_out.write_first_to_finalist_tables,
                'args': [self.state_data['rcv_obj'], self.results_dir],
                'condition': self.output_config.get('first_choice_to_finalist') and 'first_choice_to_finalist' not in self.skipped_steps,
                'depends_on': ['tabulate'],
                'fail_with': [],
                'return_key': None
            }),
            ('condorcet', {
                'f': write_out.write_condorcet_tables,
                'args': [self.contest, self.results_dir],
                'condition': self.output_config.get('condorcet') and 'condorcet' not in self.skipped_steps,
                'depends_on': [],
                'fail_with': ['convert_cvr'],
                'return_key': None
            }),
            ('first_second_choices', {
                'f': write_out.write_first_second_tables,
                'args': [self.contest, self.results_dir],
                'condition': self.output_config.get('first_second_choices') and 'first_second_choices' not in self.skipped_steps,
                'depends_on': [],
                'fail_with': ['convert_cvr'],
                'return_key': None
            }),
            ('cumulative_rankings', {
                'f': write_out.write_cumulative_ranking_tables,
                'args': [self.contest, self.results_dir],
                'condition': self.output_config.get('cumulative_rankings') and 'cumulative_rankings' not in self.skipped_steps,
                'depends_on': [],
                'fail_with': ['convert_cvr'],
                'return_key': None
            }),
            ('rank_usage', {
                'f': write_out.write_rank_usage_tables,
                'args': [self.contest, self.results_dir],
                'condition': self.output_config.get('rank_usage') and 'rank_usage' not in self.skipped_steps,
                'depends_on': [],
                'fail_with': ['convert_cvr'],
                'return_key': None
            }),
            ('crossover_support', {
                'f': write_out.write_opponent_crossover_tables,
                'args': [self.contest, self.results_dir],
                'condition': self.output_config.get('crossover_support') and 'crossover_support' not in self.skipped_steps,
                'depends_on': [],
                'fail_with': ['convert_cvr'],
                'return_key': None
            }),
        ])

        for k in self.steps:
            for cache_key in cache_keys:
                if cache_key in cache[k]:
                    self.steps[k][cache_key] = cache[k][cache_key]

    def n_steps(self):
        return len(self.steps.keys())

    def next_step(self):

        remaining_steps = [
            (k, step) for k, step in self.steps.items()
            if step['success'] is None  # step not attempted yet
            and step['condition']  # step conditions are met
            and not any(self.steps[dep_k]['success'] is False for dep_k in step['fail_with'])  # all step dependencies are met
            and all(self.steps[dep_k]['success'] for dep_k in step['depends_on'])  # all step dependencies are met
        ]

        if not remaining_steps:
            return False
        else:
            return remaining_steps[0]

    def run_steps(self):

        self.refresh_steps()

        step_reached = 0
        with tqdm.tqdm(total=self.n_steps(), bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}{postfix}', colour='GREEN') as pbar:

            pbar.set_description(self.pbar_desc)

            next_step = self.next_step()
            while next_step:

                step_name, step_details = next_step

                try:

                    pbar.set_postfix_str(step_name)

                    if step_details['return_key']:
                        self.state_data.update({
                            step_details['return_key']:
                            step_details['f'](*step_details['args'])
                            })
                    else:
                        step_details['f'](*step_details['args'])

                except Exception as e:

                    self.steps[step_name]['success'] = False

                    for writer in self.error_log_writers:
                        writer.writerow([self.contest['uid'], self.contest['split_id'], step_name, repr(e)])
                    self.state_data['n_error'] += 1

                else:
                    self.steps[step_name]['success'] = True

                finally:
                    pbar.update(step_details['order']-step_reached)
                    step_reached = step_details['order']

                self.refresh_steps()
                next_step = self.next_step()

            pbar.set_postfix_str('complete')

    def return_results(self):
        return self.state_data


def crunch_contest_set(contest_set, output_config, path_to_output, fresh_output=False):

    start_time = datetime.datetime.now()

    ##################
    # OUTPUT PATHS
    path_to_output = pathlib.Path(path_to_output)

    # cvrs from path_to_cvr used in tabulation will be converted and output here
    converted_cvr_dir = path_to_output / 'converted_cvr'
    if fresh_output and converted_cvr_dir.exists():
        print('deleting existing converted_cvr directory...')
        shutil.rmtree(util.longname(converted_cvr_dir))
    util.verifyDir(util.longname(converted_cvr_dir))

    # various tabulation stats will be output here
    results_dir = path_to_output / 'results'
    if fresh_output and results_dir.exists():
        print('deleting existing results directory...')
        shutil.rmtree(util.longname(results_dir))
    util.verifyDir(util.longname(results_dir))

    #########################
    # SOME RESULTS CONTAINERS

    candidate_details_dfs = []
    rcv_variant_stats_df_dict = {variant_name: [] for variant_name in rcv_variants.get_rcv_dict().keys()}
    rcv_group_stats_df_dict = {variant_group: [] for variant_group in
                               set(g.variant_group() for g in rcv_variants.get_rcv_dict().values())}

    allsplit_rcv_variant_stats_df_dict = {variant_name: [] for variant_name in rcv_variants.get_rcv_dict().keys()}
    allsplit_rcv_group_stats_df_dict = {variant_group: [] for variant_group in
                                        set(g.variant_group() for g in rcv_variants.get_rcv_dict().values())}

    # split skipped steps
    split_skipped_steps = ['convert_cvr',
                           'ballot_stats_debug',
                           'cvr_ballot_allocation',
                           'first_choice_to_finalist',
                           'round_by_round',
                           'condorcet',
                           'candidate_details']

    # init output files
    split_details_path = results_dir / 'split_details.csv'
    any_splits = any(contest.get('split_fields') for contest in contest_set)
    if any_splits:
        split_log_file = open(split_details_path, 'w', newline='')
        split_log_writer = csv.writer(split_log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        split_log_writer.writerow(['uid', 'jurisdiction', 'office', 'year', 'date', 'total_splits', 'error_splits', 'write_dir'])
        split_log_file.flush()

    n_errors = 0
    error_log_path = results_dir / 'error_log.csv'
    with open(error_log_path, 'w', newline='') as error_log_file:

        error_log_writer = csv.writer(error_log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        error_log_writer.writerow(['contest', 'split_id', 'cruncher_step', 'message'])
        error_log_file.flush()

        #########################
        # LOOP TROUGH CONTESTS

        for idx, contest in enumerate(contest_set):

            # RUN OPERATIONS
            pbar_desc = f'{idx+1} of {len(contest_set)} contests: {contest["uid"]}'
            if n_errors:
                pbar_desc = f'[{n_errors} ERRORS SO FAR] ' + pbar_desc

            step_obj = CrunchSteps(contest, output_config, converted_cvr_dir, results_dir, pbar_desc,
                                   error_log_writers=[error_log_writer])
            step_obj.run_steps()
            crunch_returns = step_obj.return_results()

            n_errors += crunch_returns['n_errors']

            # STORE RESULTS
            if output_config.get('candidate_details') and 'candidate_details' in crunch_returns:
                candidate_details_dfs.append(crunch_returns['candidate_details'])

            if output_config.get('per_rcv_type_stats') and 'tabulation_stats_df' in crunch_returns:
                variant = crunch_returns['variant']
                rcv_variant_stats_df_dict[variant].append(crunch_returns['tabulation_stats_df'])

            if output_config.get('per_rcv_group_stats') and 'contest_stats_df' in crunch_returns:
                variant_group = crunch_returns['variant_group']
                rcv_group_stats_df_dict[variant_group].append(crunch_returns['contest_stats_df'])

            # CHECK FOR SPLITS
            split_contest_sets = split_contest(contest)

            if split_contest_sets:

                # SPLIT PATHS
                split_path = results_dir / 'split_stats'
                util.verifyDir(split_path)

                split_contest_path = split_path / contest["uid"]
                util.verifyDir(split_contest_path)

                split_results_path = split_contest_path / "results"
                util.verifyDir(split_results_path)

                split_converted_cvr_path = split_contest_path / "converted_cvr"
                util.verifyDir(split_converted_cvr_path)

                # SPLIT RESULTS CONTAINERS
                split_candidate_details_dfs = []
                split_rcv_variant_stats_df_dict = {variant_name: [] for variant_name in rcv_variants.get_rcv_dict().keys()}
                split_rcv_group_stats_df_dict = {variant_group: [] for variant_group in
                                                 set(g.variant_group() for g in rcv_variants.get_rcv_dict().values())}

                split_error_log_path = split_results_path / 'error_log.csv'
                with open(split_error_log_path, 'w', newline='') as split_error_log_file:

                    split_error_log_writer = csv.writer(split_error_log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
                    split_error_log_writer.writerow(['contest', 'split_id', 'cruncher_step', 'message'])

                    # LOOP SPLITS
                    n_splits = len(split_contest_sets)
                    splits_completed = 0
                    for split_idx, contest_split in enumerate(split_contest_sets):

                        if n_errors:
                            pbar_desc = f'[{n_errors} ERRORS SO FAR] {idx+1} of {len(contest_set)} contests,'
                            pbar_desc += f' {split_idx+1} of {n_splits} splits:'
                            pbar_desc += f' {contest_split["uid"]} {contest_split["split_id"]}'
                        else:
                            pbar_desc = f'{idx+1} of {len(contest_set)} contests,'
                            pbar_desc += f' {split_idx+1} of {n_splits} splits:'
                            pbar_desc += f' {contest_split["uid"]} {contest_split["split_id"]}'

                        split_step_obj = CrunchSteps(contest_split, output_config, split_converted_cvr_path, split_results_path,
                                                     pbar_desc, error_log_writers=[error_log_writer, split_error_log_writer],
                                                     skipped_steps=split_skipped_steps)
                        split_step_obj.run_steps()
                        split_crunch_returns = split_step_obj.return_results()

                        n_errors += split_crunch_returns['n_errors']

                        # store crunch output for aggregation
                        if output_config.get('candidate_details') and 'candidate_details' in split_crunch_returns:
                            split_candidate_details_dfs.append(split_crunch_returns['candidate_details'])

                        if output_config.get('per_rcv_type_stats') and 'tabulation_stats_df' in split_crunch_returns:
                            variant = split_crunch_returns['variant']
                            # split-specfic aggregation
                            split_rcv_variant_stats_df_dict[variant].append(split_crunch_returns['tabulation_stats_df'])
                            # all split aggregation
                            allsplit_rcv_variant_stats_df_dict[variant].append(split_crunch_returns['tabulation_stats_df'])

                        if output_config.get('per_rcv_group_stats') and 'contest_stats_df' in split_crunch_returns:
                            variant_group = split_crunch_returns['variant_group']
                            # split-specfic aggregation
                            split_rcv_group_stats_df_dict[variant_group].append(split_crunch_returns['contest_stats_df'])
                            # all split aggregation
                            allsplit_rcv_group_stats_df_dict[variant_group].append(split_crunch_returns['contest_stats_df'])

                        splits_completed += 1
                        error_log_file.flush()
                        split_error_log_file.flush()

                    write_aggregated_stats(split_results_path,
                                           output_config,
                                           split_rcv_group_stats_df_dict,
                                           split_rcv_variant_stats_df_dict,
                                           split_candidate_details_dfs,
                                           quiet=True)

                split_log_writer.writerow([contest['uid'],
                                           contest['jurisdiction'],
                                           contest['office'],
                                           contest['year'],
                                           contest['date'],
                                           n_splits,
                                           n_splits-splits_completed,
                                           split_contest_path])
                split_log_file.flush()
            else:
                split_log_writer.writerow([contest['uid'],
                                           contest['jurisdiction'],
                                           contest['office'],
                                           contest['year'],
                                           contest['date'],
                                           "NA", "NA", "NA"])
                split_log_file.flush()

            # remove cvr from mem
            if 'cvr' in contest:
                del contest['cvr']

            # flush error log
            error_log_file.flush()

        # WRITE OUT AGGREGATED STATS FOR CONTESTS
        write_aggregated_stats(results_dir,
                               output_config,
                               rcv_group_stats_df_dict,
                               rcv_variant_stats_df_dict,
                               candidate_details_dfs,
                               quiet=False)

        # WRITE OUT AGGREGATED STATS FOR ALL SPLITS
        if os.path.isdir(results_dir / 'split_stats'):

            allsplit_agg_path = results_dir / 'split_stats' / 'all_contest_splits'
            util.verifyDir(allsplit_agg_path)

            write_aggregated_stats(allsplit_agg_path,
                                   output_config,
                                   allsplit_rcv_group_stats_df_dict,
                                   allsplit_rcv_variant_stats_df_dict,
                                   [], quiet=True)

        # make debug version of contest set
        # if stats_debugs:

        #     util.verifyDir(debug_contest_set_dir)

        #     debug_contest_set_fname = debug_contest_set_dir / 'contest_set.csv'
        #     pd.concat([t[1] for t in stats_debugs]).to_csv(util.longname(debug_contest_set_fname), index=False)

        #     debug_output_config = debug_contest_set_dir / 'output_config.csv'
        #     shutil.copy2(output_config['run_config_file_path'], util.longname(debug_output_config))

        #     print('Debug contest set created at ' + debug_contest_set_dir +
        #           '. Contests that have failed accounting identity checks have been copied there.')

        # CREATE A LOG FILE CONTAINED SCRIPTS USED IN THE GENERATION OF THESE RESULTS

        end_time = datetime.datetime.now()

        # copy scripts used for results generation into log file
        result_log_dir = results_dir / 'inputs'
        util.verifyDir(result_log_dir)

        pkg_version = pkg_resources.require("rcv_cruncher")[0].version
        pkg_url = "https://github.com/fairvotereform/rcv_cruncher"
        with open(result_log_dir / 'pkg_info.txt', 'w') as pkg_info:
            pkg_info.write(f'version: {pkg_version}\n')
            pkg_info.write(f'github: {pkg_url}\n')
            pkg_info.write(f'start_time: {start_time.strftime("%Y-%m-%d %H:%M:%S")}')
            pkg_info.write(f'end_time: {end_time.strftime("%Y-%m-%d %H:%M:%S")}')

        log_output_config = result_log_dir / 'output_config.csv'
        shutil.copy2(output_config['run_config_file_path'], log_output_config)

        log_contest_set_fname = result_log_dir / 'contest_set.csv'
        shutil.copy2(output_config['contest_set_file_path'], log_contest_set_fname)

        duration = end_time - start_time
        print(f"runtime duration: {str(duration)}")
        print("DONE!")
