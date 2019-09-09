# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
from .common import (
    unittest,
    dbfread,
)

from get_reader import _from_dbf


@unittest.skipIf(not dbfread, 'dbfread not found')
class TestFromDbf(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.filepath = os.path.join(dirname, 'sample_dbase.dbf')

    def test_dbf(self):
        reader, _ = _from_dbf(self.filepath, encoding=None)
        expected = [
            ['COL1', 'COL2'],
            ['dBASE', 1],
        ]
        self.assertEqual(list(reader), expected)

    def test_close_function(self):
        reader, close_function = _from_dbf(self.filepath, encoding=None)

        self.assertEqual(next(reader), ['COL1', 'COL2'])
        close_function()  # <- Close before next row!
        self.assertEqual(list(reader), [])
