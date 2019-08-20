# -*- coding: utf-8 -*-
import csv
import io
import sys
from abc import ABCMeta
from itertools import (
    chain,
    islice,
)

try:
    from abc import ABC  # New in version 3.4.
    ABC.__slots__  # New in version 3.7
except (ImportError, AttributeError):
    # Using Python 2 and 3 compatible syntax.
    ABC = ABCMeta('ABC', (object,), {'__slots__': ()})

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


__version__ = '0.0.2.dev0'


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


class Reader(ABC):
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
        if self._closefunc:
            self._closefunc()
            self._closefunc = None

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
    _csvreader_type = type(csv.reader([]))

    def __instancecheck__(self, inst):  # <- Only looked up on metaclass.
        if isinstance(inst, (Reader, self._csvreader_type)):
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
    def __new__(cls):
        msg = ("Can't instantiate abstract class "
               "ReaderLike, use only for type checking")
        raise TypeError(msg)


#######################################################################
# Data handling functions.
#######################################################################

if PY2:

    import codecs


    def _unicode_rows(stream, encoding, dialect, **kwds):
        """Unicode aware CSV handling for Python 2."""
        if isinstance(stream, io.IOBase):
            streamreader_type = codecs.getreader(encoding)
            decoded_stream = streamreader_type(stream)
        elif isinstance(stream, Iterable):
            decoded_stream = (row.decode(encoding) for row in stream)
        else:
            cls_name = stream.__class__.__name__
            raise TypeError('unsupported type {0}'.format(cls_name))

        encoded_utf8 = (x.encode('utf-8') for x in decoded_stream)
        reader = csv.reader(encoded_utf8, dialect=dialect, **kwds)
        make_unicode = lambda row: [unicode(s, 'utf-8') for s in row]
        return (make_unicode(row) for row in reader)


    def _from_csv_path(path, encoding, dialect, **kwds):
        fh = open(path, 'rb')
        try:
            generator = _unicode_rows(fh, encoding, dialect=dialect, **kwds)
        except Exception:
            fh.close()
            raise
        return (generator, fh)


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
        return (reader, fh)


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


def _from_namedtuples(records):
    """Takes a container of namedtuple *records* and returns a
    generator.
    """
    records = iter(records)
    first_record = next(records, None)
    if first_record:
        yield first_record._fields  # Header row.
        yield first_record

    for record in records:
        yield record


def _from_pandas(df, index=True):
    """Takes a pandas.DataFrame and returns a generator."""
    if index:
        yield list(df.index.names) + list(df.columns)
    else:
        yield list(df.columns)

    records = df.to_records(index=index)
    for record in records:
        yield list(record)


def _from_datatest(obj, fieldnames=None):
    """Takes a Select, Query, or Result and returns a generator."""
    datatest = sys.modules['datatest']
    if isinstance(obj, datatest.Query):
        query = obj
    elif isinstance(obj, datatest.Select):
        query = obj(tuple(obj.fieldnames))
    elif isinstance(obj, datatest.Result):
        query = datatest.Query.from_object(obj)
    else:
        raise TypeError('must be datatest Select, Query, or Result')

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
    if 'load' not in kwds:
        kwds['load'] = False

    def recfactory(record):
        return [x[1] for x in record]

    kwds['recfactory'] = recfactory
    table = dbfread.DBF(filename, encoding, **kwds)

    yield table.field_names  # <- Header row.

    for record in table:
        yield record


#######################################################################
# Get Reader.
#######################################################################
class GetReaderType(object):
    r"""Return a reader object which will iterate over records in the
    given data---like :py:func:`csv.reader`.

    The *obj* type is used to automatically determine the appropriate
    handler. If *obj* is a string, it is treated as a file path whose
    extension determines its content type. Any *\*args* and *\*\*kwds*
    are passed to the underlying handler::

        # CSV file.
        reader = get_reader('myfile.csv')

        # Excel file.
        reader = get_reader('myfile.xlsx', worksheet='Sheet2')

        # Pandas DataFrame.
        df = pandas.DataFrame([...])
        reader = get_reader(df)

    If the *obj* type cannot be determined automatically, you can
    call one of the "`from_...()`" constructor methods listed below.
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

            if 'datatest' in sys.modules:
                datatest = sys.modules['datatest']
                if isinstance(obj, (datatest.Query,
                                    datatest.Select,
                                    datatest.Result)):
                    return self.from_datatest(obj, *args, **kwds)

            if 'pandas' in sys.modules:
                if isinstance(obj, sys.modules['pandas'].DataFrame):
                    return self.from_pandas(obj, *args, **kwds)

            if isinstance(obj, Iterable):
                iterator = iter(obj)
                first_value = next(iterator, None)
                iterator = chain([first_value], iterator)

                if isinstance(first_value, dict):
                    return self.from_dicts(iterator, *args, **kwds)

                if hasattr(first_value, '_fields'):
                    return self.from_namedtuples(iterator, *args, **kwds)

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
            reader, fh = _from_csv_path(csvfile, encoding, dialect=dialect, **kwds)
            return Reader(reader, closefunc=fh.close)

        reader = _from_csv_iterable(csvfile, encoding, dialect=dialect, **kwds)
        return Reader(reader)

    def from_dicts(self, records, fieldnames=None):
        """Takes a container of dictionary *records* and returns a
        Reader. This can be thought of as converting a `csv.DictReader`
        into a plain, non-dictionary reader.
        """
        generator = _from_dicts(records, fieldnames=fieldnames)
        return Reader(generator)

    def from_namedtuples(self, records):
        """Takes a container of namedtuple *records* and returns a
        Reader. The first item in the reader will be a header row
        taken from the first namedtuple's `_fields` property.
        """
        generator = _from_namedtuples(records)
        return Reader(generator)

    def from_pandas(self, df, index=True):
        """Return a reader object which will iterate over records in
        the pandas.DataFrame *df*.

        .. note::

            This constructor requires the optional, third-party
            library pandas.
        """
        return Reader(_from_pandas(df, index=index))

    def from_datatest(self, obj, fieldnames=None):
        """Return a reader object which will iterate over the records
        returned from a datatest Select, Query, or Result. If the
        *fieldnames* argument is not provided, this function tries to
        construct names using the values from the underlying object.

        .. note::

            This constructor requires the optional, third-party
            library datatest.
        """
        return Reader(_from_datatest(obj, fieldnames=fieldnames))

    def from_excel(self, path, worksheet=0):
        """Return a reader object which will iterate over lines in the
        given Excel worksheet. *path* must specify to an XLSX or XLS
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
        return Reader(_from_dbf(filename, encoding=encoding, **kwds))


get_reader = GetReaderType()
