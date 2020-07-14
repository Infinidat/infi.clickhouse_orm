Class Reference
===============

infi.clickhouse_orm.database
----------------------------

### Database


Database instances connect to a specific ClickHouse database for running queries,
inserting data and other operations.

#### Database(db_name, db_url="http://localhost:8123/", username=None, password=None, readonly=False, autocreate=True, timeout=60, verify_ssl_cert=True, log_statements=False)


Initializes a database instance. Unless it's readonly, the database will be
created on the ClickHouse server if it does not already exist.

- `db_name`: name of the database to connect to.
- `db_url`: URL of the ClickHouse server.
- `username`: optional connection credentials.
- `password`: optional connection credentials.
- `readonly`: use a read-only connection.
- `autocreate`: automatically create the database if it does not exist (unless in readonly mode).
- `timeout`: the connection timeout in seconds.
- `verify_ssl_cert`: whether to verify the server's certificate when connecting via HTTPS.
- `log_statements`: when True, all database statements are logged.


#### add_setting(name, value)


Adds a database setting that will be sent with every request.
For example, `db.add_setting("max_execution_time", 10)` will
limit query execution time to 10 seconds.
The name must be string, and the value is converted to string in case
it isn't. To remove a setting, pass `None` as the value.


#### count(model_class, conditions=None)


Counts the number of records in the model's table.

- `model_class`: the model to count.
- `conditions`: optional SQL conditions (contents of the WHERE clause).


#### create_database()


Creates the database on the ClickHouse server if it does not already exist.


#### create_table(model_class)


Creates a table for the given model class, if it does not exist already.


#### does_table_exist(model_class)


Checks whether a table for the given model class already exists.
Note that this only checks for existence of a table with the expected name.


#### drop_database()


Deletes the database on the ClickHouse server.


#### drop_table(model_class)


Drops the database table of the given model class, if it exists.


#### get_model_for_table(table_name, system_table=False)


Generates a model class from an existing table in the database.
This can be used for querying tables which don't have a corresponding model class,
for example system tables.

- `table_name`: the table to create a model for
- `system_table`: whether the table is a system table, or belongs to the current database


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


#### Model.create_table_sql(db)


Returns the SQL statement for creating a table for this model.


#### Model.drop_table_sql(db)


Returns the SQL command for deleting this model's table.


#### Model.fields(writable=False)


Returns an `OrderedDict` of the model's fields (from name to `Field` instance).
If `writable` is true, only writable fields are included.
Callers should not modify the dictionary.


#### Model.from_tsv(line, field_names, timezone_in_use=UTC, database=None)


Create a model instance from a tab-separated line. The line may or may not include a newline.
The `field_names` list must match the fields defined in the model, but does not have to include all of them.

- `line`: the TSV-formatted data.
- `field_names`: names of the model fields in the data.
- `timezone_in_use`: the timezone to use when parsing dates and datetimes. Some fields use their own timezones.
- `database`: if given, sets the database that this instance belongs to.


#### get_database()


Gets the `Database` that this model instance belongs to.
Returns `None` unless the instance was read from the database or written to it.


#### get_field(name)


Gets a `Field` instance given its name, or `None` if not found.


#### Model.has_funcs_as_defaults()


Return True if some of the model's fields use a function expression
as a default value. This requires special handling when inserting instances.


#### Model.is_read_only()


Returns true if the model is marked as read only.


#### Model.is_system_model()


Returns true if the model represents a system table.


#### Model.objects_in(database)


Returns a `QuerySet` for selecting instances of this model class.


#### set_database(db)


Sets the `Database` that this model instance belongs to.
This is done automatically when the instance is read from the database or written to it.


#### Model.table_name()


Returns the model's database table name. By default this is the
class name converted to lowercase. Override this if you want to use
a different table name.


#### to_db_string()


Returns the instance as a bytestring ready to be inserted into the database.


#### to_dict(include_readonly=True, field_names=None)


Returns the instance's column values as a dict.

- `include_readonly`: if false, returns only fields that can be inserted into database.
- `field_names`: an iterable of field names to return (optional)


#### to_tskv(include_readonly=True)


Returns the instance's column keys and values as a tab-separated line. A newline is not included.
Fields that were not assigned a value are omitted.

- `include_readonly`: if false, returns only fields that can be inserted into database.


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


#### BufferModel.create_table_sql(db)


Returns the SQL statement for creating a table for this model.


#### BufferModel.drop_table_sql(db)


Returns the SQL command for deleting this model's table.


#### BufferModel.fields(writable=False)


Returns an `OrderedDict` of the model's fields (from name to `Field` instance).
If `writable` is true, only writable fields are included.
Callers should not modify the dictionary.


#### BufferModel.from_tsv(line, field_names, timezone_in_use=UTC, database=None)


Create a model instance from a tab-separated line. The line may or may not include a newline.
The `field_names` list must match the fields defined in the model, but does not have to include all of them.

- `line`: the TSV-formatted data.
- `field_names`: names of the model fields in the data.
- `timezone_in_use`: the timezone to use when parsing dates and datetimes. Some fields use their own timezones.
- `database`: if given, sets the database that this instance belongs to.


#### get_database()


Gets the `Database` that this model instance belongs to.
Returns `None` unless the instance was read from the database or written to it.


#### get_field(name)


Gets a `Field` instance given its name, or `None` if not found.


#### BufferModel.has_funcs_as_defaults()


Return True if some of the model's fields use a function expression
as a default value. This requires special handling when inserting instances.


#### BufferModel.is_read_only()


Returns true if the model is marked as read only.


#### BufferModel.is_system_model()


Returns true if the model represents a system table.


#### BufferModel.objects_in(database)


Returns a `QuerySet` for selecting instances of this model class.


#### set_database(db)


Sets the `Database` that this model instance belongs to.
This is done automatically when the instance is read from the database or written to it.


#### BufferModel.table_name()


Returns the model's database table name. By default this is the
class name converted to lowercase. Override this if you want to use
a different table name.


#### to_db_string()


Returns the instance as a bytestring ready to be inserted into the database.


#### to_dict(include_readonly=True, field_names=None)


Returns the instance's column values as a dict.

- `include_readonly`: if false, returns only fields that can be inserted into database.
- `field_names`: an iterable of field names to return (optional)


#### to_tskv(include_readonly=True)


Returns the instance's column keys and values as a tab-separated line. A newline is not included.
Fields that were not assigned a value are omitted.

- `include_readonly`: if false, returns only fields that can be inserted into database.


#### to_tsv(include_readonly=True)


Returns the instance's column values as a tab-separated line. A newline is not included.

- `include_readonly`: if false, returns only fields that can be inserted into database.


### MergeModel

Extends Model


Model for Merge engine
Predefines virtual _table column an controls that rows can't be inserted to this table type
https://clickhouse.tech/docs/en/single/index.html#document-table_engines/merge

#### MergeModel(**kwargs)


Creates a model instance, using keyword arguments as field values.
Since values are immediately converted to their Pythonic type,
invalid values will cause a `ValueError` to be raised.
Unrecognized field names will cause an `AttributeError`.


#### MergeModel.create_table_sql(db)


Returns the SQL statement for creating a table for this model.


#### MergeModel.drop_table_sql(db)


Returns the SQL command for deleting this model's table.


#### MergeModel.fields(writable=False)


Returns an `OrderedDict` of the model's fields (from name to `Field` instance).
If `writable` is true, only writable fields are included.
Callers should not modify the dictionary.


#### MergeModel.from_tsv(line, field_names, timezone_in_use=UTC, database=None)


Create a model instance from a tab-separated line. The line may or may not include a newline.
The `field_names` list must match the fields defined in the model, but does not have to include all of them.

- `line`: the TSV-formatted data.
- `field_names`: names of the model fields in the data.
- `timezone_in_use`: the timezone to use when parsing dates and datetimes. Some fields use their own timezones.
- `database`: if given, sets the database that this instance belongs to.


#### get_database()


Gets the `Database` that this model instance belongs to.
Returns `None` unless the instance was read from the database or written to it.


#### get_field(name)


Gets a `Field` instance given its name, or `None` if not found.


#### MergeModel.has_funcs_as_defaults()


Return True if some of the model's fields use a function expression
as a default value. This requires special handling when inserting instances.


#### MergeModel.is_read_only()


Returns true if the model is marked as read only.


#### MergeModel.is_system_model()


Returns true if the model represents a system table.


#### MergeModel.objects_in(database)


Returns a `QuerySet` for selecting instances of this model class.


#### set_database(db)


Sets the `Database` that this model instance belongs to.
This is done automatically when the instance is read from the database or written to it.


#### MergeModel.table_name()


Returns the model's database table name. By default this is the
class name converted to lowercase. Override this if you want to use
a different table name.


#### to_db_string()


Returns the instance as a bytestring ready to be inserted into the database.


#### to_dict(include_readonly=True, field_names=None)


Returns the instance's column values as a dict.

- `include_readonly`: if false, returns only fields that can be inserted into database.
- `field_names`: an iterable of field names to return (optional)


#### to_tskv(include_readonly=True)


Returns the instance's column keys and values as a tab-separated line. A newline is not included.
Fields that were not assigned a value are omitted.

- `include_readonly`: if false, returns only fields that can be inserted into database.


#### to_tsv(include_readonly=True)


Returns the instance's column values as a tab-separated line. A newline is not included.

- `include_readonly`: if false, returns only fields that can be inserted into database.


### DistributedModel

Extends Model


Model class for use with a `Distributed` engine.

#### DistributedModel(**kwargs)


Creates a model instance, using keyword arguments as field values.
Since values are immediately converted to their Pythonic type,
invalid values will cause a `ValueError` to be raised.
Unrecognized field names will cause an `AttributeError`.


#### DistributedModel.create_table_sql(db)


Returns the SQL statement for creating a table for this model.


#### DistributedModel.drop_table_sql(db)


Returns the SQL command for deleting this model's table.


#### DistributedModel.fields(writable=False)


Returns an `OrderedDict` of the model's fields (from name to `Field` instance).
If `writable` is true, only writable fields are included.
Callers should not modify the dictionary.


#### DistributedModel.fix_engine_table()


Remember: Distributed table does not store any data, just provides distributed access to it.

So if we define a model with engine that has no defined table for data storage
(see FooDistributed below), that table cannot be successfully created.
This routine can automatically fix engine's storage table by finding the first
non-distributed model among your model's superclasses.

>>> class Foo(Model):
...     id = UInt8Field(1)
...
>>> class FooDistributed(Foo, DistributedModel):
...     engine = Distributed('my_cluster')
...
>>> FooDistributed.engine.table
None
>>> FooDistributed.fix_engine()
>>> FooDistributed.engine.table
<class '__main__.Foo'>

However if you prefer more explicit way of doing things,
you can always mention the Foo model twice without bothering with any fixes:

>>> class FooDistributedVerbose(Foo, DistributedModel):
...     engine = Distributed('my_cluster', Foo)
>>> FooDistributedVerbose.engine.table
<class '__main__.Foo'>

See tests.test_engines:DistributedTestCase for more examples


#### DistributedModel.from_tsv(line, field_names, timezone_in_use=UTC, database=None)


Create a model instance from a tab-separated line. The line may or may not include a newline.
The `field_names` list must match the fields defined in the model, but does not have to include all of them.

- `line`: the TSV-formatted data.
- `field_names`: names of the model fields in the data.
- `timezone_in_use`: the timezone to use when parsing dates and datetimes. Some fields use their own timezones.
- `database`: if given, sets the database that this instance belongs to.


#### get_database()


Gets the `Database` that this model instance belongs to.
Returns `None` unless the instance was read from the database or written to it.


#### get_field(name)


Gets a `Field` instance given its name, or `None` if not found.


#### DistributedModel.has_funcs_as_defaults()


Return True if some of the model's fields use a function expression
as a default value. This requires special handling when inserting instances.


#### DistributedModel.is_read_only()


Returns true if the model is marked as read only.


#### DistributedModel.is_system_model()


Returns true if the model represents a system table.


#### DistributedModel.objects_in(database)


Returns a `QuerySet` for selecting instances of this model class.


#### set_database(db)


Sets the `Database` that this model instance belongs to.
This is done automatically when the instance is read from the database or written to it.


#### DistributedModel.table_name()


Returns the model's database table name. By default this is the
class name converted to lowercase. Override this if you want to use
a different table name.


#### to_db_string()


Returns the instance as a bytestring ready to be inserted into the database.


#### to_dict(include_readonly=True, field_names=None)


Returns the instance's column values as a dict.

- `include_readonly`: if false, returns only fields that can be inserted into database.
- `field_names`: an iterable of field names to return (optional)


#### to_tskv(include_readonly=True)


Returns the instance's column keys and values as a tab-separated line. A newline is not included.
Fields that were not assigned a value are omitted.

- `include_readonly`: if false, returns only fields that can be inserted into database.


#### to_tsv(include_readonly=True)


Returns the instance's column values as a tab-separated line. A newline is not included.

- `include_readonly`: if false, returns only fields that can be inserted into database.


### Constraint


Defines a model constraint.

#### Constraint(expr)


Initializer. Expects an expression that ClickHouse will verify when inserting data.


#### create_table_sql()


Returns the SQL statement for defining this constraint during table creation.


### Index


Defines a data-skipping index.

#### Index(expr, type, granularity)


Initializer.

- `expr` - a column, expression, or tuple of columns and expressions to index.
- `type` - the index type. Use one of the following methods to specify the type:
  `Index.minmax`, `Index.set`, `Index.ngrambf_v1`, `Index.tokenbf_v1` or `Index.bloom_filter`.
- `granularity` - index block size (number of multiples of the `index_granularity` defined by the engine).


#### bloom_filter()


An index that stores a Bloom filter containing values of the index expression.

- `false_positive` - the probability (between 0 and 1) of receiving a false positive
  response from the filter


#### create_table_sql()


Returns the SQL statement for defining this index during table creation.


#### minmax()


An index that stores extremes of the specified expression (if the expression is tuple, then it stores
extremes for each element of tuple). The stored info is used for skipping blocks of data like the primary key.


#### ngrambf_v1(size_of_bloom_filter_in_bytes, number_of_hash_functions, random_seed)


An index that stores a Bloom filter containing all ngrams from a block of data.
Works only with strings. Can be used for optimization of equals, like and in expressions.

- `n` — ngram size
- `size_of_bloom_filter_in_bytes` — Bloom filter size in bytes (you can use large values here,
   for example 256 or 512, because it can be compressed well).
- `number_of_hash_functions` — The number of hash functions used in the Bloom filter.
- `random_seed` — The seed for Bloom filter hash functions.


#### set()


An index that stores unique values of the specified expression (no more than max_rows rows,
or unlimited if max_rows=0). Uses the values to check if the WHERE expression is not satisfiable
on a block of data.


#### tokenbf_v1(number_of_hash_functions, random_seed)


An index that stores a Bloom filter containing string tokens. Tokens are sequences
separated by non-alphanumeric characters.

- `size_of_bloom_filter_in_bytes` — Bloom filter size in bytes (you can use large values here,
   for example 256 or 512, because it can be compressed well).
- `number_of_hash_functions` — The number of hash functions used in the Bloom filter.
- `random_seed` — The seed for Bloom filter hash functions.


infi.clickhouse_orm.fields
--------------------------

### ArrayField

Extends Field

#### ArrayField(inner_field, default=None, alias=None, materialized=None, readonly=None, codec=None)


### BaseEnumField

Extends Field


Abstract base class for all enum-type fields.

#### BaseEnumField(enum_cls, default=None, alias=None, materialized=None, readonly=None, codec=None)


### BaseFloatField

Extends Field


Abstract base class for all float-type fields.

#### BaseFloatField(default=None, alias=None, materialized=None, readonly=None, codec=None)


### BaseIntField

Extends Field


Abstract base class for all integer-type fields.

#### BaseIntField(default=None, alias=None, materialized=None, readonly=None, codec=None)


### DateField

Extends Field

#### DateField(default=None, alias=None, materialized=None, readonly=None, codec=None)


### DateTime64Field

Extends DateTimeField

#### DateTime64Field(default=None, alias=None, materialized=None, readonly=None, codec=None, timezone=None, precision=6)


### DateTimeField

Extends Field

#### DateTimeField(default=None, alias=None, materialized=None, readonly=None, codec=None, timezone=None)


### Decimal128Field

Extends DecimalField

#### Decimal128Field(scale, default=None, alias=None, materialized=None, readonly=None)


### Decimal32Field

Extends DecimalField

#### Decimal32Field(scale, default=None, alias=None, materialized=None, readonly=None)


### Decimal64Field

Extends DecimalField

#### Decimal64Field(scale, default=None, alias=None, materialized=None, readonly=None)


### DecimalField

Extends Field


Base class for all decimal fields. Can also be used directly.

#### DecimalField(precision, scale, default=None, alias=None, materialized=None, readonly=None)


### Enum16Field

Extends BaseEnumField

#### Enum16Field(enum_cls, default=None, alias=None, materialized=None, readonly=None, codec=None)


### Enum8Field

Extends BaseEnumField

#### Enum8Field(enum_cls, default=None, alias=None, materialized=None, readonly=None, codec=None)


### Field

Extends FunctionOperatorsMixin


Abstract base class for all field types.

#### Field(default=None, alias=None, materialized=None, readonly=None, codec=None)


### FixedStringField

Extends StringField

#### FixedStringField(length, default=None, alias=None, materialized=None, readonly=None)


### Float32Field

Extends BaseFloatField

#### Float32Field(default=None, alias=None, materialized=None, readonly=None, codec=None)


### Float64Field

Extends BaseFloatField

#### Float64Field(default=None, alias=None, materialized=None, readonly=None, codec=None)


### IPv4Field

Extends Field

#### IPv4Field(default=None, alias=None, materialized=None, readonly=None, codec=None)


### IPv6Field

Extends Field

#### IPv6Field(default=None, alias=None, materialized=None, readonly=None, codec=None)


### Int16Field

Extends BaseIntField

#### Int16Field(default=None, alias=None, materialized=None, readonly=None, codec=None)


### Int32Field

Extends BaseIntField

#### Int32Field(default=None, alias=None, materialized=None, readonly=None, codec=None)


### Int64Field

Extends BaseIntField

#### Int64Field(default=None, alias=None, materialized=None, readonly=None, codec=None)


### Int8Field

Extends BaseIntField

#### Int8Field(default=None, alias=None, materialized=None, readonly=None, codec=None)


### LowCardinalityField

Extends Field

#### LowCardinalityField(inner_field, default=None, alias=None, materialized=None, readonly=None, codec=None)


### NullableField

Extends Field

#### NullableField(inner_field, default=None, alias=None, materialized=None, extra_null_values=None, codec=None)


### StringField

Extends Field

#### StringField(default=None, alias=None, materialized=None, readonly=None, codec=None)


### UInt16Field

Extends BaseIntField

#### UInt16Field(default=None, alias=None, materialized=None, readonly=None, codec=None)


### UInt32Field

Extends BaseIntField

#### UInt32Field(default=None, alias=None, materialized=None, readonly=None, codec=None)


### UInt64Field

Extends BaseIntField

#### UInt64Field(default=None, alias=None, materialized=None, readonly=None, codec=None)


### UInt8Field

Extends BaseIntField

#### UInt8Field(default=None, alias=None, materialized=None, readonly=None, codec=None)


### UUIDField

Extends Field

#### UUIDField(default=None, alias=None, materialized=None, readonly=None, codec=None)


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

#### MergeTree(date_col=None, order_by=(), sampling_expr=None, index_granularity=8192, replica_table_path=None, replica_name=None, partition_key=None, primary_key=None)


### Buffer

Extends Engine


Buffers the data to write in RAM, periodically flushing it to another table.
Must be used in conjuction with a `BufferModel`.
Read more [here](https://clickhouse.tech/docs/en/engines/table-engines/special/buffer/).

#### Buffer(main_model, num_layers=16, min_time=10, max_time=100, min_rows=10000, max_rows=1000000, min_bytes=10000000, max_bytes=100000000)


### Merge

Extends Engine


The Merge engine (not to be confused with MergeTree) does not store data itself,
but allows reading from any number of other tables simultaneously.
Writing to a table is not supported
https://clickhouse.tech/docs/en/engines/table-engines/special/merge/

#### Merge(table_regex)


### Distributed

Extends Engine


The Distributed engine by itself does not store data,
but allows distributed query processing on multiple servers.
Reading is automatically parallelized.
During a read, the table indexes on remote servers are used, if there are any.

See full documentation here
https://clickhouse.tech/docs/en/engines/table-engines/special/distributed/

#### Distributed(cluster, table=None, sharding_key=None)


- `cluster`: what cluster to access data from
- `table`: underlying table that actually stores data.
If you are not specifying any table here, ensure that it can be inferred
from your model's superclass (see models.DistributedModel.fix_engine_table)
- `sharding_key`: how to distribute data among shards when inserting
straightly into Distributed table, optional


### CollapsingMergeTree

Extends MergeTree

#### CollapsingMergeTree(date_col=None, order_by=(), sign_col="sign", sampling_expr=None, index_granularity=8192, replica_table_path=None, replica_name=None, partition_key=None, primary_key=None)


### SummingMergeTree

Extends MergeTree

#### SummingMergeTree(date_col=None, order_by=(), summing_cols=None, sampling_expr=None, index_granularity=8192, replica_table_path=None, replica_name=None, partition_key=None, primary_key=None)


### ReplacingMergeTree

Extends MergeTree

#### ReplacingMergeTree(date_col=None, order_by=(), ver_col=None, sampling_expr=None, index_granularity=8192, replica_table_path=None, replica_name=None, partition_key=None, primary_key=None)


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


#### conditions_as_sql(prewhere=False)


Returns the contents of the query's `WHERE` or `PREWHERE` clause as a string.


#### count()


Returns the number of matching model instances.


#### delete()


Deletes all records matched by this queryset's conditions.
Note that ClickHouse performs deletions in the background, so they are not immediate.


#### distinct()


Adds a DISTINCT clause to the query, meaning that any duplicate rows
in the results will be omitted.


#### exclude(*q, **kwargs)


Returns a copy of this queryset that excludes all rows matching the conditions.
Pass `prewhere=True` to apply the conditions as PREWHERE instead of WHERE.


#### filter(*q, **kwargs)


Returns a copy of this queryset that includes only rows matching the conditions.
Pass `prewhere=True` to apply the conditions as PREWHERE instead of WHERE.


#### final()


Adds a FINAL modifier to table, meaning data will be collapsed to final version.
Can be used with the `CollapsingMergeTree` and `ReplacingMergeTree` engines only.


#### limit_by(offset_limit, *fields_or_expr)


Adds a LIMIT BY clause to the query.
- `offset_limit`: either an integer specifying the limit, or a tuple of integers (offset, limit).
- `fields_or_expr`: the field names or expressions to use in the clause.


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


#### select_fields_as_sql()


Returns the selected fields or expressions as a SQL string.


#### update(**kwargs)


Updates all records matched by this queryset's conditions.
Keyword arguments specify the field names and expressions to use for the update.
Note that ClickHouse performs updates in the background, so they are not immediate.


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


#### conditions_as_sql(prewhere=False)


Returns the contents of the query's `WHERE` or `PREWHERE` clause as a string.


#### count()


Returns the number of rows after aggregation.


#### delete()


Deletes all records matched by this queryset's conditions.
Note that ClickHouse performs deletions in the background, so they are not immediate.


#### distinct()


Adds a DISTINCT clause to the query, meaning that any duplicate rows
in the results will be omitted.


#### exclude(*q, **kwargs)


Returns a copy of this queryset that excludes all rows matching the conditions.
Pass `prewhere=True` to apply the conditions as PREWHERE instead of WHERE.


#### filter(*q, **kwargs)


Returns a copy of this queryset that includes only rows matching the conditions.
Pass `prewhere=True` to apply the conditions as PREWHERE instead of WHERE.


#### final()


Adds a FINAL modifier to table, meaning data will be collapsed to final version.
Can be used with the `CollapsingMergeTree` and `ReplacingMergeTree` engines only.


#### group_by(*args)


This method lets you specify the grouping fields explicitly. The `args` must
be names of grouping fields or calculated fields that this queryset was
created with.


#### limit_by(offset_limit, *fields_or_expr)


Adds a LIMIT BY clause to the query.
- `offset_limit`: either an integer specifying the limit, or a tuple of integers (offset, limit).
- `fields_or_expr`: the field names or expressions to use in the clause.


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


#### select_fields_as_sql()


Returns the selected fields or expressions as a SQL string.


#### update(**kwargs)


Updates all records matched by this queryset's conditions.
Keyword arguments specify the field names and expressions to use for the update.
Note that ClickHouse performs updates in the background, so they are not immediate.


#### with_totals()


Adds WITH TOTALS modifier ot GROUP BY, making query return extra row
with aggregate function calculated across all the rows. More information:
https://clickhouse.tech/docs/en/query_language/select/#with-totals-modifier


### Q

#### Q(*filter_funcs, **filter_fields)


#### to_sql(model_cls)


infi.clickhouse_orm.funcs
-------------------------

### F

Extends Cond, FunctionOperatorsMixin


Represents a database function call and its arguments.
It doubles as a query condition when the function returns a boolean result.

#### CAST(type)


#### CRC32()


#### IPv4CIDRToRange(cidr)


#### IPv4NumToString()


#### IPv4NumToStringClassC()


#### IPv4StringToNum()


#### IPv4ToIPv6()


#### IPv6CIDRToRange(cidr)


#### IPv6NumToString()


#### IPv6StringToNum()


#### MD5()


#### SHA1()


#### SHA224()


#### SHA256()


#### URLHash(n=None)


#### UUIDNumToString()


#### UUIDStringToNum()


#### F(name, *args)


Initializer.


#### abs()


#### acos()


#### addDays(n, timezone=NO_VALUE)


#### addHours(n, timezone=NO_VALUE)


#### addMinutes(n, timezone=NO_VALUE)


#### addMonths(n, timezone=NO_VALUE)


#### addQuarters(n, timezone=NO_VALUE)


#### addSeconds(n, timezone=NO_VALUE)


#### addWeeks(n, timezone=NO_VALUE)


#### addYears(n, timezone=NO_VALUE)


#### alphaTokens()


#### any(**kwargs)


#### anyHeavy(**kwargs)


#### anyHeavyIf(cond)


#### anyHeavyOrDefault()


#### anyHeavyOrDefaultIf(cond)


#### anyHeavyOrNull()


#### anyHeavyOrNullIf(cond)


#### anyIf(cond)


#### anyLast(**kwargs)


#### anyLastIf(cond)


#### anyLastOrDefault()


#### anyLastOrDefaultIf(cond)


#### anyLastOrNull()


#### anyLastOrNullIf(cond)


#### anyOrDefault()


#### anyOrDefaultIf(cond)


#### anyOrNull()


#### anyOrNullIf(cond)


#### appendTrailingCharIfAbsent(c)


#### argMax(**kwargs)


#### argMaxIf(y, cond)


#### argMaxOrDefault(y)


#### argMaxOrDefaultIf(y, cond)


#### argMaxOrNull(y)


#### argMaxOrNullIf(y, cond)


#### argMin(**kwargs)


#### argMinIf(y, cond)


#### argMinOrDefault(y)


#### argMinOrDefaultIf(y, cond)


#### argMinOrNull(y)


#### argMinOrNullIf(y, cond)


#### array()


#### arrayConcat()


#### arrayDifference()


#### arrayDistinct()


#### arrayElement(n)


#### arrayEnumerate()


#### arrayEnumerateDense()


#### arrayEnumerateDenseRanked()


#### arrayEnumerateUniq()


#### arrayEnumerateUniqRanked()


#### arrayIntersect()


#### arrayJoin()


#### arrayPopBack()


#### arrayPopFront()


#### arrayPushBack(x)


#### arrayPushFront(x)


#### arrayReduce(*args)


#### arrayResize(size, extender=None)


#### arrayReverse()


#### arraySlice(offset, length=None)


#### arrayStringConcat(sep=None)


#### arrayUniq()


#### asin()


#### atan()


#### avg(**kwargs)


#### avgIf(cond)


#### avgOrDefault()


#### avgOrDefaultIf(cond)


#### avgOrNull()


#### avgOrNullIf(cond)


#### base64Decode()


#### base64Encode()


#### bitAnd(y)


#### bitNot()


#### bitOr(y)


#### bitRotateLeft(y)


#### bitRotateRight(y)


#### bitShiftLeft(y)


#### bitShiftRight(y)


#### bitTest(y)


#### bitTestAll(*args)


#### bitTestAny(*args)


#### bitXor(y)


#### bitmapAnd(y)


#### bitmapAndCardinality(y)


#### bitmapAndnot(y)


#### bitmapAndnotCardinality(y)


#### bitmapBuild()


#### bitmapCardinality()


#### bitmapContains(needle)


#### bitmapHasAll(y)


#### bitmapHasAny(y)


#### bitmapOr(y)


#### bitmapOrCardinality(y)


#### bitmapToArray()


#### bitmapXor(y)


#### bitmapXorCardinality(y)


#### bitmaskToArray()


#### bitmaskToList()


#### cbrt()


#### ceiling(n=None)


#### ceiling(n=None)


#### cityHash64()


#### coalesce()


#### concat()


#### convertCharset(from_charset, to_charset)


#### corr(**kwargs)


#### corrIf(y, cond)


#### corrOrDefault(y)


#### corrOrDefaultIf(y, cond)


#### corrOrNull(y)


#### corrOrNullIf(y, cond)


#### cos()


#### count(**kwargs)


#### countEqual(x)


#### countIf()


#### countOrDefault()


#### countOrDefaultIf()


#### countOrNull()


#### countOrNullIf()


#### covarPop(**kwargs)


#### covarPopIf(y, cond)


#### covarPopOrDefault(y)


#### covarPopOrDefaultIf(y, cond)


#### covarPopOrNull(y)


#### covarPopOrNullIf(y, cond)


#### covarSamp(**kwargs)


#### covarSampIf(y, cond)


#### covarSampOrDefault(y)


#### covarSampOrDefaultIf(y, cond)


#### covarSampOrNull(y)


#### covarSampOrNullIf(y, cond)


#### dictGet(attr_name, id_expr)


#### dictGetHierarchy(id_expr)


#### dictGetOrDefault(attr_name, id_expr, default)


#### dictHas(id_expr)


#### dictIsIn(child_id_expr, ancestor_id_expr)


#### divide(**kwargs)


#### e()


#### empty()


#### emptyArrayDate()


#### emptyArrayDateTime()


#### emptyArrayFloat32()


#### emptyArrayFloat64()


#### emptyArrayInt16()


#### emptyArrayInt32()


#### emptyArrayInt64()


#### emptyArrayInt8()


#### emptyArrayString()


#### emptyArrayToSingle()


#### emptyArrayUInt16()


#### emptyArrayUInt32()


#### emptyArrayUInt64()


#### emptyArrayUInt8()


#### endsWith(suffix)


#### equals(**kwargs)


#### erf()


#### erfc()


#### exp()


#### exp10()


#### exp2()


#### extract(pattern)


#### extractAll(pattern)


#### farmHash64()


#### floor(n=None)


#### formatDateTime(format, timezone="")


#### gcd(b)


#### generateUUIDv4()


#### greater(**kwargs)


#### greaterOrEquals(**kwargs)


#### greatest(y)


#### halfMD5()


#### has(x)


#### hasAll(x)


#### hasAny(x)


#### hex()


#### hiveHash()


#### ifNotFinite(y)


#### ifNull(y)


#### indexOf(x)


#### intDiv(b)


#### intDivOrZero(b)


#### intExp10()


#### intExp2()


#### intHash32()


#### intHash64()


#### isFinite()


#### isIn(others)


#### isInfinite()


#### isNaN()


#### isNotIn(others)


#### isNotNull()


#### isNull()


#### javaHash()


#### jumpConsistentHash(buckets)


#### kurtPop(**kwargs)


#### kurtPopIf(cond)


#### kurtPopOrDefault()


#### kurtPopOrDefaultIf(cond)


#### kurtPopOrNull()


#### kurtPopOrNullIf(cond)


#### kurtSamp(**kwargs)


#### kurtSampIf(cond)


#### kurtSampOrDefault()


#### kurtSampOrDefaultIf(cond)


#### kurtSampOrNull()


#### kurtSampOrNullIf(cond)


#### lcm(b)


#### least(y)


#### length(**kwargs)


#### lengthUTF8()


#### less(**kwargs)


#### lessOrEquals(**kwargs)


#### lgamma()


#### like(pattern)


#### log()


#### log()


#### log10()


#### log2()


#### lower(**kwargs)


#### lowerUTF8()


#### match(pattern)


#### max(**kwargs)


#### maxIf(cond)


#### maxOrDefault()


#### maxOrDefaultIf(cond)


#### maxOrNull()


#### maxOrNullIf(cond)


#### metroHash64()


#### min(**kwargs)


#### minIf(cond)


#### minOrDefault()


#### minOrDefaultIf(cond)


#### minOrNull()


#### minOrNullIf(cond)


#### minus(**kwargs)


#### modulo(**kwargs)


#### multiply(**kwargs)


#### murmurHash2_32()


#### murmurHash2_64()


#### murmurHash3_128()


#### murmurHash3_32()


#### murmurHash3_64()


#### negate()


#### ngramDistance(**kwargs)


#### ngramDistanceCaseInsensitive(**kwargs)


#### ngramDistanceCaseInsensitiveUTF8(needle)


#### ngramDistanceUTF8(needle)


#### ngramSearch(**kwargs)


#### ngramSearchCaseInsensitive(**kwargs)


#### ngramSearchCaseInsensitiveUTF8(needle)


#### ngramSearchUTF8(needle)


#### notEmpty()


#### notEquals(**kwargs)


#### notLike(pattern)


#### now()


#### nullIf(y)


#### parseDateTimeBestEffort(**kwargs)


#### parseDateTimeBestEffortOrNull(timezone=NO_VALUE)


#### parseDateTimeBestEffortOrZero(timezone=NO_VALUE)


#### pi()


#### plus(**kwargs)


#### position(**kwargs)


#### positionCaseInsensitive(**kwargs)


#### positionCaseInsensitiveUTF8(needle)


#### positionUTF8(needle)


#### power(y)


#### power(y)


#### quantile(**kwargs)


#### quantileDeterministic(**kwargs)


#### quantileDeterministicIf()


#### quantileDeterministicOrDefault()


#### quantileDeterministicOrDefaultIf()


#### quantileDeterministicOrNull()


#### quantileDeterministicOrNullIf()


#### quantileExact(**kwargs)


#### quantileExactIf()


#### quantileExactOrDefault()


#### quantileExactOrDefaultIf()


#### quantileExactOrNull()


#### quantileExactOrNullIf()


#### quantileExactWeighted(**kwargs)


#### quantileExactWeightedIf()


#### quantileExactWeightedOrDefault()


#### quantileExactWeightedOrDefaultIf()


#### quantileExactWeightedOrNull()


#### quantileExactWeightedOrNullIf()


#### quantileIf()


#### quantileOrDefault()


#### quantileOrDefaultIf()


#### quantileOrNull()


#### quantileOrNullIf()


#### quantileTDigest(**kwargs)


#### quantileTDigestIf()


#### quantileTDigestOrDefault()


#### quantileTDigestOrDefaultIf()


#### quantileTDigestOrNull()


#### quantileTDigestOrNullIf()


#### quantileTDigestWeighted(**kwargs)


#### quantileTDigestWeightedIf()


#### quantileTDigestWeightedOrDefault()


#### quantileTDigestWeightedOrDefaultIf()


#### quantileTDigestWeightedOrNull()


#### quantileTDigestWeightedOrNullIf()


#### quantileTiming(**kwargs)


#### quantileTimingIf()


#### quantileTimingOrDefault()


#### quantileTimingOrDefaultIf()


#### quantileTimingOrNull()


#### quantileTimingOrNullIf()


#### quantileTimingWeighted(**kwargs)


#### quantileTimingWeightedIf()


#### quantileTimingWeightedOrDefault()


#### quantileTimingWeightedOrDefaultIf()


#### quantileTimingWeightedOrNull()


#### quantileTimingWeightedOrNullIf()


#### quantiles(**kwargs)


#### quantilesDeterministic(**kwargs)


#### quantilesDeterministicIf()


#### quantilesDeterministicOrDefault()


#### quantilesDeterministicOrDefaultIf()


#### quantilesDeterministicOrNull()


#### quantilesDeterministicOrNullIf()


#### quantilesExact(**kwargs)


#### quantilesExactIf()


#### quantilesExactOrDefault()


#### quantilesExactOrDefaultIf()


#### quantilesExactOrNull()


#### quantilesExactOrNullIf()


#### quantilesExactWeighted(**kwargs)


#### quantilesExactWeightedIf()


#### quantilesExactWeightedOrDefault()


#### quantilesExactWeightedOrDefaultIf()


#### quantilesExactWeightedOrNull()


#### quantilesExactWeightedOrNullIf()


#### quantilesIf()


#### quantilesOrDefault()


#### quantilesOrDefaultIf()


#### quantilesOrNull()


#### quantilesOrNullIf()


#### quantilesTDigest(**kwargs)


#### quantilesTDigestIf()


#### quantilesTDigestOrDefault()


#### quantilesTDigestOrDefaultIf()


#### quantilesTDigestOrNull()


#### quantilesTDigestOrNullIf()


#### quantilesTDigestWeighted(**kwargs)


#### quantilesTDigestWeightedIf()


#### quantilesTDigestWeightedOrDefault()


#### quantilesTDigestWeightedOrDefaultIf()


#### quantilesTDigestWeightedOrNull()


#### quantilesTDigestWeightedOrNullIf()


#### quantilesTiming(**kwargs)


#### quantilesTimingIf()


#### quantilesTimingOrDefault()


#### quantilesTimingOrDefaultIf()


#### quantilesTimingOrNull()


#### quantilesTimingOrNullIf()


#### quantilesTimingWeighted(**kwargs)


#### quantilesTimingWeightedIf()


#### quantilesTimingWeightedOrDefault()


#### quantilesTimingWeightedOrDefaultIf()


#### quantilesTimingWeightedOrNull()


#### quantilesTimingWeightedOrNullIf()


#### rand()


#### rand64()


#### randConstant()


#### range()


#### regexpQuoteMeta()


#### replace(pattern, replacement)


#### replaceAll(pattern, replacement)


#### replaceOne(pattern, replacement)


#### replaceRegexpAll(pattern, replacement)


#### replaceRegexpOne(pattern, replacement)


#### reverse(**kwargs)


#### reverseUTF8()


#### round(n=None)


#### roundAge()


#### roundDown(y)


#### roundDuration()


#### roundToExp2()


#### sin()


#### sipHash128()


#### sipHash64()


#### skewPop(**kwargs)


#### skewPopIf(cond)


#### skewPopOrDefault()


#### skewPopOrDefaultIf(cond)


#### skewPopOrNull()


#### skewPopOrNullIf(cond)


#### skewSamp(**kwargs)


#### skewSampIf(cond)


#### skewSampOrDefault()


#### skewSampOrDefaultIf(cond)


#### skewSampOrNull()


#### skewSampOrNullIf(cond)


#### splitByChar(s)


#### splitByString(s)


#### sqrt()


#### startsWith(prefix)


#### substring(**kwargs)


#### substringUTF8(offset, length)


#### subtractDays(n, timezone=NO_VALUE)


#### subtractHours(n, timezone=NO_VALUE)


#### subtractMinutes(n, timezone=NO_VALUE)


#### subtractMonths(n, timezone=NO_VALUE)


#### subtractQuarters(n, timezone=NO_VALUE)


#### subtractSeconds(n, timezone=NO_VALUE)


#### subtractWeeks(n, timezone=NO_VALUE)


#### subtractYears(n, timezone=NO_VALUE)


#### sum(**kwargs)


#### sumIf(cond)


#### sumOrDefault()


#### sumOrDefaultIf(cond)


#### sumOrNull()


#### sumOrNullIf(cond)


#### tan()


#### tgamma()


#### timeSlot()


#### timeSlots(duration)


#### toDate(**kwargs)


#### toDateOrNull()


#### toDateOrZero()


#### toDateTime(**kwargs)


#### toDateTime64(**kwargs)


#### toDateTime64OrNull(precision, timezone=NO_VALUE)


#### toDateTime64OrZero(precision, timezone=NO_VALUE)


#### toDateTimeOrNull()


#### toDateTimeOrZero()


#### toDayOfMonth()


#### toDayOfWeek()


#### toDayOfYear()


#### toDecimal128(**kwargs)


#### toDecimal128OrNull(scale)


#### toDecimal128OrZero(scale)


#### toDecimal32(**kwargs)


#### toDecimal32OrNull(scale)


#### toDecimal32OrZero(scale)


#### toDecimal64(**kwargs)


#### toDecimal64OrNull(scale)


#### toDecimal64OrZero(scale)


#### toFixedString(length)


#### toFloat32(**kwargs)


#### toFloat32OrNull()


#### toFloat32OrZero()


#### toFloat64(**kwargs)


#### toFloat64OrNull()


#### toFloat64OrZero()


#### toHour()


#### toIPv4()


#### toIPv6()


#### toISOWeek(timezone="")


#### toISOYear(timezone="")


#### toInt16(**kwargs)


#### toInt16OrNull()


#### toInt16OrZero()


#### toInt32(**kwargs)


#### toInt32OrNull()


#### toInt32OrZero()


#### toInt64(**kwargs)


#### toInt64OrNull()


#### toInt64OrZero()


#### toInt8(**kwargs)


#### toInt8OrNull()


#### toInt8OrZero()


#### toIntervalDay()


#### toIntervalHour()


#### toIntervalMinute()


#### toIntervalMonth()


#### toIntervalQuarter()


#### toIntervalSecond()


#### toIntervalWeek()


#### toIntervalYear()


#### toMinute()


#### toMonday()


#### toMonth()


#### toQuarter(timezone="")


#### toRelativeDayNum(timezone="")


#### toRelativeHourNum(timezone="")


#### toRelativeMinuteNum(timezone="")


#### toRelativeMonthNum(timezone="")


#### toRelativeSecondNum(timezone="")


#### toRelativeWeekNum(timezone="")


#### toRelativeYearNum(timezone="")


#### toSecond()


#### toStartOfDay()


#### toStartOfFifteenMinutes()


#### toStartOfFiveMinute()


#### toStartOfHour()


#### toStartOfISOYear()


#### toStartOfMinute()


#### toStartOfMonth()


#### toStartOfQuarter()


#### toStartOfTenMinutes()


#### toStartOfWeek(mode=0)


#### toStartOfYear()


#### toString()


#### toStringCutToZero()


#### toTime(timezone="")


#### toTimeZone(timezone)


#### toUInt16(**kwargs)


#### toUInt16OrNull()


#### toUInt16OrZero()


#### toUInt32(**kwargs)


#### toUInt32OrNull()


#### toUInt32OrZero()


#### toUInt64(**kwargs)


#### toUInt64OrNull()


#### toUInt64OrZero()


#### toUInt8(**kwargs)


#### toUInt8OrNull()


#### toUInt8OrZero()


#### toUUID()


#### toUnixTimestamp(timezone="")


#### toWeek(mode=0, timezone="")


#### toYYYYMM(timezone="")


#### toYYYYMMDD(timezone="")


#### toYYYYMMDDhhmmss(timezone="")


#### toYear()


#### to_sql(*args)


Generates an SQL string for this function and its arguments.
For example if the function name is a symbol of a binary operator:
    (2.54 * `height`)
For other functions:
    gcd(12, 300)


#### today()


#### topK(**kwargs)


#### topKIf()


#### topKOrDefault()


#### topKOrDefaultIf()


#### topKOrNull()


#### topKOrNullIf()


#### topKWeighted(**kwargs)


#### topKWeightedIf()


#### topKWeightedOrDefault()


#### topKWeightedOrDefaultIf()


#### topKWeightedOrNull()


#### topKWeightedOrNullIf()


#### trimBoth()


#### trimLeft()


#### trimRight()


#### tryBase64Decode()


#### unhex()


#### uniq(**kwargs)


#### uniqExact(**kwargs)


