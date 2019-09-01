# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .common import (
    unittest,
    pandas,
)

from get_reader import _from_pandas


@unittest.skipIf(not pandas, 'pandas not found')
class TestDataFrame(unittest.TestCase):
    def setUp(self):
        self.df = pandas.DataFrame({
            'col1': (1, 2, 3),
            'col2': ('a', 'b', 'c'),
        })

    def test_automatic_indexing(self):
        reader = _from_pandas(self.df)  # <- Includes index by default.
        expected = [
            [None, 'col1', 'col2'],
            [0, 1, 'a'],
            [1, 2, 'b'],
            [2, 3, 'c'],
        ]
        self.assertEqual(list(reader), expected)

        reader = _from_pandas(self.df, index=False)  # <- Omits index.
        expected = [
            ['col1', 'col2'],
            [1, 'a'],
            [2, 'b'],
            [3, 'c'],
        ]
        self.assertEqual(list(reader), expected)

    def test_simple_index(self):
        self.df.index = pandas.Index(['x', 'y', 'z'], name='col0')

        reader = _from_pandas(self.df)
        expected = [
            ['col0', 'col1', 'col2'],
            ['x', 1, 'a'],
            ['y', 2, 'b'],
            ['z', 3, 'c'],
        ]
        self.assertEqual(list(reader), expected)

        reader = _from_pandas(self.df, index=False)
        expected = [
            ['col1', 'col2'],
            [1, 'a'],
            [2, 'b'],
            [3, 'c'],
        ]
        self.assertEqual(list(reader), expected)

    def test_multiindex(self):
        index_values = [('x', 'one'), ('x', 'two'), ('y', 'three')]
        index = pandas.MultiIndex.from_tuples(index_values, names=['A', 'B'])
        self.df.index = index

        reader = _from_pandas(self.df)
        expected = [
            ['A', 'B', 'col1', 'col2'],
            ['x', 'one', 1, 'a'],
            ['x', 'two', 2, 'b'],
            ['y', 'three', 3, 'c'],
        ]
        self.assertEqual(list(reader), expected)

        reader = _from_pandas(self.df, index=False)
        expected = [
            ['col1', 'col2'],
            [1, 'a'],
            [2, 'b'],
            [3, 'c'],
        ]
        self.assertEqual(list(reader), expected)


@unittest.skipIf(not pandas, 'pandas not found')
class TestSeries(unittest.TestCase):
    def test_automatic_indexing(self):
        s = pandas.Series(['a', 'b', 'c'], name='mycolumn')

        reader = _from_pandas(s)  # <- Includes index by default.
        expected = [
            [None, 'mycolumn'],
            [0, 'a'],
            [1, 'b'],
            [2, 'c'],
        ]
        self.assertEqual(list(reader), expected)

        reader = _from_pandas(s, index=False)  # <- Omits index.
        expected = [
            ['mycolumn'],
            ['a'],
            ['b'],
            ['c'],
        ]
        self.assertEqual(list(reader), expected)

    def test_simple_index(self):
        s = pandas.Series(
            data=['a', 'b', 'c'],
            index=pandas.Index(['x', 'y', 'z'], name='myindex'),
            name='mycolumn',
        )

        reader = _from_pandas(s)
        expected = [
            ['myindex', 'mycolumn'],
            ['x', 'a'],
            ['y', 'b'],
            ['z', 'c'],
        ]
        self.assertEqual(list(reader), expected)

        reader = _from_pandas(s, index=False)
        expected = [
            ['mycolumn'],
            ['a'],
            ['b'],
            ['c'],
        ]
        self.assertEqual(list(reader), expected)

    def test_multiindex(self):
        multiindex = [('x', 'one'), ('x', 'two'), ('y', 'three')]
        multiindex = pandas.MultiIndex.from_tuples(multiindex, names=['A', 'B'])
        s = pandas.Series(
            data=['a', 'b', 'c'],
            index=multiindex,
            name='mycolumn',
        )

        reader = _from_pandas(s)
        expected = [
            ['A', 'B', 'mycolumn'],
            ['x', 'one', 'a'],
            ['x', 'two', 'b'],
            ['y', 'three', 'c'],
        ]
        self.assertEqual(list(reader), expected)

        reader = _from_pandas(s, index=False)
        expected = [
            ['mycolumn'],
            ['a'],
            ['b'],
            ['c'],
        ]
        self.assertEqual(list(reader), expected)

@unittest.skipIf(not pandas, 'pandas not found')
class TestIndex(unittest.TestCase):
    def test_simple_index(self):
        index = pandas.Index(['x', 'y', 'z'], name='myindex')

        reader = _from_pandas(index)
        expected = [
            ['myindex'],
            ['x'],
            ['y'],
            ['z'],
        ]
        self.assertEqual(list(reader), expected)

        reader = _from_pandas(index, index=False)
        expected = [
            ['myindex'],
            ['x'],
            ['y'],
            ['z'],
        ]
        msg = 'The `index` arg should be ingored when obj is a pandas Index.'
        self.assertEqual(list(reader), expected, msg=msg)

    def test_multiindex(self):
        multiindex = [('x', 'one'), ('x', 'two'), ('y', 'three')]
        multiindex = pandas.MultiIndex.from_tuples(multiindex, names=['A', 'B'])

        reader = _from_pandas(multiindex)
        expected = [
            ['A', 'B'],
            ['x', 'one'],
            ['x', 'two'],
            ['y', 'three'],
        ]
        self.assertEqual(list(reader), expected)

        reader = _from_pandas(multiindex, index=False)
        expected = [
            ['A', 'B'],
            ['x', 'one'],
            ['x', 'two'],
            ['y', 'three'],
        ]
        msg = 'The `index` arg should be ingored when obj is a pandas Index.'
        self.assertEqual(list(reader), expected, msg=msg)
