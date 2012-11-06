RCV Cruncher
============

A script for generating stats on RCV elections.

To process an election, you must first create a configuration file for the
election you would like to process.  See the section below on configuration
files for more details.

Here is sample command-line usage:

    python crunch config_20101102.yaml data

The last string ("data" in this case) is the directory that the script
will download the ballot data to.  Try looking in this directory after
the program runs successfully or unsuccessfully just to see where it
puts things, etc.

TODO: document how to run the script without auto-download (e.g. by
specifying the path to a directory containing the two data files).

The Configuration File
----------------------

This section contains information about setting up the configuration file
to process an election.

See the `input/` directory of the repository for examples of configuration
files (e.g. from past San Francisco elections).

Since the script does not tabulate winners, winners and finalists must be specified manually in the configuration file (e.g. using the results reported from another source or application).

The value of the configuration path `input_format/type` can be one of the
following two values:

* `sf-2008` (for the current SF format)
* `rcv-calc` (which was used to process pre-2008 SF elections)
