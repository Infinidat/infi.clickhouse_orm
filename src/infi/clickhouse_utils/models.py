from fields import *
from utils import escape, parse_tsv
from engines import *


class ModelBase(type):

    def __new__(cls, name, bases, attrs):
        new_cls = super(ModelBase, cls).__new__(cls, name, bases, attrs)
        #print name, bases, attrs
        # Build a list of fields, in the order they were listed in the class
        fields = [item for item in attrs.items() if isinstance(item[1], Field)]
        fields.sort(key=lambda item: item[1].creation_counter)
        setattr(new_cls, '_fields', fields)
        return new_cls


class Model(object):

    __metaclass__ = ModelBase
    engine = None

    def __init__(self, *args, **kwargs):
        super(Model, self).__init__()
        for name, field in self._fields:
            val = kwargs.get(name, field.default)
            setattr(self, name, val)

    @classmethod
    def table_name(cls):
        return cls.__name__.lower()

    @classmethod
    def create_table_sql(cls, db):
        parts = ['CREATE TABLE IF NOT EXISTS %s.%s (' % (db, cls.table_name())]
        for name, field in cls._fields:
            default = field.get_db_prep_value(field.default)
            parts.append('    %s %s DEFAULT %s,' % (name, field.db_type, escape(default)))
        parts.append(')')
        parts.append('ENGINE = ' + cls.engine.create_table_sql())
        return '\n'.join(parts)

    @classmethod
    def from_tsv(cls, line):
        '''
        Create a model instance from a tab-separated line. The line may or may not include a newline.
        '''
        values = iter(parse_tsv(line))
        kwargs = {}
        for name, field in cls._fields:
            kwargs[name] = field.to_python(values.next())
        return cls(**kwargs)

    def to_tsv(self):
        '''
        Returns the instance's column values as a tab-separated line. A newline is not included.
        '''
        parts = []
        for name, field in self._fields:
            value = field.get_db_prep_value(field.to_python(getattr(self, name)))
            parts.append(escape(value, quote=False))
        return '\t'.join(parts)
