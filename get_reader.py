# -*- coding: utf-8 -*-
import csv
import inspect
import io
import sys
from collections import Iterable


if sys.version_info[0] >= 3:
    def _from_csv(csvfile, fieldnames, encoding, **kwds):
        if isinstance(csvfile, str):
            csvfile = open(csvfile, 'rt', encoding=encoding, newline='')
        elif hasattr(csvfile, 'mode'):
            if 't' not in csvfile.mode:
                raise TypeError('expected text-mode file, '
                                'got {0!r}'.format(csvfile.mode))
        elif isinstance(csvfile, io.IOBase):
            if not isinstance(csvfile, io.TextIOBase):
                cls_name = csvfile.__class__.__name__
                raise TypeError('stream object must inherit from '
                                'io.TextIOBase, got {0}'.format(cls_name))
        elif not isinstance(csvfile, Iterable):
            cls_name = csvfile.__class__.__name__
            raise TypeError('unsupported type {0}'.format(cls_name))

        return csv.DictReader(csvfile, fieldnames, **kwds)

else:
    import codecs

    class UTF8Recoder(object):
        """Iterator that reads an encoded stream and reencodes the
        input to UTF-8.

        This class is adapted from example code in Python 2.7 docs
        for the csv module.
        """
        def __init__(self, f, encoding):
            self.reader = codecs.getreader(encoding)(f)

        def __iter__(self):
            return self

        def next(self):
            return self.reader.next().encode('utf-8')


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
            row = self.reader.next()
            return [unicode(s, 'utf-8') for s in row]

        def __iter__(self):
            return self


    def _from_csv(csvfile, fieldnames, encoding, **kwds):
        if isinstance(csvfile, basestring):
            csvfile = open(csvfile, 'rb')
        elif hasattr(csvfile, 'mode'):
            if 'b' not in csvfile.mode:
                raise TypeError('Python 2 compatibility expects binary-'
                                'mode file, got {0!r}'.format(csvfile.mode))
        elif isinstance(csvfile, io.IOBase):
            if isinstance(csvfile, io.TextIOBase):
                cls_name = csvfile.__class__.__name__
                raise TypeError('Python 2 compatibility expects byte '
                                'stream, got {0}'.format(cls_name))
        elif isinstance(csvfile, Iterable):
            raise TypeError('iterator input not supported in Python 2')
        else:
            cls_name = csvfile.__class__.__name__
            raise TypeError('unsupported type {0}'.format(cls_name))

        dictreader_kwds = {}
        dictreader_kwds['restkey'] = kwds.pop('restkey', None)
        dictreader_kwds['restval'] = kwds.pop('restval', None)
        dictreader_kwds['dialect'] = kwds.pop('dialect', 'excel')

        unicode_reader = UnicodeReader(csvfile, encoding=encoding, **kwds)

        if not fieldnames:
            fieldnames = next(unicode_reader)

        reader = csv.DictReader(io.StringIO(None),  # Initialize DictReader
                                fieldnames,         # with empty file object.
                                **dictreader_kwds)

        reader.reader = unicode_reader  # Swap-in unicode reader.

        return reader


def from_csv(file, **kwds):
    """Return a csv.DictReader object which will iterate over lines in
    the given *file*. The *file* can be a file path, file-like object,
    or other object supported by the csv module.
    """
    fieldnames = kwds.pop('fieldnames', None)  # Emulate keyword-only args to
    encoding = kwds.pop('encoding', 'utf-8')   # support Python 2.7 and 2.6.
    return _from_csv(file, fieldnames, encoding, **kwds)


if hasattr(inspect, 'Signature'):  # inspect.Signature() is new in 3.3
    from_csv.__signature__ = inspect.Signature([
        inspect.Parameter('file', inspect.Parameter.POSITIONAL_OR_KEYWORD),
        inspect.Parameter('fieldnames', inspect.Parameter.KEYWORD_ONLY, default=None),
        inspect.Parameter('encoding', inspect.Parameter.KEYWORD_ONLY, default='UTF-8'),
        inspect.Parameter('kwds', inspect.Parameter.VAR_KEYWORD),
    ])
