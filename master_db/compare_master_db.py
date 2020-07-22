import os
import pandas as pd
from argparse import ArgumentParser
from scripts.definitions import project_root, verifyDir

def compare_with_db(cruncher_path, db_path, matches_path, diff_out_path, grid_out_path):
    """
    Compare each cell in cruncher results and master db
    """

    # read in tables
    cruncher_df = pd.read_csv(cruncher_path)
    cruncher_df = cruncher_df.drop([0, 1])
    db_df = pd.read_csv(db_path)
    matches_df = pd.read_csv(matches_path)

    join_cols = ['place', 'date', 'office']

    # make join index column
    cruncher_df['join_col'] = cruncher_df[join_cols].agg('_'.join, axis=1)
    cruncher_df.set_index('join_col', drop=False, inplace=True, verify_integrity=True)
    cruncher_dict = cruncher_df.to_dict(orient='index')

    db_df['join_col'] = db_df[join_cols].agg('_'.join, axis=1)
    db_df.set_index('join_col', drop=False, inplace=True, verify_integrity=True)
    db_dict = db_df.to_dict(orient='index')

    mismatch_checks = []
    cols = ['cruncher_id', 'cruncher_column', 'db_column', 'cruncher_value (round 1 decimal)', 'db_value (round 1 decimal)', 'note']

    # loop through cruncher results
    for row_id in cruncher_dict:

        if row_id not in db_dict:
            mismatch_checks.append(pd.DataFrame([[cruncher_dict[row_id]['unique_id'], 'all_columns', 'all_columns',
                                                  '', '', 'cruncher_id not present in file']], columns=cols))
            continue
        else:
            for match_idx, match_row in matches_df.iterrows():

                cruncher_col = match_row['cruncher_column']
                db_col = match_row['db_column']

                cruncher_val = cruncher_dict[row_id][cruncher_col]
                db_val = db_dict[row_id][db_col]

                # clean strings and convert to numbers if necessary
                if isinstance(cruncher_val, str):
                    cruncher_val = cruncher_val.replace(",", "").lower().strip("%")
                    if cruncher_val.replace(".", "", 1).isdigit():
                        cruncher_val = float(cruncher_val)
                    else:
                        cruncher_val = cruncher_val.replace(".", "")

                if isinstance(db_val, str):
                    db_val = db_val.replace(",", "").lower().strip("%")
                    if db_val.replace(".", "", 1).isdigit():
                        db_val = float(db_val)
                    else:
                        db_val = db_val.replace(".", "")

                mismatch_msg = "same"
                if isinstance(cruncher_val, float) and isinstance(db_val, float):
                    cruncher_val_orig = cruncher_val
                    db_val_orig = db_val
                    cruncher_val = round(cruncher_val, 1)
                    db_val = round(db_val, 1)
                    if cruncher_val != db_val:
                        mismatch_msg = "mismatch"
                        if round(cruncher_val_orig, 0) == round(db_val_orig, 0):
                            mismatch_msg = "mismatch w/o more rounding"

                if isinstance(cruncher_val, str) and isinstance(db_val, str):
                    if cruncher_val != db_val:
                        mismatch_msg = "mismatch"

                if mismatch_msg != "same":
                    mismatch_checks.append(
                        pd.DataFrame([[cruncher_dict[row_id]['unique_id'], cruncher_col, db_col,
                                       cruncher_val, db_val, mismatch_msg]], columns=cols))

    all_mismatch_checks = pd.concat(mismatch_checks)
    all_mismatch_checks.to_csv(diff_out_path, index=False)

    id_set = list(set(all_mismatch_checks['cruncher_id']))
    cruncher_col_set = list(set(all_mismatch_checks['cruncher_column']))

    where_diff_df = pd.DataFrame(columns=['cruncher_id'] + cruncher_col_set, index=id_set + ['colsum'])
    where_diff_df['cruncher_id'] = id_set + ['colsum']

    for id in id_set:
        for col in cruncher_col_set:
            if any((all_mismatch_checks['cruncher_id'] == id) & (all_mismatch_checks['cruncher_column'] == col)):
                where_diff_df.loc[id, col] = 1

    colsums = where_diff_df.sum(axis=0)
    for col in cruncher_col_set:
        where_diff_df.loc['colsum', col] = colsums[col]

    if sum(where_diff_df.loc['colsum', cruncher_col_set]) != all_mismatch_checks.shape[0]:
        print("mismatch")
        raise RuntimeError

    where_diff_df.to_csv(grid_out_path, index=False)

def run_comparisons(contest_set):
    """
    Compare single winner and multi winner cruncher results with master db
    """

    # paths to cruncher results
    cruncher_single_winner_path = "contest_sets/" + contest_set + "/results/group_single_winner.csv"
    cruncher_multi_winner_path = "contest_sets/" + contest_set + "/results/group_multi_winner.csv"

    # paths to master db and column matchings
    db_single_winner_path = "master_db/single_winner.csv"
    db_single_winner_columns_path = "master_db/single_winner_columns.csv"

    db_multi_winner_path = "master_db/multi_winner.csv"
    db_multi_winner_columns_path = "master_db/multi_winner_columns.csv"

    single_winner_diff_output_path = "master_db/" + contest_set + "_single_winner_masterDB_check_diff.csv"
    multi_winner_diff_output_path = "master_db/" + contest_set + "_multi_winner_masterDB_check_diff.csv"
    single_winner_grid_output_path = "master_db/" + contest_set + "_single_winner_masterDB_check_grid.csv"
    multi_winner_grid_output_path = "master_db/" + contest_set + "_multi_winner_masterDB_check_grid.csv"

    # compare single winner results
    print("compare cruncher results and master db: single winner")
    if (os.path.isfile(cruncher_single_winner_path) and
        os.path.isfile(db_single_winner_path) and
        os.path.isfile(db_single_winner_columns_path)):

        compare_with_db(cruncher_single_winner_path, db_single_winner_path,
                        db_single_winner_columns_path, single_winner_diff_output_path, single_winner_grid_output_path)

    else:
        if not os.path.isfile(cruncher_single_winner_path):
            print("- single winner cruncher results not present. (" + cruncher_single_winner_path + ")")
        if not os.path.isfile(db_single_winner_path):
            print("- single winner master db results not present. (" + db_single_winner_path + ")")
        if not os.path.isfile(db_single_winner_columns_path):
            print("- single winner column matches not present. (" + db_single_winner_columns_path + ")")

    # compare multi winner results
    print("compare cruncher results and master db: multi winner")
    if (os.path.isfile(cruncher_multi_winner_path) and
            os.path.isfile(db_multi_winner_path) and
            os.path.isfile(db_multi_winner_columns_path)):

        compare_with_db(cruncher_multi_winner_path, db_multi_winner_path,
                        db_multi_winner_columns_path, multi_winner_diff_output_path, multi_winner_grid_output_path)

    else:
        if not os.path.isfile(cruncher_multi_winner_path):
            print("- multi winner cruncher results not present. (" + cruncher_multi_winner_path + ")")
        if not os.path.isfile(db_multi_winner_path):
            print("- multi winner master db results not present. (" + db_multi_winner_path + ")")
        if not os.path.isfile(db_multi_winner_columns_path):
            print("- multi winner column matches not present. (" + db_multi_winner_columns_path + ")")

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

    run_comparisons(contest_set_name)

if __name__ == '__main__':
    main()
