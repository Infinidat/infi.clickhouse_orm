Table Engines
=============

See: [ClickHouse Documentation](https://clickhouse.tech/docs/en/engines/table-engines/)

Each model must have an engine instance, used when creating the table in ClickHouse.

The following engines are supported by the ORM:

- TinyLog
- Log
- Memory
- MergeTree / ReplicatedMergeTree
- CollapsingMergeTree / ReplicatedCollapsingMergeTree
- SummingMergeTree / ReplicatedSummingMergeTree
- ReplacingMergeTree / ReplicatedReplacingMergeTree
- Buffer
- Merge
- Distributed


Simple Engines
--------------

`TinyLog`, `Log` and `Memory` engines do not require any parameters:

    engine = TinyLog()

    engine = Log()

    engine = Memory()


Engines in the MergeTree Family
-------------------------------

To define a `MergeTree` engine, supply the date column name and the names (or expressions) for the key columns:

    engine = MergeTree('EventDate', ('CounterID', 'EventDate'))

You may also provide a sampling expression:

    engine = MergeTree('EventDate', ('CounterID', 'EventDate'), sampling_expr=F.intHash32(UserID))

A `CollapsingMergeTree` engine is defined in a similar manner, but requires also a sign column:

    engine = CollapsingMergeTree('EventDate', ('CounterID', 'EventDate'), 'Sign')

For a `SummingMergeTree` you can optionally specify the summing columns:

    engine = SummingMergeTree('EventDate', ('OrderID', 'EventDate', 'BannerID'),
                              summing_cols=('Shows', 'Clicks', 'Cost'))

For a `ReplacingMergeTree` you can optionally specify the version column:

    engine = ReplacingMergeTree('EventDate', ('OrderID', 'EventDate', 'BannerID'), ver_col='Version')

### Custom partitioning

ClickHouse supports [custom partitioning](https://clickhouse.tech/docs/en/engines/table-engines/mergetree-family/custom-partitioning-key/) expressions since version 1.1.54310

You can use custom partitioning with any `MergeTree` family engine.
To set custom partitioning:

* Instead of specifying the `date_col` (first) constructor parameter, pass a tuple of field names or expressions in the `order_by` (second) constructor parameter.
* Add `partition_key` parameter. It should be a tuple of expressions, by which partitions are built.

Standard monthly partitioning by date column can be specified using the `toYYYYMM(date)` function.

Example:

    engine = ReplacingMergeTree(order_by=('OrderID', 'EventDate', 'BannerID'), ver_col='Version',
                                partition_key=(F.toYYYYMM(EventDate), 'BannerID'))


### Primary key
ClickHouse supports [custom primary key](https://clickhouse.tech/docs/en/engines/table-engines/mergetree-family/mergetree/#primary-keys-and-indexes-in-queries) expressions since version 1.1.54310

You can use custom primary key with any `MergeTree` family engine.
To set custom partitioning add `primary_key` parameter. It should be a tuple of expressions, by which partitions are built.

By default primary key is equal to order_by expression

Example:

    engine = ReplacingMergeTree(order_by=('OrderID', 'EventDate', 'BannerID'), ver_col='Version',
                                partition_key=(F.toYYYYMM(EventDate), 'BannerID'), primary_key=('OrderID',))

### Data Replication

Any of the above engines can be converted to a replicated engine (e.g. `ReplicatedMergeTree`) by adding two parameters, `replica_table_path` and `replica_name`:

    engine = MergeTree('EventDate', ('CounterID', 'EventDate'),
                       replica_table_path='/clickhouse/tables/{layer}-{shard}/hits',
                       replica_name='{replica}')


Buffer Engine
-------------

A `Buffer` engine is only used in conjunction with a `BufferModel`.
The model should be a subclass of both `BufferModel` and the main model.
The main model is also passed to the engine:

    class PersonBuffer(BufferModel, Person):

        engine = Buffer(Person)

Additional buffer parameters can optionally be specified:

        engine = Buffer(Person, num_layers=16, min_time=10,
                        max_time=100, min_rows=10000, max_rows=1000000,
                        min_bytes=10000000, max_bytes=100000000)

Then you can insert objects into Buffer model and they will be handled by ClickHouse properly:

    db.create_table(PersonBuffer)
    suzy = PersonBuffer(first_name='Suzy', last_name='Jones')
    dan = PersonBuffer(first_name='Dan', last_name='Schwartz')
    db.insert([dan, suzy])


Merge Engine
-------------

[ClickHouse docs](https://clickhouse.tech/docs/en/operations/table_engines/merge/)

A `Merge` engine is only used in conjunction with a `MergeModel`.
This table does not store data itself, but allows reading from any number of other tables simultaneously. So you can't insert in it.
Engine parameter specifies re2 (similar to PCRE) regular expression, from which data is selected.

    class MergeTable(MergeModel):
        engine = Merge('^table_prefix')


---

[<< Field Types](field_types.md) | [Table of Contents](toc.md) | [Schema Migrations >>](schema_migrations.md)