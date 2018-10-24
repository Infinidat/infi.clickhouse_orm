Field Types
===========

See: [ClickHouse Documentation](https://clickhouse.yandex/docs/en/data_types/)

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
| DecimalField       | Decimal    | Decimal             | Pythonic values are rounded to fit the scale of the database field
| Decimal32Field     | Decimal32  | Decimal             | Ditto
| Decimal64Field     | Decimal64  | Decimal             | Ditto
| Decimal128Field    | Decimal128 | Decimal             | Ditto
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
-   string in `YYYY-MM-DD HH:MM:SS` format or [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601)-compatible format

The assigned value always gets converted to a timezone-aware `datetime` in UTC. If the assigned value is a timezone-aware `datetime` in another timezone, it will be converted to UTC. Otherwise, the assigned value is assumed to already be in UTC.

DateTime values that are read from the database are also converted to UTC. ClickHouse formats them according to the timezone of the server, and the ORM makes the necessary conversions. This requires a ClickHouse
version which is new enough to support the `timezone()` function, otherwise it is assumed to be using UTC. In any case, we recommend settings the server timezone to UTC in order to prevent confusion.

Working with enum fields
------------------------

`Enum8Field` and `Enum16Field` provide support for working with ClickHouse enum columns. They accept strings or integers as values, and convert them to the matching Pythonic Enum member.

Python 3.4 and higher supports Enums natively. When using previous Python versions you need to install the enum34 library.

Example of a model with an enum field:

```python
Gender = Enum('Gender', 'male female unspecified')

class Person(models.Model):

    first_name = fields.StringField()
    last_name = fields.StringField()
    birthday = fields.DateField()
    gender = fields.Enum32Field(Gender)

    engine = engines.MergeTree('birthday', ('first_name', 'last_name', 'birthday'))

suzy = Person(first_name='Suzy', last_name='Jones', gender=Gender.female)
```

Working with array fields
-------------------------

You can create array fields containing any data type, for example:

```python
class SensorData(models.Model):

    date = fields.DateField()
    temperatures = fields.ArrayField(fields.Float32Field())
    humidity_levels = fields.ArrayField(fields.UInt8Field())

    engine = engines.MergeTree('date', ('date',))

data = SensorData(date=date.today(), temperatures=[25.5, 31.2, 28.7], humidity_levels=[41, 39, 66])
```

Note that multidimensional arrays are not supported yet by the ORM.

Working with materialized and alias fields
------------------------------------------

ClickHouse provides an opportunity to create MATERIALIZED and ALIAS Fields.

See documentation [here](https://clickhouse.yandex/docs/en/query_language/queries/#default-values).

Both field types can't be inserted into the database directly, so they are ignored when using the `Database.insert()` method. ClickHouse does not return the field values if you use `"SELECT * FROM ..."` - you have to list these field names explicitly in the query.

Usage:

```python
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
```

Working with nullable fields
----------------------------
From [some time](https://github.com/yandex/ClickHouse/pull/70) ClickHouse provides a NULL value support.
Also see some information [here](https://github.com/yandex/ClickHouse/blob/master/dbms/tests/queries/0_stateless/00395_nullable.sql).

Wrapping another field in a `NullableField` makes it possible to assign `None` to that field. For example:

```python
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
```

The `extra_null_values` parameter is an iterable of additional values that should be converted
to `None`.

NOTE: `ArrayField` of `NullableField` is not supported. Also `EnumField` cannot be nullable.

Creating custom field types
---------------------------
Sometimes it is convenient to use data types that are supported in Python, but have no corresponding column type in ClickHouse. In these cases it is possible to define a custom field class that knows how to convert the Pythonic object to a suitable representation in the database, and vice versa.

For example, we can create a BooleanField which will hold `True` and `False` values, but write them to the database as 0 and 1 (in a `UInt8` column). For this purpose we'll subclass the `Field` class, and implement two methods:

- `to_python` which converts any supported value to a `bool`. The method should know how to handle strings (which typically come from the database), booleans, and possibly other valid options. In case the value is not supported, it should raise a `ValueError`.
- `to_db_string` which converts a `bool` into a string for writing to the database.

Here's the full implementation:

```python
from infi.clickhouse_orm.fields import Field

class BooleanField(Field):

    # The ClickHouse column type to use
    db_type = 'UInt8'

    # The default value
    class_default = False

    def to_python(self, value, timezone_in_use):
        # Convert valid values to bool
        if value in (1, '1', True):
            return True
        elif value in (0, '0', False):
            return False
        else:
            raise ValueError('Invalid value for BooleanField: %r' % value)

    def to_db_string(self, value, quote=True):
        # The value was already converted by to_python, so it's a bool
        return '1' if value else '0'
```

Here's another example - a field for storing UUIDs in the database as 16-byte strings. We'll use Python's built-in `UUID` class to handle the conversion from strings, ints and tuples into UUID instances. So in our Python code we'll have the convenience of working with UUID objects, but they will be stored in the database as efficiently as possible:

```python
from infi.clickhouse_orm.fields import Field
from infi.clickhouse_orm.utils import escape
from uuid import UUID
import six

class UUIDField(Field):

    # The ClickHouse column type to use
    db_type = 'FixedString(16)'

    # The default value if empty
    class_default = UUID(int=0)

    def to_python(self, value, timezone_in_use):
        # Convert valid values to UUID instance
        if isinstance(value, UUID):
            return value
        elif isinstance(value, six.string_types):
            return UUID(bytes=value.encode('latin1')) if len(value) == 16 else UUID(value)
        elif isinstance(value, six.integer_types):
            return UUID(int=value)
        elif isinstance(value, tuple):
            return UUID(fields=value)
        else:
            raise ValueError('Invalid value for UUIDField: %r' % value)

    def to_db_string(self, value, quote=True):
        # The value was already converted by to_python, so it's a UUID instance
        val = value.bytes
        if six.PY3:
            val = str(val, 'latin1')
        return escape(val, quote)

```

Note that the latin-1 encoding is used as an identity encoding for converting between raw bytes and strings. This is required in Python 3, where `str` and `bytes` are different types.

---

[<< Querysets](querysets.md) | [Table of Contents](toc.md) | [Table Engines >>](table_engines.md)