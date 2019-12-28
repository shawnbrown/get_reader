# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
from .common import (
    unittest,
    sqlite3,
    dbfread,
    pandas,
    xlrd,
    PY2,
    squint,
    unicode_ash,
    unicode_alpha,
)

from get_reader import Reader
from get_reader import get_reader


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

        reader = get_reader('sample_text_utf8_bom.csv', encoding='utf-8')
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

    @unittest.skipIf(not sqlite3, 'sqlite3 not found')
    def test_sql(self):
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
        reader = get_reader(connection, 'mytable')
        expected = [
            ('foo', 'bar'),
            ('a', 0.8),
            ('a', 1.2),
            ('b', 2.5),
            ('b', 3.0),
        ]
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

        s = pandas.Series(['a', 'b', 'c'], name='mydata')
        reader = get_reader(s, index=False)
        expected = [
            ['mydata'],
            ['a'],
            ['b'],
            ['c'],
        ]
        self.assertEqual(list(reader), expected)
        self.assertIsInstance(reader, Reader)

        index = pandas.Index(['x', 'y', 'z'], name='myindex')
        reader = get_reader(index)
        expected = [
            ['myindex'],
            ['x'],
            ['y'],
            ['z'],
        ]
        self.assertEqual(list(reader), expected)

        multiindex = pandas.MultiIndex.from_tuples(
            tuples=[('x', 'one'), ('x', 'two'), ('y', 'three')],
            names=['A', 'B'],
        )
        reader = get_reader(multiindex)
        expected = [
            ['A', 'B'],
            ['x', 'one'],
            ['x', 'two'],
            ['y', 'three'],
        ]
        self.assertEqual(list(reader), expected)

    @unittest.skipIf(not squint, 'squint not found')
    def test_squint(self):
        select = squint.Select([['A', 'B'], ['x', 1], ['y', 2]])

        query = select(('A', 'B'))
        reader = get_reader(query)  # <- squint.Query
        self.assertEqual(list(reader), [('A', 'B'), ('x', 1), ('y', 2)])
        self.assertIsInstance(reader, Reader)

        reader = get_reader(select)  # <- squint.Select
        self.assertEqual(list(reader), [('A', 'B'), ('x', 1), ('y', 2)])
        self.assertIsInstance(reader, Reader)

        result = select({'A': 'B'}).execute()
        reader = get_reader(query)  # <- squint.Result
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
