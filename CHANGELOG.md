
Get-Reader Changelog
====================

COMING SOON (0.0.2)
-------------------

* Add `from_sql()` constructor to read database tables or SQL results.
* Add support for `Series`, `Index`, and `MultiIndex` objects to the
  existing `from_pandas()` constructor.
* Add a `Reader` class to provide consistent return values and automatic
  resource-handling (for closing files, database cursors, etc.).
* Change all constructors to return `Reader` instances.
* Fix file-closing behavior when DBF files are not fully consumed.
* Change `from_datatest()` to `from_squint()` to reflect new package name.
* Add Python 2 support statement to README:

  > While official support for Python 2 ends on January 1, 2020, this
  > project will continue to support older versions as long as the
  > existing ecosystem provides the ability to run automated tests
  > on those older versions.


2019-08-11 (0.0.1)
------------------

* First public release of packaged module.


2019-08-04 (0.0.1.dev4)
-----------------------

* Add `ReaderLike` class to help make type-checking more convenient.
* Remove support for Python 3.1.


2018-07-09 (0.0.1.dev3)
-----------------------

* Add `from_datatest()` constructor method to read datatest `Select` and
  `Query` objects.


2018-01-28 (0.0.1.dev2)
-----------------------

* Add `from_dicts()` constructor method to read iterables of
  dictionary rows.
* Add `from_dbf()` to read DBF files (dBase, FoxPro, etc.).


2018-01-18 (0.0.1.dev1)
-----------------------

* Add `get_reader()` to auto-detect objects and use appropriate constructor.
* Add `from_csv()` to support Unicode-aware CSV handling in Python 2 and
  Python 3.
* Add `from_pandas()` constructor method to read pandas `DataFrame` objects.
* Add `from_excel()` to read MS Excel files.
