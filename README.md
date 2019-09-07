get_reader
==========

![devstatus]&#32;[![build-img]][build-url] ![pyversions] ![license]

This module provides a `get_reader()` function that returns reader
objects similar to those returned by `csv.reader()`. This function:

* reads data from a variety of sources (CSV, Excel, pandas, etc.)
* provides a single interface across Python versions (including
  Unicode-aware CSV support for Python 2).
* optionally manages file handling and reduces boilerplate code

Open a UTF-8 encoded CSV (also works on old Python 2 versions without
modification):

```python
from get_reader import get_reader

reader = get_reader('myfile.csv')

for row in reader:
    print(', '.join(row))
```

Open a Latin-1 (ISO-8859-1) encoded CSV file:

```python
from get_reader import get_reader

reader = get_reader('myfile.csv', encoding='latin-1')

for row in reader:
    print(', '.join(row))
```

Use the reader as a context manager:

```python
from get_reader import get_reader

with get_reader('myfile.csv') as reader:
    for row in reader:
        print(', '.join(row))
```

Access other data sources if optional extras are installed:

```python
from get_reader import get_reader

# From an MS Excel file.
reader = get_reader('myfile.xlsx')

# From a DBF file.
reader = get_reader('myfile.dbf')

# From a DataFrame.
df = pd.DataFrame([...])
reader = get_reader(df)  # requires pandas
```

Override auto-detect behavior by calling constructors directly:

```python
from get_reader import get_reader

# Specify tab-delimited data from a text file.
reader = get_reader.from_csv('myfile.txt', delimiter='\t')
```


Install
-------

The `get_reader` module has no hard dependencies; is tested on
Python 2.6, 2.7, 3.2 through 3.8, PyPy, PyPy3, and Jython; and
is freely available under the Apache License, version 2.

You can install `get_reader` using `pip`:

```shell
pip install get_reader
```

To install optional support for MS Excel, and DBF files (dBase,
Foxpro, etc.), use the following:

```shell
pip install get_reader[excel,dbf]
```


Reference
---------

**get\_reader**(*obj*, \**args*, \*\**kwds*)

Return a Reader object which will iterate over records in the
given *obj*—like a `csv.reader()`.

The given *obj* is used to automatically determine the appropriate
data handler. If *obj* is a string, it is treated as a file path
whose extension determines its content type. Any \**args* and
\*\**kwds* are passed to the appropriate constructor method. If the
*obj* type cannot be determined automatically, you can call one of
the "`from_x()`" constructor methods directly.

When *obj* is a path, the Reader contains a file object that is
handled internally. Users can close the file by calling the Reader's
`close()` method. Otherwise this underlying file will be automatically
closed when:

* its iterator is exhausted
* the Reader is deleted
* exiting a `with` statement (if used as a context manager)

When given a file-like *obj* (rather than a path), users are
responsible for properly closing this file themselves.

Using auto-detection:

```python
from get_reader import get_reader
...

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

# DBF file.
reader = get_reader('myfile.dbf')
```


> **from\_csv**(*csvfile*, *encoding*='utf-8', dialect='excel', \*\**kwds*)
>
> Return a reader object which will iterate over lines in the
> given *csvfile*. The *csvfile* can be a string (treated as a
>  file path) or any object which supports the iterator protocol
> and returns a string each time its `__next__()` method is
> called---file objects and list objects are both suitable. If
> *csvfile* is a file object, it should be opened with `newline=''`.
>
> ```python
> from get_reader import get_reader
>
> reader = get_reader.from_csv('myfile.tab', delimiter='\t')
> ```
>
> Using explicit file handling:
>
> ```python
> from get_reader import get_reader
>
> with open('myfile.csv') as csvfile:
>
>     reader = get_reader.from_csv(fh)
> ```


> **from\_dicts**(*records*, *fieldnames*=None)
>
> Return a reader object which will iterate over the given
> dictionary *records*. This can be thought of as converting a
> `csv.DictReader()` into a plain, non-dictionary `csv.reader()`.
>
> ```python
> from get_reader import get_reader
>
> dictrows = [
>     {'A': 1, 'B': 'x'},
>     {'A': 2, 'B': 'y'},
> ]
>
> reader = get_reader.from_dicts(dictrows)
> ```
>
> This method assumes that record contents are consistent. If the first
> record is a dictionary, it is assumed that all following records will
> be dictionaries with matching keys.


> **from\_sql**(*connection*, *table\_or\_query*)
>
> Return a reader object which will iterate over the records
> from a given database table or over the records returned from
> a SQL query. The *connection* should be a DBAPI2 compatible
> database connection and *table\_or\_query* must be a string
> with a table name or a SQL query.
>
> Read records from a specified table:
>
> ```python
> from get_reader import get_reader
>
> connection = ...
> reader = get_reader.from_sql(connection, 'mytable')
>```
>
> Read records from the results of a SQL query:
>
> ```python
> reader = get_reader.from_sql(connection, 'SELECT col1, col2 FROM mytable;')
>```
>

> **from\_excel**(*path*, *worksheet*=0)
>
> Return a reader object which will iterate over lines in the given
> Excel worksheet. The *path* must specify an XLSX or XLS file and
> *worksheet* must specify the index or name of the worksheet to
> load (defaults to the first worksheet).
>
> Load first worksheet:
>
> ```python
> from get_reader import get_reader
>
> reader = get_reader.from_excel('mydata.xlsx')
> ```
>
> Specific worksheets can be loaded by name (a string) or index
> (an integer):
>
> ```python
> reader = get_reader.from_excel('mydata.xlsx', 'Sheet 2')
> ```


> **from\_pandas**(*obj*, *index*=True)
>
> Return a reader object which will iterate over records in
> a pandas `DataFrame`, `Series`, `Index` or `MultiIndex`.


> **from\_dbf**(*filename*, *encoding*=None, \*\**kwds*)
>
> Return a reader object which will iterate over lines in the given
> DBF file (from dBase, FoxPro, etc.).


> **from\_squint**(*obj*, *fieldnames*=None)
>
> Return a reader object which will iterate over the records returned
> from a squint `Select`, `Query`, or `Result`. If the *fieldnames*
> argument is not provided, this function tries to construct names
> using the values from the underlying object.


------------------------------------

Freely licensed under the Apache License, Version 2.0

(C) Copyright 2018 – 2019 Shawn Brown.


[devstatus]: https://img.shields.io/pypi/status/get_reader.svg
[build-img]: https://api.travis-ci.org/shawnbrown/get_reader.svg?branch=master
[build-url]: https://travis-ci.org/shawnbrown/get_reader
[pyversions]: https://img.shields.io/pypi/pyversions/get_reader.svg
[license]: https://img.shields.io/badge/license-Apache%202-blue.svg
