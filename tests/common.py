# -*- coding: utf-8 -*-
import sys

if sys.version_info[:2] > (2, 6):
    import unittest
else:
    try:
        import unittest2 as unittest
    except ImportError:
        message = 'tests require `unittest2` for Python 2.6 and earlier'
        raise ImportError(message)

try:
    import sqlite3  # Not included in Jython.
except ImportError:
    sqlite3 = None

try:
    import squint
except ImportError:
    squint = None

try:
    import dbfread
except ImportError:
    dbfread = None

try:
    import pandas
except ImportError:
    pandas = None

try:
    import xlrd
except ImportError:
    xlrd = None


#######################################
# Python version compatibility helpers.
#######################################

PY2 = sys.version_info[0] == 2


try:
    FileNotFoundError = FileNotFoundError  # New in 3.3
except NameError:
    FileNotFoundError = IOError


try:
    unichr  # unichr() only defined in Python 2
except NameError:
    unichr = chr  # chr() is Unicode-aware in Python 3


####################################
# Sample Unicode values for testing.
####################################

unicode_ash = unichr(0xe6)              # æ (Old English ash)
unicode_eth = unichr(0xf0)              # ð (Old English eth)
unicode_thorn = unichr(0xfe)            # þ (Old English thorn)
unicode_alpha = unichr(0x003b1)         # α (Greek alpha)
unicode_om = unichr(0x00950)            # ॐ (Devanagari Om)
try:
    unicode_math_a = unichr(0x1d538)    # 𝔸 (mathematical double-struck A)
except ValueError:
    # To support older "narrow" (2-byte character) builds
    # of Python, we use a "surrogate pair" to represent "𝔸".
    unicode_math_a = unichr(0xd835) + unichr(0xdd38)
