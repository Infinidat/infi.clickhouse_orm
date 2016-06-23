from fields import *
from utils import escape, parse_tsv
from engines import *


class ModelBase(type):
    '''
    A metaclass for ORM models. It adds the _fields list to model classes.
    '''

    def __new__(cls, name, bases, attrs):
        new_cls = super(ModelBase, cls).__new__(cls, name, bases, attrs)
        # Build a list of fields, in the order they were listed in the class
        fields = [item for item in attrs.items() if isinstance(item[1], Field)]
        fields.sort(key=lambda item: item[1].creation_counter)
        setattr(new_cls, '_fields', fields)
        return new_cls


class Model(object):
    '''
    A base class for ORM models.
    '''

    __metaclass__ = ModelBase
    engine = None

    def __init__(self, **kwargs):
        '''
        Creates a model instance, using keyword arguments as field values.
        Since values are immediately converted to their Pythonic type,
        invalid values will cause a ValueError to be raised.
        '''
        super(Model, self).__init__()
        for name, field in self._fields:
            val = kwargs.get(name, field.default)
            setattr(self, name, val)

    def __setattr__(self, name, value):
        field = self.get_field(name)
        if field:
            value = field.to_python(value)
        super(Model, self).__setattr__(name, value)

    def get_field(self, name):
        field = getattr(self.__class__, name, None)
        return field if isinstance(field, Field) else None

    @classmethod
    def table_name(cls):
        return cls.__name__.lower()

    @classmethod
    def create_table_sql(cls, db_name):
        parts = ['CREATE TABLE IF NOT EXISTS %s.%s (' % (db_name, cls.table_name())]
        cols = []
        for name, field in cls._fields:
            default = field.get_db_prep_value(field.default)
            cols.append('    %s %s DEFAULT %s' % (name, field.db_type, escape(default)))
        parts.append(',\n'.join(cols))
        parts.append(')')
        parts.append('ENGINE = ' + cls.engine.create_table_sql())
        return '\n'.join(parts)

    @classmethod
    def drop_table_sql(cls, db_name):
        return 'DROP TABLE IF EXISTS %s.%s' % (db_name, cls.table_name())

    @classmethod
    def from_tsv(cls, line):
        '''
        Create a model instance from a tab-separated line. The line may or may not include a newline.
        '''
        values = iter(parse_tsv(line))
        kwargs = {}
        for name, field in cls._fields:
            kwargs[name] = values.next()
        return cls(**kwargs)
        # TODO verify that the number of values matches the number of fields

    def to_tsv(self):
        '''
        Returns the instance's column values as a tab-separated line. A newline is not included.
        '''
        parts = []
        for name, field in self._fields:
            value = field.get_db_prep_value(field.to_python(getattr(self, name)))
            parts.append(escape(value, quote=False))
        return '\t'.join(parts)
