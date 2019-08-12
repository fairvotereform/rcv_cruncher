Invocation:
To calculate selected stats on selected elections do:
python3 crunch.py

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
This file contains election data for crunch.py. They contain the path of 
the raw ballot data, rules about the election (whether to truncate the ballot
at the first overvote, or consecutive undervote). Defaults to the rules, and
other starter stats are defined as functions in crunch.py

TODO:

- Further generalize to incorporate other sources besides ballot images
- Allow user to search for stats/elections to use
- More flexibility in save decorator
    - add ability to handle partials
    - add ability to invalidate cache based on custom function
        (turn save into a function that returns a decorator)
- Make it easier to create excerpts that do one particular thing

