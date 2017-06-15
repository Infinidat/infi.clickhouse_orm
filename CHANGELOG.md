Change Log
==========

Unreleased
----------
- Added `ne` and `not_in` queryset operators
- Querysets no longer have a default order unless `order_by` is called
- Added `autocreate` flag to database initializer
- Fix some Python 2/3 incompatibilities (TvoroG, tsionyx)
- To work around a JOIN bug in ClickHouse, `$table` now inserts only the table name,
  and the database name is sent in the query params instead

v0.9.0
------
- Major new feature: building model queries using QuerySets
- Refactor and expand the documentation
- Add support for FixedString fields
- Add support for more engine types: TinyLog, Log, Memory
- Bug fix: Do not send readonly=1 when connection is already in readonly mode

v0.8.2
------
- Fix broken Python 3 support (M1hacka)

v0.8.1
------
- Add support for ReplacingMergeTree (leenr)
- Fix problem with SELECT WITH TOTALS (pilosus)
- Update serialization format of DateTimeField to 10 digits, zero padded (nikepan)
- Greatly improve performance when inserting large strings (credit to M1hacka for identifying the problem)
- Reduce memory footprint of Database.insert()

v0.8.0
------
- Always keep datetime fields in UTC internally, and convert server timezone to UTC when parsing query results
- Support for ALIAS and MATERIALIZED fields (M1ha)
- Pagination: passing -1 as the page number now returns the last page
- Accept datetime values for date fields (Zloool)
- Support readonly mode in Database class (tswr)
- Added support for the Buffer table engine (emakarov)
- Added the SystemPart readonly model, which provides operations on partitions (M1ha)
- Added Model.to_dict() that converts a model instance to a dictionary (M1ha)
- Added Database.raw() to perform arbitrary queries (M1ha)

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


