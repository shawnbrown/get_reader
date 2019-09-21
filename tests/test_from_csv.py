# -*- coding: utf-8 -*-
from __future__ import absolute_import
import csv
import io
import os
from .common import (
    unittest,
    PY2,
    FileNotFoundError,
    unicode_ash,
    unicode_eth,
    unicode_thorn,
    unicode_alpha,
    unicode_om,
    unicode_math_a,
)

from get_reader import (
    _from_csv_path,
    _from_csv_iterable,
)


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
    _original_dir = os.path.abspath(os.getcwd())
    _relative_dir = os.path.abspath(os.path.dirname(__file__))

    def setUp(self):
        self.addCleanup(lambda: os.chdir(self._original_dir))
        os.chdir(self._relative_dir)

    def test_utf8(self):
        reader, closefunc = _from_csv_path(
            'sample_text_utf8.csv', encoding='utf-8', dialect='excel')
        self.addCleanup(closefunc)

        expected = [
            ['col1', 'col2'],
            ['utf8', unicode_alpha],
        ]
        self.assertEqual(list(reader), expected)

    def test_utf16(self):
        reader, closefunc = _from_csv_path(
            'sample_text_utf16.csv', encoding='utf-16', dialect='excel')
        self.addCleanup(closefunc)

        expected = [
            ['col1', 'col2'],
            ['utf16', 'abc'],
        ]
        self.assertEqual(list(reader), expected)

    def test_iso88591(self):
        reader, closefunc = _from_csv_path(
            'sample_text_iso88591.csv', encoding='iso8859-1', dialect='excel')
        self.addCleanup(closefunc)

        expected = [
            ['col1', 'col2'],
            ['iso88591', unicode_ash],
        ]
        self.assertEqual(list(reader), expected)

    def test_wrong_encoding(self):
        with self.assertRaises(UnicodeDecodeError):
            reader, closefunc = _from_csv_path(
                'sample_text_utf16.csv', encoding='utf-8', dialect='excel')
            self.addCleanup(closefunc)

            list(reader)  # Trigger evaluation.

        with self.assertRaises(UnicodeDecodeError):
            reader, closefunc = _from_csv_path(
                'sample_text_iso88591.csv', encoding='ascii', dialect='excel')
            self.addCleanup(closefunc)
            list(reader)  # Trigger evaluation.

        if PY2:
            return  # <- EXIT!

        # Following ISO-8859-1 (mis-identified as UTF-8) doesn't fail on Py 2.x.
        with self.assertRaises(UnicodeDecodeError):
            reader, closefunc = _from_csv_path(
                'sample_text_iso88591.csv', encoding='utf-8', dialect='excel')
            self.addCleanup(closefunc)
            list(reader)  # Trigger evaluation.

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            reader, _ = _from_csv_path(
                'missing_file.csv', encoding='iso8859-1', dialect='excel')
