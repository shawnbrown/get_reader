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
    def test_dbf(self):
        dirname = os.path.dirname(__file__)
        filepath = os.path.join(dirname, 'sample_dbase.dbf')

        reader = _from_dbf(filepath, encoding=None)
        expected = [
            ['COL1', 'COL2'],
            ['dBASE', 1],
        ]
        self.assertEqual(list(reader), expected)
