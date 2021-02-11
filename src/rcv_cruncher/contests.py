
import json
import os
import re
import shutil
from functools import partial  # noqa: F401 - remove once parsers are edited
from os.path import dirname

import pandas as pd
import tqdm

import rcv_cruncher.parsers as parsers
import rcv_cruncher.rcv_base as rcv_base
import rcv_cruncher.rcv_variants as rcv_variants
import rcv_cruncher.util as util
import rcv_cruncher.write_out as write_out

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


def cast_func(s):

    if s in rcv_dict and s in parser_dict:
        raise RuntimeError('(developer error) An rcv variant class and a parser function share the same name. Make them unique.')

    if s in rcv_dict:
        return rcv_dict[s]

    if s in parser_dict:
        return parser_dict[s]


# other helpers
def dop(ctx):
    return '_'.join([ctx['year'], ctx['place'], ctx['office']])


def unique_id(ctx):
    filled_date = "/".join([piece if len(piece) > 1 else "0" + piece for piece in ctx['date'].split("/")])
    pieces = [ctx['jurisdiction'], filled_date, ctx['office']]
    cleaned_pieces = [re.sub('[^0-9a-zA-Z_]+', '', x) for x in pieces]
    return "_".join(cleaned_pieces)


def read_contest_set(contest_set_path, override_cvr_root_dir=None):

    # assemble typecast funcs
    cast_dict = {'str': cast_str, 'int': cast_int,
                 'bool': cast_bool, 'func': cast_func}

    # settings/defaults
    contest_set_settings_fpath = f'{dirname(__file__)}/contest_set_settings.json'
    if os.path.isfile(contest_set_settings_fpath) is False:
        raise RuntimeError(f'(developer error) not a valid file path: {contest_set_settings_fpath}')

    with open(contest_set_settings_fpath) as contest_set_settings_file:
        contest_set_settings = json.load(contest_set_settings_file)

    run_config_settings_fpath = f'{dirname(__file__)}/run_config_settings.json'
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
                                       'on line {line_num} for option "{l_splits[0]}". Must be "true" or "false".')
                input_value = eval(input_value.title())

            run_config.update({input_option: input_value})

    # add in defaults for missing options
    for field in run_config_settings:
        if field not in run_config:
            run_config.update({field: run_config_settings[field]['default']})

    # make sure cvr path is provided
    # if not run_config['cvr_path_root']:
    #     raise RuntimeError('No "cvr_path_root" provided in run_config.txt. This is required.')

    # read contest_set.csv
    contest_set_fpath = f'{contest_set_path}/contest_set.csv'
    if os.path.isfile(contest_set_fpath) is False:
        raise RuntimeError(f'not a valid file path: {contest_set_fpath}')

    contest_set_df = pd.read_csv(contest_set_fpath, dtype=object)
    cols_in_order = contest_set_df.columns

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

    # add dop, unique_id, cvr_path_root
    for d in competitions:
        d['unique_id'] = unique_id(d)
        d['contest_set_line_df'] = pd.DataFrame([[d[col].__name__ if callable(d[col]) else d[col] for col in cols_in_order]],
                                                columns=cols_in_order)
        if override_cvr_root_dir:
            d['cvr_path'] = f"{override_cvr_root_dir}/{d['cvr_path']}"
        else:
            d['cvr_path'] = f"{run_config['cvr_path_root']}/{d['cvr_path']}"

        if d['master_lookup']:
            d['master_lookup'] = f"{run_config['cvr_path_root']}/{d['master_lookup']}"
        if d['candidate_map']:
            d['candidate_map'] = f"{run_config['cvr_path_root']}/{d['candidate_map']}"

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

    no_parser_uniqueID = [comp['unique_id'] for comp in no_parser]
    valid_competitions = [comp for comp in competitions if comp['unique_id'] not in no_parser_uniqueID]

    if no_parser:
        print(f'info -- {len(no_parser)} contests in contest_set.csv did not include a valid cvr parser field. They will be ignored.')

    return valid_competitions, run_config


def crunch_contest_set(contest_set, output_config, path_to_output):

    # cvrs from path_to_cvr used in tabulation will be converted and output here
    converted_cvr_dir = f'{path_to_output}/converted_cvr'
    util.verifyDir(converted_cvr_dir)

    # various tabulation stats will be output here
    results_dir = f'{path_to_output}/results'
    util.verifyDir(results_dir)

    stats_check_fname = f'{results_dir}/stats_consistency_check.txt'

    # copied contest set file with failed stats checks will go here
    debug_contest_set_dir = f'{path_to_output}/debug'
    util.verifyDir(debug_contest_set_dir)

    # some results containers
    candidate_details_dfs = []
    rcv_variant_stats_df_dict = {variant_name: [] for variant_name in rcv_variants.get_rcv_dict().keys()}
    rcv_group_stats_df_dict = {variant_group: [] for variant_group in
                               set(g.variant_group() for g in rcv_variants.get_rcv_dict().values())}

    stats_debugs = []

    # loop through contests and tabulate the elections
    for idx, contest in enumerate(contest_set):

        with tqdm.tqdm(total=16, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}{postfix}', colour="MAGENTA") as pbar:

            pbar.set_description(f'{idx+1} of {len(contest_set)}: {contest["unique_id"]}')

            pbar.update(1)
            pbar.set_postfix_str("converting cvr")
            if output_config.get('convert_cvr', False):
                write_out.write_converted_cvr(contest, converted_cvr_dir)

            # create RCV obj + tabulate
            pbar.update(1)
            pbar.set_postfix_str("tabulating")
            rcv_obj = rcv_base.RCV.run_rcv(contest)

            # stats double check
            pbar.update(1)
            pbar.set_postfix_str("check stats")
            stats_debugs.append(rcv_obj.get_stats_check_log())

            ########################
            # RESULTS-BASED OUTPUTS

            pbar.update(1)
            if output_config.get('per_rcv_type_stats', False):
                pbar.set_postfix_str("store tabulation stats")
                if not rcv_variant_stats_df_dict[rcv_obj.__class__.__name__]:
                    rcv_variant_stats_df_dict[rcv_obj.__class__.__name__].append(rcv_obj.tabulation_stats_comments_df())
                rcv_variant_stats_df_dict[rcv_obj.__class__.__name__].append(rcv_obj.tabulation_stats_df())

            pbar.update(1)
            if output_config.get('per_rcv_group_stats', False):
                pbar.set_postfix_str("store contest stats")
                if not rcv_group_stats_df_dict[rcv_obj.variant_group()]:
                    rcv_group_stats_df_dict[rcv_obj.variant_group()].append(rcv_obj.contest_stats_comments_df())
                rcv_group_stats_df_dict[rcv_obj.variant_group()].append(rcv_obj.contest_stats_df())

            pbar.update(1)
            if output_config.get('candidate_details', False):
                pbar.set_postfix_str("store candidate details")
                candidate_details_dfs.append(write_out.prepare_candidate_details(rcv_obj))

            pbar.update(1)
            if output_config.get('round_by_round', False):
                pbar.set_postfix_str("write round by round results")
                write_out.write_rcv_rounds(rcv_obj, results_dir)

            pbar.update(1)
            if output_config.get('ballot_stats_debug', False):
                pbar.set_postfix_str("write ballot stats debug")
                write_out.write_ballot_debug_info(rcv_obj, results_dir)

            pbar.update(1)
            if output_config.get('cvr_ballot_allocation', False):
                pbar.set_postfix_str("write cvr with final allocations")
                write_out.write_converted_cvr_annotated(rcv_obj, results_dir)

            pbar.update(1)
            if output_config.get('first_choice_to_finalist', False):
                pbar.set_postfix_str("write first choice to finalist table")
                write_out.write_first_to_finalist_tables(rcv_obj, results_dir)

            ################
            # BALLOT-BASED OUTPUTS

            pbar.update(1)
            if output_config.get('condorcet', False):
                pbar.set_postfix_str("write condorcet table")
                write_out.write_condorcet_tables(contest, results_dir)

            pbar.update(1)
            if output_config.get('first_second_choices', False):
                pbar.set_postfix_str("write first and second choices table")
                write_out.write_first_second_tables(contest, results_dir)

            pbar.update(1)
            if output_config.get('cumulative_rankings', False):
                pbar.set_postfix_str("write cumulative ranking table")
                write_out.write_cumulative_ranking_tables(contest, results_dir)

            pbar.update(1)
            if output_config.get('rank_usage', False):
                pbar.set_postfix_str("write rank usage table")
                write_out.write_rank_usage_tables(contest, results_dir)

            pbar.update(1)
            if output_config.get('crossover_support', False):
                pbar.set_postfix_str("write crossover support table")
                write_out.write_opponent_crossover_tables(contest, results_dir)

            # free memory from cvr
            contest['cvr'] = None

            pbar.update(1)
            pbar.set_postfix_str("completed")

    # WRITE OUT AGGREGATED STATS

    print()
    print("Write stored results")
    if output_config.get('per_rcv_group_stats', False):
        print("write group stats ...")
        for group in rcv_group_stats_df_dict:
            if rcv_group_stats_df_dict[group]:
                df = pd.concat(rcv_group_stats_df_dict[group], axis=0, ignore_index=True, sort=False)
                df.to_csv(results_dir + '/group_' + group + '.csv', index=False)

    if output_config.get('per_rcv_group_stats_fvDBfmt', False):
        print("write group stats in fvDB order ...")
        for group in rcv_group_stats_df_dict:
            format_fpath = "extra/fv_db_format/" + group + "_columns.csv"
            if rcv_group_stats_df_dict[group] and os.path.isfile(format_fpath):

                # read in column order
                fmt_df = pd.read_csv(format_fpath)
                fmt_order = fmt_df['cruncher_col'].tolist()

                df = pd.concat(rcv_group_stats_df_dict[group], axis=0, ignore_index=True, sort=False)
                df = df.reindex(fmt_order, axis=1)
                df.to_csv(results_dir + '/group_' + group + '_fvDBfmt.csv', index=False)

    if output_config.get('per_rcv_type_stats', False):
        print("Write tabulation stats ...")
        for variant in rcv_variant_stats_df_dict:
            if rcv_variant_stats_df_dict[variant]:
                df = pd.concat(rcv_variant_stats_df_dict[variant], axis=0, ignore_index=True, sort=False)
                df.to_csv(results_dir + '/' + variant + '.csv', index=False)

    if output_config.get('candidate_details', False):
        print("Write candidate details ...")
        df = pd.concat(util.flatten_list(candidate_details_dfs), axis=0, ignore_index=True, sort=False)
        df.to_csv(results_dir + '/candidate_details.csv', index=False)

    # WRITE OUT INFORMATION ON CONTESTS THAT DID NOT PASS THE STATS CHECK

    # write out contest names that failed the stats check
    stats_debugs = util.flatten_list(stats_debugs)
    stats_f = open(stats_check_fname, 'w')
    for debug_str in stats_debugs:
        stats_f.write(debug_str[0] + "\n")
    stats_f.close()

    print(f"{len(stats_debugs)} contests failed the stats consistency check. They are listed in {stats_check_fname}")

    # make debug version of contest set
    if stats_debugs:

        debug_contest_set_fname = debug_contest_set_dir + '/contest_set.csv'
        pd.concat([t[1] for t in stats_debugs]).to_csv(debug_contest_set_fname, index=False)

        debug_output_config = debug_contest_set_dir + '/output_config.csv'
        shutil.copy2(output_config['file_path'], debug_output_config)

        print('Debug contest set created at ' + debug_contest_set_dir +
              '. Contests that have failed consistency checks have been copied there.')

    # CREATE A LOG FILE CONTAINED SCRIPTS USED IN THE GENERATION OF THESE RESULTS

    # copy scripts used for results generation into log file
    result_log_dir = f'{results_dir}/.record_log'
    util.verifyDir(result_log_dir)

    package_mod_dir = os.path.dirname(util.__file__)

    shutil.copytree(f'{package_mod_dir}/scripts', f'{package_mod_dir}/scripts')
    shutil.copytree(f'{package_mod_dir}/rcv_parsers', f'{package_mod_dir}/rcv_parsers')

    log_output_config = f'{results_dir}/output_config.csv'
    shutil.copy2(output_config['file_path'], log_output_config)

    log_contest_set_fname = f'{results_dir}/contest_set.csv'
    pd.concat([t[1] for t in stats_debugs]).to_csv(log_contest_set_fname, index=False)

    shutil.make_archive(result_log_dir, 'zip', result_log_dir)
    shutil.rmtree(result_log_dir)

    print("DONE!")
