Invocation:
To calculate selected stats on selected elections do:
python3 crunch.py -s [stats] -e [elections]
You may leave out the -s to choose all stats and/or leave out -e to choose all
elections

file descriptions:
crunch.py:
This file contains functions for calculating stats on individual contests.

Some of these stats depend on other stats to be calculated beforehand.
Because of this, each 'stat' functions takes a single argument, a python
dictionary, referred to as a 'ctx', which contains all information computed
about a contest. When a stat function is called, the @save and @tmpsave wrappers
first check to see if the stat has been already calculated. @save writes results
to a .pickle file so that computations can be saved between sessions.

parsers.py:
This file contains functions for generating a list of ballots (each itself
represented as a list). There are functions in this file for generating
ballots from many different juristictions, Santa Fe, Cambridge, San Francisco,
etc., etc.

manifest.py:
This file contains 'starter' contexts for crunch.py. They contain the path of 
the raw ballot data, rules about the election (whether to truncate the ballot
at the first overvote, or consecutive undervote). Defaults to the rules, and
other starter stats are defined as functions in crunch.py

TODO:
Expand ability of parsers to retrive more metadata from ballot (e.g. voter id,
precinct).

Generalize to calculate stats about groups of elections

Generalize to incorporate other sources besides ballot images

Allow user to search for stats/elections to use

Improve cache-to-disk method to be simpler and more robust
- lean on git status or os modified time
- don't just blindly overwrite old file

Meaningful file paths?


