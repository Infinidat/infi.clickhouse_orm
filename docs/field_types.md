Field Types
===========

Currently the following field types are supported:

| Class              | DB Type    | Pythonic Type       | Comments
| ------------------ | ---------- | ------------------- | -----------------------------------------------------
| StringField        | String     | unicode             | Encoded as UTF-8 when written to ClickHouse
| FixedStringField   | String     | unicode             | Encoded as UTF-8 when written to ClickHouse
| DateField          | Date       | datetime.date       | Range 1970-01-01 to 2038-01-19
| DateTimeField      | DateTime   | datetime.datetime   | Minimal value is 1970-01-01 00:00:00; Always in UTC
| Int8Field          | Int8       | int                 | Range -128 to 127
| Int16Field         | Int16      | int                 | Range -32768 to 32767
| Int32Field         | Int32      | int                 | Range -2147483648 to 2147483647
| Int64Field         | Int64      | int/long            | Range -9223372036854775808 to 9223372036854775807
| UInt8Field         | UInt8      | int                 | Range 0 to 255
| UInt16Field        | UInt16     | int                 | Range 0 to 65535
| UInt32Field        | UInt32     | int                 | Range 0 to 4294967295
| UInt64Field        | UInt64     | int/long            | Range 0 to 18446744073709551615
| Float32Field       | Float32    | float               |
| Float64Field       | Float64    | float               |
| Enum8Field         | Enum8      | Enum                | See below
| Enum16Field        | Enum16     | Enum                | See below
| ArrayField         | Array      | list                | See below
| NullableField      | Nullable   | See below           | See below

DateTimeField and Time Zones
----------------------------

A `DateTimeField` can be assigned values from one of the following types:

-   datetime
-   date
-   integer - number of seconds since the Unix epoch
-   string in `YYYY-MM-DD HH:MM:SS` format

The assigned value always gets converted to a timezone-aware `datetime` in UTC. If the assigned value is a timezone-aware `datetime` in another timezone, it will be converted to UTC. Otherwise, the assigned value is assumed to already be in UTC.

DateTime values that are read from the database are also converted to UTC. ClickHouse formats them according to the timezone of the server, and the ORM makes the necessary conversions. This requires a ClickHouse
version which is new enough to support the `timezone()` function, otherwise it is assumed to be using UTC. In any case, we recommend settings the server timezone to UTC in order to prevent confusion.

Working with enum fields
------------------------

`Enum8Field` and `Enum16Field` provide support for working with ClickHouse enum columns. They accept strings or integers as values, and convert them to the matching Pythonic Enum member.

Python 3.4 and higher supports Enums natively. When using previous Python versions you need to install the enum34 library.

Example of a model with an enum field:

    Gender = Enum('Gender', 'male female unspecified')

    class Person(models.Model):

        first_name = fields.StringField()
        last_name = fields.StringField()
        birthday = fields.DateField()
        gender = fields.Enum32Field(Gender)

        engine = engines.MergeTree('birthday', ('first_name', 'last_name', 'birthday'))

    suzy = Person(first_name='Suzy', last_name='Jones', gender=Gender.female)

Working with array fields
-------------------------

You can create array fields containing any data type, for example:

    class SensorData(models.Model):

        date = fields.DateField()
        temperatures = fields.ArrayField(fields.Float32Field())
        humidity_levels = fields.ArrayField(fields.UInt8Field())

        engine = engines.MergeTree('date', ('date',))

    data = SensorData(date=date.today(), temperatures=[25.5, 31.2, 28.7], humidity_levels=[41, 39, 66])

Working with materialized and alias fields
------------------------------------------

ClickHouse provides an opportunity to create MATERIALIZED and ALIAS Fields.

See documentation [here](https://clickhouse.yandex/reference_en.html#Default%20values).

Both field types can't be inserted into the database directly, so they are ignored when using the `Database.insert()` method. ClickHouse does not return the field values if you use `"SELECT * FROM ..."` - you have to list these field names explicitly in the query.

Usage:

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

Working with nullable fields
----------------------------
From [some time](https://github.com/yandex/ClickHouse/pull/70) ClickHouse provides a NULL value support.
Also see some information [here](https://github.com/yandex/ClickHouse/blob/master/dbms/tests/queries/0_stateless/00395_nullable.sql).

Wrapping another field in a `NullableField` makes it possible to assign `None` to that field. For example:

    class EventData(models.Model):

        date = fields.DateField()
        comment = fields.NullableField(fields.StringField(), extra_null_values={''})
        score = fields.NullableField(fields.UInt8Field())
        serie = fields.NullableField(fields.ArrayField(fields.UInt8Field()))

        engine = engines.MergeTree('date', ('date',))


    score_event = EventData(date=date.today(), comment=None, score=5, serie=None)
    comment_event = EventData(date=date.today(), comment='Excellent!', score=None, serie=None)
    another_event = EventData(date=date.today(), comment='', score=None, serie=None)
    action_event = EventData(date=date.today(), comment='', score=None, serie=[1, 2, 3])

The `extra_null_values` parameter is an iterable of additional values that should be converted
to `None`.

NOTE: `ArrayField` of `NullableField` is not supported. Also `EnumField` cannot be nullable.

---

[<< Querysets](querysets.md) | [Table of Contents](toc.md) | [Table Engines >>](table_engines.md)