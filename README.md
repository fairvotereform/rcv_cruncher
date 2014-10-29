RCV Cruncher
============

A script for generating stats on RCV elections.


Setup
-----

Use Python 2.7.

Install dependencies:

    $ pip install PyYAML pystache


Usage
-----

For command-line usage help (running from the repo root):

    $ python crunch --help

To process an election, you must first create a configuration file for the
election you would like to process.  See the section below on configuration
files for more details.

Here is sample command-line usage which will be used to process SF 2012:

    python crunch input/SF_201211.yaml data output

Running the script does the following.  For each contest listed in the
configuration file, it--

1. Downloads the zip file for the contest from an URL in the config file.
   (This step can be suppressed with a command-line option.)
2. Extracts the contents of the zip file into a directory.
3. Detects the "master" and "ballot" files from file name globs in the
   config file.
4. Reads and analyzes the files.
5. Outputs the analysis to an HTML file.

The last string in the sample command usage ("data" in this case) is the
directory that the script will download the ballot data to.  Try looking in
this directory after the program runs successfully or unsuccessfully just to
see where it puts things, etc.


Config File
-----------

This section contains information about setting up the configuration file
to process an election.

See the `input/` directory of the repository for examples of configuration
files (e.g. from past San Francisco elections).

The configuration files are in a [JSON](http://www.json.org/)-like format
called [YAML](http://www.yaml.org/).  YAML is somewhat richer and more
flexible than JSON.

Since the script does not tabulate winners, winners and finalists must be specified manually in the configuration file (e.g. using the results reported from another source or application).

The value of the configuration path `input_format/type` can be one of the
following two values:

* `sf-2008` (for the current SF format)
* `rcv-calc` (which was used to process pre-2008 SF elections)
