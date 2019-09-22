
Get-Reader Changelog
====================

2019-09-22 (0.0.2)
------------------

* Added `from_sql()` constructor to read database tables or SQL results.
* Added support for `Series`, `Index`, and `MultiIndex` objects to the
  existing `from_pandas()` constructor.
* Added a `Reader` class to provide consistent return values and automatic
  resource-handling (for closing files, database cursors, etc.).
* Changed all constructors to return `Reader` instances.
* Fixed file-closing behavior when DBF files are not fully consumed.
* Changed `from_datatest()` to `from_squint()` to reflect new package name.
* Added Python 2 support statement to README:

  > While official support for Python 2 ends on January 1, 2020, this
  > project will continue to support older versions as long as the
  > existing ecosystem provides the ability to run automated tests
  > on those older versions.


2019-08-11 (0.0.1)
------------------

* First public release of packaged module.


2019-08-04 (0.0.1.dev4)
-----------------------

* Added `ReaderLike` class to help make type-checking more convenient.
* Removed support for Python 3.1.


2018-07-09 (0.0.1.dev3)
-----------------------

* Added `from_datatest()` constructor method to read datatest `Select` and
  `Query` objects.


2018-01-28 (0.0.1.dev2)
-----------------------

* Added `from_dicts()` constructor method to read iterables of
  dictionary rows.
* Added `from_dbf()` to read DBF files (dBase, FoxPro, etc.).


2018-01-18 (0.0.1.dev1)
-----------------------

* Added `get_reader()` to auto-detect objects and use appropriate constructor.
* Added `from_csv()` to support Unicode-aware CSV handling in Python 2 and
  Python 3.
* Added `from_pandas()` constructor method to read pandas `DataFrame` objects.
* Added `from_excel()` to read MS Excel files.
