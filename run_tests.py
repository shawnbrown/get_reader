#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys


if sys.version_info[:2] < (2, 7):
    try:
        import unittest2 as unittest
    except ImportError:
        message = 'tests require `unittest2` for Python 2.6 and earlier'
        raise ImportError(message)
else:
    import unittest


if __name__ == '__main__':
    # Handle test-discovery explicitly for Python 2.6.
    start_dir = os.path.abspath(os.path.dirname(__file__))
    testsuite = unittest.TestLoader().discover(start_dir)
    unittest.TextTestRunner().run(testsuite)
