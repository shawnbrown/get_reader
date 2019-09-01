#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import csv
import os
from .common import (
    unittest,
    datatest,
    dbfread,
    pandas,
    xlrd,
    PY2,
    unicode_ash,
    unicode_alpha,
)
from get_reader import Reader
from get_reader import ReaderLike
from get_reader import get_reader
from get_reader import _from_dicts
from get_reader import _from_datatest
from get_reader import _from_dbf
from get_reader import _from_sql


##############################
# Begin test case definitions.
##############################

class TestReader(unittest.TestCase):
    def setUp(self):
        self.log = {'is_closed': False}  # Record if close() has been called.

        def close():
            self.log['is_closed'] = True

        self.closefunc = close

    def test_init_from_list(self):
        msg = '__wrapped__ should be get an iterator'
        list_obj = []
        reader = Reader(list_obj)
        self.assertIsNot(reader.__wrapped__, list_obj, msg=msg)

    def test_init_from_iterator(self):
        msg = 'already-existing iterators should be used as-is'
        iterator = iter([])
        reader = Reader(iterator)
        self.assertIs(reader.__wrapped__, iterator, msg=msg)

        msg = 'csv.reader() objects should be treated the same as other iterators'
        csvreader_obj = csv.reader([])
        reader = Reader(csvreader_obj)
        self.assertIs(reader.__wrapped__, csvreader_obj, msg=msg)

    def test_init_from_Reader(self):
        msg = 'a Reader object should not be wrapped directly, but ' \
              'its __wrapped__ property should be used as-is'
        reader_obj = Reader([])
        reader = Reader(reader_obj)
        self.assertIsNot(reader.__wrapped__, reader_obj, msg=msg)
        self.assertIs(reader.__wrapped__, reader_obj.__wrapped__, msg=msg)

    def test_init_handling_of_closefunc(self):
        reader = Reader([])
        self.assertIsNone(reader._closefunc)

        # Dummy closefunc callables for testing.
        dummyfunc1 = lambda: True
        dummyfunc2 = lambda: True

        reader = Reader([], dummyfunc1)
        self.assertIs(reader._closefunc, dummyfunc1)

        reader = Reader(reader)  # <- Make using existing reader.
        self.assertIs(reader._closefunc, dummyfunc1, msg='inherit closefunc from existing Reader')

        reader = Reader(reader, dummyfunc2)  # <- Override inheritance with new func.
        self.assertIs(reader._closefunc, dummyfunc2, msg='specified closefunc overrides inherited value')

        reader = Reader(reader, None)  # <- Override inheritance with None.
        self.assertIsNone(reader._closefunc, msg='remove inherited closefunc with None')

    def test_type_checking(self):
        reader = Reader([])
        self.assertTrue(isinstance(reader, Reader))

        msg = 'not a Reader (though it is ReaderLike)'

        csv_reader = csv.reader([])
        self.assertFalse(isinstance(csv_reader, Reader), msg=msg)

        list_of_strings = [['a', 'x'], ['b', 'y']]
        self.assertFalse(isinstance(list_of_strings, Reader), msg=msg)

    def test_iterator(self):
        reader = Reader([['a', 'x'], ['b', 'y']])
        self.assertEqual(next(reader), ['a', 'x'])
        self.assertEqual(next(reader), ['b', 'y'])

    def test_close_explicitly(self):
        reader = Reader([['a', 'x'], ['b', 'y']], self.closefunc)
        reader.close()
        self.assertTrue(self.log['is_closed'])

    def test_close_repeated(self):
        reader = Reader([['a', 'x'], ['b', 'y']], self.closefunc)
        reader.close()
        reader.close()  # <- Already closed, should pass without error.
        self.assertTrue(self.log['is_closed'])

    def test_close_on_stopiteration(self):
        reader = Reader([['a', 'x'], ['b', 'y']], self.closefunc)
        for row in reader:
            pass
        msg = 'should auto-close when iterator is exhausted'
        self.assertTrue(self.log['is_closed'], msg=msg)

    def test_close_on_context_exit(self):
        with Reader([['a', 'x'], ['b', 'y']], self.closefunc) as reader:
            pass
        msg = 'should auto-close when exiting context manager'
        self.assertTrue(self.log['is_closed'], msg=msg)

    def test_close_on_del(self):
        reader = Reader([['a', 'x'], ['b', 'y']], self.closefunc)
        reader.__del__()
        msg = 'should auto-close when reader is deleted'
        self.assertTrue(self.log['is_closed'], msg=msg)


class TestReaderLike(unittest.TestCase):
    def test_instantiation(self):
        msg = 'should not instantiate, used only for type-checking'
        with self.assertRaises(TypeError, msg=msg):
            inst = ReaderLike()

    def test_readerlike_objects(self):
        """The following items should test as instances of ReaderLike:

            * Reader instances.
            * csv.reader() type instances.
            * Non-consumable iterables containing non-string sequences.
        """
        reader = Reader([])
        self.assertTrue(isinstance(reader, ReaderLike))

        csv_reader = csv.reader([])
        self.assertTrue(isinstance(csv_reader, ReaderLike))

        list_of_lists = [['a', 'b'], ['c', 'd']]
        self.assertTrue(isinstance(list_of_lists, ReaderLike))

        tuple_of_tuples = (('a', 'b'), ('c', 'd'))
        self.assertTrue(isinstance(tuple_of_tuples, ReaderLike))

    def test_non_readerlike_objects(self):
        list_of_sets = [set(['a', 'b']), set(['c', 'd'])]
        msg = 'must contain sequences, but sets are not sequences'
        self.assertFalse(isinstance(list_of_sets, ReaderLike), msg=msg)

        list_of_iterators = [iter(['a', 'b']), iter(['c', 'd'])]
        msg = 'must contain sequences, but iterators are not sequences'
        self.assertFalse(isinstance(list_of_iterators, ReaderLike), msg=msg)

        iterator_of_lists = iter([['a', 'b'], ['c', 'd']])
        msg = 'consumable iterators must not be altered via side-effect'
        self.assertFalse(isinstance(iterator_of_lists, ReaderLike), msg=msg)

        list_of_strings = ['a', 'c']
        msg = 'must contain non-string sequences'
        self.assertFalse(isinstance(list_of_strings, ReaderLike), msg=msg)

        non_iterable = 123
        msg = 'cannot be non-iterable'
        self.assertFalse(isinstance(non_iterable, ReaderLike), msg=msg)


class TestFunctionDispatching(unittest.TestCase):
    def setUp(self):
        self._orig_dir = os.getcwd()
        os.chdir(os.path.dirname(__file__) or '.')

        def restore_dir():
            os.chdir(self._orig_dir)
        self.addCleanup(restore_dir)

    def test_csv(self):
        reader = get_reader('sample_text_utf8.csv', encoding='utf-8')
        expected = [
            ['col1', 'col2'],
            ['utf8', unicode_alpha],
        ]
        self.assertEqual(list(reader), expected)
        self.assertIsInstance(reader, Reader)

        reader = get_reader('sample_text_iso88591.csv', encoding='iso8859-1')
        expected = [
            ['col1', 'col2'],
            ['iso88591', unicode_ash],
        ]
        self.assertEqual(list(reader), expected)
        self.assertIsInstance(reader, Reader)

        path = 'sample_text_utf8.csv'
        encoding = 'utf-8'

        def open_file(path, encoding):  # <- Helper function.
            if PY2:
                return open(path, 'rb')
            return open(path, 'rt', encoding=encoding, newline='')

        with open_file(path, encoding) as fh:
            reader = get_reader(fh, encoding=encoding)
            expected = [
                ['col1', 'col2'],
                ['utf8', unicode_alpha],
            ]
            self.assertEqual(list(reader), expected)
        self.assertIsInstance(reader, Reader)

    def test_dicts(self):
        records = [
            {'col1': 'first'},
            {'col1': 'second'},
        ]
        reader = get_reader(records)  # <- No fieldnames arg.
        self.assertIsInstance(reader, Reader)
        expected = [['col1'], ['first'], ['second']]
        self.assertEqual(list(reader), expected)

        reader = get_reader(records, ['col1'])  # <- Give fieldnames arg.
        self.assertIsInstance(reader, Reader)
        expected = [['col1'], ['first'], ['second']]
        self.assertEqual(list(reader), expected)

    @unittest.skipIf(not pandas, 'pandas not found')
    def test_pandas(self):
        df = pandas.DataFrame({
            'col1': (1, 2, 3),
            'col2': ('a', 'b', 'c'),
        })
        reader = get_reader(df, index=False)
        expected = [
            ['col1', 'col2'],
            [1, 'a'],
            [2, 'b'],
            [3, 'c'],
        ]
        self.assertEqual(list(reader), expected)
        self.assertIsInstance(reader, Reader)

    @unittest.skipIf(not datatest, 'datatest not found')
    def test_datatest(self):
        select = datatest.Select([['A', 'B'], ['x', 1], ['y', 2]])

        query = select(('A', 'B'))
        reader = get_reader(query)  # <- datatest.Query
        self.assertEqual(list(reader), [('A', 'B'), ('x', 1), ('y', 2)])
        self.assertIsInstance(reader, Reader)

        reader = get_reader(select)  # <- datatest.Select
        self.assertEqual(list(reader), [('A', 'B'), ('x', 1), ('y', 2)])
        self.assertIsInstance(reader, Reader)

        result = select({'A': 'B'}).execute()
        reader = get_reader(query)  # <- datatest.Result
        self.assertEqual(list(reader), [('A', 'B'), ('x', 1), ('y', 2)])
        self.assertIsInstance(reader, Reader)

    @unittest.skipIf(not xlrd, 'xlrd not found')
    def test_excel(self):
        reader = get_reader('sample_excel2007.xlsx')
        expected = [
            ['col1', 'col2'],
            ['excel2007', 1],
        ]
        self.assertEqual(list(reader), expected)
        self.assertIsInstance(reader, Reader)

        reader = get_reader('sample_excel1997.xls')
        expected = [
            ['col1', 'col2'],
            ['excel1997', 1],
        ]
        self.assertEqual(list(reader), expected)
        self.assertIsInstance(reader, Reader)

    @unittest.skipIf(not dbfread, 'dbfread not found')
    def test_dbf(self):
        reader = get_reader('sample_dbase.dbf')
        expected = [
            ['COL1', 'COL2'],
            ['dBASE', 1],
        ]
        self.assertEqual(list(reader), expected)
        self.assertIsInstance(reader, Reader)

    def test_readerlike_wrapping(self):
        """Reader-like lists should simply be wrapped."""
        readerlike = [['col1', 'col2'], [1, 'a'], [2, 'b']]
        reader = get_reader(readerlike)
        self.assertEqual(list(reader), readerlike)

        readerlike = [('col1', 'col2'), (1, 'a'), (2, 'b')]
        reader = get_reader(readerlike)
        self.assertEqual(list(reader), readerlike)

    def test_unhandled_types(self):
        """Should raise error, not return a generator."""
        with self.assertRaises(TypeError):
            get_reader(object())

        with self.assertRaises(TypeError):
            get_reader([object(), object()])


if __name__ == '__main__':
    unittest.main()
