Tabulating an RCV election
==========================

Tabulating a ranked choice voting election from a CVR requires knowing:
 * the parser for the CVR
 * the tabulation method you want to use
 * the election rules you want to apply

The following examples demonstrate how to create an RCV object, tabulate the election, and write out a round-by-round table of the results (or a json version of results for use on the `RCVIS <https://www.rcvis.com/>`_ site).

Single Winner
-------------

This example uses the `2017 Minneapolis mayoral election <https://github.com/fairvotereform/rcv_cruncher/tree/big_changes/src/rcv_cruncher/example/example_cvr/minneapolis2017/2017-mayor-cvr.csv>`_. It is a single winner race, the CVR is stored in rank column csv format, and the election has does not have special ballot exhaustion rules (like exhaustion by overvote).

.. code-block:: py

   from rcv_cruncher import SingleWinner, rank_column_csv
   from pathlib import Path

   # CVR file assumed to be downloaded and in current working directory
   cvr_file = Path.cwd() / '2017-mayor-cvr.csv'
   out_dir = Path.cwd() / 'output/minneapolis2017'

   # the constructor for the election class will run the tabulation
   election = SingleWinner(
        jurisdiction='Minneapolis',
        state='MN',
        year='2017',
        office='Mayor',
        parser_func=rank_column_csv,
        parser_args={'cvr_path': cvr_file},
        exhaust_on_duplicate_candidate_marks=False,
        exhaust_on_overvote_marks=False,
        exhaust_on_N_repeated_skipped_marks=0
    )

   # save a csv table of the results to out_dir
   SingleWinner.write_round_by_round_table(election, out_dir)

   # or the json for RCVIS
   SingleWinner.write_round_by_round_json(election, out_dir)


Multi Winner
-------------

This example uses the `2017 Minneapolis election for the Board of Estimates and Taxation <https://github.com/fairvotereform/rcv_cruncher/tree/big_changes/src/rcv_cruncher/example/example_cvr/minneapolis2017/2017-boe-cvr.csv>`_. It is a two winner election using STV with fractional ballot transfer, the CVR is stored in rank column csv format, and, like the mayoral election above, does not have special ballot exhaustion rules (like exhaustion by overvote).

.. code-block:: py

   from rcv_cruncher import STVFractionalBallot, rank_column_csv
   from pathlib import Path

   # CVR file assumed to be downloaded and in current working directory
   cvr_file = Path.cwd() / '2017-boe-cvr.csv'
   out_dir = Path.cwd() / 'output/minneapolis2017'

   # the constructor for the election class will run the tabulation
   election = STVFractionalBallot(
        jurisdiction='Minneapolis',
        state='MN',
        year='2017',
        office='Board of Estimates and Taxation',
        parser_func=rank_column_csv,
        parser_args={'cvr_path': cvr_file},
        exhaust_on_duplicate_candidate_marks=False,
        exhaust_on_overvote_marks=False,
        exhaust_on_N_repeated_skipped_marks=0,
        n_winners=2
    )

   # save a csv table of the results to out_dir
   STVFractionalBallot.write_round_by_round_table(election, out_dir)

   # or the json for RCVIS
   STVFractionalBallot.write_round_by_round_json(election, out_dir)
