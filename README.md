get_reader
==========

Get `reader` objects, like those returned by `csv.reader()`, from
various data sources.

The same syntax works on both Python 2.x and 3.x:

```python
from get_reader import get_reader

reader = get_reader('myfile.csv')

for row in reader:
    print(', '.join(row))
```

Supports explicit file handling:

```python
from get_reader import get_reader

with open('myfile.csv', newline='') as csvfile:

    reader = get_reader(csvfile)

    for row in reader:
        print(', '.join(row))
```

Automatically detects other data sources if optional extras are
installed:

```python
from get_reader import get_reader

# From an Excel file
reader = get_reader('myfile.xlsx')  # requires xlrd package

# From a DataFrame
df = pd.DataFrame([...])
reader = get_reader(df)  # requires pandas

# From a DBF file
reader = get_reader('myfile.dbf')  # requires dbfread package
```

Explicit constructors can be called directly to override auto-detect
behavior:

```python
from get_reader import get_reader

# From a tab-delimited text file
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

Return a reader object which will iterate over records in the
given *obj*—like a `csv.reader()`.

The given *obj* is used to automatically determine the appropriate
file handler. If *obj* is a string, it is treated as a file path
whose extension determines its content type. Any \**args* and
\*\**kwds* are passed to the appropriate constructor method. If the
*obj* type cannot be determined automatically, you can call one of
the "`from_x()`" constructor methods directly.

When *obj* is a path, a file object is implicitly created and handled
internally. This underlying file is automatically closed when the
iterator is exhausted, when the reader is deleted, or—if used as a
context manager—when exiting the `with` statement. Users can explicitly
close the underlying file by calling the reader's `close()` method.
However, when the given *obj* is a file-like object (rather than a
path), users are responsible for properly closing the file themselves.

Using auto-detection:

```python
from get_reader import get_reader
...

# CSV file.
reader = get_reader('myfile.csv')

# Excel file.
reader = get_reader('myfile.xlsx', worksheet='Sheet2')

# Pandas DataFrame.
df = pandas.DataFrame([...])
reader = get_reader(df)

# DBF file.
reader = get_reader('myfile.dbf')
```


> **from\_csv**(*csvfile*, *encoding*='utf-8', \*\**kwds*)
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
>  dictionary *records*. This can be thought of as converting a
>  `csv.DictReader()` into a plain, non-dictionary `csv.reader()`.
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


> **from\_excel**(*path*, *worksheet*=0)
>
> Return a reader object which will iterate over lines in the given
> Excel worksheet. path must specify to an XLSX or XLS file and
> worksheet should specify the index or name of the worksheet to
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


> **from\_pandas**(*df*, *index*=True)
>
> Return a reader object which will iterate over records in
> the `pandas.DataFrame` *df*.


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
