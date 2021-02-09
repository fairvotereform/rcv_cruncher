========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |requires|
        | |coveralls| |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/rcv_cruncher/badge/?style=flat
    :target: https://readthedocs.org/projects/rcv_cruncher
    :alt: Documentation Status

.. |requires| image:: https://requires.io/github/fairvotereform/rcv_cruncher/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/fairvotereform/rcv_cruncher/requirements/?branch=master

.. |coveralls| image:: https://coveralls.io/repos/fairvotereform/rcv_cruncher/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/r/fairvotereform/rcv_cruncher

.. |codecov| image:: https://codecov.io/gh/fairvotereform/rcv_cruncher/branch/master/graphs/badge.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/fairvotereform/rcv_cruncher

.. |version| image:: https://img.shields.io/pypi/v/rcv-cruncher.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/rcv_cruncher

.. |wheel| image:: https://img.shields.io/pypi/wheel/rcv-cruncher.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/rcv_cruncher

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/rcv-cruncher.svg
    :alt: Supported versions
    :target: https://pypi.org/project/rcv_cruncher

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/rcv-cruncher.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/rcv_cruncher

.. |commits-since| image:: https://img.shields.io/github/commits-since/fairvotereform/rcv_cruncher/v0.0.0.svg
    :alt: Commits since latest release
    :target: https://github.com/fairvotereform/rcv_cruncher/compare/v0.0.0...master



.. end-badges

Analyze RCV elections

Installation
============

::

    pip install rcv_cruncher

You can also install the in-development version with::

    pip install https://github.com/fairvotereform/rcv_cruncher/archive/master.zip


Documentation
=============


https://rcv_cruncher.readthedocs.io/


Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
