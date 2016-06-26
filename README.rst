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

It is possible to provide a default value for a field, instead of it's "natural" default (empty string for string fields, zero for numeric fields etc.).

See below for the supported model field types.

Using Models
------------

Once you have a model, you can create model instances:

.. code:: python

    >>> dan = Person(first_name='Dan', last_name='Schwartz')
    >>> suzy = Person(first_name='Suzy', last_name='Jones')
    >>> dan.first_name
    u'Dan'

When values are assigned to a model fields, they are immediately converted to their Pythonic data type.
In case the value is invalid, a ValueError is raised:

.. code:: python

    >>> suzy.birthday = '1980-01-17'
    >>> suzy.birthday
    datetime.date(1980, 1, 17)
    >>> suzy.birthday = 0.5
    ValueError: Invalid value for DateField - 0.5
    >>> suzy.birthday = '1922-05-31'
    ValueError: DateField out of range - 1922-05-31 is not between 1970-01-01 and 2038-01-19

To write your instances to ClickHouse, you need a Database instance:

.. code:: python

    from infi.clickhouse_orm.database import Database

    db = Database('my_test_db')

This automatically connects to http://localhost:8123 and creates a database called my_test_db, unless it already exists.
If necessary, you can specify a different database URL and optional credentials:

.. code:: python

    db = Database('my_test_db', db_url='http://192.168.1.1:8050', username='scott', password='tiger')

Using the Database instance you can create a table for your model, and insert instances to it:

.. code:: python

    db.create_table(Person)
    db.insert([dan, suzy])

The insert method can take any iterable of model instances, but they all must belong to the same model class.



Field Types
-----------

Currently the following field types are supported:

- UInt8Field
- UInt16Field
- UInt32Field
- UInt64Field
- Int8Field
- Int16Field
- Int32Field
- Int64Field
- Float32Field
- Float64Field
- StringField
- DateField
- DateTimeField



Development
===========

After cloning the project, run the following commands::

    easy_install -U infi.projector
    cd infi.clickhouse_orm
    projector devenv build

To run the tests, ensure that the ClickHouse server is running on http://localhost:8123/ (this is the default), and run::

    bin/nosetests
