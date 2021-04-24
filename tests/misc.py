

import rcv_cruncher.batch as batch


# read in contest set info
contest_set, run_config = batch.read_contest_set('../rcv_cruncher_test/single_winner_choice_distrib')

# analyze contests
batch.crunch_contest_set(contest_set, run_config, '../rcv_cruncher_test/single_winner_choice_distrib', fresh_output=False)
