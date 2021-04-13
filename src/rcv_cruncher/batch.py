
# import json
# import os
# import pathlib
# import re
# import shutil
# import pkg_resources
# import collections
# import datetime
# import abc

# import pandas as pd
# import tqdm

# import rcv_cruncher.parsers as parsers
# import rcv_cruncher.rcv_base as rcv_base
# import rcv_cruncher.rcv_variants as rcv_variants
# import rcv_cruncher.util as util
# import rcv_cruncher.write_out as write_out


# # read functions in parsers and rcv_variants
# rcv_dict = rcv_variants.get_rcv_dict()
# parser_dict = parsers.get_parser_dict()


# @staticmethod
# def new_rcv_contest(contest_dict: Dict) -> Type[RCV]:
#     """
#     Pass in a dictionary and run the constructor function stored within it
#     """
#     param_names = inspect.signature(contest_dict['rcv_type'].__init__)
#     param_dict = {k: v for k, v in contest_dict.items() if k in param_names}
#     return contest_dict['rcv_type'](**param_dict)


# def dummy(*args):
#     pass


# # typecast functions
# def cast_str(s):
#     """
#     If string-in-string '"0006"', evaluate to '0006'
#     If 'None', return None (since this string cannot be evaluated)
#     else, return str() result
#     """
#     if (s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'"):
#         return eval(s)
#     elif s == 'None':
#         return None
#     else:
#         return str(s)


# def cast_int(s):
#     if isinstance(s, int):
#         return s
#     return int(s)


# def cast_bool(s):
#     if isinstance(s, bool):
#         return s
#     return eval(s.title())


# def cast_list(lst):
#     if lst == "":
#         return []
#     return lst.strip('\n').split(",")


# def cast_dict(dct):
#     dct_return = {}
#     if dct == "":
#         return dct_return
#     comma_split = dct.strip("\n").split(",")
#     for i in comma_split:
#         equal_split = i.split("=")
#         dct_return.update({equal_split[0]: "=".join(equal_split[1:])})
#     return dct_return


# def cast_func(s):

#     if s in rcv_dict and s in parser_dict:
#         raise RuntimeError('(developer error) An rcv variant class and a parser function share the same name. Make them unique.')

#     if s in rcv_dict:
#         return rcv_dict[s]

#     if s in parser_dict:
#         return parser_dict[s]


# # other helpers
# # def dop(ctx):
# #     return '_'.join([ctx['year'], ctx['place'], ctx['office']])

# def unique_id(ctx):
#     filled_date = "/".join([piece if len(piece) > 1 else "0" + piece for piece in ctx['date'].split("/")])
#     pieces = [ctx['jurisdiction'], filled_date, ctx['office']]
#     cleaned_pieces = [re.sub('[^0-9a-zA-Z_]+', '', x) for x in pieces]
#     return "_".join(cleaned_pieces)

# def read_contest_set(contest_set_path, override_cvr_root_dir=None):

#     contest_set_path = pathlib.Path(contest_set_path)

#     # assemble typecast funcs
#     cast_dict = {'str': cast_str, 'int': cast_int, 'dict': cast_dict,
#                  'bool': cast_bool, 'func': cast_func, 'list': cast_list}

#     # settings/defaults
#     contest_set_settings_fpath = f'{os.path.dirname(__file__)}/contest_set_settings.json'
#     if os.path.isfile(contest_set_settings_fpath) is False:
#         raise RuntimeError(f'(developer error) Looking for contest_set_settings.json. Not a valid file path: {contest_set_settings_fpath}')

#     with open(contest_set_settings_fpath) as contest_set_settings_file:
#         contest_set_settings = json.load(contest_set_settings_file)

#     run_config_settings_fpath = f'{os.path.dirname(__file__)}/run_config_settings.json'
#     if os.path.isfile(run_config_settings_fpath) is False:
#         raise RuntimeError(f'(developer error) Looking for run_config_settings.json. Not a valid file path: {run_config_settings_fpath}')

#     with open(run_config_settings_fpath) as run_config_settings_file:
#         run_config_settings = json.load(run_config_settings_file)

#     # read run_config.txt
#     run_config_fpath = contest_set_path / 'run_config.txt'
#     if os.path.isfile(run_config_fpath) is False:
#         raise RuntimeError(f'not a valid file path: {run_config_fpath}')

#     run_config = {}
#     with open(run_config_fpath) as run_config_file:
#         for line_num, l in enumerate(run_config_file, start=1):

#             l_splits = l.strip('\n').split("=")
#             l_splits = [s.strip() for s in l_splits]

#             if len(l_splits) < 2:
#                 continue

#             input_option = l_splits[0]
#             input_value = l_splits[1]

#             if input_option not in run_config_settings:
#                 continue

#             if run_config_settings[input_option]['type'] == "bool":
#                 if input_value.title() != "True" and input_value.title() != "False":
#                     raise RuntimeError(f'invalid value ({input_value}) provided in run_config.txt'
#                                        f'on line {line_num} for option "{l_splits[0]}". Must be "true" or "false".')
#                 input_value = eval(input_value.title())

#             run_config.update({input_option: input_value})

#     # add in defaults for missing options
#     for field in run_config_settings:
#         if field not in run_config:
#             run_config.update({field: run_config_settings[field]['default']})

#     run_config['cvr_path_root'] = pathlib.Path(run_config['cvr_path_root'])

#     # read contest_set.csv
#     contest_set_fpath = contest_set_path / 'contest_set.csv'
#     if os.path.isfile(contest_set_fpath) is False:
#         raise RuntimeError(f'not a valid file path: {contest_set_fpath}')

#     contest_set_df = pd.read_csv(contest_set_fpath, dtype=object)

#     # add in default values for missing columns
#     for setting in contest_set_settings:
#         if setting not in contest_set_df.columns:
#             contest_set_df[setting] = contest_set_settings[setting]['default']

#     # fill in na values with defaults and evaluate column, if indicated
#     for col in contest_set_df:

#         if col not in contest_set_settings:
#             print(f'info -- "{col}" is an unrecognized column in contest_set.csv, it will be ignored.')
#         else:
#             contest_set_df[col] = contest_set_df[col].fillna(contest_set_settings[col]['default'])
#             contest_set_df[col] = [cast_dict[contest_set_settings[col]['type']](i) for i in contest_set_df[col].tolist()]

#     contest_set_df['contest_set_path'] = contest_set_path

#     # convert df to listOdicts, one dict per row
#     competitions = contest_set_df.to_dict('records')

#     # add dop, uid, cvr_path_root
#     for d in competitions:

#         if override_cvr_root_dir:
#             d['cvr_path'] = pathlib.Path(override_cvr_root_dir) / d['cvr_path']
#         else:
#             d['cvr_path'] = run_config['cvr_path_root'] / d['cvr_path']

#         d['parser_args'] = {'cvr_path': d['cvr_path']}
#         d['parser_args'].update(d['extra_parser_args'])

#         if d['candidate_map']:
#             d['candidate_map'] = run_config['cvr_path_root'] / d['candidate_map']

#         d['uid'] = util.unique_id(d)

#     # remove contest that should be ignored
#     competitions = [comp for comp in competitions if not comp.get('ignore_contest', True)]

#     # remove contests with invalid parser, print warning.
#     no_parser = []
#     for comp in competitions:
#         if comp['parser'] == dummy:
#             no_parser.append(comp)

#     no_parser_uniqueID = [comp['uid'] for comp in no_parser]
#     valid_competitions = [comp for comp in competitions if comp['uid'] not in no_parser_uniqueID]

#     if no_parser:
#         print(f'info -- {len(no_parser)} contests in contest_set.csv did not include a valid cvr parser field. They will be ignored.')

#     # store file locations
#     run_config['contest_set_file_path'] = contest_set_fpath
#     run_config['run_config_file_path'] = run_config_fpath

#     return valid_competitions, run_config


# def write_aggregated_stats(results_dir,
#                            output_config,
#                            rcv_group_stats_df_dict,
#                            rcv_variant_stats_df_dict,
#                            candidate_details_dfs,
#                            quiet=False):

#     if not quiet:
#         print("####################")
#         print("Write stored results")

#     if output_config.get('per_rcv_group_stats', False):

#         if not quiet:
#             print("write group stats ...")

#         for group in rcv_group_stats_df_dict:
#             if rcv_group_stats_df_dict[group]:
#                 df = pd.concat(rcv_group_stats_df_dict[group], axis=0, ignore_index=True, sort=False)
#                 df.to_csv(util.longname(results_dir / f'group_{group}.csv'), index=False)

#     if output_config.get('per_rcv_group_stats_fvDBfmt', False):

#         if not quiet:
#             print("write group stats in fvDB order ...")

#         for group in rcv_group_stats_df_dict:
#             format_fpath = f"extra/fv_db_format/{group}_columns.csv"
#             if rcv_group_stats_df_dict[group] and os.path.isfile(format_fpath):

#                 # read in column order
#                 fmt_df = pd.read_csv(format_fpath)
#                 fmt_order = fmt_df['cruncher_col'].tolist()

#                 df = pd.concat(rcv_group_stats_df_dict[group], axis=0, ignore_index=True, sort=False)
#                 df = df.reindex(fmt_order, axis=1)
#                 df.to_csv(util.longname(results_dir / f'group_{group}_fvDBfmt.csv'), index=False)

#     if output_config.get('per_rcv_type_stats', False):

#         if not quiet:
#             print("Write tabulation stats ...")

#         for variant in rcv_variant_stats_df_dict:
#             if rcv_variant_stats_df_dict[variant]:
#                 df = pd.concat(rcv_variant_stats_df_dict[variant], axis=0, ignore_index=True, sort=False)
#                 df.to_csv(util.longname(results_dir / f'{variant}.csv'), index=False)

#     if output_config.get('candidate_details', False) and candidate_details_dfs:

#         if not quiet:
#             print("Write candidate details ...")

#         df = pd.concat(util.flatten_list(candidate_details_dfs), axis=0, ignore_index=True, sort=False)
#         df.to_csv(util.longname(results_dir / 'candidate_details.csv'), index=False)


# class Steps(abc.ABC):

#     def __init__(self, contest, output_config, converted_cvr_dir, results_dir, pbar_desc):

#         self.contest = contest
#         self.output_config = output_config
#         self.converted_cvr_dir = converted_cvr_dir
#         self.results_dir = results_dir
#         self.pbar_desc = pbar_desc
#         self.error_log_writers = []

#         self.state_data = {
#             'n_errors': 0,
#             'rcv_obj': None
#         }
#         self.steps = {}

#     def update_state(self, dct):
#         self.state_data.update(dct)

#     def update_pbar_desc(self, desc):
#         self.pbar_desc = desc

#     def update_error_log_writers(self, writers_list):
#         self.error_log_writers = writers_list if isinstance(writers_list, list) else [writers_list]

#     def refresh_steps(self):

#         cache_keys = ['success', 'order']
#         cache = collections.defaultdict(dict)
#         for k1 in self.steps:
#             for k2 in cache_keys:
#                 if k2 in self.steps[k1]:
#                     cache[k1].update({k2: self.steps[k1][k2]})

#         self.steps = self.generate_steps()

#         for k in self.steps:
#             for cache_key in cache_keys:
#                 if cache_key in cache[k]:
#                     self.steps[k][cache_key] = cache[k][cache_key]

#     @abc.abstractmethod
#     def generate_steps(self):
#         pass

#     def n_steps(self):
#         return len(self.steps.keys())

#     def next_step(self):

#         remaining_steps = [
#             (k, step) for k, step in self.steps.items()
#             if step['success'] is None  # step not attempted yet
#             and step['condition']  # step conditions are met
#             and not any(self.steps[dep_k]['success'] is False for dep_k in step['fail_with'])  # all step dependencies are met
#             and all(self.steps[dep_k]['success'] for dep_k in step['depends_on'])  # all step dependencies are met
#         ]

#         if not remaining_steps:
#             return False
#         else:
#             return remaining_steps[0]

#     def run_steps(self):

#         self.state_data['n_errors'] = 0

#         # init
#         self.refresh_steps()
#         for step_num, k in enumerate(self.steps, start=1):
#             self.steps[k]['success'] = None
#             self.steps[k]['order'] = step_num

#         step_reached = 0

#         pbar = tqdm.tqdm(total=self.n_steps(), bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}{postfix}', colour='GREEN')
#         pbar.set_description(self.pbar_desc)

#         next_step = self.next_step()
#         while next_step:

#             step_name, step_details = next_step

#             try:

#                 pbar.set_postfix_str(step_name)

#                 if step_details['return_key']:
#                     self.state_data.update({
#                         step_details['return_key']:
#                         step_details['f'](*step_details['args'])
#                         })
#                 else:
#                     step_details['f'](*step_details['args'])

#             except Exception as e:

#                 self.steps[step_name]['success'] = False

#                 for writer in self.error_log_writers:
#                     writer.write([self.contest['uid'], self.contest['split_id'], step_name, repr(e)])
#                 self.state_data['n_errors'] += 1

#             else:
#                 self.steps[step_name]['success'] = True

#             finally:
#                 pbar.update(step_details['order']-step_reached)
#                 step_reached = step_details['order']

#             self.refresh_steps()
#             next_step = self.next_step()

#         pbar.set_postfix_str('complete')
#         pbar.close()

#     def return_results(self):
#         return self.state_data


# class CrunchSteps(Steps):

#     def generate_steps(self):

#         return collections.OrderedDict([
#             ('convert_cvr_rank', {
#                 'f': write_out.write_converted_cvr,
#                 'args': [self.contest, self.converted_cvr_dir, 'rank'],
#                 'condition': self.output_config.get('convert_cvr_rank_format'),
#                 'fail_with': [],
#                 'depends_on': [],
#                 'return_key': None
#             }),
#             ('convert_cvr_candidate', {
#                 'f': write_out.write_converted_cvr,
#                 'args': [self.contest, self.converted_cvr_dir, 'candidate'],
#                 'condition': self.output_config.get('convert_cvr_candidate_format'),
#                 'fail_with': [],
#                 'depends_on': [],
#                 'return_key': None
#             }),
#             ('tabulate', {
#                 'f': rcv_base.RCV.run_rcv,
#                 'args': [self.contest],
#                 'condition': True,
#                 'depends_on': [],
#                 'fail_with': [],
#                 'return_key': 'rcv_obj'
#             }),
#             ('tabulation_stats', {
#                 'f': rcv_base.RCV.get_tabulation_stats_df,
#                 'args': [self.state_data['rcv_obj']],
#                 'condition': self.output_config.get('per_rcv_type_stats'),
#                 'depends_on': ['tabulate'],
#                 'fail_with': [],
#                 'return_key': 'tabulation_stats_df'
#             }),
#             ('rcv_variant', {
#                 'f': rcv_base.RCV.get_variant_name,
#                 'args': [self.state_data['rcv_obj']],
#                 'condition': True,
#                 'depends_on': ['tabulate'],
#                 'fail_with': [],
#                 'return_key': 'variant'
#             }),
#             ('contest_stats', {
#                 'f': rcv_base.RCV.get_contest_stats_df,
#                 'args': [self.state_data['rcv_obj']],
#                 'condition': self.output_config.get('per_rcv_group_stats'),
#                 'depends_on': ['tabulate'],
#                 'fail_with': [],
#                 'return_key': 'contest_stats_df'
#             }),
#             ('rcv_group', {
#                 'f': rcv_base.RCV.get_variant_group,
#                 'args': [self.state_data['rcv_obj']],
#                 'condition': True,
#                 'depends_on': ['tabulate'],
#                 'fail_with': [],
#                 'return_key': 'variant_group'
#             }),
#             ('candidate_details', {
#                 'f': write_out.prepare_candidate_details,
#                 'args': [self.state_data['rcv_obj']],
#                 'condition': self.output_config.get('candidate_details'),
#                 'depends_on': ['tabulate'],
#                 'fail_with': [],
#                 'return_key': 'candidate_details'
#             }),
#             ('round_by_round', {
#                 'f': write_out.write_rcv_rounds,
#                 'args': [self.state_data['rcv_obj'], self.results_dir],
#                 'condition': self.output_config.get('round_by_round'),
#                 'depends_on': ['tabulate'],
#                 'fail_with': [],
#                 'return_key': None
#             }),
#             ('ballot_stats_debug', {
#                 'f': write_out.write_ballot_debug_info,
#                 'args': [self.state_data['rcv_obj'], self.results_dir],
#                 'condition': self.output_config.get('ballot_stats_debug'),
#                 'depends_on': ['tabulate'],
#                 'fail_with': [],
#                 'return_key': None
#             }),
#             ('cvr_ballot_allocation_rank', {
#                 'f': write_out.write_converted_cvr_annotated,
#                 'args': [self.state_data['rcv_obj'], self.results_dir, 'rank'],
#                 'condition': self.output_config.get('cvr_ballot_allocation_rank_format'),
#                 'depends_on': ['tabulate'],
#                 'fail_with': [],
#                 'return_key': None
#             }),
#             ('cvr_ballot_allocation_candidate', {
#                 'f': write_out.write_converted_cvr_annotated,
#                 'args': [self.state_data['rcv_obj'], self.results_dir, 'candidate'],
#                 'condition': self.output_config.get('cvr_ballot_allocation_candidate_format'),
#                 'depends_on': ['tabulate'],
#                 'fail_with': [],
#                 'return_key': None
#             }),
#             ('first_choice_to_finalist', {
#                 'f': write_out.write_first_to_finalist_tables,
#                 'args': [self.state_data['rcv_obj'], self.results_dir],
#                 'condition': self.output_config.get('first_choice_to_finalist'),
#                 'depends_on': ['tabulate'],
#                 'fail_with': [],
#                 'return_key': None
#             }),
#             ('condorcet', {
#                 'f': write_out.write_condorcet_tables,
#                 'args': [self.contest, self.results_dir],
#                 'condition': self.output_config.get('condorcet'),
#                 'depends_on': [],
#                 'fail_with': [],
#                 'return_key': None
#             }),
#             ('first_second_choices', {
#                 'f': write_out.write_first_second_tables,
#                 'args': [self.contest, self.results_dir],
#                 'condition': self.output_config.get('first_second_choices'),
#                 'depends_on': [],
#                 'fail_with': [],
#                 'return_key': None
#             }),
#             ('cumulative_rankings', {
#                 'f': write_out.write_cumulative_ranking_tables,
#                 'args': [self.contest, self.results_dir],
#                 'condition': self.output_config.get('cumulative_rankings'),
#                 'depends_on': [],
#                 'fail_with': [],
#                 'return_key': None
#             }),
#             ('rank_usage', {
#                 'f': write_out.write_rank_usage_tables,
#                 'args': [self.contest, self.results_dir],
#                 'condition': self.output_config.get('rank_usage'),
#                 'depends_on': [],
#                 'fail_with': [],
#                 'return_key': None
#             }),
#             ('crossover_support', {
#                 'f': write_out.write_opponent_crossover_tables,
#                 'args': [self.contest, self.results_dir],
#                 'condition': self.output_config.get('crossover_support'),
#                 'depends_on': [],
#                 'fail_with': [],
#                 'return_key': None
#             }),
#             ('split_stats', {
#                 'f': rcv_base.RCV.get_split_stats,
#                 'args': [self.state_data['rcv_obj']],
#                 'condition': True,
#                 'depends_on': ['tabulate'],
#                 'fail_with': [],
#                 'return_key': 'split_stats'
#             })
#         ])


# def init_error_logger(results_dir):
#     header_list = ['contest', 'split_id', 'cruncher_step', 'message']
#     error_log_path = results_dir / 'error_log.csv'
#     return util.CSVLogger(error_log_path, header_list)


# def write_input_dir(results_dir, output_config, start_time, end_time):

#     # copy input files
#     result_log_dir = results_dir / 'inputs'
#     util.verifyDir(result_log_dir)

#     pkg_version = pkg_resources.require("rcv_cruncher")[0].version
#     pkg_url = "https://github.com/fairvotereform/rcv_cruncher"
#     with open(result_log_dir / 'pkg_info.txt', 'w') as pkg_info:
#         pkg_info.write(f'version: {pkg_version}\n')
#         pkg_info.write(f'github: {pkg_url}\n')
#         pkg_info.write(f'start_time: {start_time.strftime("%Y-%m-%d %H:%M:%S")}\n')
#         pkg_info.write(f'end_time: {end_time.strftime("%Y-%m-%d %H:%M:%S")}')

#     log_output_config = result_log_dir / 'output_config.csv'
#     shutil.copy2(output_config['run_config_file_path'], log_output_config)

#     log_contest_set_fname = result_log_dir / 'contest_set.csv'
#     shutil.copy2(output_config['contest_set_file_path'], log_contest_set_fname)


# def crunch_contest_set(contest_set, output_config, path_to_output, fresh_output=False):

#     start_time = datetime.datetime.now()

#     ##################
#     # OUTPUT PATHS
#     path_to_output = pathlib.Path(path_to_output)

#     # cvrs from path_to_cvr used in tabulation will be converted and output here
#     converted_cvr_dir = path_to_output / 'converted_cvr'
#     if fresh_output and converted_cvr_dir.exists():
#         print('deleting existing converted_cvr directory...')
#         shutil.rmtree(util.longname(converted_cvr_dir))
#     util.verifyDir(util.longname(converted_cvr_dir))

#     # various tabulation stats will be output here
#     results_dir = path_to_output / 'results'
#     if fresh_output and results_dir.exists():
#         print('deleting existing results directory...')
#         shutil.rmtree(util.longname(results_dir))
#     util.verifyDir(util.longname(results_dir))

#     #########################
#     # SOME RESULTS CONTAINERS

#     candidate_details_dfs = []
#     rcv_variant_stats_df_dict = {variant_name: [] for variant_name in rcv_variants.get_rcv_dict().keys()}
#     rcv_group_stats_df_dict = {variant_group: [] for variant_group in
#                                set(g.variant_group() for g in rcv_variants.get_rcv_dict().values())}

#     allsplit_rcv_variant_stats_df_dict = {variant_name: [] for variant_name in rcv_variants.get_rcv_dict().keys()}
#     allsplit_rcv_group_stats_df_dict = {variant_group: [] for variant_group in
#                                         set(g.variant_group() for g in rcv_variants.get_rcv_dict().values())}

#     # init loggers
#     error_logger = init_error_logger(results_dir)

#     n_errors = 0
#     #########################
#     # LOOP TROUGH CONTESTS

#     for idx, contest in enumerate(contest_set):

#         # RUN OPERATIONS
#         pbar_desc = f'{idx+1} of {len(contest_set)} contests: '
#         pbar_desc += f'{contest["jurisdiction"]} {contest["date"]} {contest["office"]}'
#         if n_errors:
#             pbar_desc = f'[{n_errors} ERRORS SO FAR] ' + pbar_desc

#         step_obj = CrunchSteps(contest, output_config, converted_cvr_dir, results_dir, pbar_desc)
#         step_obj.update_error_log_writers([error_logger])
#         step_obj.run_steps()

#         crunch_returns = step_obj.return_results()
#         n_errors += crunch_returns['n_errors']

#         # STORE RESULTS
#         if output_config.get('candidate_details') and crunch_returns.get('candidate_details'):
#             candidate_details_dfs.append(crunch_returns['candidate_details'])

#         if output_config.get('per_rcv_type_stats') and crunch_returns.get('tabulation_stats_df'):
#             variant = crunch_returns['variant']
#             rcv_variant_stats_df_dict[variant].append(crunch_returns['tabulation_stats_df'])

#         if output_config.get('per_rcv_group_stats') and crunch_returns.get('contest_stats_df'):
#             variant_group = crunch_returns['variant_group']
#             rcv_group_stats_df_dict[variant_group].append(crunch_returns['contest_stats_df'])

#         if crunch_returns.get('split_stats'):

#             split_stats = crunch_returns['split_stats']

#             # SPLIT PATHS
#             split_path = results_dir / 'split_stats'
#             util.verifyDir(split_path)

#             split_contest_path = split_path / contest["uid"]
#             util.verifyDir(split_contest_path)

#             # SPLIT RESULTS CONTAINERS
#             split_rcv_variant_stats_df_dict = {variant_name: [] for variant_name in rcv_variants.get_rcv_dict().keys()}
#             split_rcv_group_stats_df_dict = {variant_group: [] for variant_group in
#                                              set(g.variant_group() for g in rcv_variants.get_rcv_dict().values())}

#             for split_stat in split_stats:

#                 if output_config.get('per_rcv_type_stats') and split_stat.get('tabulation_stats_df'):
#                     variant = split_stat['variant']
#                     split_rcv_variant_stats_df_dict[variant].append(split_stat['tabulation_stats_df'])
#                     allsplit_rcv_variant_stats_df_dict[variant].append(split_stat['tabulation_stats_df'])

#                 if output_config.get('per_rcv_group_stats') and split_stat.get('contest_stats_df'):
#                     variant_group = split_stat['variant_group']
#                     split_rcv_group_stats_df_dict[variant_group].append(split_stat['contest_stats_df'])
#                     allsplit_rcv_group_stats_df_dict[variant_group].append(split_stat['contest_stats_df'])

#             write_aggregated_stats(split_contest_path, output_config,
#                                    split_rcv_group_stats_df_dict, split_rcv_variant_stats_df_dict,
#                                    [], quiet=True)

#         # remove cvr from mem
#         if 'cvr' in contest:
#             del contest['cvr']

#     # close logs
#     error_logger.close()

#     # WRITE OUT AGGREGATED STATS FOR CONTESTS
#     write_aggregated_stats(results_dir,
#                            output_config,
#                            rcv_group_stats_df_dict,
#                            rcv_variant_stats_df_dict,
#                            candidate_details_dfs,
#                            quiet=False)

#     # WRITE OUT AGGREGATED STATS FOR ALL SPLITS
#     if os.path.isdir(results_dir / 'split_stats'):

#         allsplit_agg_path = results_dir / 'split_stats' / 'all_contest_splits'
#         util.verifyDir(allsplit_agg_path)

#         write_aggregated_stats(allsplit_agg_path,
#                                output_config,
#                                allsplit_rcv_group_stats_df_dict,
#                                allsplit_rcv_variant_stats_df_dict,
#                                [], quiet=True)

#     end_time = datetime.datetime.now()

#     write_input_dir(results_dir, output_config, start_time, end_time)

#     duration = end_time - start_time
#     print(f"runtime duration: {str(duration)}")
#     print("DONE!")
