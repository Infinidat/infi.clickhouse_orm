Overview
========

This project is simple ORM for working with the `ClickHouse database <https://clickhouse.yandex/>`_.
It allows you to define model classes whose instances can be written to the database and read from it.

Installation
============

To install infi.clickhouse_orm::

    pip install infi.clickhouse_orm

Usage
=====

Defining Models
---------------

Models are defined in a way reminiscent of Django's ORM:

.. code:: python

    from infi.clickhouse_orm import models, fields, engines

    class Person(models.Model):

        first_name = fields.StringField()
        last_name = fields.StringField()
        birthday = fields.DateField()
        height = fields.Float32Field()

        engine = engines.MergeTree('birthday', ('first_name', 'last_name', 'birthday'))

It is possible to provide a default value for a field, instead of its "natural" default (empty string for string fields, zero for numeric fields etc.).

See below for the supported field types and table engines.

Using Models
------------

Once you have a model, you can create model instances:

.. code:: python

    >>> dan = Person(first_name='Dan', last_name='Schwartz')
    >>> suzy = Person(first_name='Suzy', last_name='Jones')
    >>> dan.first_name
    u'Dan'

When values are assigned to model fields, they are immediately converted to their Pythonic data type.
In case the value is invalid, a ``ValueError`` is raised:

.. code:: python

    >>> suzy.birthday = '1980-01-17'
    >>> suzy.birthday
    datetime.date(1980, 1, 17)
    >>> suzy.birthday = 0.5
    ValueError: Invalid value for DateField - 0.5
    >>> suzy.birthday = '1922-05-31'
    ValueError: DateField out of range - 1922-05-31 is not between 1970-01-01 and 2038-01-19

Inserting to the Database
-------------------------

To write your instances to ClickHouse, you need a ``Database`` instance:

.. code:: python

    from infi.clickhouse_orm.database import Database

    db = Database('my_test_db')

This automatically connects to http://localhost:8123 and creates a database called my_test_db, unless it already exists.
If necessary, you can specify a different database URL and optional credentials:

.. code:: python

    db = Database('my_test_db', db_url='http://192.168.1.1:8050', username='scott', password='tiger')

Using the ``Database`` instance you can create a table for your model, and insert instances to it:

.. code:: python

    db.create_table(Person)
    db.insert([dan, suzy])

The ``insert`` method can take any iterable of model instances, but they all must belong to the same model class.

Reading from the Database
-------------------------

Loading model instances from the database is simple:

.. code:: python

    for person in db.select("SELECT * FROM my_test_db.person", model_class=Person):
        print person.first_name, person.last_name

Do not include a ``FORMAT`` clause in the query, since the ORM automatically sets the format to ``TabSeparatedWithNamesAndTypes``.

It is possible to select only a subset of the columns, and the rest will receive their default values:

.. code:: python

    for person in db.select("SELECT first_name FROM my_test_db.person WHERE last_name='Smith'", model_class=Person):
        print person.first_name

Ad-Hoc Models
*************

Specifying a model class is not required. In case you do not provide a model class, an ad-hoc class will
be defined based on the column names and types returned by the query:

.. code:: python

    for row in db.select("SELECT max(height) as max_height FROM my_test_db.person"):
        print row.max_height

This is a very convenient feature that saves you the need to define a model for each query, while still letting
you work with Pythonic column values and an elegant syntax.

Counting
--------

The ``Database`` class also supports counting records easily:

.. code:: python

    >>> db.count(Person)
    117
    >>> db.count(Person, conditions="height > 1.90")
    6

Field Types
-----------

Currently the following field types are supported:

=============  ========    =================  ===================================================
Class          DB Type     Pythonic Type      Comments
=============  ========    =================  ===================================================
StringField    String      unicode            Encoded as UTF-8 when written to ClickHouse
DateField      Date        datetime.date      Range 1970-01-01 to 2038-01-19
DateTimeField  DateTime    datetime.datetime  Minimal value is 1970-01-01 00:00:00; Always in UTC
Int8Field      Int8        int                Range -128 to 127
Int16Field     Int16       int                Range -32768 to 32767
Int32Field     Int32       int                Range -2147483648 to 2147483647
Int64Field     Int64       int/long           Range -9223372036854775808 to 9223372036854775807
UInt8Field     UInt8       int                Range 0 to 255
UInt16Field    UInt16      int                Range 0 to 65535
UInt32Field    UInt32      int                Range 0 to 4294967295
UInt64Field    UInt64      int/long           Range 0 to 18446744073709551615
Float32Field   Float32     float
Float64Field   Float64     float
=============  ========    =================  ===================================================

Table Engines
-------------

Each model must have an engine instance, used when creating the table in ClickHouse.

To define a ``MergeTree`` engine, supply the date column name and the names (or expressions) for the key columns:

.. code:: python

    engine = engines.MergeTree('EventDate', ('CounterID', 'EventDate'))

You may also provide a sampling expression:

.. code:: python

    engine = engines.MergeTree('EventDate', ('CounterID', 'EventDate'), sampling_expr='intHash32(UserID)')

A ``CollapsingMergeTree`` engine is defined in a similar manner, but requires also a sign column:

.. code:: python

    engine = engines.CollapsingMergeTree('EventDate', ('CounterID', 'EventDate'), 'Sign')

For a ``SummingMergeTree`` you can optionally specify the summing columns:

.. code:: python

    engine = engines.SummingMergeTree('EventDate', ('OrderID', 'EventDate', 'BannerID'),
                                      summing_cols=('Shows', 'Clicks', 'Cost'))

Data Replication
****************

Any of the above engines can be converted to a replicated engine (e.g. ``ReplicatedMergeTree``) by adding two parameters, ``replica_table_path`` and ``replica_name``:

.. code:: python

    engine = engines.MergeTree('EventDate', ('CounterID', 'EventDate'),
                               replica_table_path='/clickhouse/tables/{layer}-{shard}/hits',
                               replica_name='{replica}')

Development
===========

After cloning the project, run the following commands::

    easy_install -U infi.projector
    cd infi.clickhouse_orm
    projector devenv build

To run the tests, ensure that the ClickHouse server is running on http://localhost:8123/ (this is the default), and run::

    bin/nosetests
