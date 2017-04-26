Models and Databases
====================

Models represent ClickHouse tables, allowing you to work with them using familiar pythonic syntax.

Database instances connect to a specific ClickHouse database for running queries, inserting data and other operations.

Defining Models
---------------

Models are defined in a way reminiscent of Django's ORM:

    from infi.clickhouse_orm import models, fields, engines

    class Person(models.Model):

        first_name = fields.StringField()
        last_name = fields.StringField()
        birthday = fields.DateField()
        height = fields.Float32Field()

        engine = engines.MergeTree('birthday', ('first_name', 'last_name', 'birthday'))

It is possible to provide a default value for a field, instead of its "natural" default (empty string for string fields, zero for numeric fields etc.). Alternatively it is possible to pass alias or materialized parameters (see below for usage examples). Only one of `default`, `alias` and `materialized` parameters can be provided.

For more details see [Field Types](field_types.md) and [Table Engines](table_engines.md).

### Table Names

The table name used for the model is its class name, converted to lowercase. To override the default name, implement the `table_name` method:

    class Person(models.Model):

        ...

        @classmethod
        def table_name(cls):
            return 'people'

Using Models
------------

Once you have a model, you can create model instances:

    >>> dan = Person(first_name='Dan', last_name='Schwartz')
    >>> suzy = Person(first_name='Suzy', last_name='Jones')
    >>> dan.first_name
    u'Dan'

When values are assigned to model fields, they are immediately converted to their Pythonic data type. In case the value is invalid, a `ValueError` is raised:

    >>> suzy.birthday = '1980-01-17'
    >>> suzy.birthday
    datetime.date(1980, 1, 17)
    >>> suzy.birthday = 0.5
    ValueError: Invalid value for DateField - 0.5
    >>> suzy.birthday = '1922-05-31'
    ValueError: DateField out of range - 1922-05-31 is not between 1970-01-01 and 2038-01-19

Inserting to the Database
-------------------------

To write your instances to ClickHouse, you need a `Database` instance:

    from infi.clickhouse_orm.database import Database

    db = Database('my_test_db')

This automatically connects to <http://localhost:8123> and creates a database called my_test_db, unless it already exists. If necessary, you can specify a different database URL and optional credentials:

    db = Database('my_test_db', db_url='http://192.168.1.1:8050', username='scott', password='tiger')

Using the `Database` instance you can create a table for your model, and insert instances to it:

    db.create_table(Person)
    db.insert([dan, suzy])

The `insert` method can take any iterable of model instances, but they all must belong to the same model class.

Creating a read-only database is also supported. Such a `Database` instance can only read data, and cannot modify data or schemas:

    db = Database('my_test_db', readonly=True)

Reading from the Database
-------------------------

Loading model instances from the database is simple:

    for person in db.select("SELECT * FROM my_test_db.person", model_class=Person):
        print person.first_name, person.last_name

Do not include a `FORMAT` clause in the query, since the ORM automatically sets the format to `TabSeparatedWithNamesAndTypes`.

It is possible to select only a subset of the columns, and the rest will receive their default values:

    for person in db.select("SELECT first_name FROM my_test_db.person WHERE last_name='Smith'", model_class=Person):
        print person.first_name

The ORM provides a way to build simple queries without writing SQL by hand. The previous snippet can be written like this:

    for person in Person.objects_in(db).filter(last_name='Smith').only('first_name'):
        print person.first_name

See [Querysets](querysets.md) for more information.


Reading without a Model
-----------------------

When running a query, specifying a model class is not required. In case you do not provide a model class, an ad-hoc class will be defined based on the column names and types returned by the query:

    for row in db.select("SELECT max(height) as max_height FROM my_test_db.person"):
        print row.max_height

This is a very convenient feature that saves you the need to define a model for each query, while still letting you work with Pythonic column values and an elegant syntax.

SQL Placeholders
----------------

There are a couple of special placeholders that you can use inside the SQL to make it easier to write: `$db` and `$table`. The first one is replaced by the database name, and the second is replaced by the database name plus table name (but is available only when the model is specified).

So instead of this:

    db.select("SELECT * FROM my_test_db.person", model_class=Person)

you can use:

    db.select("SELECT * FROM $db.person", model_class=Person)

or even:

    db.select("SELECT * FROM $table", model_class=Person)

Counting
--------

The `Database` class also supports counting records easily:

    >>> db.count(Person)
    117
    >>> db.count(Person, conditions="height > 1.90")
    6

Pagination
----------

It is possible to paginate through model instances:

    >>> order_by = 'first_name, last_name'
    >>> page = db.paginate(Person, order_by, page_num=1, page_size=10)
    >>> print page.number_of_objects
    2507
    >>> print page.pages_total
    251
    >>> for person in page.objects:
    >>>     # do something

The `paginate` method returns a `namedtuple` containing the following fields:

-   `objects` - the list of objects in this page
-   `number_of_objects` - total number of objects in all pages
-   `pages_total` - total number of pages
-   `number` - the page number, starting from 1; the special value -1
    may be used to retrieve the last page
-   `page_size` - the number of objects per page

You can optionally pass conditions to the query:

    >>> page = db.paginate(Person, order_by, page_num=1, page_size=100, conditions='height > 1.90')

Note that `order_by` must be chosen so that the ordering is unique, otherwise there might be inconsistencies in the pagination (such as an instance that appears on two different pages).

