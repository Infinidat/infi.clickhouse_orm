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

For filters with compound conditions you can use `Q` objects inside `filter` with overloaded operators `&` (AND), `|` (OR) and `~` (NOT):

    >>> qs = Person.objects_in(database).filter((Q(first_name='Ciaran', last_name='Carver') | Q(height_lte=1.8)) & ~Q(first_name='David'))
    >>> qs.conditions_as_sql()
    u"((first_name = 'Ciaran' AND last_name = 'Carver') OR height <= 1.8) AND (NOT (first_name = 'David'))"

There are different operators that can be used, by passing `<fieldname>__<operator>=<value>` (two underscores separate the field name from the operator). In case no operator is given, `eq` is used by default. Below are all the supported operators.

| Operator       | Equivalent SQL                               | Comments                           |
| --------       | -------------------------------------------- | ---------------------------------- |
| `eq`           | `field = value`                              |                                    |
| `ne`           | `field != value`                             |                                    |
| `gt`           | `field > value`                              |                                    |
| `gte`          | `field >= value`                             |                                    |
| `lt`           | `field < value`                              |                                    |
| `lte`          | `field <= value`                             |                                    |
| `between`      | `field BETWEEN value1 AND value2`            |                                    |
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

Distinct
--------

Adds a DISTINCT clause to the query, meaning that any duplicate rows in the results will be omitted.

    >>> Person.objects_in(database).only('first_name').count()
    100
    >>> Person.objects_in(database).only('first_name').distinct().count()
    94

Slicing
-------

It is possible to get a specific item from the queryset by index:

      qs = Person.objects_in(database).order_by('last_name', 'first_name')
      first = qs[0]

It is also possible to get a range a instances using a slice. This returns a queryset,
that you can either iterate over or convert to a list.

      qs = Person.objects_in(database).order_by('last_name', 'first_name')
      first_ten_people = list(qs[:10])
      next_ten_people  = list(qs[10:20])

You should use `order_by` to ensure a consistent ordering of the results.

Trying to use negative indexes or a slice with a step (e.g. [0:100:2]) is not supported and will raise an `AssertionError`.

Pagination
----------

Similar to `Database.paginate`, you can go over the queryset results one page at a time:

    >>> qs = Person.objects_in(database).order_by('last_name', 'first_name')
    >>> page = qs.paginate(page_num=1, page_size=10)
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
-   `number` - the page number, starting from 1; the special value -1 may be used to retrieve the last page
-   `page_size` - the number of objects per page

Note that you should use `QuerySet.order_by` so that the ordering is unique, otherwise there might be inconsistencies in the pagination (such as an instance that appears on two different pages).

Aggregation
-----------

It is possible to use aggregation functions over querysets using the `aggregate` method. The simplest form of aggregation works over all rows in the queryset:

    >>> qs = Person.objects_in(database).aggregate(average_height='avg(height)')
    >>> print qs.count()
    1
    >>> for row in qs: print row.average_height
    1.71

The returned row or rows are no longer instances of the base model (`Person` in this example), but rather instances of an ad-hoc model that includes only the fields specified in the call to `aggregate`.

You can pass names of fields from the model that will be included in the query. By default, they will be also used in the GROUP BY clause. For example to count the number of people per last name you could do this:

    qs = Person.objects_in(database).aggregate('last_name', num='count()')

The underlying SQL query would be something like this:

    SELECT last_name, count() AS num FROM person GROUP BY last_name

If you would like to control the GROUP BY explicitly, use the `group_by` method. This is useful when you need to group by a calculated field, instead of a field that exists in the model. For example, to count the number of people born on each weekday:

    qs = Person.objects_in(database).aggregate(weekday='toDayOfWeek(birthday)', num='count()').group_by('weekday')

This queryset is translated to:

    SELECT toDayOfWeek(birthday) AS weekday, count() AS num FROM person GROUP BY weekday

After calling `aggregate` you can still use most of the regular queryset methods, such as `count`, `order_by` and `paginate`. It is not possible, however, to call `only` or `aggregate`. It is also not possible to filter the queryset on calculated fields, only on fields that exist in the model.

---

[<< Models and Databases](models_and_databases.md) | [Table of Contents](toc.md) | [Field Types >>](field_types.md)