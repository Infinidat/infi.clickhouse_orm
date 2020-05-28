Class Reference
===============

infi.clickhouse_orm.database
----------------------------

### Database

#### Database(db_name, db_url="http://localhost:8123/", username=None, password=None, readonly=False)

Initializes a database instance. Unless it's readonly, the database will be
created on the ClickHouse server if it does not already exist.

- `db_name`: name of the database to connect to.
- `db_url`: URL of the ClickHouse server.
- `username`: optional connection credentials.
- `password`: optional connection credentials.
- `readonly`: use a read-only connection.


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

A base class for ORM models.

#### Model(**kwargs)

Creates a model instance, using keyword arguments as field values.
Since values are immediately converted to their Pythonic type,
invalid values will cause a `ValueError` to be raised.
Unrecognized field names will cause an `AttributeError`.


#### Model.create_table_sql(db)

Returns the SQL command for creating a table for this model.


#### Model.drop_table_sql(db)

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


#### BufferModel.create_table_sql(db)

Returns the SQL command for creating a table for this model.


#### BufferModel.drop_table_sql(db)

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

#### Field(default=None, alias=None, materialized=None)


### StringField

Extends Field

#### StringField(default=None, alias=None, materialized=None)


### DateField

Extends Field

#### DateField(default=None, alias=None, materialized=None)


### DateTimeField

Extends Field

#### DateTimeField(default=None, alias=None, materialized=None)


### BaseIntField

Extends Field

Abstract base class for all integer-type fields.

#### BaseIntField(default=None, alias=None, materialized=None)


### BaseFloatField

Extends Field

Abstract base class for all float-type fields.

#### BaseFloatField(default=None, alias=None, materialized=None)


### BaseEnumField

Extends Field

Abstract base class for all enum-type fields.

#### BaseEnumField(enum_cls, default=None, alias=None, materialized=None)


### ArrayField

Extends Field

#### ArrayField(inner_field, default=None, alias=None, materialized=None)


### FixedStringField

Extends StringField

#### FixedStringField(length, default=None, alias=None, materialized=None)


### UInt8Field

Extends BaseIntField

#### UInt8Field(default=None, alias=None, materialized=None)


### UInt16Field

Extends BaseIntField

#### UInt16Field(default=None, alias=None, materialized=None)


### UInt32Field

Extends BaseIntField

#### UInt32Field(default=None, alias=None, materialized=None)


### UInt64Field

Extends BaseIntField

#### UInt64Field(default=None, alias=None, materialized=None)


### Int8Field

Extends BaseIntField

#### Int8Field(default=None, alias=None, materialized=None)


### Int16Field

Extends BaseIntField

#### Int16Field(default=None, alias=None, materialized=None)


### Int32Field

Extends BaseIntField

#### Int32Field(default=None, alias=None, materialized=None)


### Int64Field

Extends BaseIntField

#### Int64Field(default=None, alias=None, materialized=None)


### Float32Field

Extends BaseFloatField

#### Float32Field(default=None, alias=None, materialized=None)


### Float64Field

Extends BaseFloatField

#### Float64Field(default=None, alias=None, materialized=None)


### Enum8Field

Extends BaseEnumField

#### Enum8Field(enum_cls, default=None, alias=None, materialized=None)


### Enum16Field

Extends BaseEnumField

#### Enum16Field(enum_cls, default=None, alias=None, materialized=None)


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

Here we define Buffer engine
Read more here https://clickhouse.tech/reference_en.html#Buffer

#### Buffer(main_model, num_layers=16, min_time=10, max_time=100, min_rows=10000, max_rows=1000000, min_bytes=10000000, max_bytes=100000000)


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

#### QuerySet(model_cls, database)


#### conditions_as_sql(prewhere=True)

Return the contents of the queryset's WHERE or `PREWHERE` clause.


#### count()

Returns the number of matching model instances.


#### exclude(**kwargs)

Returns a new QuerySet instance that excludes all rows matching the conditions.


#### filter(**kwargs)

Returns a new QuerySet instance that includes only rows matching the conditions.


#### only(*field_names)

Limit the query to return only the specified field names.
Useful when there are large fields that are not needed,
or for creating a subquery to use with an IN operator.


#### order_by(*field_names)

Returns a new QuerySet instance with the ordering changed.


#### order_by_as_sql()

Return the contents of the queryset's ORDER BY clause.


#### query()

Return the the queryset as SQL.


