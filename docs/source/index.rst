.. rcv-cruncher documentation master file, created by
   sphinx-quickstart on Mon May 17 18:26:24 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to rcv-cruncher's documentation!
========================================

The **rcv-cruncher** python package contains tools for analyzing ranked choice voting **cast vote record** election data. Some of its features include:

- tools to read many of the current and historical cast vote record file formats used in US RCV elections and convert them into Excel-friendly csv files
- tabulation methods for various RCV variants in use throughout the US (single winner IRV, multi winner STV, etc)
- a variety of useful statistics calculated for each election including (e.g. number of ballots inactivated and the cause of inactivation, rank usage distribution by candidate, condorcet tables, ...)
- the ability to analyze elections in batches

To get started follow the installation instructions below, then check out the how-to guides to explore the package's features.

Installation
------------

**rcv-cruncher** requires Python version >= 3.9

Install using :code:`pip`:

.. code-block:: python

   pip install rcv-cruncher

Further Documentation
---------------------

.. toctree::
   :maxdepth: 1

   how-tos/index
   tabulation
   statistics
   api

This package is a project of `FairVote <https://www.fairvote.org/>`_. The source code is available on `github <https://github.com/fairvotereform/rcv_cruncher>`_.
