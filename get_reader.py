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


__version__ = '0.0.2.dev0'


try:
    string_types = basestring
    file_types = (io.IOBase, file)
except NameError:
    string_types = str
    file_types = io.IOBase


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


########################################################################
# Unicode Aware CSV Handling.
########################################################################
if sys.version_info[0] >= 3:

    def _from_csv_iterable(iterable, encoding, **kwds):
        return csv.reader(iterable, **kwds)
        # Above, the *encoding* arg is not used but is included so
        # that the csv-helper functions have the same signature.

    def _from_csv_path(path, encoding, **kwds):
        with open(path, 'rt', encoding=encoding, newline='') as f:
            for row in csv.reader(f, **kwds):
                yield row

else:
    import codecs

    class UTF8Recoder(object):
        """Iterator that reads an encoded stream and reencodes the
        input to UTF-8.

        This class is adapted from example code in Python 2.7 docs
        for the csv module.
        """
        def __init__(self, f, encoding):
            if isinstance(f, io.IOBase):
                stream_reader = codecs.getreader(encoding)
                self.reader = stream_reader(f)
            elif isinstance(f, Iterable):
                self.reader = (row.decode(encoding) for row in f)
            else:
                cls_name = f.__class__.__name__
                raise TypeError('unsupported type {0}'.format(cls_name))

        def __iter__(self):
            return self

        def next(self):
            return next(self.reader).encode('utf-8')


    class UnicodeReader(object):
        """A CSV reader which will iterate over lines in the CSV
        file *f*, which is encoded in the given encoding.

        This class is adapted from example code in Python 2.7 docs
        for the csv module.
        """
        def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
            f = UTF8Recoder(f, encoding)
            self.reader = csv.reader(f, dialect=dialect, **kwds)

        @property
        def line_num(self):
            return self.reader.line_num

        @line_num.setter
        def line_num(self, value):
            self.reader.line_num = value

        def next(self):
            row = next(self.reader)
            return [unicode(s, 'utf-8') for s in row]

        def __iter__(self):
            return self

    def _from_csv_iterable(iterable, encoding, **kwds):
        # Check that iterable is expected to return bytes (not strings).
        if isinstance(iterable, file):
            using_bytes = 'b' in iterable.mode
        elif isinstance(iterable, io.IOBase):
            using_bytes = not isinstance(iterable, io.TextIOBase)
        else:
            # If *iterable* is a generic iterator, we just have to
            # trust that the user knows what they're doing. Because
            # in Python 2, there's no reliable way to tell the
            # difference between encoded bytes and decoded strings:
            #
            #   >>> b'x' == 'x'
            #   True
            #
            using_bytes = True

        if not using_bytes:
            msg = ('Python 2 unicode compatibility expects bytes, not '
                   'strings (did you open the file in binary mode?)')
            raise TypeError(msg)

        return UnicodeReader(iterable, encoding=encoding, **kwds)


    def _from_csv_path(path, encoding, **kwds):
        with open(path, 'rb') as f:
            for row in UnicodeReader(f, encoding=encoding, **kwds):
                yield row


class Reader(ABC):
    def __init__(self, iterable, closefunc=None):
        self.__wrapped__ = iter(iterable)
        self._close = closefunc

    def close(self):
        if self._close:
            self._close()
            self._close = None

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


########################################################################
# Get Reader.
########################################################################
class get_reader(object):
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
    def __new__(cls, obj, *args, **kwds):
        if isinstance(obj, string_types):
            lowercase = obj.lower()

            if lowercase.endswith('.csv'):
                return cls.from_csv(obj, *args, **kwds)

            if lowercase.endswith('.xlsx') or lowercase.endswith('.xls'):
                return cls.from_excel(obj, *args, **kwds)

            if lowercase.endswith('.dbf'):
                return cls.from_dbf(obj, *args, **kwds)

        else:
            if isinstance(obj, file_types) \
                    and getattr(obj, 'name', '').lower().endswith('.csv'):
                return cls.from_csv(obj, *args, **kwds)

            if 'datatest' in sys.modules:
                datatest = sys.modules['datatest']
                if isinstance(obj, (datatest.Query,
                                    datatest.Select,
                                    datatest.Result)):
                    return cls.from_datatest(obj, *args, **kwds)

            if 'pandas' in sys.modules:
                if isinstance(obj, sys.modules['pandas'].DataFrame):
                    return cls.from_pandas(obj, *args, **kwds)

            if isinstance(obj, Iterable):
                iterator = iter(obj)
                first_value = next(iterator, None)
                iterator = chain([first_value], iterator)

                if isinstance(first_value, dict):
                    return cls.from_dicts(iterator, *args, **kwds)

                if hasattr(first_value, '_fields'):
                    return cls.from_namedtuples(iterator, *args, **kwds)

                if isinstance(first_value, (list, tuple)):
                    return iterator  # Already seems reader-like.

        msg = ('unable to determine constructor for {0!r}: specify a '
               'constructor to load, for example get_reader.from_csv(...), '
               'get_reader.from_pandas(...), etc.')
        raise TypeError(msg.format(obj))

    @staticmethod
    def from_csv(csvfile, encoding='utf-8', **kwds):
        """Return a reader object which will iterate over lines in
        the given *csvfile*. The *csvfile* can be a string (treated
        as a file path) or any object which supports the iterator
        protocol and returns a string each time its __next__() method
        is called---file objects and list objects are both suitable.
        If *csvfile* is a file object, it should be opened with
        ``newline=''``.
        """
        if isinstance(csvfile, string_types):
            return _from_csv_path(csvfile, encoding, **kwds)
        return _from_csv_iterable(csvfile, encoding, **kwds)

    @staticmethod
    def from_dicts(records, fieldnames=None):
        """Return a reader object which will iterate over the given
        dictionary records. This can be thought of as converting a
        :py:func:`csv.DictReader` into a plain, non-dictionary reader.
        """
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

    @staticmethod
    def from_namedtuples(records):
        """Return a reader object which will iterate over the given
        namedtuple records.
        """
        records = iter(records)
        first_record = next(records, None)
        if first_record:
            yield first_record._fields  # Header row.
            yield first_record

        for record in records:
            yield record

    @staticmethod
    def from_datatest(obj, fieldnames=None):
        """Return a reader object which will iterate over the records
        returned from a datatest Select, Query, or Result. If the
        *fieldnames* argument is not provided, this function tries to
        construct names using the values from the underlying object.

        .. note::

            This constructor requires the optional, third-party
            library datatest.
        """
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

    @staticmethod
    def from_pandas(df, index=True):
        """Return a reader object which will iterate over records in
        the pandas.DataFrame *df*.

        .. note::

            This constructor requires the optional, third-party
            library pandas.
        """
        if index:
            yield list(df.index.names) + list(df.columns)
        else:
            yield list(df.columns)

        records = df.to_records(index=index)
        for record in records:
            yield list(record)

    @staticmethod
    def from_excel(path, worksheet=0):
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
        try:
            if isinstance(worksheet, int):
                sheet = book.sheet_by_index(worksheet)
            else:
                sheet = book.sheet_by_name(worksheet)

            for index in range(sheet.nrows):
                yield sheet.row_values(index)

        finally:
            book.release_resources()

    @staticmethod
    def from_dbf(filename, encoding=None, **kwds):
        """Return a reader object which will iterate over lines in the
        given DBF file (from dBase, FoxPro, etc.).

        .. note::

            This constructor requires the optional, third-party
            library dbfread.
        """
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
