Querysets
=========

A queryset is an object that represents a database query using a specific Model. It is lazy, meaning that it does not hit the database until you iterate over its matching rows (model instances). To create a base queryset for a model class, use:

    qs = Person.objects_in(database)

This queryset matches all Person instances in the database. You can get these instances using iteration:

    for person in qs:
        print person.first_name, person.last_name

Filtering
---------

The `filter` and `exclude` methods are used for filtering the matching instances. Calling these methods returns a new queryset instance, with the added conditions. For example:

    >>> qs = Person.objects_in(database)
    >>> qs = qs.filter(first_name__startswith='V').exclude(birthday__lt='2000-01-01')
    >>> qs.conditions_as_sql()
    u"first_name LIKE 'V%' AND NOT (birthday < '2000-01-01')"

It is possible to specify several fields to filter or exclude by:

    >>> qs = Person.objects_in(database).filter(last_name='Smith', height__gt=1.75)
    >>> qs.conditions_as_sql()
    u"last_name = 'Smith' AND height > 1.75"

There are different operators that can be used, by passing `<fieldname>__<operator>=<value>` (two underscores separate the field name from the operator). In case no operator is given, `eq` is used by default. Below are all the supported operators.

| Operator       | Equivalent SQL                               | Comments                           |
| --------       | -------------------------------------------- | ---------------------------------- |
| `eq`           | `field = value`                              |                                    |
| `ne`           | `field != value`                             |                                    |
| `gt`           | `field > value`                              |                                    |
| `gte`          | `field >= value`                             |                                    |
| `lt`           | `field < value`                              |                                    |
| `lte`          | `field <= value`                             |                                    |
| `in`           | `field IN (values)`                          | See below                          |
| `not_in`       | `field NOT IN (values)`                      | See below                          |
| `contains`     | `field LIKE '%value%'`                       | For string fields only             |
| `startswith`   | `field LIKE 'value%'`                        | For string fields only             |
| `endswith`     | `field LIKE '%value'`                        | For string fields only             |
| `icontains`    | `lowerUTF8(field) LIKE lowerUTF8('%value%')` | For string fields only             |
| `istartswith`  | `lowerUTF8(field) LIKE lowerUTF8('value%')`  | For string fields only             |
| `iendswith`    | `lowerUTF8(field) LIKE lowerUTF8('%value')`  | For string fields only             |
| `iexact`       | `lowerUTF8(field) = lowerUTF8(value)`        | For string fields only             |

### Using the `in` Operator

The `in` and `not_in` operators expect one of three types of values:
* A list or tuple of simple values
* A string, which is used verbatim as the contents of the parentheses
* Another queryset (subquery)

For example if we want to select only people with Irish last names:

    # A list of simple values
    qs = Person.objects_in(database).filter(last_name__in=["Murphy", "O'Sullivan"])

    # A string
    subquery = "SELECT name from $db.irishlastname"
    qs = Person.objects_in(database).filter(last_name__in=subquery)

    # A queryset
    subquery = IrishLastName.objects_in(database).only("name")
    qs = Person.objects_in(database).filter(last_name__in=subquery)

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


Slicing
-------

It is possible to get a specific item from the queryset by index.

      qs = Person.objects_in(database).order_by('last_name', 'first_name')
      first = qs[0]

It is also possible to get a range a instances using a slice. This returns a queryset,
that you can either iterate over or convert to a list.

      qs = Person.objects_in(database).order_by('last_name', 'first_name')
      first_ten_people = list(qs[:10])
      next_ten_people  = list(qs[10:20])

You should use `order_by` to ensure a consistent ordering of the results.

Trying to use negative indexes or a slice with a step (e.g. [0:100:2]) is not supported and will raise an `AssertionError`.

---

[<< Models and Databases](models_and_databases.md) | [Table of Contents](toc.md) | [Field Types >>](field_types.md)