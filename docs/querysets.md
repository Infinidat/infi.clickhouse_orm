
Querysets
=========

A queryset is an object that represents a database query using a specific Model. It is lazy, meaning that it does not hit the database until you iterate over its matching rows (model instances). To create a base queryset for a model class, use:

    qs = Person.objects_in(database)

This queryset matches all Person instances in the database. You can get these instances using iteration:

    for person in qs:
        print(person.first_name, person.last_name)

Filtering
---------

The `filter` and `exclude` methods are used for filtering the matching instances. Calling these methods returns a new queryset instance, with the added conditions. For example:

    >>> qs = Person.objects_in(database)
    >>> qs = qs.filter(F.like(Person.first_name, 'V%')).exclude(Person.birthday < '2000-01-01')
    >>> qs.conditions_as_sql()
    "first_name LIKE 'V%' AND NOT (birthday < '2000-01-01')"

It is possible to specify several expressions to filter or exclude by, and they will be ANDed together:

    >>> qs = Person.objects_in(database).filter(Person.last_name == 'Smith', Person.height > 1.75)
    >>> qs.conditions_as_sql()
    "last_name = 'Smith' AND height > 1.75"

For compound conditions you can use the overloaded operators `&` (AND), `|` (OR) and `~` (NOT):

    >>> qs = Person.objects_in(database)
    >>> qs = qs.filter(((Person.first_name == 'Ciaran') & (Person.last_name == 'Carver')) | (Person.height <= 1.8) & ~(Person.first_name = 'David'))
    >>> qs.conditions_as_sql()
    "((first_name = 'Ciaran' AND last_name = 'Carver') OR height <= 1.8) AND (NOT (first_name = 'David'))"

Note that Python's bitwise operators (`&`, `|`, `~`, `^`) have higher precedence than comparison operators, so always use parentheses when combining these two types of operators in an expression. Otherwise the resulting SQL might be different than what you would expect.

### Using `IN` and `NOT IN`

Filtering queries using ClickHouse's `IN` and `NOT IN` operators requires using the `isIn` and `isNotIn` functions (trying to use Python's `in` keyword will not work!).
For example:
```python
# Is it Monday, Tuesday or Wednesday?
F.isIn(F.toDayOfWeek(F.now()), [1, 2, 3])
# This will not work:
F.toDayOfWeek(F.now()) in [1, 2, 3]
```

In case of model fields, there is a simplified syntax:
```python
# Filtering using F.isIn:
qs.filter(F.isIn(Person.first_name, ['Robert', 'Rob', 'Robbie']))
# Simpler syntax using isIn directly on the field:
qs.filter(Person.first_name.isIn(['Robert', 'Rob', 'Robbie']))
```

The `isIn` and `isNotIn` functions expect either a list/tuple of values, or another queryset (a subquery). For example if we want to select only people with Irish last names:
```python
# Last name is in a list of values
qs = Person.objects_in(database).filter(Person.last_name.isIn(["Murphy", "O'Sullivan"]))
# Last name is in a subquery
subquery = IrishLastName.objects_in(database).only("name")
qs = Person.objects_in(database).filter(Person.last_name.isIn(subquery))
```

### Specifying PREWHERE conditions

By default conditions from `filter` and `exclude` methods are add to `WHERE` clause.
For better aggregation performance you can add them to `PREWHERE` section by adding a `prewhere=True` parameter:

    >>> qs = Person.objects_in(database)
    >>> qs = qs.filter(F.like(Person.first_name, 'V%'), prewhere=True)
    >>> qs.conditions_as_sql(prewhere=True)
    "first_name LIKE 'V%'"

### Old-style filter conditions

Prior to version 2 of the ORM, filtering conditions were limited to a predefined set of operators, and complex expressions were not supported. This old syntax is still available, so you can use it alongside or even intermixed with new-style functions and expressions.

The old syntax uses keyword arguments to the `filter` and `exclude` methods, that are built as `<fieldname>__<operator>=<value>` (two underscores separate the field name from the operator). In case no operator is given, `eq` is used by default. For example:
```python
qs = Position.objects.in(database)
# New style
qs = qs.filter(Position.x > 100, Position.y < 20, Position.terrain == 'water')
# Old style
qs = qs.filter(x__gt=100, y__lt=20, terrain='water')
```
Below are all the supported operators.

| Operator       | Equivalent SQL                               | Comments                           |
| --------       | -------------------------------------------- | ---------------------------------- |
| `eq`           | `field = value`                              |                                    |
| `ne`           | `field != value`                             |                                    |
| `gt`           | `field > value`                              |                                    |
| `gte`          | `field >= value`                             |                                    |
| `lt`           | `field < value`                              |                                    |
| `lte`          | `field <= value`                             |                                    |
| `between`      | `field BETWEEN value1 AND value2`            |                                    |
| `in`           | `field IN (values)`                          |                                    |
| `not_in`       | `field NOT IN (values)`                      |                                    |
| `contains`     | `field LIKE '%value%'`                       | For string fields only             |
| `startswith`   | `field LIKE 'value%'`                        | For string fields only             |
| `endswith`     | `field LIKE '%value'`                        | For string fields only             |
| `icontains`    | `lowerUTF8(field) LIKE lowerUTF8('%value%')` | For string fields only             |
| `istartswith`  | `lowerUTF8(field) LIKE lowerUTF8('value%')`  | For string fields only             |
| `iendswith`    | `lowerUTF8(field) LIKE lowerUTF8('%value')`  | For string fields only             |
| `iexact`       | `lowerUTF8(field) = lowerUTF8(value)`        | For string fields only             |

Counting and Checking Existence
-------------------------------

Use the `count` method to get the number of matches:

    Person.objects_in(database).count()

To check if there are any matches at all, you can use any of the following equivalent options:

    if qs.count(): ...
    if bool(qs): ...
    if qs: ...

Ordering
--------

The sorting order of the results can be controlled using the `order_by` method:

    qs = Person.objects_in(database).order_by('last_name', 'first_name')

The default order is ascending. To use descending order, add a minus sign before the field name:

    qs = Person.objects_in(database).order_by('-height')

If you do not use `order_by`, the rows are returned in arbitrary order.

Omitting Fields
---------------

When some of the model fields aren't needed, it is more efficient to omit them from the query. This is especially true when there are large fields that may slow the query down. Use the `only` method to specify which fields to retrieve:

    qs = Person.objects_in(database).only('first_name', 'birthday')

Distinct
--------

Adds a DISTINCT clause to the query, meaning that any duplicate rows in the results will be omitted.

    >>> Person.objects_in(database).only('first_name').count()
    100
    >>> Person.objects_in(database).only('first_name').distinct().count()
    94

Final
-----

This method can be used only with `CollapsingMergeTree` engine.
Adds a FINAL modifier to the query, meaning that the selected data is fully "collapsed" by the engine's sign field.

    >>> Person.objects_in(database).count()
    100
    >>> Person.objects_in(database).final().count()
    94

Slicing
-------

It is possible to get a specific item from the queryset by index:

      qs = Person.objects_in(database).order_by('last_name', 'first_name')
      first = qs[0]

It is also possible to get a range a instances using a slice. This returns a queryset, that you can either iterate over or convert to a list.

      qs = Person.objects_in(database).order_by('last_name', 'first_name')
      first_ten_people = list(qs[:10])
      next_ten_people  = list(qs[10:20])

You should use `order_by` to ensure a consistent ordering of the results.

Trying to use negative indexes or a slice with a step (e.g. [0 : 100 : 2]) is not supported and will raise an `AssertionError`.

Pagination
----------

Similar to `Database.paginate`, you can go over the queryset results one page at a time:

    >>> qs = Person.objects_in(database).order_by('last_name', 'first_name')
    >>> page = qs.paginate(page_num=1, page_size=10)
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

Note that you should use `QuerySet.order_by` so that the ordering is unique, otherwise there might be inconsistencies in the pagination (such as an instance that appears on two different pages).

Mutations
---------

To delete all records that match a queryset's conditions use the `delete` method:

    Person.objects_in(database).filter(first_name='Max').delete()

To update records that match a queryset's conditions call the `update` method and provide the field names to update and the expressions to use (as keyword arguments):

    Person.objects_in(database).filter(first_name='Max').update(first_name='Maximilian')

Note a few caveats:

- ClickHouse cannot update columns that are used in the calculation of the primary or the partition key.
- Mutations happen in the background, so they are not immediate.
- Only tables in the `MergeTree` family support mutations.

Aggregation
-----------

It is possible to use aggregation functions over querysets using the `aggregate` method. The simplest form of aggregation works over all rows in the queryset:

    >>> qs = Person.objects_in(database).aggregate(average_height=F.avg(Person.height))
    >>> print(qs.count())
    1
    >>> for row in qs: print(row.average_height)
    1.71

The returned row or rows are no longer instances of the base model (`Person` in this example), but rather instances of an ad-hoc model that includes only the fields specified in the call to `aggregate`.

You can pass fields from the model that will be included in the query. By default, they will be also used in the GROUP BY clause. For example to count the number of people per last name you could do this:

    qs = Person.objects_in(database).aggregate(Person.last_name, num=F.count())

The underlying SQL query would be something like this:

    SELECT last_name, count() AS num
    FROM person
    GROUP BY last_name

If you would like to control the GROUP BY explicitly, use the `group_by` method. This is useful when you need to group by a calculated field, instead of a field that exists in the model. For example, to count the number of people born on each weekday:

    qs = Person.objects_in(database).aggregate(weekday=F.toDayOfWeek(Person.birthday), num=F.count()).group_by('weekday')

This queryset is translated to:

    SELECT toDayOfWeek(birthday) AS weekday, count() AS num
    FROM person
    GROUP BY weekday

After calling `aggregate` you can still use most of the regular queryset methods, such as `count`, `order_by` and `paginate`. It is not possible, however, to call `only` or `aggregate`. It is also not possible to filter the aggregated queryset on calculated fields, only on fields that exist in the model.

### Adding totals

If you limit aggregation results, it might be useful to get total aggregation values for all rows.
To achieve this, you can use `with_totals` method. It will return extra row (last) with
values aggregated for all rows suitable for filters.

    qs = Person.objects_in(database).aggregate(Person.first_name, num=F.count()).with_totals().order_by('-count')[:3]
    >>> print(qs.count())
    4
    >>> for row in qs:
    >>>     print("'{}': {}".format(row.first_name, row.count))
    'Cassandra': 2
    'Alexandra': 2
    '': 100

---

[<< Importing ORM Classes](importing_orm_classes.md) | [Table of Contents](toc.md) | [Field Options >>](field_options.md)
