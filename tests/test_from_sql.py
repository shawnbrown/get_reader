# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .common import (
    unittest,
    sqlite3,
)

from get_reader import _from_sql


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
        reader, _ = _from_sql(self.connection, 'mytable')
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
        reader, _ = _from_sql(self.connection, query)
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
        reader, _ = _from_sql(self.connection, query)
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
        reader, _ = _from_sql(self.connection, query)
        expected = [('foo', 'total')]
        self.assertEqual(list(reader), expected)

    def test_barebones_cursor(self):
        """Should not assume that all cursor objects are iterable.
        While it's common for cursors to be iterable, this behavior
        is part of DBAPI2's "Optional DB API Extensions" and should
        not be required for correct operation.
        """
        class WrappedConnection(object):
            def __init__(_self, connection):
                _self._connection = connection

            def cursor(_self):
                class NonIterableCursor(object):
                    def __init__(_self, cursor):
                        _self._cursor = cursor

                    def execute(_self, *args, **kwds):
                        _self._cursor.execute(*args, **kwds)

                    @property
                    def description(_self):
                        return _self._cursor.description

                    def fetchone(_self):
                        return _self._cursor.fetchone()

                    def close(_self):
                        _self._cursor.close()

                cursor = _self._connection.cursor()
                return NonIterableCursor(cursor)

        connection = WrappedConnection(self.connection)

        # Check cursor.
        with self.assertRaises(TypeError, msg='should not be iterable'):
            iter(connection.cursor())

        # Check reader result.
        reader, _ = _from_sql(connection, 'mytable')
        expected = [
            ('foo', 'bar'),
            ('a', 0.8),
            ('a', 1.2),
            ('b', 2.5),
            ('b', 3.0),
        ]
        self.assertEqual(list(reader), expected)

    def test_close_on_error(self):
        log = {'is_closed': False}  # Indicate if close() has been called.

        class MockConnection(object):
            def cursor(_self):
                class MockCursor(object):
                    def execute(_self, *args, **kwds):
                        raise Exception('Failed execution!')

                    def close(_self):
                        log['is_closed'] = True

                return MockCursor()

        try:
            reader, _ = _from_sql(MockConnection(), 'Bad query, failed execution!')
        except Exception:
            pass

        self.assertTrue(log['is_closed'], msg='internal cursor should be closed on error')
