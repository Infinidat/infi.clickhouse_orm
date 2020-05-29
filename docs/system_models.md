System Models
=============

[Clickhouse docs](https://clickhouse.tech/docs/en/operations/system-tables/).

System models are read only models for implementing part of the system's functionality, and for providing access to information about how the system is working.

Currently the following system models are supported:

| Class        | DB Table       | Comments
| ------------ | -------------- | ---------------------------------------------------
| SystemPart   | system.parts   | Gives methods to work with partitions. See below.

Partitions and Parts
--------------------

[ClickHouse docs](https://clickhouse.tech/docs/en/sql-reference/statements/alter/#alter_manipulations-with-partitions).

A partition in a table is data for a single calendar month. Table "system.parts" contains information about each part.

| Method                | Parameters                | Comments
| --------------------- | ------------------------- | -----------------------------------------------------------------------------------------------
| get(static)           | database, conditions=""   | Gets database partitions, filtered by conditions
| get_active(static)    | database, conditions=""   | Gets only active (not detached or dropped) partitions, filtered by conditions
| detach                | settings=None             | Detaches the partition. Settings is a dict of params to pass to http request
| drop                  | settings=None             | Drops the partition. Settings is a dict of params to pass to http request
| attach                | settings=None             | Attaches already detached partition. Settings is a dict of params to pass to http request
| freeze                | settings=None             | Freezes (makes backup) of the partition. Settings is a dict of params to pass to http request
| fetch                 | settings=None             | Fetches partition. Settings is a dict of params to pass to http request

Usage example:

    from infi.clickhouse_orm import Database, SystemPart
    db = Database('my_test_db', db_url='http://192.168.1.1:8050', username='scott', password='tiger')
    partitions = SystemPart.get_active(db, conditions='')  # Getting all active partitions of the database
    if len(partitions) > 0:
        partitions = sorted(partitions, key=lambda obj: obj.name)  # Partition name is YYYYMM, so we can sort so
        partitions[0].freeze()  # Make a backup in /opt/clickhouse/shadow directory
        partitions[0].drop()  # Dropped partition

`Note`: system.parts stores information for all databases. To be correct, SystemPart model was designed to receive only parts belonging to the given database instance.


---

[<< Schema Migrations](schema_migrations.md) | [Table of Contents](toc.md) | [Contributing >>](contributing.md)