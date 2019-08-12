#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ast
import os
import setuptools


WORKING_DIR = os.path.dirname(os.path.abspath(__file__))


def get_version(filename):
    """Return __version__ from *filename*."""
    with open(os.path.join(WORKING_DIR, filename)) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith('__version__'):
                return ast.parse(line).body[0].value.s
    raise Exception('Unable to find __version__ attribute.')


def get_long_description(filename):
    """Return entire contents of *filename*."""
    with open(os.path.join(WORKING_DIR, filename)) as fh:
        return fh.read()


setuptools.setup(
    # Required fields:
    name='get_reader',
    version=get_version('get_reader.py'),
    description='Simple interface to get reader-like objects for Python 3 and 2.',
    py_modules=['get_reader'],

    # Recommended fields:
    url='https://github.com/shawnbrown/get_reader',
    author='Shawn Brown',
    author_email='shawnbrown@users.noreply.github.com',

    # Optional fields:
    install_requires=[],  # <- No hard requirements!
    extras_require={
        'excel': ['xlrd'],
        'dbf': ['dbfread'],
    },
    long_description=get_long_description('README.md'),
    long_description_content_type='text/markdown',
    license='Apache 2.0',
    python_requires='>=2.6.*, !=3.0.*, !=3.1.*',
    classifiers  = [
        'License :: OSI Approved :: Apache Software License',
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: Jython',
        'Operating System :: OS Independent',
        'Topic :: Utilities',
    ],
)
