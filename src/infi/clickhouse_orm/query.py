from __future__ import unicode_literals
import six
import pytz
from copy import copy
from math import ceil
from .utils import comma_join


# TODO
# - and/or between Q objects
# - check that field names are valid
# - operators for arrays: length, has, empty

class Operator(object):
    """
    Base class for filtering operators.
    """

    def to_sql(self, model_cls, field_name, value):
        """
        Subclasses should implement this method. It returns an SQL string
        that applies this operator on the given field and value.
        """
        raise NotImplementedError   # pragma: no cover


class SimpleOperator(Operator):
    """
    A simple binary operator such as a=b, a<b, a>b etc.
    """

    def __init__(self, sql_operator):
        self._sql_operator = sql_operator

    def to_sql(self, model_cls, field_name, value):
        field = getattr(model_cls, field_name)
        value = field.to_db_string(field.to_python(value, pytz.utc))
        return ' '.join([field_name, self._sql_operator, value])


class InOperator(Operator):
    """
    An operator that implements IN.
    Accepts 3 different types of values:
    - a list or tuple of simple values
    - a string (used verbatim as the contents of the parenthesis)
    - a queryset (subquery)
    """

    def to_sql(self, model_cls, field_name, value):
        field = getattr(model_cls, field_name)
        if isinstance(value, QuerySet):
            value = value.as_sql()
        elif isinstance(value, six.string_types):
            pass
        else:
            value = comma_join([field.to_db_string(field.to_python(v, pytz.utc)) for v in value])
        return '%s IN (%s)' % (field_name, value)


class LikeOperator(Operator):
    """
    A LIKE operator that matches the field to a given pattern. Can be
    case sensitive or insensitive.
    """

    def __init__(self, pattern, case_sensitive=True):
        self._pattern = pattern
        self._case_sensitive = case_sensitive

    def to_sql(self, model_cls, field_name, value):
        field = getattr(model_cls, field_name)
        value = field.to_db_string(field.to_python(value, pytz.utc), quote=False)
        value = value.replace('\\', '\\\\').replace('%', '\\\\%').replace('_', '\\\\_')
        pattern = self._pattern.format(value)
        if self._case_sensitive:
            return '%s LIKE \'%s\'' % (field_name, pattern)
        else:
            return 'lowerUTF8(%s) LIKE lowerUTF8(\'%s\')' % (field_name, pattern)


class IExactOperator(Operator):
    """
    An operator for case insensitive string comparison.
    """

    def to_sql(self, model_cls, field_name, value):
        field = getattr(model_cls, field_name)
        value = field.to_db_string(field.to_python(value, pytz.utc))
        return 'lowerUTF8(%s) = lowerUTF8(%s)' % (field_name, value)


class NotOperator(Operator):
    """
    A wrapper around another operator, which negates it.
    """

    def __init__(self, base_operator):
        self._base_operator = base_operator

    def to_sql(self, model_cls, field_name, value):
        # Negate the base operator
        return 'NOT (%s)' % self._base_operator.to_sql(model_cls, field_name, value)


# Define the set of builtin operators

_operators = {}

def register_operator(name, sql):
    _operators[name] = sql

register_operator('eq',          SimpleOperator('='))
register_operator('ne',          SimpleOperator('!='))
register_operator('gt',          SimpleOperator('>'))
register_operator('gte',         SimpleOperator('>='))
register_operator('lt',          SimpleOperator('<'))
register_operator('lte',         SimpleOperator('<='))
register_operator('in',          InOperator())
register_operator('not_in',      NotOperator(InOperator()))
register_operator('contains',    LikeOperator('%{}%'))
register_operator('startswith',  LikeOperator('{}%'))
register_operator('endswith',    LikeOperator('%{}'))
register_operator('icontains',   LikeOperator('%{}%', False))
register_operator('istartswith', LikeOperator('{}%', False))
register_operator('iendswith',   LikeOperator('%{}', False))
register_operator('iexact',      IExactOperator())


class FOV(object):
    """
    An object for storing Field + Operator + Value.
    """

    def __init__(self, field_name, operator, value):
        self._field_name = field_name
        self._operator = _operators[operator]
        self._value = value

    def to_sql(self, model_cls):
        return self._operator.to_sql(model_cls, self._field_name, self._value)


class Q(object):

    def __init__(self, **kwargs):
        self._fovs = [self._build_fov(k, v) for k, v in six.iteritems(kwargs)]
        self._negate = False

    def _build_fov(self, key, value):
        if '__' in key:
            field_name, operator = key.rsplit('__', 1)
        else:
            field_name, operator = key, 'eq'
        return FOV(field_name, operator, value)

    def to_sql(self, model_cls):
        if not self._fovs:
            return '1'
        sql = ' AND '.join(fov.to_sql(model_cls) for fov in self._fovs)
        if self._negate:
            sql = 'NOT (%s)' % sql
        return sql

    def __invert__(self):
        q = copy(self)
        q._negate = True
        return q


@six.python_2_unicode_compatible
class QuerySet(object):
    """
    A queryset is an object that represents a database query using a specific `Model`.
    It is lazy, meaning that it does not hit the database until you iterate over its
    matching rows (model instances).
    """

    def __init__(self, model_cls, database):
        """
        Initializer. It is possible to create a queryset like this, but the standard
        way is to use `MyModel.objects_in(database)`.
        """
        self._model_cls = model_cls
        self._database = database
        self._order_by = []
        self._q = []
        self._fields = []
        self._limits = None

    def __iter__(self):
        """
        Iterates over the model instances matching this queryset
        """
        return self._database.select(self.as_sql(), self._model_cls)

    def __bool__(self):
        """
        Returns true if this queryset matches any rows.
        """
        return bool(self.count())

    def __nonzero__(self):      # Python 2 compatibility
        return type(self).__bool__(self)

    def __str__(self):
        return self.as_sql()

    def __getitem__(self, s):
        if isinstance(s, six.integer_types):
            # Single index
            assert s >= 0, 'negative indexes are not supported'
            qs = copy(self)
            qs._limits = (s, 1)
            return six.next(iter(qs))
        else:
            # Slice
            assert s.step in (None, 1), 'step is not supported in slices'
            start = s.start or 0
            stop = s.stop or 2**63 - 1
            assert start >= 0 and stop >= 0, 'negative indexes are not supported'
            assert start <= stop, 'start of slice cannot be smaller than its end'
            qs = copy(self)
            qs._limits = (start, stop - start)
            return qs

    def as_sql(self):
        """
        Returns the whole query as a SQL string.
        """
        fields = '*'
        if self._fields:
            fields = comma_join('`%s`' % field for field in self._fields)
        ordering = '\nORDER BY ' + self.order_by_as_sql() if self._order_by else ''
        limit = '\nLIMIT %d, %d' % self._limits if self._limits else ''
        params = (fields, self._model_cls.table_name(),
                  self.conditions_as_sql(), ordering, limit)
        return u'SELECT %s\nFROM `%s`\nWHERE %s%s%s' % params

    def order_by_as_sql(self):
        """
        Returns the contents of the query's `ORDER BY` clause as a string.
        """
        return comma_join([
            '%s DESC' % field[1:] if field[0] == '-' else field
            for field in self._order_by
        ])

    def conditions_as_sql(self):
        """
        Returns the contents of the query's `WHERE` clause as a string.
        """
        if self._q:
            return u' AND '.join([q.to_sql(self._model_cls) for q in self._q])
        else:
            return u'1'

    def count(self):
        """
        Returns the number of matching model instances.
        """
        return self._database.count(self._model_cls, self.conditions_as_sql())

    def order_by(self, *field_names):
        """
        Returns a copy of this queryset with the ordering changed.
        """
        qs = copy(self)
        qs._order_by = field_names
        return qs

    def only(self, *field_names):
        """
        Returns a copy of this queryset limited to the specified field names.
        Useful when there are large fields that are not needed,
        or for creating a subquery to use with an IN operator.
        """
        qs = copy(self)
        qs._fields = field_names
        return qs

    def filter(self, **kwargs):
        """
        Returns a copy of this queryset that includes only rows matching the conditions.
        """
        qs = copy(self)
        qs._q = list(self._q) + [Q(**kwargs)]
        return qs

    def exclude(self, **kwargs):
        """
        Returns a copy of this queryset that excludes all rows matching the conditions.
        """
        qs = copy(self)
        qs._q = list(self._q) + [~Q(**kwargs)]
        return qs

    def paginate(self, page_num=1, page_size=100):
        '''
        Returns a single page of model instances that match the queryset.
        Note that `order_by` should be used first, to ensure a correct
        partitioning of records into pages.

        - `page_num`: the page number (1-based), or -1 to get the last page.
        - `page_size`: number of records to return per page.

        The result is a namedtuple containing `objects` (list), `number_of_objects`,
        `pages_total`, `number` (of the current page), and `page_size`.
        '''
        from .database import Page
        count = self.count()
        pages_total = int(ceil(count / float(page_size)))
        if page_num == -1:
            page_num = pages_total
        elif page_num < 1:
            raise ValueError('Invalid page number: %d' % page_num)
        offset = (page_num - 1) * page_size
        return Page(
            objects=list(self[offset : offset + page_size]),
            number_of_objects=count,
            pages_total=pages_total,
            number=page_num,
            page_size=page_size
        )

    def aggregate(self, *args, **kwargs):
        '''
        Returns an `AggregateQuerySet` over this query, with `args` serving as
        grouping fields and `kwargs` serving as calculated fields. At least one
        calculated field is required. For example:
        ```
            Event.objects_in(database).filter(date__gt='2017-08-01').aggregate('event_type', count='count()')
        ```
        is equivalent to:
        ```
            SELECT event_type, count() AS count FROM event
            WHERE data > '2017-08-01'
            GROUP BY event_type
        ```
        '''
        return AggregateQuerySet(self, args, kwargs)


class AggregateQuerySet(QuerySet):
    """
    A queryset used for aggregation.
    """

    def __init__(self, base_qs, grouping_fields, calculated_fields):
        """
        Initializer. Normally you should not call this but rather use `QuerySet.aggregate()`.

        The grouping fields should be a list/tuple of field names from the model. For example:
        ```
            ('event_type', 'event_subtype')
        ```
        The calculated fields should be a mapping from name to a ClickHouse aggregation function. For example:
        ```
            {'weekday': 'toDayOfWeek(event_date)', 'number_of_events': 'count()'}
        ```
        At least one calculated field is required.
        """
        super(AggregateQuerySet, self).__init__(base_qs._model_cls, base_qs._database)
        assert calculated_fields, 'No calculated fields specified for aggregation'
        self._fields = grouping_fields
        self._grouping_fields = grouping_fields
        self._calculated_fields = calculated_fields
        self._order_by = list(base_qs._order_by)
        self._q = list(base_qs._q)
        self._limits = base_qs._limits

    def group_by(self, *args):
        """
        This method lets you specify the grouping fields explicitly. The `args` must
        be names of grouping fields or calculated fields that this queryset was
        created with.
        """
        for name in args:
            assert name in self._fields or name in self._calculated_fields, \
                   'Cannot group by `%s` since it is not included in the query' % name
        qs = copy(self)
        qs._grouping_fields = args
        return qs

    def only(self, *field_names):
        """
        This method is not supported on `AggregateQuerySet`.
        """
        raise NotImplementedError('Cannot use "only" with AggregateQuerySet')

    def aggregate(self, *args, **kwargs):
        """
        This method is not supported on `AggregateQuerySet`.
        """
        raise NotImplementedError('Cannot re-aggregate an AggregateQuerySet')

    def as_sql(self):
        """
        Returns the whole query as a SQL string.
        """
        grouping = comma_join('`%s`' % field for field in self._grouping_fields)
        fields = comma_join(list(self._fields) + ['%s AS %s' % (v, k) for k, v in self._calculated_fields.items()])
        params = dict(
            grouping=grouping or "''",
            fields=fields,
            table=self._model_cls.table_name(),
            conds=self.conditions_as_sql()
        )
        sql = u'SELECT %(fields)s\nFROM `%(table)s`\nWHERE %(conds)s\nGROUP BY %(grouping)s' % params
        if self._order_by:
            sql += '\nORDER BY ' + self.order_by_as_sql()
        if self._limits:
            sql += '\nLIMIT %d, %d' % self._limits
        return sql

    def __iter__(self):
        return self._database.select(self.as_sql()) # using an ad-hoc model

    def count(self):
        """
        Returns the number of rows after aggregation.
        """
        sql = u'SELECT count() FROM (%s)' % self.as_sql()
        raw = self._database.raw(sql)
        return int(raw) if raw else 0
