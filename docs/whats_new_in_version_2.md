What's New in Version 2
=======================

## Python 3.5+ Only

This version of the ORM no longer support Python 2.

## New flexible syntax for database expressions and functions

Expressions that use model fields, database functions and Python operators are now first-class citizens of the ORM. They provide infinite expressivity and flexibility when defining models and generating queries.

Example of expressions in model definition:
```python
class Temperature(Model):

    station_id = UInt16Field()
    timestamp = DateTimeField(default=F.now()) # function as default value
    degrees_celsius = Float32Field()
    degrees_fahrenheit = Float32Field(alias=degrees_celsius * 1.8 + 32) # expression as field alias

    # expressions in engine definition
    engine = MergeTree(partition_key=[F.toYYYYMM(timestamp)], order_by=[station_id, timestamp])
```

Example of expressions in queries:
```python
db = Database('default')
start = F.toStartOfMonth(F.now())
expr = (Temperature.timestamp > start) & (Temperature.station_id == 123) & (Temperature.degrees_celsius > 30)
for t in Temperature.objects_in(db).filter(expr):
    print(t.timestamp, t.degrees_celsius)
```

See [Expressions](expressions.md).

## Support for IPv4 and IPv6 fields

Two new fields classes were added: `IPv4Field` and `IPv6Field`. Their values are represented by Python's `ipaddress.IPv4Address` and `ipaddress.IPv6Address`.

See [Field Types](field_types.md).

## Automatic generation of models by inspecting existing tables

It is now easy to generate a model class on the fly for an existing table in the database using `Database.get_model_for_table`. This is particularly useful for querying system tables, for example:
```python
QueryLog = db.get_model_for_table('query_log', system_table=True)
for row in QueryLog.objects_in(db).filter(QueryLog.query_duration_ms > 10000):
    print(row.query)
```

## Convenient ways to import ORM classes

You can now import all ORM classes directly from `infi.clickhouse_orm`, without worrying about sub-modules. For example:
```python
from infi.clickhouse_orm import Database, Model, StringField, DateTimeField, MergeTree
```
See [Importing ORM Classes](importing_orm_classes.md).

