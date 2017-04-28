Table Engines
=============

See: [ClickHouse Documentation](https://clickhouse.yandex/reference_en.html#Table+engines)

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


Simple Engines
--------------

`TinyLog`, `Log` and `Memory` engines do not require any parameters:

    engine = engines.TinyLog()

    engine = engines.Log()
    
    engine = engines.Memory()


Engines in the MergeTree Family
-------------------------------

To define a `MergeTree` engine, supply the date column name and the names (or expressions) for the key columns:

    engine = engines.MergeTree('EventDate', ('CounterID', 'EventDate'))

You may also provide a sampling expression:

    engine = engines.MergeTree('EventDate', ('CounterID', 'EventDate'), sampling_expr='intHash32(UserID)')

A `CollapsingMergeTree` engine is defined in a similar manner, but requires also a sign column:

    engine = engines.CollapsingMergeTree('EventDate', ('CounterID', 'EventDate'), 'Sign')

For a `SummingMergeTree` you can optionally specify the summing columns:

    engine = engines.SummingMergeTree('EventDate', ('OrderID', 'EventDate', 'BannerID'),
                                      summing_cols=('Shows', 'Clicks', 'Cost'))

For a `ReplacingMergeTree` you can optionally specify the version column:

    engine = engines.ReplacingMergeTree('EventDate', ('OrderID', 'EventDate', 'BannerID'), ver_col='Version')

### Data Replication

Any of the above engines can be converted to a replicated engine (e.g. `ReplicatedMergeTree`) by adding two parameters, `replica_table_path` and `replica_name`:

    engine = engines.MergeTree('EventDate', ('CounterID', 'EventDate'),
                               replica_table_path='/clickhouse/tables/{layer}-{shard}/hits',
                               replica_name='{replica}')


Buffer Engine
-------------

A `Buffer` engine is only used in conjunction with a `BufferModel`.
The model should be a subclass of both `models.BufferModel` and the main model. 
The main model is also passed to the engine:

    class PersonBuffer(models.BufferModel, Person):

        engine = engines.Buffer(Person)

Additional buffer parameters can optionally be specified:

        engine = engines.Buffer(Person, num_layers=16, min_time=10, 
                                max_time=100, min_rows=10000, max_rows=1000000, 
                                min_bytes=10000000, max_bytes=100000000)

Then you can insert objects into Buffer model and they will be handled by ClickHouse properly:

    db.create_table(PersonBuffer)
    suzy = PersonBuffer(first_name='Suzy', last_name='Jones')
    dan = PersonBuffer(first_name='Dan', last_name='Schwartz')
    db.insert([dan, suzy])


---

[<< Field Types](field_types.md) | [Table of Contents](toc.md) | [Schema Migrations >>](schema_migrations.md)