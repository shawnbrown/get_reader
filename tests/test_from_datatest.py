# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .common import (
    unittest,
    squint,
)

from get_reader import _from_squint


@unittest.skipIf(not squint, 'squint not found')
class TestFromSquint(unittest.TestCase):
    def setUp(self):
        self.select = squint.Select([['A', 'B'], ['x', 1], ['y', 2]])

    def test_query_multicolumn_implicit_fieldnames(self):
        query = self.select(('B', 'A'))
        reader = _from_squint(query)  # <- No fieldnames specified.
        self.assertEqual(list(reader), [('B', 'A'), (1, 'x'), (2, 'y')])

    def test_query_multicolumn_explicit_fieldnames(self):
        query = self.select(['B', 'A'])
        reader = _from_squint(query, fieldnames=['foo', 'bar'])
        self.assertEqual(list(reader), [['foo', 'bar'], [1, 'x'], [2, 'y']])

    def test_query_multicolumn_non_select(self):
        query = squint.Query.from_object([['x', 1], ['y', 2]])

        reader = _from_squint(query)  # <- No fieldnames.
        self.assertEqual(list(reader), [['x', 1], ['y', 2]])

        reader = _from_squint(query, fieldnames=['foo', 'bar'])
        self.assertEqual(list(reader), [['foo', 'bar'], ['x', 1], ['y', 2]])

    def test_query_singlecolumn_implicit_fieldname(self):
        query = self.select('A')
        reader = _from_squint(query)
        self.assertEqual(list(reader), [('A',), ('x',), ('y',)])

    def test_query_singlecolumn_explicit_fieldname(self):
        query = self.select('A')
        reader = _from_squint(query, fieldnames='foo')
        self.assertEqual(list(reader), [('foo',), ('x',), ('y',)])

    def test_query_singlecolumn_non_select(self):
        query = squint.Query.from_object(['x', 'y'])

        reader = _from_squint(query)  # <- No fieldnames.
        self.assertEqual(list(reader), [('x',), ('y',)])

        reader = _from_squint(query, fieldnames='foo')
        self.assertEqual(list(reader), [('foo',), ('x',), ('y',)])

    def test_query_summed_single_value(self):
        query = self.select('B').sum()
        reader = _from_squint(query)
        self.assertEqual(list(reader), [('B',), (3,)])

    def test_query_dict_single_key_and_value(self):
        query = self.select({'A': 'B'})
        reader = _from_squint(query)
        self.assertEqual(list(reader), [('A', 'B'), ('x', 1), ('y', 2)])

    def test_query_dict_tuplevalue(self):
        query = self.select({'A': ('A', 'B')})
        reader = _from_squint(query)
        self.assertEqual(list(reader), [('A', 'A', 'B'), ('x', 'x', 1), ('y', 'y', 2)])

    def test_query_dict_tuplekey(self):
        query = self.select({('A', 'A'): 'B'})
        reader = _from_squint(query)
        self.assertEqual(list(reader), [('A', 'A', 'B'), ('x', 'x', 1), ('y', 'y', 2)])

    def test_query_dict_tuplekey_tuplevalue(self):
        query = self.select({('A', 'A'): ('B', 'B')})
        reader = _from_squint(query)
        self.assertEqual(list(reader), [('A', 'A', 'B', 'B'), ('x', 'x', 1, 1), ('y', 'y', 2, 2)])

    def test_select_object(self):
        reader = _from_squint(self.select)  # <- No fieldnames specified.
        self.assertEqual(list(reader), [('A', 'B'), ('x', 1), ('y', 2)])

        reader = _from_squint(self.select, fieldnames=('foo', 'bar'))
        self.assertEqual(list(reader), [('foo', 'bar'), ('x', 1), ('y', 2)])

    def test_result_list(self):
        result = squint.Result([['x', 1], ['y', 2]], evaluation_type=list)
        reader = _from_squint(result)  # <- No fieldnames specified.
        self.assertEqual(list(reader), [['x', 1], ['y', 2]])

        result = squint.Result([['x', 1], ['y', 2]], evaluation_type=list)
        reader = _from_squint(result, fieldnames=['foo', 'bar'])
        self.assertEqual(list(reader), [['foo', 'bar'], ['x', 1], ['y', 2]])

    def test_result_dict(self):
        source_dict = {'x': [1, 1], 'y': [2]}

        result = squint.Result(source_dict, evaluation_type=dict)
        reader = _from_squint(result)  # <- No fieldnames specified.
        reader_list = list(reader)
        self.assertEqual(reader_list.count(('x', 1)), 2)
        self.assertEqual(reader_list.count(('y', 2)), 1)

        result = squint.Result(source_dict, evaluation_type=dict)
        reader = _from_squint(result, fieldnames=('foo', 'bar'))
        reader_list = list(reader)
        self.assertEqual(reader_list[0], ('foo', 'bar'))
        self.assertEqual(reader_list.count(('x', 1)), 2)
        self.assertEqual(reader_list.count(('y', 2)), 1)
