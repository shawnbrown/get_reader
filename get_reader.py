# -*- coding: utf-8 -*-
import csv
import io
import itertools
import sys
from collections import Iterable
from collections import OrderedDict


try:
    callable  # Removed from 3.0 and 3.1, added back in 3.2.
except NameError:
    def callable(obj):
        parent_types = type(obj).__mro__
        return any('__call__' in typ.__dict__ for typ in parent_types)

try:
    string_types = basestring
    file_types = (io.IOBase, file)
except NameError:
    string_types = str
    file_types = io.IOBase


def _dict_generator(reader, fieldnames=None, restkey=None, restval=None):
    """Accepts a csv.reader-like object and yields csv.DictReader-like
    rows.
    """
    iterator = iter(reader)
    if not fieldnames:
        fieldnames = next(iterator, [])

    for row in iterator:
        if row == []:                          # This code is
            continue                           # adapted from the
        d = OrderedDict(zip(fieldnames, row))  # csv.DictReader
        lf = len(fieldnames)                   # class in the
        lr = len(row)                          # Python 3.6
        if lf < lr:                            # Standard Library.
            d[restkey] = row[lf:]
        elif lf > lr:
            for key in fieldnames[lr:]:
                d[key] = restval
        yield d


########################################################################
# CSV Reader.
########################################################################
if sys.version_info[0] >= 3:

    def _from_csv_iterable(iterable, encoding, fieldnames=None, restkey=None,
                           restval=None, **kwds):
        # The *encoding* arg is not used but it's included so that
        # all of the csv-helper functions have the same signature.
        return csv.DictReader(iterable, fieldnames, restkey, restval, **kwds)


    def _from_csv_path(path, encoding, fieldnames=None, restkey=None,
                       restval=None, **kwds):
        with open(path, 'rt', encoding=encoding, newline='') as f:
            reader = csv.reader(f, **kwds)
            for d in _dict_generator(reader, fieldnames, restkey, restval):
                yield d

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


    def _from_csv_iterable(iterable, encoding, fieldnames=None, restkey=None,
                           restval=None, **kwds):
        # Check that iterable is expected to return bytes (not strings).
        try:
            if isinstance(iterable, file):
                assert 'b' in iterable.mode
            elif isinstance(iterable, io.IOBase):
                assert not isinstance(iterable, io.TextIOBase)
            else:
                pass
                # If *iterable* is a generic iterator, we just have to
                # trust that the user knows what they're doing. Because
                # in Python 2, there's no reliable way to tell the
                # difference between encoded bytes and decoded strings:
                #
                #   >>> b'x' == 'x'
                #   True
                #
        except AssertionError:
            msg = ('Python 2 unicode compatibility expects bytes, not '
                   'strings (did you open the file in binary mode?)')
            raise TypeError(msg)

        # Create an empty csv.DictReader---by default, it contains
        # a non-unicode csv.reader internally. Then, replace its
        # internal reader with a unicode-compatible one.
        dict_reader = csv.DictReader([], fieldnames, restkey, restval)
        dict_reader.reader = UnicodeReader(iterable, encoding=encoding, **kwds)
        return dict_reader


    def _from_csv_path(path, encoding, fieldnames=None, restkey=None,
                       restval=None, **kwds):
        with io.open(path, 'rb') as f:
            reader = UnicodeReader(f, encoding=encoding, **kwds)
            for d in _dict_generator(reader, fieldnames, restkey, restval):
                yield d


def from_csv(csvfile, encoding='utf-8', fieldnames=None, **kwds):
    """Return a csv.DictReader or DictReader-like iterator which will
    iterate over lines in the given data. The *csvfile* can be a file
    path (a string) or any object supported by the csv.reader function.
    """
    if isinstance(csvfile, string_types):
        return _from_csv_path(csvfile, encoding, fieldnames, **kwds)
    return _from_csv_iterable(csvfile, encoding, fieldnames, **kwds)


########################################################################
# Pandas DataFrame Reader.
########################################################################
def from_pandas(df, index=True):
    """Takes a pandas DataFrame and returns a generator that operates
    like a csv.DictReader---it yields rows as OrderedDict objects whose
    keys are derived from the DataFrame's index and column names.
    """
    if index:
        fieldnames = list(df.index.names) + list(df.columns)
    else:
        fieldnames = list(df.columns)

    records = df.to_records(index=index)
    for record in records:
        yield OrderedDict(zip(fieldnames, record))


########################################################################
# MS Excel Reader.
########################################################################
def from_excel(path, worksheet=0):
    """Returns a generator that operates like a csv.DictReader---it
    yields rows as OrderedDict objects whose keys are derived from
    values in the first row of the specified *worksheet*.

    The given *path* must specify an XLSX or XLS file and *worksheet*
    must specify the index or name of the worksheet to load (defaults
    to the first worksheet).

    Load first worksheet::

        source = from_excel('somefile.xlsx')

    Specific worksheets can be loaded by name (a string) or
    index (an integer)::

        source = from_excel('somefile.xlsx', 'Sheet 2')

    .. note::
        This function requires the optional, third-party
        package `xlrd <https://pypi.python.org/pypi/xlrd>`_.
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
        data = (sheet.row_values(index) for index in range(sheet.nrows))

        for d in _dict_generator(data):
            yield d

    finally:
        book.release_resources()


########################################################################
# DBF Reader.
########################################################################
def from_dbf(filename, encoding=None, **kwds):
    """Takes a DBF file (from dBase, FoxPro, etc.) and returns
    a generator that operates like a csv.DictReader---it yields
    rows as OrderedDict objects whose keys are derived from the
    DBF table's field names.
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
    if 'load' not in kwds:                           # In this function,
        kwds['load'] = False                         # dbfread does all of the
    kwds['recfactory'] = OrderedDict                 # work--it is included
                                                     # so that the get_reader()
    table = dbfread.DBF(filename, encoding, **kwds)  # dispatcher can more
    for record in table:                             # easily detect and
        yield record                                 # auto-load DBF files.


########################################################################
# Function Dispatching.
########################################################################
def get_reader(obj, *args, **kwds):
    """Returns a csv.DictReader or a DictReader-like iterator."""
    if isinstance(obj, string_types):
        lowercase = obj.lower()
        if lowercase.endswith('.csv'):
            return from_csv(obj, *args, **kwds)
        if lowercase.endswith('.xlsx') or lowercase.endswith('.xls'):
            return from_excel(obj, *args, **kwds)
        if lowercase.endswith('.dbf'):
            return from_dbf(obj, *args, **kwds)
        raise TypeError('file {0!r} has no recognized extension'.format(obj))

    if isinstance(obj, file_types) \
            and getattr(obj, 'name', '').lower().endswith('.csv'):
        return from_csv(obj, *args, **kwds)

    if 'pandas' in sys.modules:
        if isinstance(obj, sys.modules['pandas'].DataFrame):
            return from_pandas(obj, *args, **kwds)

    msg = ('unable to determine constructor for {0!r}, specify a '
           'constructor to load - for example: get_reader.from_csv(...), '
           'get_reader.from_pandas(...), etc.')
    raise TypeError(msg.format(obj))


# Add specific constructors functions as properties to
# get_reader()--this mimics alternate class constructors.
get_reader.from_csv = from_csv
get_reader.from_pandas = from_pandas
get_reader.from_excel = from_excel
get_reader.from_dbf = from_dbf
