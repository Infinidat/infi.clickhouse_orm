Field Options
=============

All field types accept the following arguments:

 - default
 - alias
 - materialized
 - readonly
 - codec

Note that `default`, `alias` and `materialized` are mutually exclusive - you cannot use more than one of them in a single field.

## default

Specifies a default value to use for the field. If not given, the field will have a default value based on its type: empty string for string fields, zero for numeric fields, etc.
The default value can be a Python value suitable for the field type, or an expression. For example:
```python
class Event(Model):

    name = StringField(default="EVENT")
    repeated = UInt32Field(default=1)
    created = DateTimeField(default=F.now())

    engine = Memory()
    ...
```
When creating a model instance, any fields you do not specify get their default value. Fields that use a default expression are assigned a sentinel value of `infi.clickhouse_orm.utils.NO_VALUE` instead. For example:
```python
>>> event = Event()
>>> print(event.to_dict())
{'name': 'EVENT', 'repeated': 1, 'created': <NO_VALUE>}
```
:warning: Due to a bug in ClickHouse versions prior to 20.1.2.4, insertion of records with expressions for default values may fail.

## alias / materialized

The `alias` and `materialized` attributes expect an expression that gets calculated by the database. The difference is that `alias` fields are calculated on the fly, while `materialized` fields are calculated when the record is inserted, and are stored on disk.
You can use any expression, and can refer to other model fields. For example:
```python
class Event(Model):

    created = DateTimeField()
    created_date = DateTimeField(materialized=F.toDate(created))
    name = StringField()
    normalized_name = StringField(alias=F.upper(F.trim(name)))

    engine = Memory()
```
For backwards compatibility with older versions of the ORM, you can pass the expression as an SQL string:
```python
    created_date = DateTimeField(materialized="toDate(created)")
```
Both field types can't be inserted into the database directly, so they are ignored when using the `Database.insert()` method. ClickHouse does not return the field values if you use `"SELECT * FROM ..."` - you have to list these field names explicitly in the query.

Usage:
```python
obj = Event(created=datetime.now(), name='MyEvent')
db = Database('my_test_db')
db.insert([obj])
# All values will be retrieved from database
db.select('SELECT created, created_date, username, name FROM $db.event', model_class=Event)
# created_date and username will contain a default value
db.select('SELECT * FROM $db.event', model_class=Event)
```
When creating a model instance, any alias or materialized fields are assigned a sentinel value of `infi.clickhouse_orm.utils.NO_VALUE` since their real values can only be known after insertion to the database.

## codec

This attribute specifies the compression algorithm to use for the field (instead of the default data compression algorithm defined in server settings).

Supported compression algorithms:

| Codec                | Argument                                   | Comment
| -------------------- | -------------------------------------------| ----------------------------------------------------
| NONE                 | None                                       | No compression.
| LZ4                  | None                                       | LZ4 compression.
| LZ4HC(`level`)       | Possible `level` range: [3, 12].           | Default value: 9. Greater values stands for better compression and higher CPU usage. Recommended value range: [4,9].
| ZSTD(`level`)        | Possible `level`range: [1, 22].            | Default value: 1. Greater values stands for better compression and higher CPU usage. Levels >= 20, should be used with caution, as they require more memory.
| Delta(`delta_bytes`) | Possible `delta_bytes` range: 1, 2, 4 , 8. | Default value for `delta_bytes` is `sizeof(type)` if it is equal to 1, 2,4 or 8 and equals to 1 otherwise.

Codecs can be combined by separating their names with commas. The default database codec is not included into pipeline (if it should be applied to a field, you have to specify it explicitly in pipeline).

Recommended usage for codecs:
- When values for particular metric do not differ significantly from point to point, delta-encoding allows to reduce disk space usage significantly.
- DateTime works great with pipeline of Delta, ZSTD and the column size can be compressed to 2-3% of its original size (given a smooth datetime data)
- Numeric types usually enjoy best compression rates with ZSTD
- String types enjoy good compression rates with LZ4HC

Example:
```python
class Stats(Model):

    id                  = UInt64Field(codec='ZSTD(10)')
    timestamp           = DateTimeField(codec='Delta,ZSTD')
    timestamp_date      = DateField(codec='Delta(4),ZSTD(22)')
    metadata_id         = Int64Field(codec='LZ4')
    status              = StringField(codec='LZ4HC(10)')
    calculation         = NullableField(Float32Field(), codec='ZSTD')
    alerts              = ArrayField(FixedStringField(length=15), codec='Delta(2),LZ4HC')

    engine = MergeTree('timestamp_date', ('id', 'timestamp'))
```
Note: This feature is supported on ClickHouse version 19.1.16 and above. Codec arguments will be ignored by the ORM for older versions of ClickHouse.

## readonly

This attribute is set automatically for fields with `alias` or `materialized` attributes, you do not need to pass it yourself.

---

[<< Querysets](querysets.md) | [Table of Contents](toc.md) | [Field Types >>](field_types.md)