Parsing and converting a CVR
============================

Cast vote record files come in all kinds of file formats. Often it can be handy to covert a CVR into a more easily shareable format, such as a Excel-friendly csv file. The first step to performing this conversion with the rcv-cruncher package is selecting a parser function to use in reading the format of CVR you have. The package has several parsers implemented (you can see the full list in the parsers module :mod:`parsers`).

Parse
-------

Once you've found the one that matches your CVR file(s), you can use it to create a :class:`cvr.base.CastVoteRecord` object. In the example below, I am parsing the `2017 Minneapolis mayoral election <https://github.com/fairvotereform/rcv_cruncher/tree/big_changes/src/rcv_cruncher/example/example_cvr/minneapolis2017/2017-mayor-cvr.csv>`_

.. code-block::

   from rcv_cruncher import CastVoteRecord, rank_column_csv
   from pathlib import Path

   # CVR file assumed to be downloaded and in current working directory
   cvr_file = Path.cwd() / '2017-mayor-cvr.csv'

   # initialize the object with optional details about the election (state, date, office, ..)
   # along with the parser function and parser function arguments. As described in the
   # documentation the only argument for this parser is the path to the CVR file.
   cvr = CastVoteRecord(
        jurisdiction='Minneapolis',
        state='MN',
        year='2017',
        office='Mayor',
        parser_func=rank_column_csv,
        parser_args={'cvr_path': cvr_file}
   )

Convert
--------

The constructor will parse the CVR. The next step is to write out a converted version of it. There are two conversions that are available: rank column format and candidate column format. Examples for each are show below. (More details on each conversion format can be learned from looking at their respective parser functions in :mod:`parsers`)

rank column format
^^^^^^^^^^^^^^^^^^

The rank column format has rank numbers as column names with candidate names appearing in row cells. Each row is one ballot.

.. code-block::

   # an output directory, rooted in current working directory
   out_dir = Path.cwd() / 'output/minneapolis2017/rank'

   # rank column format
   CastVoteRecord.write_cvr_table(cvr, out_dir, table_format='rank')

   # the file written to out_dir will have an automatically
   # generated name following the format {jurisdiction}_{year}_{office}.csv.

candidate column format
^^^^^^^^^^^^^^^^^^^^^^^

The candidate column format has candidate names as column names with candidate rank numbers appearing in row cells. Each row is one ballot.

.. code-block::

   # an output directory, rooted in current working directory
   out_dir = Path.cwd() / 'output/minneapolis2017/candidate'

   # candidate column format
   CastVoteRecord.write_cvr_table(cvr, out_dir, table_format='candidate')

   # the file written to out_dir will have an automatically
   # generated name following the format {jurisdiction}_{year}_{office}.csv.
