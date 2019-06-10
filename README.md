get_reader
==========

A simple interface for getting reader objects (like those returned from
`csv.reader()` from various data sources (CSV, XLSX, DBF, etc.).

* Provides two simple interfaces: `get_reader()` and `ReaderLike`
* Unicode aware text handling
* Supports Python 3 and 2 with the same interface
* No hard dependencies---though `xlrd` and `dbfread` are required to
  load Excel or DBF data from file paths
* Autodetects file types in many cases
* Provides accessor methods to use where autodetection is inadequate
* Apache 2 license


Install
-------

You can install `get_reader` using `pip` or you can vendor it directly in
your own projects:

> ```shell
> pip install get_reader
> ```


Reference
---------

**get\_reader**(*obj*, \**args*, \*\**kwds*)

> Return a reader object which will iterate over records in the
> given data—like a `csv.reader()`.
>
> The *obj* type is used to automatically determine the appropriate
> handler. If obj is a string, it is treated as a file path whose
> extension determines its content type. Any \**args* and \*\**kwds*
> are passed to the underlying handler.
>
> Using auto-detection:
>
>> ```python
>> from get_reader import get_reader
>>
>> # CSV file.
>> reader = get_reader('myfile.csv')
>>
>> # Excel file.
>> reader = get_reader('myfile.xlsx', worksheet='Sheet2')
>>
>> # Pandas DataFrame.
>> df = pandas.DataFrame([...])
>> reader = get_reader(df)
>>
>> # DBF file.
>> reader = get_reader('myfile.dbf')
>> ```
>
> If the *obj* type cannot be automatically determined, you can call one
> of the `from_...()` methods listed below.
>
>
> **from\_csv**(*csvfile*, *encoding*='utf-8', \*\**kwds*)
>
>> Return a reader object which will iterate over lines in the
>> given *csvfile*. The *csvfile* can be a string (treated as a
>>  file path) or any object which supports the iterator protocol
>> and returns a string each time its `__next__()` method is
>> called---file objects and list objects are both suitable. If
>> *csvfile* is a file object, it should be opened with `newline=''`.
>>
>>> ```python
>>> from get_reader import get_reader
>>> reader = get_reader.from_csv('myfile.tab', delimiter='\t')
>>> ```
>
>
> **from\_excel**(*path*, *worksheet*=0)
>
>> Return a reader object which will iterate over lines in the given Excel
>> worksheet. path must specify to an XLSX or XLS file and worksheet should
>> specify the index or name of the worksheet to load (defaults to the first
>> worksheet).
>>
>> Load first worksheet:
>>
>>> ```python
>>> from get_reader import get_reader
>>> reader = get_reader.from_excel('mydata.xlsx')
>>> ```
>>
>> Specific worksheets can be loaded by name (a string) or index
>> (an integer):
>>
>>> ```python
>>> reader = get_reader.from_excel('mydata.xlsx', 'Sheet 2')
>>> ```
>
>
> **from\_pandas**(*df*, *index*=True)
>
>> Return a reader object which will iterate over records in
>> the `pandas.DataFrame` *df*.
>
>
> **from\_dbf**(*filename*, *encoding*=None, \*\**kwds*)
>
>> Return a reader object which will iterate over lines in the given
>> DBF file (from dBase, FoxPro, etc.).
>
>
> **from\_squint**(*obj*, *fieldnames*=None)
>
>> Return a reader object which will iterate over the records returned from
>> a squint `Select`, `Query`, or `Result`. If the *fieldnames* argument is
>> not provided, this function tries to construct names using the values from
>> the underlying object.
>
>
> **from\_dicts**(*records*, *fieldnames*=None)
>
>> Return a reader object which will iterate over the given
>>  dictionary *records*. This can be thought of as converting a
>>  `csv.DictReader()` into a plain, non-dictionary `csv.reader()`.
>>
>>> ```python
>>> from get_reader import get_reader
>>>
>>> dictrows = [
>>>     {'A': 1, 'B': 'x'},
>>>     {'A': 2, 'B': 'y'},
>>> ]
>>> reader = get_reader.from_dict(dictrows)
>>> ```
>>
>> This method assumes that record contents are consistent. If the first record
>> in a dictionary, it is assumed that all following records will be dictionaries
>> with matching keys.
>
>
> **from\_namedtuples**(*records*)
>
>> Return a reader object which will iterate over the given
>> `namedtuple` records.
>>
>>> ```python
>>> from collections import namedtuple
>>> from get_reader import get_reader
>>>
>>> ntup = namedtuple('mytuple', ['A', 'B'])
>>>
>>> tuplerows = [
>>>     ntup(A=1, B='x'),
>>>     ntup(A=2, B='y'),
>>> ]
>>> reader = get_reader.from_dict(tuplerows)
>>> ```

------------------------------------

Freely licensed under the Apache License, Version 2.0

(C) Copyright 2018 -- 2019 Shawn Brown.
