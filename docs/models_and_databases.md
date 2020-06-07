Models and Databases
====================

Models represent ClickHouse tables, allowing you to work with them using familiar pythonic syntax.

Database instances connect to a specific ClickHouse database for running queries, inserting data and other operations.

Defining Models
---------------

Models are defined in a way reminiscent of Django's ORM, by subclassing `Model`:
```python
from infi.clickhouse_orm import Model, StringField, DateField, Float32Field, MergeTree

class Person(Model):

    first_name = StringField()
    last_name = StringField()
    birthday = DateField()
    height = Float32Field()

    engine = MergeTree('birthday', ('first_name', 'last_name', 'birthday'))
```

The columns in the database table are represented by model fields. Each field has a type, which matches the type of the corresponding database column. All the supported fields types are listed [here](field_types.md).

A model must have an `engine`, which determines how its table is stored on disk (if at all), and what capabilities it has. For more details about table engines see [here](table_engines.md).

### Default values

Each field has a "natural" default value - empty string for string fields, zero for numeric fields etc. To specify a different value use the `default` parameter:

        first_name = StringField(default="anonymous")

For additional details see [here](field_options.md).

### Null values

To allow null values in a field, wrap it inside a `NullableField`:

        birthday = NullableField(DateField())

In this case, the default value for that field becomes `null` unless otherwise specified.

For more information about `NullableField` see [Field Types](field_types.md).

### Materialized fields

The value of a materialized field is calculated from other fields in the model. For example:

        year_born = Int16Field(materialized=F.toYear(birthday))

Materialized fields are read-only, meaning that their values are not sent to the database when inserting records.

For additional details see [here](field_options.md).

### Alias fields

An alias field is a field whose value is calculated by ClickHouse on the fly, as a function of other fields. It is not physically stored by the database. For example:

        weekday_born = field.UInt8Field(alias=F.toDayOfWeek(birthday))

Alias fields are read-only, meaning that their values are not sent to the database when inserting records.

For additional details see [here](field_options.md).

### Table Names

The table name used for the model is its class name, converted to lowercase. To override the default name, implement the `table_name` method:
```python
class Person(Model):

    ...

    @classmethod
    def table_name(cls):
        return 'people'
```

### Model Constraints

It is possible to define constraints which ClickHouse verifies when data is inserted. Trying to insert invalid records will raise a `ServerError`. Each constraint has a name and an expression to validate. For example:
```python
class Person(Model):

    ...

    # Ensure that the birthday is not a future date
    birthday_is_in_the_past = Constraint(birthday <= F.today())
```

### Data Skipping Indexes

Models that use an engine from the `MergeTree` family can define additional indexes over one or more columns or expressions. These indexes are used in SELECT queries for reducing the amount of data to read from the disk by skipping big blocks of data that do not satisfy the query's conditions.

For example:
```python
class Person(Model):

    ...

    # A minmax index that can help find people taller or shorter than some height
    height_index = Index(height, type=Index.minmax(), granularity=2)

    # A trigram index that can help find substrings inside people names
    names_index = Index((F.lower(first_name), F.lower(last_name)),
                        type=Index.ngrambf_v1(3, 256, 2, 0), granularity=1)
```


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
    ValueError: DateField out of range - 1922-05-31 is not between 1970-01-01 and 2105-12-31

Inserting to the Database
-------------------------

To write your instances to ClickHouse, you need a `Database` instance:

    from infi.clickhouse_orm import Database

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
        print(person.first_name, person.last_name)

Do not include a `FORMAT` clause in the query, since the ORM automatically sets the format to `TabSeparatedWithNamesAndTypes`.

It is possible to select only a subset of the columns, and the rest will receive their default values:

    for person in db.select("SELECT first_name FROM my_test_db.person WHERE last_name='Smith'", model_class=Person):
        print(person.first_name)

The ORM provides a way to build simple queries without writing SQL by hand. The previous snippet can be written like this:

    for person in Person.objects_in(db).filter(Person.last_name == 'Smith').only('first_name'):
        print(person.first_name)

See [Querysets](querysets.md) for more information.


Reading without a Model
-----------------------

When running a query, specifying a model class is not required. In case you do not provide a model class, an ad-hoc class will be defined based on the column names and types returned by the query:

    for row in db.select("SELECT max(height) as max_height FROM my_test_db.person"):
        print(row.max_height)

This is a very convenient feature that saves you the need to define a model for each query, while still letting you work with Pythonic column values and an elegant syntax.

It is also possible to generate a model class on the fly for an existing table in the database using `get_model_for_table`. This is particularly useful for querying system tables, for example:

    QueryLog = db.get_model_for_table('query_log', system_table=True)
    for row in QueryLog.objects_in(db).filter(QueryLog.query_duration_ms > 10000):
        print(row.query)

SQL Placeholders
----------------

There are a couple of special placeholders that you can use inside the SQL to make it easier to write: `$db` and `$table`. The first one is replaced by the database name, and the second is replaced by the table name (but is available only when the model is specified).

So instead of this:

    db.select("SELECT * FROM my_test_db.person", model_class=Person)

you can use:

    db.select("SELECT * FROM $db.$table", model_class=Person)

Note: normally it is not necessary to specify the database name, since it's already sent in the query parameters to ClickHouse. It is enough to specify the table name.

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
    >>> print(page.number_of_objects)
    2507
    >>> print(page.pages_total)
    251
    >>> for person in page.objects:
    >>>     # do something

The `paginate` method returns a `namedtuple` containing the following fields:

-   `objects` - the list of objects in this page
-   `number_of_objects` - total number of objects in all pages
-   `pages_total` - total number of pages
-   `number` - the page number, starting from 1; the special value -1 may be used to retrieve the last page
-   `page_size` - the number of objects per page

You can optionally pass conditions to the query:

    >>> page = db.paginate(Person, order_by, page_num=1, page_size=100, conditions='height > 1.90')

Note that `order_by` must be chosen so that the ordering is unique, otherwise there might be inconsistencies in the pagination (such as an instance that appears on two different pages).


---

[<< Overview](index.md) | [Table of Contents](toc.md) | [Expressions >>](expressions.md)