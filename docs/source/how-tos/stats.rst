Computing CVR and RCV stats
===========================

A default set of statistics can obtained for either a CVR or and RCV election. To see the default list check :ref:`statistics_list`.

CVR stats
---------

This example uses the `2017 Minneapolis mayoral election <https://github.com/fairvotereform/rcv_cruncher/tree/big_changes/src/rcv_cruncher/example/example_cvr/minneapolis2017/2017-mayor-cvr.csv>`_

.. code-block:: py

   from rcv_cruncher import CastVoteRecord, rank_column_csv
   from pathlib import Path

   # CVR file assumed to be downloaded and in current working directory
   cvr_file = Path.cwd() / '2017-mayor-cvr.csv'

   # the constructor for the election class will run the tabulation
   cvr = CastVoteRecord(
        jurisdiction='Minneapolis',
        state='MN',
        year='2017',
        office='Mayor',
        parser_func=rank_column_csv,
        parser_args={'cvr_path': cvr_file},
        split_fields=['Precinct'] # add split field column name
    )

   # receive a pandas dataframes with statistics
   stats = cvr.get_stats()

   # add rows to output dataframe for each split category
   stats = cvr.get_stats(add_split_stats=True)

RCV stats
---------

This example uses the `2017 Minneapolis election for the Board of Estimates and Taxation <https://github.com/fairvotereform/rcv_cruncher/tree/big_changes/src/rcv_cruncher/example/example_cvr/minneapolis2017/2017-boe-cvr.csv>`_. It is a three winner election using STV with fractional ballot transfer, the CVR is stored in rank column csv format, and, like the mayoral election above, does not have special ballot exhaustion rules (like exhaustion by overvote).

.. code-block:: py

   from rcv_cruncher import STVFractionalBallot, rank_column_csv
   from pathlib import Path

   # CVR file assumed to be downloaded and in current working directory
   cvr_file = Path.cwd() / '2017-boe-cvr.csv'

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
        n_winners=2,
        split_fields=['Precinct'] # add split field column name
    )

   # receive list of pandas dataframes with statistics
   stats = election.get_stats()

   # add rows to output dataframes for each split category
   stats = election.get_stats(add_split_stats=True)
