Table Engines
=============

Each model must have an engine instance, used when creating the table in ClickHouse.

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

A `Buffer` engine is available for BufferModels. (See below how to use BufferModel). You can specify following parameters:

    engine = engines.Buffer(Person) # you need to initialize engine with main Model. Other default parameters will be used
    # or:
    engine = engines.Buffer(Person, num_layers=16, min_time=10, 
                            max_time=100, min_rows=10000, max_rows=1000000, 
                            min_bytes=10000000, max_bytes=100000000)

Buffer Models
-------------

Here's how you can define Model for Buffer Engine. The Buffer Model should be inherited from models.BufferModel and main Model:

    class PersonBuffer(models.BufferModel, Person):

        engine = engines.Buffer(Person)

Then you can insert objects into Buffer model and they will be handled by ClickHouse properly:

    db.create_table(PersonBuffer)
    suzy = PersonBuffer(first_name='Suzy', last_name='Jones')
    dan = PersonBuffer(first_name='Dan', last_name='Schwartz')
    db.insert([dan, suzy])

Data Replication
----------------

Any of the above engines can be converted to a replicated engine (e.g. `ReplicatedMergeTree`) by adding two parameters, `replica_table_path` and `replica_name`:

    engine = engines.MergeTree('EventDate', ('CounterID', 'EventDate'),
                               replica_table_path='/clickhouse/tables/{layer}-{shard}/hits',
                               replica_name='{replica}')
