Change Log
==========

v2.1.3
------
- Fix pagination for models with alias columns

v2.1.2
------
- Add `QuerySet.model` to support django-rest-framework 3

v2.1.1
------
- Improve support of ClickHouse v21.9 (mangototango)
- Ignore non-numeric parts in ClickHouse version (mangototango)
- Fix precedence of ~ operator in Q objects	(mangototango)
- Support for adding a column to the beginning of a table (meanmail)
- Add stddevPop and stddevSamp functions (k.peskov)

v2.1.0
------
- Support for model constraints
- Support for data skipping indexes
- Support for mutations: `QuerySet.update` and `QuerySet.delete`
- Added functions for working with external dictionaries
- Support FINAL for `ReplacingMergeTree` (chripede)
- Added `DateTime64Field` (NiyazNz)
- Make `DateTimeField` and `DateTime64Field` timezone-aware (NiyazNz)

**Backwards incompatible changes**

Previously, `DateTimeField` always converted its value from the database timezone to UTC. This is no longer the case: the field's value now preserves the timezone it was defined with, or if not specified - the database's global timezone. This change has no effect if your database timezone is set to UTC.

v2.0.1
------
- Remove unnecessary import of `six`

v2.0.0
------
- Dropped support for Python 2.x
- New flexible syntax for database expressions and functions
- Expressions as default values for model fields
- Support for IPv4 and IPv6 fields
- Automatic generation of models by inspecting existing tables
- Convenient ways to import ORM classes

See [What's new in version 2](docs/whats_new_in_version_2.md) for details.

v1.4.0
------
- Added primary_key parameter to MergeTree engines (M1hacka)
- Support negative enum values (Romamo)

v1.3.0
------
- Support LowCardinality columns in ad-hoc queries
- Support for LIMIT BY in querysets (utapyngo)

v1.2.0
------
- Add support for per-field compression codecs (rbelio, Chocorean)
- Add support for low cardinality fields (rbelio)

v1.1.0
------
- Add PREWHERE support to querysets (M1hacka)
- Add WITH TOTALS support to querysets (M1hacka)
- Extend date field range (trthhrtz)
- Fix parsing of server errors in ClickHouse v19.3.3+
- Fix pagination when asking for the last page on a query that matches no records
- Use HTTP Basic Authentication instead of passing the credentials in the URL
- Support default/alias/materialized for nullable fields
- Add UUIDField (kpotehin)
- Add `log_statements` parameter to database initializer
- Fix test_merge which fails on ClickHouse v19.8.3
- Fix querysets using the SystemPart model

v1.0.4
------
- Added `timeout` parameter to database initializer (SUHAR1K)
- Added `verify_ssl_cert` parameter to database initializer
- Added `final()` method to querysets (M1hacka)
- Fixed a migrations problem - cannot add a new materialized field after a regular field

v1.0.3
------
- Bug fix: `QuerySet.count()` ignores slicing
- Bug fix: wrong parentheses when building queries using Q objects
- Support Decimal fields
- Added `Database.add_setting` method

v1.0.2
----------
- Include alias and materialized fields in queryset results
- Check for database existence, to allow delayed creation
- Added `Database.does_table_exist` method
- Support for `IS NULL` and `IS NOT NULL` in querysets (kalombos)

v1.0.1
------
- NullableField: take extra_null_values into account in `validate` and `to_python`
- Added `Field.isinstance` method
- Validate the inner field passed to `ArrayField`

v1.0.0
------
- Add support for compound filters with Q objects (desile)
- Add support for BETWEEN operator (desile)
- Distributed engine support (tsionyx)
- `_fields` and `_writable_fields` are OrderedDicts - note that this might break backwards compatibility (tsionyx)
- Improve error messages returned from the database with the `ServerError` class (tsionyx)
- Added support for custom partitioning (M1hacka)
- Added attribute `server_version` to Database class (M1hacka)
- Changed `Engine.create_table_sql()`, `Engine.drop_table_sql()`, `Model.create_table_sql()`, `Model.drop_table_sql()` parameter to db from db_name (M1hacka)
- Fix parsing of datetime column type when it includes a timezone (M1hacka)
- Rename `Model.system` to `Model._system` to prevent collision with a column that has the same name
- Rename `Model.readonly` to `Model._readonly` to prevent collision with a column that has the same name
- The `field_names` argument to `Model.to_tsv` is now mandatory
- Improve creation time of model instances by keeping a dictionary of default values
- Fix queryset bug when field name contains double underscores (YouCanKeepSilence)
- Prevent exception when determining timezone of old ClickHouse versions (vv-p)

v0.9.8
------
- Bug fix: add field names list explicitly to Database.insert method (anci)
- Added RunPython and RunSQL migrations (M1hacka)
- Allow ISO-formatted datetime values (tsionyx)
- Show field name in error message when invalid value assigned (tsionyx)
- Bug fix: select query fails when query contains '$' symbol (M1hacka)
- Prevent problems with AlterTable migrations related to field order (M1hacka)
- Added documentation about custom fields.

v0.9.7
------
- Add `distinct` method to querysets
- Add `AlterTableWithBuffer` migration operation
- Support Merge engine (M1hacka)

v0.9.6
------
- Fix python3 compatibility (TvoroG)
- Nullable arrays not supported in latest ClickHouse version
- system.parts table no longer includes "replicated" column in latest ClickHouse version

v0.9.5
------
- Added `QuerySet.paginate()`
- Support for basic aggregation in querysets

v0.9.4
------
- Migrations: when creating a table for a `BufferModel`, create the underlying table too if necessary

v0.9.3
------
- Changed license from PSF to BSD
- Nullable fields support (yamiou)
- Support for queryset slicing

v0.9.2
------
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


