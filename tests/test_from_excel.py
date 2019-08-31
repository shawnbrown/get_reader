# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
from .common import (
    unittest,
    xlrd,
)

from get_reader import _from_excel


@unittest.skipIf(not xlrd, 'xlrd not found')
class TestFromExcel(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.filepath = os.path.join(dirname, 'sample_multiworksheet.xlsx')

    def test_default_worksheet(self):
        reader, _ = _from_excel(self.filepath)  # <- Defaults to 1st worksheet.

        expected = [
            ['col1', 'col2'],
            [1, 'a'],
            [2, 'b'],
            [3, 'c'],
        ]
        self.assertEqual(list(reader), expected)

    def test_specified_worksheet(self):
        reader, _ = _from_excel(self.filepath, 'Sheet2')  # <- Specified worksheet.

        expected = [
            ['col1', 'col2'],
            [4, 'd'],
            [5, 'e'],
            [6, 'f'],
        ]
        self.assertEqual(list(reader), expected)
