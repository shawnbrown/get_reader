#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import io
import os
import sys
import unittest

try:
    import xlrd
except ImportError:
    xlrd = None

from get_reader import from_csv
from get_reader import from_excel


PY3 = sys.version_info[0] == 3

if not PY3:
    chr = unichr


def emulate_fh(string, encoding=None):
    """Test-helper to return file-like object for *string* data.

    In Python 2, Unicode files should be opened in binary-mode but
    in Python 3, they should be opened in text-mode. This function
    emulates the appropriate mode using the file-like stream objects.
    """
    fh = io.BytesIO(string)
    if not PY3:
        return fh
    return io.TextIOWrapper(fh, encoding=encoding)


class TestFromCsv(unittest.TestCase):
    def test_file_ascii(self):
        fh = emulate_fh((
            b'col1,col2\n'
            b'1,a\n'
            b'2,b\n'
            b'3,c\n'
        ), encoding='ascii')

        reader = from_csv(fh, encoding='ascii')
        self.assertTrue(isinstance(reader, csv.DictReader))

        expected = [
            {'col1': '1', 'col2': 'a'},
            {'col1': '2', 'col2': 'b'},
            {'col1': '3', 'col2': 'c'},
        ]
        self.assertEqual(list(reader), expected)

    def test_file_iso88591(self):
        fh = emulate_fh((
            b'col1,col2\n'
            b'1,\xe6\n'  # '\xe6' -> æ (ash)
            b'2,\xf0\n'  # '\xf0' -> ð (eth)
            b'3,\xfe\n'  # '\xfe' -> þ (thorn)
        ), encoding='iso8859-1')

        reader = from_csv(fh, encoding='iso8859-1')
        self.assertTrue(isinstance(reader, csv.DictReader))

        expected = [
            {'col1': '1', 'col2': chr(0xe6)},  # chr(0xe6) -> æ
            {'col1': '2', 'col2': chr(0xf0)},  # chr(0xf0) -> ð
            {'col1': '3', 'col2': chr(0xfe)},  # chr(0xfe) -> þ
        ]
        self.assertEqual(list(reader), expected)

    def test_file_utf8(self):
        fh = emulate_fh((
            b'col1,col2\n'
            b'1,\xce\xb1\n'          # '\xce\xb1'         -> α (Greek alpha)
            b'2,\xe0\xa5\x90\n'      # '\xe0\xa5\x90'     -> ॐ (Devanagari Om)
            b'3,\xf0\x9d\x94\xb8\n'  # '\xf0\x9d\x94\xb8' -> 𝔸 (mathematical double-struck A)
        ), encoding='utf-8')

        reader = from_csv(fh, encoding='utf-8')
        self.assertTrue(isinstance(reader, csv.DictReader))

        expected = [
            {'col1': '1', 'col2': chr(0x003b1)},  # chr(0x03b1)  -> α
            {'col1': '2', 'col2': chr(0x00950)},  # chr(0x0950)  -> ॐ
            {'col1': '3', 'col2': chr(0x1d538)},  # chr(0x1d538) -> 𝔸
        ]
        self.assertEqual(list(reader), expected)

    def test_iterable(self):
        iterable = iter([
            'col1,col2',
            '1,a',
            '2,b',
            '3,c',
        ])

        if PY3:
            reader = from_csv(iterable, encoding='ascii')
            self.assertTrue(isinstance(reader, csv.DictReader))

            expected = [
                {'col1': '1', 'col2': 'a'},
                {'col1': '2', 'col2': 'b'},
                {'col1': '3', 'col2': 'c'},
            ]
            self.assertEqual(list(reader), expected)
        else:
            # Using old assertRaises syntax for Python 2.6 support.
            def fn():
                reader = from_csv(iterable, encoding='ascii')
            self.assertRaises(TypeError, fn)


class TestFromExcel(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.filepath = os.path.join(dirname, 'sample_file.xlsx')

    def test_default_worksheet(self):
        if not xlrd:
            return

        reader = from_excel(self.filepath)  # <- Defaults to 1st worksheet.

        expected = [
            {'col1': 1, 'col2': 'a'},
            {'col1': 2, 'col2': 'b'},
            {'col1': 3, 'col2': 'c'},
        ]
        self.assertEqual(list(reader), expected)

    def test_specified_worksheet(self):
        if not xlrd:
            return

        reader = from_excel(self.filepath, 'Sheet2')  # <- Specified worksheet.

        expected = [
            {'col1': 4, 'col2': 'd'},
            {'col1': 5, 'col2': 'e'},
            {'col1': 6, 'col2': 'f'},
        ]
        self.assertEqual(list(reader), expected)


if __name__ == '__main__':
    unittest.main()
