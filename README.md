RCV Cruncher
============

A script for generating stats on RCV elections.

To process an election, a configuration file must be created for the election you would like to process.  See the `input/` directory for examples of configuration files (e.g. from past San Francisco elections).

Note that the script does not tabulate winners.  Winners and finalists must be specified manually in the configuration file (e.g. using the results reported from another source or application).

Here is sample command-line usage:

    python crunch config_20101102.yaml data

The last string ("data" in this case) is the directory that the script
will download the ballot data to.  Try looking in this directory after
the program runs successfully or unsuccessfully just to see where it
puts things, etc.

TODO: document how to run the script without auto-download (e.g. by
specifying the path to a directory containing the two data files).

