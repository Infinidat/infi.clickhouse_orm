import six
import pytz
from copy import copy


# TODO
# - and/or between Q objects
# - check that field names are valid
# - qs slicing
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
        raise NotImplementedError


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
            value = ', '.join([field.to_db_string(field.to_python(v, pytz.utc)) for v in value])
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

    def __unicode__(self):
        return self.as_sql()
        
    def as_sql(self):
        """
        Returns the whole query as a SQL string.
        """
        fields = '*'
        if self._fields:
            fields = ', '.join('`%s`' % field for field in self._fields)
        ordering = '\nORDER BY ' + self.order_by_as_sql() if self._order_by else ''
        params = (fields, self._database.db_name, self._model_cls.table_name(), self.conditions_as_sql(), ordering)
        return u'SELECT %s\nFROM `%s`.`%s`\nWHERE %s%s' % params

    def order_by_as_sql(self):
        """
        Returns the contents of the query's `ORDER BY` clause as a string.
        """
        return u', '.join([
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
        Returns a new `QuerySet` instance with the ordering changed.
        """
        qs = copy(self)
        qs._order_by = field_names
        return qs

    def only(self, *field_names):
        """
        Returns a new `QuerySet` instance limited to the specified field names.
        Useful when there are large fields that are not needed,
        or for creating a subquery to use with an IN operator.
        """
        qs = copy(self)
        qs._fields = field_names
        return qs

    def filter(self, **kwargs):
        """
        Returns a new `QuerySet` instance that includes only rows matching the conditions.
        """
        qs = copy(self)
        qs._q = list(self._q) + [Q(**kwargs)]
        return qs

    def exclude(self, **kwargs):
        """
        Returns a new `QuerySet` instance that excludes all rows matching the conditions.
        """
        qs = copy(self)
        qs._q = list(self._q) + [~Q(**kwargs)]
        return qs
