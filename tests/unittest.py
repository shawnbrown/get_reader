# -*- coding: utf-8 -*-
"""compatibility layer to handle importing unittest or unittest2"""
from __future__ import absolute_import
import sys as _sys

if _sys.version_info[:2] < (2, 7):
    try:
        from unittest2 import *
    except ImportError:
        message = 'tests require `unittest2` for Python 2.6 and earlier'
        raise ImportError(message)
else:
    from unittest import *
