#!/usr/bin/env python
# -*- coding: utf-8 -*-
import collections
import csv
import functools
import io
import os
import sys
try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    import sqlite3  # Not included in Jython.
except ImportError:
    sqlite3 = None

try:
    import datatest
except ImportError:
    datatest = None

try:
    import pandas
except ImportError:
    pandas = None

try:
    import xlrd
except ImportError:
    xlrd = None

try:
    import dbfread
except ImportError:
    dbfread = None

from get_reader import Reader
from get_reader import ReaderLike
from get_reader import get_reader
from get_reader import _from_csv_iterable
from get_reader import _from_csv_path
from get_reader import _from_dicts
from get_reader import _from_namedtuples
from get_reader import _from_pandas
from get_reader import _from_datatest
from get_reader import _from_excel
from get_reader import _from_dbf
from get_reader import _from_sql


PY2 = sys.version_info[0] == 2

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


############################
# Helper function for tests.
############################

def using_relative_directory(func):
    """Decorator to set the working directory to the same directory
    where __file__ is located before calling *func* and then reverting
    back to the original directory afterward.
    """
    original_dir = os.path.abspath(os.getcwd())

    @functools.wraps(func)
    def wrapper(*args, **kwds):
        try:
            os.chdir(os.path.abspath(os.path.dirname(__file__)))
            result = func(*args, **kwds)
        finally:
            os.chdir(original_dir)  # Revert to original directory.
        return result

    return wrapper


###########################################
# Define sample Unicode values for testing.
###########################################

try:
    unichr  # unichr() only defined in Python 2
except NameError:
    unichr = chr  # chr() is Unicode-aware in Python 3

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


class TestFromNamedtuples(unittest.TestCase):
    def test_namedtuple_records(self):
        ntup = collections.namedtuple('ntup', ['col1', 'col2'])
        records = [
            ntup(1, 'a'),
            ntup(2, 'b'),
            ntup(3, 'c'),
        ]
        reader = _from_namedtuples(records)

        expected = [
            ('col1', 'col2'),
            (1, 'a'),
            (2, 'b'),
            (3, 'c'),
        ]
        self.assertEqual(list(reader), expected)

    def test_empty_records(self):
        records = []
        reader = _from_namedtuples(records)
        self.assertEqual(list(records), [])


class TestFromCsvIterable(unittest.TestCase):
    """Test Unicode CSV support.

    Calling _from_csv_iterable() on Python 2 uses the UnicodeReader
    and UTF8Recoder classes internally for consistent behavior across
    versions.
    """
    @staticmethod
    def get_stream(string, encoding=None):
        """Accepts string and returns file-like stream object.

        In Python 2, Unicode files should be opened in binary-mode
        but in Python 3, they should be opened in text-mode. This
        function emulates the appropriate opening behavior.
        """
        fh = io.BytesIO(string)
        if PY2:
            return fh
        return io.TextIOWrapper(fh, encoding=encoding)

    def test_ascii(self):
        stream = self.get_stream((
            b'col1,col2\n'
            b'1,a\n'
            b'2,b\n'
            b'3,c\n'
        ), encoding='ascii')

        reader = _from_csv_iterable(stream, encoding='ascii', dialect='excel')
        expected = [
            ['col1', 'col2'],
            ['1', 'a'],
            ['2', 'b'],
            ['3', 'c'],
        ]
        self.assertEqual(list(reader), expected)

    def test_iso88591(self):
        stream = self.get_stream((
            b'col1,col2\n'
            b'1,\xe6\n'  # '1,æ\n'
            b'2,\xf0\n'  # '2,ð\n'
            b'3,\xfe\n'  # '3,þ\n'
        ), encoding='iso8859-1')

        reader = _from_csv_iterable(stream, encoding='iso8859-1', dialect='excel')
        expected = [
            ['col1', 'col2'],
            ['1', unicode_ash],
            ['2', unicode_eth],
            ['3', unicode_thorn],
        ]
        self.assertEqual(list(reader), expected)

    def test_utf8(self):
        stream = self.get_stream((
            b'col1,col2\n'
            b'1,\xce\xb1\n'          # '1,α\n'
            b'2,\xe0\xa5\x90\n'      # '2,ॐ\n'
            b'3,\xf0\x9d\x94\xb8\n'  # '3,𝔸\n'
        ), encoding='utf-8')
        reader = _from_csv_iterable(stream, encoding='utf-8', dialect='excel')

        expected = [
            ['col1', 'col2'],
            ['1', unicode_alpha],
            ['2', unicode_om],
            ['3', unicode_math_a],
        ]
        self.assertEqual(list(reader), expected)

    def test_unicode(self):
        """Test an iterator of Unicode strings."""
        try:
            u = unicode  # For Python 2 only.
        except NameError:
            u = str  # In Python 3, all strings are unicode.

        stream = iter([
            u('col1,col2\n'),
            u('1,{0}\n').format(unicode_alpha),   # u'1,α\n'
            u('2,{0}\n').format(unicode_om),      # u'2,ॐ\n'
            u('3,{0}\n').format(unicode_math_a),  # u'3,𝔸\n'
        ])
        reader = _from_csv_iterable(stream, encoding=None, dialect='excel')

        expected = [
            ['col1', 'col2'],
            ['1', unicode_alpha],
            ['2', unicode_om],
            ['3', unicode_math_a],
        ]
        self.assertEqual(list(reader), expected)

    def test_fmtparams(self):
        stream = self.get_stream((
            b'|col1| |col2|\n'
            b'|1| |a|\n'
            b'|2| |b|\n'
            b'|3| |c|\n'
        ), encoding='utf-8')

        fmtparams = {'delimiter': ' ', 'quotechar': '|'}
        reader = _from_csv_iterable(stream, encoding='utf-8', dialect='excel', **fmtparams)
        expected = [
            ['col1', 'col2'],
            ['1', 'a'],
            ['2', 'b'],
            ['3', 'c'],
        ]
        self.assertEqual(list(reader), expected)

    def test_bad_types(self):
        bytes_literal = (
            b'col1,col2\n'
            b'1,a\n'
            b'2,b\n'
            b'3,c\n'
        )
        if PY2:
            bytes_stream = io.BytesIO(bytes_literal)
            text_stream = io.TextIOWrapper(bytes_stream, encoding='ascii')
            with self.assertRaises(TypeError):
                reader = _from_csv_iterable(text_stream, 'ascii', dialect='excel')
        else:
            bytes_stream = io.BytesIO(bytes_literal)
            with self.assertRaises((csv.Error, TypeError)):
                reader = _from_csv_iterable(bytes_stream, 'ascii', dialect='excel')
                list(reader)  # Trigger evaluation.

    def test_empty_file(self):
        stream = self.get_stream(b'', encoding='ascii')
        reader = _from_csv_iterable(stream, encoding='ascii', dialect='excel')
        expected = []
        self.assertEqual(list(reader), expected)


class TestFromCsvPath(unittest.TestCase):
    @using_relative_directory
    def test_utf8(self):
        reader, _ = _from_csv_path('sample_text_utf8.csv', encoding='utf-8', dialect='excel')
        expected = [
            ['col1', 'col2'],
            ['utf8', unicode_alpha],
        ]
        self.assertEqual(list(reader), expected)

    @using_relative_directory
    def test_utf16(self):
        reader, _ = _from_csv_path('sample_text_utf16.csv', encoding='utf-16', dialect='excel')
        expected = [
            ['col1', 'col2'],
            ['utf16', 'abc'],
        ]
        self.assertEqual(list(reader), expected)

    @using_relative_directory
    def test_iso88591(self):
        reader, _ = _from_csv_path('sample_text_iso88591.csv', encoding='iso8859-1', dialect='excel')

        expected = [
            ['col1', 'col2'],
            ['iso88591', unicode_ash],
        ]
        self.assertEqual(list(reader), expected)

    @using_relative_directory
    def test_wrong_encoding(self):
        with self.assertRaises(UnicodeDecodeError):
            reader, _ = _from_csv_path('sample_text_utf16.csv', encoding='utf-8', dialect='excel')
            list(reader)  # Trigger evaluation.

        with self.assertRaises(UnicodeDecodeError):
            reader, _ = _from_csv_path('sample_text_iso88591.csv', encoding='ascii', dialect='excel')
            list(reader)  # Trigger evaluation.

        if PY2:
            return  # <- EXIT!

        # Following ISO-8859-1 (mis-identified as UTF-8) doesn't fail on Py 2.x.
        with self.assertRaises(UnicodeDecodeError):
            reader, _ = _from_csv_path('sample_text_iso88591.csv', encoding='utf-8', dialect='excel')
            list(reader)  # Trigger evaluation.

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            reader, _ = _from_csv_path('missing_file.csv', encoding='iso8859-1', dialect='excel')


@unittest.skipIf(not datatest, 'datatest not found')
class TestFromDatatest(unittest.TestCase):
    def setUp(self):
        self.select = datatest.Select([['A', 'B'], ['x', 1], ['y', 2]])

    def test_query_multicolumn_implicit_fieldnames(self):
        query = self.select(('B', 'A'))
        reader = _from_datatest(query)  # <- No fieldnames specified.
        self.assertEqual(list(reader), [('B', 'A'), (1, 'x'), (2, 'y')])

    def test_query_multicolumn_explicit_fieldnames(self):
        query = self.select(['B', 'A'])
        reader = _from_datatest(query, fieldnames=['foo', 'bar'])
        self.assertEqual(list(reader), [['foo', 'bar'], [1, 'x'], [2, 'y']])

    def test_query_multicolumn_non_select(self):
        query = datatest.Query.from_object([['x', 1], ['y', 2]])

        reader = _from_datatest(query)  # <- No fieldnames.
        self.assertEqual(list(reader), [['x', 1], ['y', 2]])

        reader = _from_datatest(query, fieldnames=['foo', 'bar'])
        self.assertEqual(list(reader), [['foo', 'bar'], ['x', 1], ['y', 2]])

    def test_query_singlecolumn_implicit_fieldname(self):
        query = self.select('A')
        reader = _from_datatest(query)
        self.assertEqual(list(reader), [('A',), ('x',), ('y',)])

    def test_query_singlecolumn_explicit_fieldname(self):
        query = self.select('A')
        reader = _from_datatest(query, fieldnames='foo')
        self.assertEqual(list(reader), [('foo',), ('x',), ('y',)])

    def test_query_singlecolumn_non_select(self):
        query = datatest.Query.from_object(['x', 'y'])

        reader = _from_datatest(query)  # <- No fieldnames.
        self.assertEqual(list(reader), [('x',), ('y',)])

        reader = _from_datatest(query, fieldnames='foo')
        self.assertEqual(list(reader), [('foo',), ('x',), ('y',)])

    def test_query_summed_single_value(self):
        query = self.select('B').sum()
        reader = _from_datatest(query)
        self.assertEqual(list(reader), [('B',), (3,)])

    def test_query_dict_single_key_and_value(self):
        query = self.select({'A': 'B'})
        reader = _from_datatest(query)
        self.assertEqual(list(reader), [('A', 'B'), ('x', 1), ('y', 2)])

    def test_query_dict_tuplevalue(self):
        query = self.select({'A': ('A', 'B')})
        reader = _from_datatest(query)
        self.assertEqual(list(reader), [('A', 'A', 'B'), ('x', 'x', 1), ('y', 'y', 2)])

    def test_query_dict_tuplekey(self):
        query = self.select({('A', 'A'): 'B'})
        reader = _from_datatest(query)
        self.assertEqual(list(reader), [('A', 'A', 'B'), ('x', 'x', 1), ('y', 'y', 2)])

    def test_query_dict_tuplekey_tuplevalue(self):
        query = self.select({('A', 'A'): ('B', 'B')})
        reader = _from_datatest(query)
        self.assertEqual(list(reader), [('A', 'A', 'B', 'B'), ('x', 'x', 1, 1), ('y', 'y', 2, 2)])

    def test_select_object(self):
        reader = _from_datatest(self.select)  # <- No fieldnames specified.
        self.assertEqual(list(reader), [('A', 'B'), ('x', 1), ('y', 2)])

        reader = _from_datatest(self.select, fieldnames=('foo', 'bar'))
        self.assertEqual(list(reader), [('foo', 'bar'), ('x', 1), ('y', 2)])

    def test_result_list(self):
        result = datatest.Result([['x', 1], ['y', 2]], evaluation_type=list)
        reader = _from_datatest(result)  # <- No fieldnames specified.
        self.assertEqual(list(reader), [['x', 1], ['y', 2]])

        result = datatest.Result([['x', 1], ['y', 2]], evaluation_type=list)
        reader = _from_datatest(result, fieldnames=['foo', 'bar'])
        self.assertEqual(list(reader), [['foo', 'bar'], ['x', 1], ['y', 2]])

    def test_result_dict(self):
        source_dict = {'x': [1, 1], 'y': [2]}

        result = datatest.Result(source_dict, evaluation_type=dict)
        reader = _from_datatest(result)  # <- No fieldnames specified.
        reader_list = list(reader)
        self.assertEqual(reader_list.count(('x', 1)), 2)
        self.assertEqual(reader_list.count(('y', 2)), 1)

        result = datatest.Result(source_dict, evaluation_type=dict)
        reader = _from_datatest(result, fieldnames=('foo', 'bar'))
        reader_list = list(reader)
        self.assertEqual(reader_list[0], ('foo', 'bar'))
        self.assertEqual(reader_list.count(('x', 1)), 2)
        self.assertEqual(reader_list.count(('y', 2)), 1)


@unittest.skipIf(not pandas, 'pandas not found')
class TestFromPandas(unittest.TestCase):
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


@unittest.skipIf(not sqlite3, 'sqlite3 not found')
class TestFromSql(unittest.TestCase):
    def setUp(self):
        connection = sqlite3.connect(':memory:')
        connection.executescript("""
            CREATE TABLE mytable (
                foo TEXT,
                bar REAL
            );
            INSERT INTO mytable
            VALUES ('a', 0.8),
                   ('a', 1.2),
                   ('b', 2.5),
                   ('b', 3.0);
        """)
        self.connection = connection

    def test_table_name(self):
        """When given a table name (instead of a query), return all rows."""
        reader = _from_sql(self.connection, 'mytable')
        expected = [
            ('foo', 'bar'),
            ('a', 0.8),
            ('a', 1.2),
            ('b', 2.5),
            ('b', 3.0),
        ]
        self.assertEqual(list(reader), expected)

    def test_query_select_all(self):
        """Should use names from cursor.description for header row."""
        query = 'SELECT * FROM mytable;'
        reader = _from_sql(self.connection, query)
        expected = [
            ('foo', 'bar'),
            ('a', 0.8),
            ('a', 1.2),
            ('b', 2.5),
            ('b', 3.0),
        ]
        self.assertEqual(list(reader), expected)

    def test_query_sum_groupby(self):
        """Check that column alias ("AS total") is used in header."""
        query = """
            SELECT foo, SUM(bar) AS total
            FROM mytable
            GROUP BY foo;
        """
        reader = _from_sql(self.connection, query)
        expected = [
            ('foo', 'total'),
            ('a', 2.0),
            ('b', 5.5),
        ]
        self.assertEqual(list(reader), expected)

    def test_query_empty_result(self):
        query = """
            SELECT foo, SUM(bar) AS total
            FROM mytable
            WHERE foo='c' /* <- No matching records. */
            GROUP BY foo;
        """
        reader = _from_sql(self.connection, query)
        expected = [('foo', 'total')]
        self.assertEqual(list(reader), expected)


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


#@unittest.skip('skip while refactoring')
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

    def test_namedtuples(self):
        ntup = collections.namedtuple('ntup', ['col1', 'col2'])

        records = [ntup(1, 'a'), ntup(2, 'b')]
        reader = get_reader(records)

        self.assertIsInstance(reader, Reader)

        expected = [('col1', 'col2'), (1, 'a'), (2, 'b')]
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
