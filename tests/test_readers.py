# -*- coding: utf-8 -*-
from __future__ import absolute_import
import csv
from .common import unittest

from get_reader import Reader
from get_reader import ReaderLike


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
