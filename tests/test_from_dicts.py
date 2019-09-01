# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .common import (
    unittest,
)

from get_reader import _from_dicts


class TestFromDicts(unittest.TestCase):
    def test_dict_records_using_fieldnames(self):
        records = [
            {'col1': 1, 'col2': 'a'},
            {'col1': 2, 'col2': 'b'},
            {'col1': 3, 'col2': 'c'},
        ]
        reader = _from_dicts(records, ['col1', 'col2'])  # <- Using fieldnames!

        expected = [
            ['col1', 'col2'],
            [1, 'a'],
            [2, 'b'],
            [3, 'c'],
        ]
        self.assertEqual(list(reader), expected)

    def test_dict_records_without_fieldnames(self):
        records = [
            {'col1': 1, 'col2': 'a'},
            {'col1': 2, 'col2': 'b'},
            {'col1': 3, 'col2': 'c'},
        ]
        reader = _from_dicts(records)  # <- No fieldnames supplied.

        reader = list(reader)
        if reader[0][0] == 'col1':  # Check for key order
            expected = [            # (not guaranteed in
                ['col1', 'col2'],   # older versions of
                [1, 'a'],           # Python).
                [2, 'b'],
                [3, 'c'],
            ]
        else:
            expected = [
                ['col2', 'col1'],
                ['a', 1],
                ['b', 2],
                ['c', 3],
            ]
        self.assertEqual(reader, expected)

    def test_empty_records(self):
        records = []
        reader = _from_dicts(records)
        self.assertEqual(list(records), [])

        reader = _from_dicts(records, ['col1', 'col2'])
        self.assertEqual(list(records), [])
