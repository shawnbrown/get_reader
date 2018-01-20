# -*- coding: utf-8 -*-
import csv
import inspect
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
except NameError:
    string_types = str


def _dict_generator(reader, fieldnames=None, restkey=None, restval=None):
    if not fieldnames:
        fieldnames = next(reader, [])

    for row in reader:
        if row == []:                          # This code is
            continue                           # adapted from the
        d = OrderedDict(zip(fieldnames, row))  # csv.DictReader
        lf = len(fieldnames)                   # class in the
        lr = len(row)                          # Python 3.6
        if lf < lr:                            # Standard Library.
            d[self.restkey] = row[lf:]
        elif lf > lr:
            for key in fieldnames[lr:]:
                d[key] = restval
        yield d


########################################################################
# CSV Reader.
########################################################################
if sys.version_info[0] >= 3:

    def _from_csv_path(path, encoding, fieldnames, restkey=None,
                       restval=None, **kwds):
        with open(path, 'rt', encoding=encoding, newline='') as f:
            reader = csv.reader(f, **kwds)
            for d in _dict_generator(reader, fieldnames, restkey, restval):
                yield d


    def _from_csv_iterable(iterable, encoding, fieldnames, restkey=None,
                           restval=None, **kwds):
        # The *encoding* arg is not used but included so that
        # all csv-helper functions have the same signature.
        return csv.DictReader(iterable, fieldnames, restkey, restval, **kwds)

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


    def _from_csv_path(path, encoding, fieldnames, restkey=None,
                       restval=None, **kwds):
        with io.open(path, 'rb') as f:
            reader = UnicodeReader(f, encoding=encoding, **kwds)
            for d in _dict_generator(reader, fieldnames, restkey, restval):
                yield d


    def _from_csv_iterable(iterable, encoding, fieldnames, restkey=None,
                           restval=None, **kwds):
        # Make sure that iterable returns bytes (not strings or other types).
        iterator = iter(iterable)
        first_value = next(iterator, b'')
        if not isinstance(first_value, bytes):
            raise TypeError('Python 2 compatibility expects bytes, not '
                            'strings (did you open the file in binary mode?)')
        iterator = itertools.chain([first_value], iterator)

        # Get unicode-compatible reader and create DictReader instance.
        unicode_reader = UnicodeReader(iterator, encoding=encoding, **kwds)
        if not fieldnames:
            fieldnames = next(unicode_reader, [])
        reader = csv.DictReader(io.BytesIO(None),  # Use an empty stream
                                fieldnames,        # because csv.DictReader
                                restkey=restkey,   # creates a non-unicode
                                restval=restval)   # reader when initialized.
        reader.reader = unicode_reader  # <- Swap-in unicode reader.

        return reader


def from_csv(file, **kwds):
    """Return a csv.DictReader or DictReader-like iterator which will
    iterate over lines in the given *file*. The *file* can be a file
    path (a string) or any object supported by the csv.reader function.
    """
    fieldnames = kwds.pop('fieldnames', None)  # Emulate keyword-only args to
    encoding = kwds.pop('encoding', 'utf-8')   # support Python 2.7 and 2.6.
    if isinstance(file, string_types):
        return _from_csv_path(file, encoding, fieldnames, **kwds)
    return _from_csv_iterable(file, encoding, fieldnames, **kwds)


if hasattr(inspect, 'Signature'):  # inspect.Signature() is new in 3.3
    from_csv.__signature__ = inspect.Signature([
        inspect.Parameter('file', inspect.Parameter.POSITIONAL_OR_KEYWORD),
        inspect.Parameter('encoding', inspect.Parameter.KEYWORD_ONLY, default='UTF-8'),
        inspect.Parameter('fieldnames', inspect.Parameter.KEYWORD_ONLY, default=None),
        inspect.Parameter('kwds', inspect.Parameter.VAR_KEYWORD),
    ])


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
        data = (sheet.row(i) for i in range(sheet.nrows))
        data = ([x.value for x in row] for row in data)
        for d in _dict_generator(data):
            yield d
    finally:
        book.release_resources()


########################################################################
# Function Dispatching.
########################################################################
def get_reader(obj, *args, **kwds):
    """Returns a csv.DictReader or a DictReader-like iterator."""
    if isinstance(obj, string_types):
        if obj.endswith('.csv'):
            return from_csv(obj, *args, **kwds)
        if obj.endswith('.xlsx') or obj.endswith('.xls'):
            return from_excel(obj, *args, **kwds)
        raise TypeError('file {0!r} has no recognized extension'.format(obj))

    if isinstance(obj, io.IOBase) \
            and getattr(obj, 'name', '').endswith('.csv'):
        return from_csv(obj, *args, **kwds)

    if 'pandas' in sys.modules:
        if isinstance(obj, sys.modules['pandas'].DataFrame):
            return from_pandas(obj, *args, **kwds)

    raise TypeError('unsupported type {0}'.format(obj.__class__.__name__))
