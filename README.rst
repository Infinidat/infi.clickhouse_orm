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

Models are defined in a way reminiscent of Django's ORM::

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

Once you have a model, you can create model instances::

    >>> dan = Person(first_name='Dan', last_name='Schwartz')
    >>> suzy = Person(first_name='Suzy', last_name='Jones')
    >>> dan.first_name
    u'Dan'

When values are assigned to model fields, they are immediately converted to their Pythonic data type.
In case the value is invalid, a ``ValueError`` is raised::

    >>> suzy.birthday = '1980-01-17'
    >>> suzy.birthday
    datetime.date(1980, 1, 17)
    >>> suzy.birthday = 0.5
    ValueError: Invalid value for DateField - 0.5
    >>> suzy.birthday = '1922-05-31'
    ValueError: DateField out of range - 1922-05-31 is not between 1970-01-01 and 2038-01-19

Inserting to the Database
-------------------------

To write your instances to ClickHouse, you need a ``Database`` instance::

    from infi.clickhouse_orm.database import Database

    db = Database('my_test_db')

This automatically connects to http://localhost:8123 and creates a database called my_test_db, unless it already exists.
If necessary, you can specify a different database URL and optional credentials::

    db = Database('my_test_db', db_url='http://192.168.1.1:8050', username='scott', password='tiger')

Using the ``Database`` instance you can create a table for your model, and insert instances to it::

    db.create_table(Person)
    db.insert([dan, suzy])

The ``insert`` method can take any iterable of model instances, but they all must belong to the same model class.

Reading from the Database
-------------------------

Loading model instances from the database is simple::

    for person in db.select("SELECT * FROM my_test_db.person", model_class=Person):
        print person.first_name, person.last_name

Do not include a ``FORMAT`` clause in the query, since the ORM automatically sets the format to ``TabSeparatedWithNamesAndTypes``.

It is possible to select only a subset of the columns, and the rest will receive their default values::

    for person in db.select("SELECT first_name FROM my_test_db.person WHERE last_name='Smith'", model_class=Person):
        print person.first_name

SQL Placeholders
****************

There are a couple of special placeholders that you can use inside the SQL to make it easier to write:
``$db`` and ``$table``. The first one is replaced by the database name, and the second is replaced by
the database name plus table name (but is available only when the model is specified).

So instead of this::

    db.select("SELECT * FROM my_test_db.person", model_class=Person)

you can use::

    db.select("SELECT * FROM $db.person", model_class=Person)

or even::

    db.select("SELECT * FROM $table", model_class=Person)

Ad-Hoc Models
*************

Specifying a model class is not required. In case you do not provide a model class, an ad-hoc class will
be defined based on the column names and types returned by the query::

    for row in db.select("SELECT max(height) as max_height FROM my_test_db.person"):
        print row.max_height

This is a very convenient feature that saves you the need to define a model for each query, while still letting
you work with Pythonic column values and an elegant syntax.

Counting
--------

The ``Database`` class also supports counting records easily::

    >>> db.count(Person)
    117
    >>> db.count(Person, conditions="height > 1.90")
    6

Pagination
----------

It is possible to paginate through model instances::

    >>> order_by = 'first_name, last_name'
    >>> page = db.paginate(Person, order_by, page_num=1, page_size=100)
    >>> print page.number_of_objects
    2507
    >>> print page.pages_total
    251
    >>> for person in page.objects:
    >>>     # do something

The ``paginate`` method returns a ``namedtuple`` containing the following fields:

- ``objects`` - the list of objects in this page
- ``number_of_objects`` - total number of objects in all pages
- ``pages_total`` - total number of pages
- ``number`` - the page number
- ``page_size`` - the number of objects per page

You can optionally pass conditions to the query::

    >>> page = db.paginate(Person, order_by, page_num=1, page_size=100, conditions='height > 1.90')

Note that ``order_by`` must be chosen so that the ordering is unique, otherwise there might be
inconsistencies in the pagination (such as an instance that appears on two different pages).

Schema Migrations
-----------------

Over time, your models may change and the database will have to be modified accordingly.
Migrations allow you to describe these changes succinctly using Python, and to apply them
to the database. A migrations table automatically keeps track of which migrations were already applied.

For details please refer to the MIGRATIONS.rst document.

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

To define a ``MergeTree`` engine, supply the date column name and the names (or expressions) for the key columns::

    engine = engines.MergeTree('EventDate', ('CounterID', 'EventDate'))

You may also provide a sampling expression::

    engine = engines.MergeTree('EventDate', ('CounterID', 'EventDate'), sampling_expr='intHash32(UserID)')

A ``CollapsingMergeTree`` engine is defined in a similar manner, but requires also a sign column::

    engine = engines.CollapsingMergeTree('EventDate', ('CounterID', 'EventDate'), 'Sign')

For a ``SummingMergeTree`` you can optionally specify the summing columns::

    engine = engines.SummingMergeTree('EventDate', ('OrderID', 'EventDate', 'BannerID'),
                                      summing_cols=('Shows', 'Clicks', 'Cost'))

Data Replication
****************

Any of the above engines can be converted to a replicated engine (e.g. ``ReplicatedMergeTree``) by adding two parameters, ``replica_table_path`` and ``replica_name``::

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