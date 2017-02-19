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
Alternatively it is possible to pass alias or materialized parameters (see below for usage examples).
Only one of ``default``, ``alias`` and ``materialized`` parameters can be provided.

See below for the supported field types and table engines.

Table Names
***********

The table name used for the model is its class name, converted to lowercase. To override the default name,
implement the ``table_name`` method::

    class Person(models.Model):

        ...

        @classmethod
        def table_name(cls):
            return 'people'

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

Creating a read-only database is also supported. Such a ``Database`` instance can only read data, and cannot
modify data or schemas::

    db = Database('my_test_db', readonly=True)

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
    >>> page = db.paginate(Person, order_by, page_num=1, page_size=10)
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
- ``number`` - the page number, starting from 1; the special value -1 may be used to retrieve the last page
- ``page_size`` - the number of objects per page

You can optionally pass conditions to the query::

    >>> page = db.paginate(Person, order_by, page_num=1, page_size=100, conditions='height > 1.90')

Note that ``order_by`` must be chosen so that the ordering is unique, otherwise there might be
inconsistencies in the pagination (such as an instance that appears on two different pages).


System models
-------------

`Clickhouse docs <https://clickhouse.yandex/reference_en.html#System tables>`_.

System models are read only models for implementing part of the system's functionality,
and for providing access to information about how the system is working.

Currently the following system models are supported:

===================  ============    ===================================================
Class                DB Table        Comments
===================  ============    ===================================================
SystemPart           system.parts    Gives methods to work with partitions. See below.
===================  ============    ===================================================


Partitions and parts
--------------------

`ClickHouse docs <https://clickhouse.yandex/reference_en.html#Manipulations with partitions and parts>`_.

A partition in a table is data for a single calendar month. Table "system.parts" contains information about each part.

===================  =======================    =============================================================================================
Method               Parameters                 Comments
===================  =======================    =============================================================================================
get(static)          database, conditions=""    Gets database partitions, filtered by conditions
get_active(static)   database, conditions=""    Gets only active (not detached or dropped) partitions, filtered by conditions
detach               settings=None              Detaches the partition. Settings is a dict of params to pass to http request
drop                 settings=None              Drops the partition. Settings is a dict of params to pass to http request
attach               settings=None              Attaches already detached partition. Settings is a dict of params to pass to http request
freeze               settings=None              Freezes (makes backup) of the partition. Settings is a dict of params to pass to http request
fetch                settings=None              Fetches partition. Settings is a dict of params to pass to http request
===================  =======================    =============================================================================================

Usage example::

    from infi.clickhouse_orm.database import Database
    from infi.clickhouse_orm.system_models import SystemPart
    db = Database('my_test_db', db_url='http://192.168.1.1:8050', username='scott', password='tiger')
    partitions = SystemPart.get_active(db, conditions='')  # Getting all active partitions of the database
    if len(partitions) > 0:
        partitions = sorted(partitions, key=lambda obj: obj.name)  # Partition name is YYYYMM, so we can sort so
        partitions[0].freeze()  # Make a backup in /opt/clickhouse/shadow directory
        partitions[0].drop()  # Dropped partition

``Note``: system.parts stores information for all databases. To be correct,
SystemPart model was designed to receive only given database parts.


Schema Migrations
-----------------

Over time, your models may change and the database will have to be modified accordingly.
Migrations allow you to describe these changes succinctly using Python, and to apply them
to the database. A migrations table automatically keeps track of which migrations were already applied.

For details please refer to the MIGRATIONS.rst document.

Field Types
-----------

Currently the following field types are supported:

===================  ========    =================  ===================================================
Class                DB Type     Pythonic Type      Comments
===================  ========    =================  ===================================================
StringField          String      unicode            Encoded as UTF-8 when written to ClickHouse
DateField            Date        datetime.date      Range 1970-01-01 to 2038-01-19
DateTimeField        DateTime    datetime.datetime  Minimal value is 1970-01-01 00:00:00; Always in UTC
Int8Field            Int8        int                Range -128 to 127
Int16Field           Int16       int                Range -32768 to 32767
Int32Field           Int32       int                Range -2147483648 to 2147483647
Int64Field           Int64       int/long           Range -9223372036854775808 to 9223372036854775807
UInt8Field           UInt8       int                Range 0 to 255
UInt16Field          UInt16      int                Range 0 to 65535
UInt32Field          UInt32      int                Range 0 to 4294967295
UInt64Field          UInt64      int/long           Range 0 to 18446744073709551615
Float32Field         Float32     float
Float64Field         Float64     float
Enum8Field           Enum8       Enum               See below
Enum16Field          Enum16      Enum               See below
ArrayField           Array       list               See below
===================  ========    =================  ===================================================

DateTimeField and Time Zones
****************************

A ``DateTimeField`` can be assigned values from one of the following types:

- datetime
- date
- integer - number of seconds since the Unix epoch
- string in ``YYYY-MM-DD HH:MM:SS`` format

The assigned value always gets converted to a timezone-aware ``datetime`` in UTC. If the assigned
value is a timezone-aware ``datetime`` in another timezone, it will be converted to UTC. Otherwise, the assigned value is assumed to already be in UTC. 

DateTime values that are read from the database are also converted to UTC. ClickHouse formats them according to the
timezone of the server, and the ORM makes the necessary conversions. This requires a ClickHouse version which is new
enough to support the ``timezone()`` function, otherwise it is assumed to be using UTC. In any case, we recommend
settings the server timezone to UTC in order to prevent confusion.

Working with enum fields
************************

``Enum8Field`` and ``Enum16Field`` provide support for working with ClickHouse enum columns. They accept
strings or integers as values, and convert them to the matching Pythonic Enum member.

Python 3.4 and higher supports Enums natively. When using previous Python versions you 
need to install the `enum34` library.

Example of a model with an enum field::

    Gender = Enum('Gender', 'male female unspecified')

    class Person(models.Model):

        first_name = fields.StringField()
        last_name = fields.StringField()
        birthday = fields.DateField()
        gender = fields.Enum32Field(Gender)

        engine = engines.MergeTree('birthday', ('first_name', 'last_name', 'birthday'))

    suzy = Person(first_name='Suzy', last_name='Jones', gender=Gender.female)

Working with array fields
*************************

You can create array fields containing any data type, for example::

    class SensorData(models.Model):

        date = fields.DateField()
        temperatures = fields.ArrayField(fields.Float32Field())
        humidity_levels = fields.ArrayField(fields.UInt8Field())

        engine = engines.MergeTree('date', ('date',))

    data = SensorData(date=date.today(), temperatures=[25.5, 31.2, 28.7], humidity_levels=[41, 39, 66])


Working with materialized and alias fields
******************************************

ClickHouse provides an opportunity to create MATERIALIZED and ALIAS Fields.

See documentation `here <https://clickhouse.yandex/reference_en.html#Default values>`_.

Both field types can't be inserted into the database directly, so they are ignored when using the ``Database.insert()`` method.
ClickHouse does not return the field values if you use ``"SELECT * FROM ..."`` - you have to list these field
names explicitly in the query.

Usage::

    class Event(models.Model):

        created = fields.DateTimeField()
        created_date = fields.DateTimeField(materialized='toDate(created)')
        name = fields.StringField()
        username = fields.StringField(alias='name')

        engine = engines.MergeTree('created_date', ('created_date', 'created'))

    obj = Event(created=datetime.now(), name='MyEvent')
    db = Database('my_test_db')
    db.insert([obj])
    # All values will be retrieved from database
    db.select('SELECT created, created_date, username, name FROM $db.event', model_class=Event)
    # created_date and username will contain a default value
    db.select('SELECT * FROM $db.event', model_class=Event)


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

A ``Buffer`` engine is available for BufferModels. (See below how to use BufferModel). You can specify following parameters::

    engine = engines.Buffer(Person) # you need to initialize engine with main Model. Other default parameters will be used
    # or:
    engine = engines.Buffer(Person, num_layers=16, min_time=10, 
                            max_time=100, min_rows=10000, max_rows=1000000, 
                            min_bytes=10000000, max_bytes=100000000)

Buffer Models
-------------
Here's how you can define Model for Buffer Engine. The Buffer Model should be inherited from models.BufferModel and main Model::

    class PersonBuffer(models.BufferModel, Person):

        engine = engines.Buffer(Person)

Then you can insert objects into Buffer model and they will be handled by Clickhouse properly::

    db.create_table(PersonBuffer)
    suzy = PersonBuffer(first_name='Suzy', last_name='Jones')
    dan = PersonBuffer(first_name='Dan', last_name='Schwartz')
    db.insert([dan, suzy])


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
=======

To see test coverage information run::

    bin/nosetests --with-coverage --cover-package=infi.clickhouse_orm
