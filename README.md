get-reader
==========

![devstatus]&#32;[![build-img]][build-url] ![pyversions] ![license]

This module provides a `get_reader()` function that returns reader
objects similar to those returned by `csv.reader()`. This package:

* reduces common boilerplate code for handling files and reading
  records
* reads data from CSV, pandas, SQL connections, MS Excel, DBF, and squint
* provides a single interface across Python versions (including
  seamless Unicode-aware CSV support for Python 2)
* is easy to incorporate into your own projects:

  * has no hard dependencies
  * runs on Python 2.6, 2.7, 3.2 through 3.8, PyPy, PyPy3, and Jython
  * is freely available under the Apache License, version 2
  * can be easily vendored directly into your codebase if you don't
    want to include it as a dependency


**Open a UTF-8 encoded CSV:**

```python
from get_reader import get_reader

reader = get_reader('myfile.csv')

for row in reader:
    print(', '.join(row))
```

In the above example, file handling is managed automatically by the
reader object. The file is automatically closed when the iterator is
exhausted or when the object is deleted. It also handles Unicode in
Python 2 without changes.


**Open a Latin-1 (ISO-8859-1) encoded CSV file:**

```python
reader = get_reader('myfile.csv', encoding='latin-1')

for row in reader:
    print(', '.join(row))
```


**Use the reader as a context manager:**

```python
with get_reader('myfile.csv') as reader:
    for row in reader:
        print(', '.join(row))
```

In this example, `reader` automatically closes its internal file object
when exiting the `with` block even if the for-loop doesn't finish
exhausting the `reader`.


**Access other data sources:**

```python
# From a pandas DataFrame, Series, Index, or MultiIndex.
df = pd.DataFrame([...])
reader = get_reader(df)  # requires pandas

# From a database connection.
connection = ...
reader = get_reader(connection, 'SELECT col1, col2 FROM mytable;')

# From an Excel file--must install with 'excel' option.
reader = get_reader('myfile.xlsx')

# From a DBF file--must install with 'dbf' option.
reader = get_reader('myfile.dbf')

# From a squint Select, Query, or Result.
select = ...
reader = get_reader(select({'col1': 'col2'}).sum())
```


**Call constructors directly to override auto-detect behavior:**

```python
# Specify tab-delimited data from a text file.
reader = get_reader.from_csv('myfile.dat', delimiter='\t')
```


## Install

The `get_reader` module has no hard dependencies; is tested on
Python 2.6, 2.7, 3.2 through 3.8, PyPy, PyPy3, and Jython; and
is freely available under the Apache License, version 2.

You can install `get_reader` using `pip`:

```shell
pip install get_reader
```

To install optional support for MS Excel and DBF files (dBase,
Foxpro, etc.), use the following:

```shell
pip install get_reader[excel,dbf]
```

**Python 2 Support Statement**

While official support for Python 2 ends on January 1, 2020, this
project will continue to support older versions as long as the
existing ecosystem provides the ability to run automated tests
on those older versions.


## Reference

### get\_reader(*obj*, \**args*, \*\**kwds*)

Return a `Reader` object which will iterate over records in
the given *obj*—like a `csv.reader()`. The given *obj* may
be one of the following:

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
are passed along to the matching constructor:

```python
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
```

If the *obj* type cannot be determined automatically, users can
call the constructor methods directly.


#### Constructor Methods

**get\_reader.from\_csv**(*csvfile*, *encoding*='utf-8', *dialect*='excel', \*\**kwds*)

Return a reader object which will iterate over lines in the
given *csvfile*. The *csvfile* can be a string (treated as a
file path) or any object which supports the iterator protocol
and returns a string each time its `__next__()` method is
called—file objects and list objects are both suitable. If
*csvfile* is a file object, it should be opened with `newline=''`.

```python
from get_reader import get_reader

reader = get_reader.from_csv('myfile.tab', delimiter='\t')
```

Using explicit file handling:

```python
from get_reader import get_reader

with open('myfile.csv') as csvfile:
    reader = get_reader.from_csv(fh)
```


**get\_reader.from\_dicts**(*records*, *fieldnames*=None)

Return a reader object which will iterate over the given
dictionary *records*. This can be thought of as converting a
`csv.DictReader()` into a plain, non-dictionary `csv.reader()`.

```python
from get_reader import get_reader

dictrows = [
    {'A': 1, 'B': 'x'},
    {'A': 2, 'B': 'y'},
]

reader = get_reader.from_dicts(dictrows)
```

This method assumes that record contents are consistent. If the first
record is a dictionary, it is assumed that all following records will
be dictionaries with matching keys.


**get\_reader.from\_sql**(*connection*, *table\_or\_query*)

Return a reader object which will iterate over the records
from a given database table or over the records returned from
a SQL query. The *connection* should be a DBAPI2 compatible
database connection and *table\_or\_query* must be a string
with a table name or a SQL query.

Read records from a specified table:

```python
from get_reader import get_reader

connection = ...
reader = get_reader.from_sql(connection, 'mytable')
```

Read records from the results of a SQL query:

```python
reader = get_reader.from_sql(connection, 'SELECT col1, col2 FROM mytable;')
```


**get\_reader.from\_excel**(*path*, *worksheet*=0)

Return a reader object which will iterate over lines in the given
Excel worksheet. The *path* must specify an XLSX or XLS file and
*worksheet* must specify the index or name of the worksheet to
load (defaults to the first worksheet).

Load first worksheet:

```python
from get_reader import get_reader

reader = get_reader.from_excel('mydata.xlsx')
```

Specific worksheets can be loaded by name (a string) or index
(an integer):

```python
reader = get_reader.from_excel('mydata.xlsx', 'Sheet 2')
```


**get\_reader.from\_pandas**(*obj*, *index*=True)

Return a reader object which will iterate over records in
a pandas `DataFrame`, `Series`, `Index` or `MultiIndex`.

```python
import pandas as pd
from get_reader import get_reader

df = pd.DataFrame(...)
reader = get_reader.from_pandas(df)
```


**get\_reader.from\_dbf**(*filename*, *encoding*=None, \*\**kwds*)

Return a reader object which will iterate over lines in the given
DBF file (from dBase, FoxPro, etc.).

```python
from get_reader import get_reader

reader = get_reader.from_dbf('myfile.dbf')
```


**get\_reader.from\_squint**(*obj*, *fieldnames*=None)

Return a reader object which will iterate over the records returned
from a squint `Select`, `Query`, or `Result`. If the *fieldnames*
argument is not provided, this function tries to construct names
using the values from the underlying object.

```python
import squint
from get_reader import get_reader

select = squint.Select(...)
reader = get_reader.from_squint(select)
```


### *class* Reader(*iterable*, *closefunc=\<no value\>*)

An iterator which will produce rows from the given *iterable*. The
given *iterable* should produce non-string sequences. An optional
*closefunc* may be provided to close associated resources (files,
database cursors, etc.) once the reader is no longer needed—it will
be automatically called when:

* the iterable is exhausted
* exiting a `with` statement (if used as a context manager)
* the Reader is garbage collected


**Reader.close**()

Closes any associated resources (calls *closefunc* early):

```python
from get_reader import Reader

reader = Reader(..., closefunc=...)
reader.close()  # <- Explicitly close resources.
```

If the resources have already been closed, this method passes
without error.


### *class* ReaderLike()

An abstract class that can be used for type checking. Objects
will test as `ReaderLike` if they are one of the following:

* instance of the `Reader` class
* object returned by `csv.reader()`
* non-exhaustible iterable that produces non-string sequences

See the following examples:


```python
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
```

------------------------------------

Freely licensed under the Apache License, Version 2.0

(C) Copyright 2018 – 2019 Shawn Brown.


[devstatus]: https://img.shields.io/pypi/status/get_reader.svg
[build-img]: https://api.travis-ci.org/shawnbrown/get_reader.svg?branch=master
[build-url]: https://travis-ci.org/shawnbrown/get_reader
[pyversions]: https://img.shields.io/pypi/pyversions/get_reader.svg
[license]: https://img.shields.io/badge/license-Apache%202-blue.svg
