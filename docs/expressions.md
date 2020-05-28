
Expressions
===========

One of the ORM's core concepts is _expressions_, which are composed using functions, operators and model fields. Expressions are used in multiple places in the ORM:

- When defining [field options](field_options.md) - `default`, `alias` and `materialized`.
- In [table engine](table_engines.md) parameters for engines in the `MergeTree` family.
- In [queryset](querysets.md) methods such as `filter`, `exclude`, `order_by`, `aggregate` and `limit_by`.

Using Expressions
-----------------

Expressions usually include ClickHouse database functions, which are made available by the `F` class. Here's a simple function:
```python
from infi.clickhouse_orm import F
expr = F.today()
```

Functions that accept arguments can be composed, just like when using SQL:
```python
expr = F.toDayOfWeek(F.today())
```

You can see the SQL expression that is represented by an ORM expression by calling its `to_sql` method or converting it to a string:
```python
>>> print(expr)
toDayOfWeek(today())
```

### Operators

ORM expressions support Python's standard arithmetic operators, so you can compose expressions using `+`, `-`, `*`, `/`, `//` and `%`. For example:
```python
# A random integer between 1 and 10
F.rand() % 10 + 1
```

There is also support for comparison operators (`<`, `<=`, `==`, `>=`, `>`, `!=`) and logical operators (`&`, `|`, `~`, `^`) which are often used for filtering querysets:
```python
# Is it Friday the 13th?
(F.toDayOfWeek(F.today()) == 6) & (F.toDayOfMonth(F.today()) == 13)
```

Note that Python's bitwise operators (`&`, `|`, `~`, `^`) have higher precedence than comparison operators, so always use parentheses when combining these two types of operators in an expression. Otherwise the resulting SQL might be different than what you would expect.

### Referring to model fields

To refer to a model field inside an expression, use `<class>.<field>` syntax, for example:
```python
# Convert the temperature from Celsius to Fahrenheit
Sensor.temperature * 1.8 + 32
```

Inside model class definitions omit the class name:
```python
class Person(Model):
    height_cm = Float32Field()
    height_inch = Float32Field(alias=height_cm/2.54)
    ...
```

### Parametric functions

Some of ClickHouse's aggregate functions can accept one or more parameters - constants for initialization that affect the way the function works. The syntax is two pairs of brackets instead of one. The first is for parameters, and the second is for arguments. For example:
```python
# Most common last names
F.topK(5)(Person.last_name)
# Find 90th, 95th and 99th percentile of heights
F.quantiles(0.9, 0.95, 0.99)(Person.height)
```

### Creating new "functions"

Since expressions are just Python objects until they get converted to SQL, it is possible to invent new "functions" by combining existing ones into useful building blocks. For example, we can create a reusable expression that takes a string and trims whitespace, converts it to uppercase, and changes blanks to underscores:
```python
def normalize_string(s):
    return F.replaceAll(F.upper(F.trimBoth(s)), ' ', '_')
```

Then we can use this expression anywhere we need it:
```python
class Event(Model):
    code = StringField()
    normalized_code = StringField(materialized=normalize_string(code))
```

### Which functions are available?

ClickHouse has many hundreds of functions, and new ones often get added. Many, but not all of them, are already covered by the ORM. If you encounter a function that the database supports but is not available in the `F` class, please report this via a GitHub issue. You can still use the function by providing its name:
```python
expr = F("someFunctionName", arg1, arg2, ...)
```

Note that higher-order database functions (those that use lambda expressions) are not supported.

---

[<< Models and Databases](models_and_databases.md) | [Table of Contents](toc.md) | [Importing ORM Classes >>](importing_orm_classes.md)
