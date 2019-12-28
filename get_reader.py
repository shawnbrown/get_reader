# -*- coding: utf-8 -*-
import codecs
import csv
import io
import sys
from abc import ABCMeta
from itertools import (
    chain,
    islice,
)

try:
    from collections.abc import Iterable
    from collections.abc import Mapping
    from collections.abc import Sequence
except ImportError:
    from collections import Iterable
    from collections import Mapping
    from collections import Sequence

try:
    range.__iter__  # New in version 3.0.
except AttributeError:
    range = xrange


__version__ = '1.0.0'


__all__ = [
    'get_reader',
    'Reader',
    'ReaderLike',
]


try:
    string_types = basestring
    file_types = (io.IOBase, file)
except NameError:
    string_types = str
    file_types = io.IOBase


PY2 = sys.version_info[0] == 2


def nonstringiter(obj):
    """Returns True if *obj* is a non-string iterable object."""
    return not isinstance(obj, string_types) and isinstance(obj, Iterable)


def iterpeek(iterable):
    if iter(iterable) is iter(iterable):  # <- If exhaustible.
        try:
            first_item = next(iterable)
            iterable = chain([first_item], iterable)
        except StopIteration:
            first_item = None
    else:
        first_item = next(iter(iterable), None)
    return first_item, iterable


NOVALUE = type(
    'novalue',
    (object,),
    {'__repr__': (lambda x: '<no value>')},
)()


class Reader(object):
    """An iterator which will produce rows from the given *iterable*.
    By convention the first row is expected to be a header. The given
    *iterable* can be any `ReaderLike` object. The optional *closefunc*
    will be called to close any associated resources (files, database
    cursors, etc.) when:

    * the iterable is exhausted
    * the Reader is deleted
    * exiting a `with` statement (if used as a context manager)
    """
    def __init__(self, iterable, closefunc=NOVALUE):
        if isinstance(iterable, Reader):
            if closefunc is NOVALUE:
                closefunc = iterable._closefunc
            iterable = iterable.__wrapped__
        else:
            if closefunc is NOVALUE:
                closefunc = None
            iterable = iter(iterable)

        self.__wrapped__ = iterable
        self._closefunc = closefunc

    def close(self):
        """Closes any associated resources (calls *closefunc* early).
        If the resources have already been closed, this method passes
        without error.
        """
        if self._closefunc:
            self._closefunc()
            self._closefunc = None

    def __del__(self):
        self.close()

    # Iterator protocol.

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(self.__wrapped__)
        except StopIteration:
            self.close()
            raise

    def next(self):  # Python 2.x support.
        return self.__next__()

    # Context manager protocol (for `with` statement).

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()


class ReaderLikeABCMeta(ABCMeta):
    """A meta class for ReaderLike."""
    _reader_types = (Reader, type(csv.reader([])))

    def __instancecheck__(self, inst):  # <- Only looked up on metaclass.
        if isinstance(inst, self._reader_types):
            return True

        if not isinstance(inst, Iterable):  # Must be iterable.
            return False

        if iter(inst) is iter(inst):  # Must not be exhaustible.
            return False

        rows_to_check = 2                            # Must contain
        for x in islice(iter(inst), rows_to_check):  # non-string sequences.
            if (not isinstance(x, Sequence)) or isinstance(x, string_types):
                return False
        return True


class ReaderLike(ReaderLikeABCMeta('ReaderLikeABC', (object,), {})):
    """An abstract class that can be used for type checking. Objects
    will test as `ReaderLike` if they are one of the following:

    * instance of the `Reader` class
    * object returned by `csv.reader()`
    * non-exhaustible iterable that produces non-string sequences

    See the following examples::

        >>> isinstance(get_reader(csvfile), ReaderLike)
        True

        >>> isinstance(csv.reader(csvfile), ReaderLike)
        True

        >>> list_of_lists = [['col1', 'col2'], ['a', 'b']]
        >>> isinstance(list_of_lists, ReaderLike)
        True

        >>> list_of_strings = ['col1,col2', 'a,b']
        >>> isinstance(list_of_strings, ReaderLike)
        False

        >>> list_of_sets = [{'col1', 'col2'}, {'a', 'b'}]
        >>> isinstance(list_of_sets, ReaderLike)
        False
    """
    def __new__(cls):
        msg = ("Can't instantiate abstract class "
               "ReaderLike, use only for type checking")
        raise TypeError(msg)


#######################################################################
# Data handling functions.
#######################################################################

_utf8_no_bom = codecs.getdecoder('utf-8')

def _normalize_decoder(encoding):
    """Changes UTF-8 into Python's BOM-aware utf_8_sig encoding
    or returns encoding unchanged. If encoding is invalid, an error
    will be raised.
    """
    if codecs.getdecoder(encoding) is _utf8_no_bom:
        return 'utf_8_sig'  # <- EXIT! Return BOM-aware UTF-8 encoding.
    return encoding


if PY2:

    def _unicode_rows(stream, encoding, dialect, **kwds):
        """Returns a generator that yields rows as lists of Unicode
        values. The Python 2 `csv` module does not support Unicode
        directly. For best results, the official docs recommend
        encoding text as UTF-8 before passing it to csv.reader().
        """
        # Get Unicode stream.
        if isinstance(stream, io.IOBase):
            streamreader_type = codecs.getreader(encoding)
            unicode_stream = streamreader_type(stream)
        elif isinstance(stream, Iterable):
            first_row, stream = iterpeek(stream)
            if isinstance(first_row, unicode):
                unicode_stream = stream  # Ignores given *encoding*.
            else:
                unicode_stream = (row.decode(encoding) for row in stream)
        else:
            cls_name = stream.__class__.__name__
            raise TypeError('unsupported type {0}'.format(cls_name))

        # Re-encode as UTF-8.
        utf8_stream = (x.encode('utf-8') for x in unicode_stream)

        # Pass to csv.reader() and return generator.
        reader = csv.reader(utf8_stream, dialect=dialect, **kwds)
        make_unicode = lambda row: [unicode(s, 'utf-8') for s in row]
        return (make_unicode(row) for row in reader)


    def _from_csv_path(path, encoding, dialect, **kwds):
        fh = io.open(path, 'rb')
        try:
            generator = _unicode_rows(fh, encoding, dialect=dialect, **kwds)
        except Exception:
            fh.close()
            raise
        return (generator, fh.close)


    def _from_csv_iterable(iterable, encoding, dialect, **kwds):
        # Check that iterable is expected to return bytes (not strings).
        if isinstance(iterable, file):
            using_bytes = 'b' in iterable.mode
        elif isinstance(iterable, io.IOBase):
            using_bytes = not isinstance(iterable, io.TextIOBase)
        else:
            using_bytes = True
            # If *iterable* is a generic iterator, we just have to trust that
            # the user knows what they're doing. Because in Python 2, there's
            # no reliable way to tell the difference between encoded bytes and
            # decoded strings:
            #
            #   >>> b'x' == 'x'
            #   True

        if not using_bytes:
            msg = ('Python 2 unicode compatibility expects bytes, not '
                   'strings (did you open the file in binary mode?)')
            raise TypeError(msg)

        return _unicode_rows(iterable, encoding, dialect=dialect, **kwds)

else:  # Python 3

    def _from_csv_path(path, encoding, dialect, **kwds):
        fh = open(path, 'rt', encoding=encoding, newline='')
        try:
            reader = csv.reader(fh, dialect=dialect, **kwds)
        except Exception:
            fh.close()
            raise
        return (reader, fh.close)


    def _from_csv_iterable(iterable, encoding, dialect, **kwds):
        return csv.reader(iterable, dialect=dialect, **kwds)
        # Above, the *encoding* arg is not used but is included so
        # that the csv-helper functions have the same signature.


def _from_dicts(records, fieldnames=None):
    """Takes a container of dict *records* and returns a generator."""
    if fieldnames:
        fieldnames = list(fieldnames)  # Needs to be a sequence.
        yield fieldnames  # Header row.
    else:
        records = iter(records)
        first_record = next(records, None)
        if first_record:
            fieldnames = list(first_record.keys())
            yield fieldnames  # Header row.
            yield list(first_record.values())

    for row in records:
        yield [row.get(key, None) for key in fieldnames]


def _from_pandas(obj, index=True):
    """Takes a pandas DataFrame, Series, Index, or MultiIndex and
    returns a generator.
    """
    if hasattr(obj, 'to_frame') and hasattr(obj, 'index'):
        # Convert series to DataFrame.
        df = obj.to_frame()
    elif hasattr(obj, 'to_frame') and not hasattr(obj, 'index'):
        # Convert MultiIndex (pandas >=0.20.0) or Index (pandas >=0.21.0)
        # to DataFrame.
        index = False
        df = obj.to_frame()
    elif hasattr(obj, 'to_series'):
        # Convert Index (pandas >=0.20.0,<0.21.0) to DataFrame.
        index = False
        df = obj.to_series().to_frame()
    else:
        # Else, it's already a DataFrame.
        df = obj

    if index:
        yield list(df.index.names) + list(df.columns)
    else:
        yield list(df.columns)

    records = df.to_records(index=index)
    for record in records:
        yield list(record)


def _from_squint(obj, fieldnames=None):
    """Takes a Select, Query, or Result and returns a generator."""
    squint = sys.modules['squint']
    if isinstance(obj, squint.Query):
        query = obj
    elif isinstance(obj, squint.Select):
        query = obj(tuple(obj.fieldnames))
    elif isinstance(obj, squint.Result):
        query = squint.Query.from_object(obj)
    else:
        raise TypeError('must be squint Select, Query, or Result')

    iterable = query.flatten().execute()
    if not nonstringiter(iterable):
        iterable = [(iterable,)]

    first_row, iterable = iterpeek(iterable)
    if not nonstringiter(first_row):
        first_row = (first_row,)
        iterable = ((x,) for x in iterable)

    if fieldnames:
        if not nonstringiter(fieldnames):
            fieldnames = (fieldnames,)
    else:
        if query.args:
            fieldnames = query.__class__.from_object(query.args[0])
            (fieldnames,) = fieldnames.flatten().fetch()
            if not nonstringiter(fieldnames):
                fieldnames = (fieldnames,)
            if len(first_row) != len(fieldnames):
                fieldnames = None

    if fieldnames:
        yield fieldnames

    for value in iterable:
        yield value


def _from_excel(path, worksheet=0):
    """Takes a Excel path and returns a generator and close method."""
    try:
        import xlrd
    except ImportError:
        raise ImportError(
            "No module named 'xlrd'\n"
            "\n"
            "This is an optional constructor that requires the "
            "third-party library 'xlrd'."
        )
    book = xlrd.open_workbook(path, on_demand=True)

    if isinstance(worksheet, int):
        sheet = book.sheet_by_index(worksheet)
    else:
        sheet = book.sheet_by_name(worksheet)

    reader = (sheet.row_values(index) for index in range(sheet.nrows))
    release_resources = book.release_resources
    return (reader, release_resources)


def _from_dbf(filename, encoding, **kwds):
    """Takes a DBF path and returns a generator."""
    try:
        import dbfread
    except ImportError:
        raise ImportError(
            "No module named 'dbfread'\n"
            "\n"
            "This is an optional constructor that requires the "
            "third-party library 'dbfread'."
        )

    kwds['recfactory'] = lambda record: [x[1] for x in record]
    if 'load' not in kwds:
        kwds['load'] = False

    table = dbfread.DBF(filename, encoding, **kwds)
    field_names = table.field_names

    generator = iter(table)
    close_generator = getattr(generator, 'close', None)

    reader = chain([field_names], generator)
    return reader, close_generator


def _from_sql(connection, table_or_query):
    """Return a reader object which will iterate over records from the
    given table or query result.
    """
    cursor = connection.cursor()
    try:
        cursor.execute(table_or_query)
    except Exception:
        try:
            cursor.execute('SELECT * FROM {0}'.format(table_or_query))
        except Exception:
            cursor.close()
            raise

    try:
        # If iterable, use cursor directly.
        iter(cursor)
        results = cursor
    except TypeError:
        # If not iterable, build a generator.
        def result_generator(cursor):
            row = cursor.fetchone()
            while row != None:
                yield row
                row = cursor.fetchone()
        results = result_generator(cursor)

    header = tuple(x[0] for x in cursor.description)
    reader = chain([header], results)
    return (reader, cursor.close)


#######################################################################
# Get Reader.
#######################################################################
class GetReaderType(object):
    r"""Return a `Reader` object which will iterate over records in
    the given *obj*---like a `csv.reader()`. The given *obj* may be
    one of the following:

    * CSV file (string path or file object)
    * iterable of dictionary rows
    * database connection (should be DBAPI2 compatible)
    * pandas DataFrame, Series, Index, or MultiIndex
    * squint Select, Query, or Result

    If optional extras are installed, *obj* may also be:

    * MS Excel file path
    * DBF file path

    When *obj* is a file path, the `Reader` contains a file object
    that is handled internally. When given a file-like *obj* (rather
    than a path), users are responsible for properly closing this
    file themselves.

    The given *obj* is checked against supported types and
    automatically passed to the appropriate constructor if a match is
    found. If *obj* is a string, it is treated as a file path whose
    extension determines its content type. Any \**args* and \*\**kwds*
    are passed along to the matching constructor::

        from get_reader import get_reader

        # CSV file.
        reader = get_reader('myfile.csv')

        # Database connection.
        connection = ...
        reader = get_reader(connection, 'SELECT col1, col2 FROM mytable;')

        # Pandas DataFrame.
        df = pd.DataFrame([...])
        reader = get_reader(df)

        # Excel file.
        reader = get_reader('myfile.xlsx', worksheet='Sheet2')

    If the *obj* type cannot be determined automatically, users can
    call the constructor methods directly.
    """
    def __call__(self, obj, *args, **kwds):
        if isinstance(obj, string_types):
            lowercase = obj.lower()

            if lowercase.endswith('.csv'):
                return self.from_csv(obj, *args, **kwds)

            if lowercase.endswith('.xlsx') or lowercase.endswith('.xls'):
                return self.from_excel(obj, *args, **kwds)

            if lowercase.endswith('.dbf'):
                return self.from_dbf(obj, *args, **kwds)

        else:
            if isinstance(obj, file_types) \
                    and getattr(obj, 'name', '').lower().endswith('.csv'):
                return self.from_csv(obj, *args, **kwds)

            if all(hasattr(obj, x) for x in ('cursor', 'commit', 'close')):
                return self.from_sql(obj, *args, **kwds)

            squint = sys.modules.get('squint')
            if squint:
                if isinstance(obj, (squint.Query,
                                    squint.Select,
                                    squint.Result)):
                    return self.from_squint(obj, *args, **kwds)

            pandas = sys.modules.get('pandas')
            if pandas:
                if isinstance(obj, (pandas.DataFrame, pandas.Series, pandas.Index)):
                    return self.from_pandas(obj, *args, **kwds)

            if isinstance(obj, Iterable):
                iterator = iter(obj)
                first_value = next(iterator, None)
                iterator = chain([first_value], iterator)

                if isinstance(first_value, dict):
                    return self.from_dicts(iterator, *args, **kwds)

                if isinstance(first_value, (list, tuple)):
                    return iterator  # Already seems reader-like.

        msg = ('unable to determine constructor for {0!r}: specify a '
               'constructor to load, for example get_reader.from_csv(...), '
               'get_reader.from_pandas(...), etc.')
        raise TypeError(msg.format(obj))

    def from_csv(self, csvfile, encoding='utf-8', dialect='excel', **kwds):
        """Return a reader object which will iterate over lines in
        the given *csvfile*. The *csvfile* can be a string (treated
        as a file path) or any object which supports the iterator
        protocol and returns a string each time its __next__() method
        is called---file objects and list objects are both suitable.
        If *csvfile* is a file object, it should be opened with
        ``newline=''``.
        """
        if isinstance(csvfile, string_types):
            encoding = _normalize_decoder(encoding)
            reader, close_file = _from_csv_path(csvfile, encoding, dialect=dialect, **kwds)
            return Reader(reader, closefunc=close_file)

        reader = _from_csv_iterable(csvfile, encoding, dialect=dialect, **kwds)
        return Reader(reader)

    def from_dicts(self, records, fieldnames=None):
        """Takes a container of dictionary *records* and returns a
        Reader. This can be thought of as converting a `csv.DictReader`
        into a plain, non-dictionary reader.
        """
        generator = _from_dicts(records, fieldnames=fieldnames)
        return Reader(generator)

    def from_sql(self, connection, table_or_query):
        """Return a reader object which will iterate over the records
        from a given database table or over the records returned from
        a SQL query.
        """
        reader, close_cursor = _from_sql(connection, table_or_query)
        return Reader(reader, closefunc=close_cursor)

    def from_pandas(self, obj, index=True):
        """Return a reader object which will iterate over records in
        a pandas DataFrame, Series, Index, or MultiIndex.
        """
        return Reader(_from_pandas(obj, index=index))

    def from_squint(self, obj, fieldnames=None):
        """Return a reader object which will iterate over the records
        returned from a squint Select, Query, or Result. If the
        *fieldnames* argument is not provided, this function tries to
        construct names using the values from the underlying object.

        .. note::

            This constructor requires the optional, third-party
            library squint.
        """
        return Reader(_from_squint(obj, fieldnames=fieldnames))

    def from_excel(self, path, worksheet=0):
        """Return a reader object which will iterate over lines in the
        given Excel worksheet. The *path* must specify an XLSX or XLS
        file and *worksheet* should specify the index or name of the
        worksheet to load (defaults to the first worksheet).

        Load first worksheet::

            reader = get_reader.from_excel('mydata.xlsx')

        Specific worksheets can be loaded by name (a string) or
        index (an integer)::

            reader = get_reader.from_excel('mydata.xlsx', 'Sheet 2')

        .. note::

            This constructor requires the optional, third-party
            library xlrd.
        """
        reader, release_resources = _from_excel(path, worksheet=worksheet)
        return Reader(reader, closefunc=release_resources)

    def from_dbf(self, filename, encoding=None, **kwds):
        """Return a reader object which will iterate over lines in the
        given DBF file (from dBase, FoxPro, etc.).

        .. note::

            This constructor requires the optional, third-party
            library dbfread.
        """
        reader, close_generator = _from_dbf(filename, encoding=encoding, **kwds)
        return Reader(reader, closefunc=close_generator)


get_reader = GetReaderType()
