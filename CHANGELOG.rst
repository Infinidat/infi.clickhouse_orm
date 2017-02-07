Change Log
==========

[Unreleased]
------------
- Always keep datetime fields in UTC internally, and convert server timezone to UTC when parsing query results
- Support for ALIAS and MATERIALIZED fields (M1ha)
- Pagination: passing -1 as the page number now returns the last page
- Accept datetime values for date fields (Zloool)
- Support readonly mode in Database class (tswr)

v0.7.1
------
- Accept '0000-00-00 00:00:00' as a datetime value (tsionyx)
- Bug fix: parse_array fails on int arrays
- Improve performance when inserting many rows

v0.7.0
------
- Support array fields
- Support enum fields

v0.6.3
------
- Python 3 support


