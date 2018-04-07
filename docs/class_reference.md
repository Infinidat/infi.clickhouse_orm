Class Reference
===============

infi.clickhouse_orm.database
----------------------------

### Database


Database instances connect to a specific ClickHouse database for running queries,
inserting data and other operations.

#### Database(db_name, db_url="http://localhost:8123/", username=None, password=None, readonly=False, autocreate=True)


Initializes a database instance. Unless it's readonly, the database will be
created on the ClickHouse server if it does not already exist.

- `db_name`: name of the database to connect to.
- `db_url`: URL of the ClickHouse server.
- `username`: optional connection credentials.
- `password`: optional connection credentials.
- `readonly`: use a read-only connection.
- `autocreate`: automatically create the database if does not exist (unless in readonly mode).


#### count(model_class, conditions=None)


Counts the number of records in the model's table.

- `model_class`: the model to count.
- `conditions`: optional SQL conditions (contents of the WHERE clause).


#### create_database()


Creates the database on the ClickHouse server if it does not already exist.


#### create_table(model_class)


Creates a table for the given model class, if it does not exist already.


#### drop_database()


Deletes the database on the ClickHouse server.


#### drop_table(model_class)


Drops the database table of the given model class, if it exists.


#### insert(model_instances, batch_size=1000)


Insert records into the database.

- `model_instances`: any iterable containing instances of a single model class.
- `batch_size`: number of records to send per chunk (use a lower number if your records are very large).


#### migrate(migrations_package_name, up_to=9999)


Executes schema migrations.

- `migrations_package_name` - fully qualified name of the Python package
  containing the migrations.
- `up_to` - number of the last migration to apply.


#### paginate(model_class, order_by, page_num=1, page_size=100, conditions=None, settings=None)


Selects records and returns a single page of model instances.

- `model_class`: the model class matching the query's table,
  or `None` for getting back instances of an ad-hoc model.
- `order_by`: columns to use for sorting the query (contents of the ORDER BY clause).
- `page_num`: the page number (1-based), or -1 to get the last page.
- `page_size`: number of records to return per page.
- `conditions`: optional SQL conditions (contents of the WHERE clause).
- `settings`: query settings to send as HTTP GET parameters

The result is a namedtuple containing `objects` (list), `number_of_objects`,
`pages_total`, `number` (of the current page), and `page_size`.


#### raw(query, settings=None, stream=False)


Performs a query and returns its output as text.

- `query`: the SQL query to execute.
- `settings`: query settings to send as HTTP GET parameters
- `stream`: if true, the HTTP response from ClickHouse will be streamed.


#### select(query, model_class=None, settings=None)


Performs a query and returns a generator of model instances.

- `query`: the SQL query to execute.
- `model_class`: the model class matching the query's table,
  or `None` for getting back instances of an ad-hoc model.
- `settings`: query settings to send as HTTP GET parameters


### DatabaseException

Extends Exception


Raised when a database operation fails.

infi.clickhouse_orm.models
--------------------------

### Model


A base class for ORM models. Each model class represent a ClickHouse table. For example:

    class CPUStats(Model):
        timestamp = DateTimeField()
        cpu_id = UInt16Field()
        cpu_percent = Float32Field()
        engine = Memory()

#### Model(**kwargs)


Creates a model instance, using keyword arguments as field values.
Since values are immediately converted to their Pythonic type,
invalid values will cause a `ValueError` to be raised.
Unrecognized field names will cause an `AttributeError`.


#### Model.create_table_sql(db_name)


Returns the SQL command for creating a table for this model.


#### Model.drop_table_sql(db_name)


Returns the SQL command for deleting this model's table.


#### Model.from_tsv(line, field_names=None, timezone_in_use=UTC, database=None)


Create a model instance from a tab-separated line. The line may or may not include a newline.
The `field_names` list must match the fields defined in the model, but does not have to include all of them.
If omitted, it is assumed to be the names of all fields in the model, in order of definition.

- `line`: the TSV-formatted data.
- `field_names`: names of the model fields in the data.
- `timezone_in_use`: the timezone to use when parsing dates and datetimes.
- `database`: if given, sets the database that this instance belongs to.


#### get_database()


Gets the `Database` that this model instance belongs to.
Returns `None` unless the instance was read from the database or written to it.


#### get_field(name)


Gets a `Field` instance given its name, or `None` if not found.


#### Model.objects_in(database)


Returns a `QuerySet` for selecting instances of this model class.


#### set_database(db)


Sets the `Database` that this model instance belongs to.
This is done automatically when the instance is read from the database or written to it.


#### Model.table_name()


Returns the model's database table name. By default this is the
class name converted to lowercase. Override this if you want to use
a different table name.


#### to_dict(include_readonly=True, field_names=None)


Returns the instance's column values as a dict.

- `include_readonly`: if false, returns only fields that can be inserted into database.
- `field_names`: an iterable of field names to return (optional)


#### to_tsv(include_readonly=True)


Returns the instance's column values as a tab-separated line. A newline is not included.

- `include_readonly`: if false, returns only fields that can be inserted into database.


### BufferModel

Extends Model

#### BufferModel(**kwargs)


Creates a model instance, using keyword arguments as field values.
Since values are immediately converted to their Pythonic type,
invalid values will cause a `ValueError` to be raised.
Unrecognized field names will cause an `AttributeError`.


#### BufferModel.create_table_sql(db_name)


Returns the SQL command for creating a table for this model.


#### BufferModel.drop_table_sql(db_name)


Returns the SQL command for deleting this model's table.


#### BufferModel.from_tsv(line, field_names=None, timezone_in_use=UTC, database=None)


Create a model instance from a tab-separated line. The line may or may not include a newline.
The `field_names` list must match the fields defined in the model, but does not have to include all of them.
If omitted, it is assumed to be the names of all fields in the model, in order of definition.

- `line`: the TSV-formatted data.
- `field_names`: names of the model fields in the data.
- `timezone_in_use`: the timezone to use when parsing dates and datetimes.
- `database`: if given, sets the database that this instance belongs to.


#### get_database()


Gets the `Database` that this model instance belongs to.
Returns `None` unless the instance was read from the database or written to it.


#### get_field(name)


Gets a `Field` instance given its name, or `None` if not found.


#### BufferModel.objects_in(database)


Returns a `QuerySet` for selecting instances of this model class.


#### set_database(db)


Sets the `Database` that this model instance belongs to.
This is done automatically when the instance is read from the database or written to it.


#### BufferModel.table_name()


Returns the model's database table name. By default this is the
class name converted to lowercase. Override this if you want to use
a different table name.


#### to_dict(include_readonly=True, field_names=None)


Returns the instance's column values as a dict.

- `include_readonly`: if false, returns only fields that can be inserted into database.
- `field_names`: an iterable of field names to return (optional)


#### to_tsv(include_readonly=True)


Returns the instance's column values as a tab-separated line. A newline is not included.

- `include_readonly`: if false, returns only fields that can be inserted into database.


infi.clickhouse_orm.fields
--------------------------

### Field


Abstract base class for all field types.

#### Field(default=None, alias=None, materialized=None, readonly=None)


### StringField

Extends Field

#### StringField(default=None, alias=None, materialized=None, readonly=None)


### DateField

Extends Field

#### DateField(default=None, alias=None, materialized=None, readonly=None)


### DateTimeField

Extends Field

#### DateTimeField(default=None, alias=None, materialized=None, readonly=None)


### BaseIntField

Extends Field


Abstract base class for all integer-type fields.

#### BaseIntField(default=None, alias=None, materialized=None, readonly=None)


### BaseFloatField

Extends Field


Abstract base class for all float-type fields.

#### BaseFloatField(default=None, alias=None, materialized=None, readonly=None)


### BaseEnumField

Extends Field


Abstract base class for all enum-type fields.

#### BaseEnumField(enum_cls, default=None, alias=None, materialized=None, readonly=None)


### ArrayField

Extends Field

#### ArrayField(inner_field, default=None, alias=None, materialized=None, readonly=None)


### NullableField

Extends Field

#### NullableField(inner_field, default=None, alias=None, materialized=None, extra_null_values=None)


### FixedStringField

Extends StringField

#### FixedStringField(length, default=None, alias=None, materialized=None, readonly=None)


### UInt8Field

Extends BaseIntField

#### UInt8Field(default=None, alias=None, materialized=None, readonly=None)


### UInt16Field

Extends BaseIntField

#### UInt16Field(default=None, alias=None, materialized=None, readonly=None)


### UInt32Field

Extends BaseIntField

#### UInt32Field(default=None, alias=None, materialized=None, readonly=None)


### UInt64Field

Extends BaseIntField

#### UInt64Field(default=None, alias=None, materialized=None, readonly=None)


### Int8Field

Extends BaseIntField

#### Int8Field(default=None, alias=None, materialized=None, readonly=None)


### Int16Field

Extends BaseIntField

#### Int16Field(default=None, alias=None, materialized=None, readonly=None)


### Int32Field

Extends BaseIntField

#### Int32Field(default=None, alias=None, materialized=None, readonly=None)


### Int64Field

Extends BaseIntField

#### Int64Field(default=None, alias=None, materialized=None, readonly=None)


### Float32Field

Extends BaseFloatField

#### Float32Field(default=None, alias=None, materialized=None, readonly=None)


### Float64Field

Extends BaseFloatField

#### Float64Field(default=None, alias=None, materialized=None, readonly=None)


### Enum8Field

Extends BaseEnumField

#### Enum8Field(enum_cls, default=None, alias=None, materialized=None, readonly=None)


### Enum16Field

Extends BaseEnumField

#### Enum16Field(enum_cls, default=None, alias=None, materialized=None, readonly=None)


infi.clickhouse_orm.engines
---------------------------

### Engine

### TinyLog

Extends Engine

### Log

Extends Engine

### Memory

Extends Engine

### MergeTree

Extends Engine

#### MergeTree(date_col, key_cols, sampling_expr=None, index_granularity=8192, replica_table_path=None, replica_name=None)


### Buffer

Extends Engine


Buffers the data to write in RAM, periodically flushing it to another table.
Must be used in conjuction with a `BufferModel`.
Read more [here](https://clickhouse.yandex/reference_en.html#Buffer).

#### Buffer(main_model, num_layers=16, min_time=10, max_time=100, min_rows=10000, max_rows=1000000, min_bytes=10000000, max_bytes=100000000)


### Merge

Extends Engine


The Merge engine (not to be confused with MergeTree) does not store data itself,
but allows reading from any number of other tables simultaneously.
Writing to a table is not supported
https://clickhouse.yandex/docs/en/single/index.html#document-table_engines/merge

#### Merge(table_regex)


### CollapsingMergeTree

Extends MergeTree

#### CollapsingMergeTree(date_col, key_cols, sign_col, sampling_expr=None, index_granularity=8192, replica_table_path=None, replica_name=None)


### SummingMergeTree

Extends MergeTree

#### SummingMergeTree(date_col, key_cols, summing_cols=None, sampling_expr=None, index_granularity=8192, replica_table_path=None, replica_name=None)


### ReplacingMergeTree

Extends MergeTree

#### ReplacingMergeTree(date_col, key_cols, ver_col=None, sampling_expr=None, index_granularity=8192, replica_table_path=None, replica_name=None)


infi.clickhouse_orm.query
-------------------------

### QuerySet


A queryset is an object that represents a database query using a specific `Model`.
It is lazy, meaning that it does not hit the database until you iterate over its
matching rows (model instances).

#### QuerySet(model_cls, database)


Initializer. It is possible to create a queryset like this, but the standard
way is to use `MyModel.objects_in(database)`.


#### aggregate(*args, **kwargs)


Returns an `AggregateQuerySet` over this query, with `args` serving as
grouping fields and `kwargs` serving as calculated fields. At least one
calculated field is required. For example:
```
    Event.objects_in(database).filter(date__gt='2017-08-01').aggregate('event_type', count='count()')
```
is equivalent to:
```
    SELECT event_type, count() AS count FROM event
    WHERE data > '2017-08-01'
    GROUP BY event_type
```


#### as_sql()


Returns the whole query as a SQL string.


#### conditions_as_sql()


Returns the contents of the query's `WHERE` clause as a string.


#### count()


Returns the number of matching model instances.


#### distinct()


Adds a DISTINCT clause to the query, meaning that any duplicate rows
in the results will be omitted.


#### exclude(**filter_fields)


Returns a copy of this queryset that excludes all rows matching the conditions.


#### filter(*q, **filter_fields)


Returns a copy of this queryset that includes only rows matching the conditions.
Add q object to query if it specified.


#### only(*field_names)


Returns a copy of this queryset limited to the specified field names.
Useful when there are large fields that are not needed,
or for creating a subquery to use with an IN operator.


#### order_by(*field_names)


Returns a copy of this queryset with the ordering changed.


#### order_by_as_sql()


Returns the contents of the query's `ORDER BY` clause as a string.


#### paginate(page_num=1, page_size=100)


Returns a single page of model instances that match the queryset.
Note that `order_by` should be used first, to ensure a correct
partitioning of records into pages.

- `page_num`: the page number (1-based), or -1 to get the last page.
- `page_size`: number of records to return per page.

The result is a namedtuple containing `objects` (list), `number_of_objects`,
`pages_total`, `number` (of the current page), and `page_size`.


### AggregateQuerySet

Extends QuerySet


A queryset used for aggregation.

#### AggregateQuerySet(base_qs, grouping_fields, calculated_fields)


Initializer. Normally you should not call this but rather use `QuerySet.aggregate()`.

The grouping fields should be a list/tuple of field names from the model. For example:
```
    ('event_type', 'event_subtype')
```
The calculated fields should be a mapping from name to a ClickHouse aggregation function. For example:
```
    {'weekday': 'toDayOfWeek(event_date)', 'number_of_events': 'count()'}
```
At least one calculated field is required.


#### aggregate(*args, **kwargs)


This method is not supported on `AggregateQuerySet`.


#### as_sql()


Returns the whole query as a SQL string.


#### conditions_as_sql()


Returns the contents of the query's `WHERE` clause as a string.


#### count()


Returns the number of rows after aggregation.


#### distinct()


Adds a DISTINCT clause to the query, meaning that any duplicate rows
in the results will be omitted.


#### exclude(**filter_fields)


Returns a copy of this queryset that excludes all rows matching the conditions.


#### filter(*q, **filter_fields)


Returns a copy of this queryset that includes only rows matching the conditions.
Add q object to query if it specified.


#### group_by(*args)


This method lets you specify the grouping fields explicitly. The `args` must
be names of grouping fields or calculated fields that this queryset was
created with.


#### only(*field_names)


This method is not supported on `AggregateQuerySet`.


#### order_by(*field_names)


Returns a copy of this queryset with the ordering changed.


#### order_by_as_sql()


Returns the contents of the query's `ORDER BY` clause as a string.


#### paginate(page_num=1, page_size=100)


Returns a single page of model instances that match the queryset.
Note that `order_by` should be used first, to ensure a correct
partitioning of records into pages.

- `page_num`: the page number (1-based), or -1 to get the last page.
- `page_size`: number of records to return per page.

The result is a namedtuple containing `objects` (list), `number_of_objects`,
`pages_total`, `number` (of the current page), and `page_size`.


