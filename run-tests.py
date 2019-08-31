#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys

sys.dont_write_bytecode = True
from tests.common import unittest


if __name__ == '__main__':
    # Handle test-discovery explicitly for Python 2.6 compatibility.
    start_dir = os.path.abspath(os.path.dirname(__file__))
    testsuite = unittest.TestLoader().discover(start_dir)
    result = unittest.TextTestRunner().run(testsuite)
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
