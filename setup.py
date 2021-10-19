#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import io
import pathlib
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    with io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ) as fh:
        return fh.read()

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()


setup(
    name='rcv_cruncher',
    version='0.0.5',
    description='Analyze RCV elections',
    # long_description='%s\n%s' % (
    #     re.compile('^.. start-badges.*^.. end-badges', re.M | re.S).sub('', read('README.rst')),
    #     re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read('CHANGELOG.rst'))
    # ),
    long_description=README,
    long_description_content_type="text/markdown",
    #long_description="",
    author='Chris Zawora',
    author_email='christopher.zawora@gmail.com',
    url='https://github.com/fairvotereform/rcv_cruncher',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 5 - Production/Stable',
        # 'Intended Audience :: Developers',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        # 'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3 :: Only',
        # 'Programming Language :: Python :: 3.6',
        # 'Programming Language :: Python :: 3.7',
        # 'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        # uncomment if you test on these interpreters:
        # 'Programming Language :: Python :: Implementation :: IronPython',
        # 'Programming Language :: Python :: Implementation :: Jython',
        # 'Programming Language :: Python :: Implementation :: Stackless',
        'Topic :: Utilities',
    ],
    project_urls={
        'Documentation': 'https://rcv_cruncher.readthedocs.io/',
        'Changelog': 'https://rcv_cruncher.readthedocs.io/en/latest/changelog.html',
        'Issue Tracker': 'https://github.com/fairvotereform/rcv_cruncher/issues',
    },
    keywords=[
        # eg: 'keyword1', 'keyword2', 'keyword3',
    ],
    python_requires='>=3.6',
    install_requires=[
        'tqdm>=4.56.0',
        'pandas>=1.2.0',
        'xmltodict>=0.12.0',
        'weightedstats>=0.4.1',
        'pytest>=6.2.4',
        'rcvformats==0.0.22'
    ],
    extras_require={},
    entry_points={
        'console_scripts': [
            'rcv-cruncher = rcv_cruncher.cli:main',
        ]
    },
)
