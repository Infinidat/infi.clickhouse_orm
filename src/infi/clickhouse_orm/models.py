from utils import escape, parse_tsv
from engines import *
from fields import Field


class ModelBase(type):
    '''
    A metaclass for ORM models. It adds the _fields list to model classes.
    '''

    def __new__(cls, name, bases, attrs):
        new_cls = super(ModelBase, cls).__new__(cls, name, bases, attrs)
        # Collect fields from parent classes
        base_fields = []
        for base in bases:
            if isinstance(base, ModelBase):
                base_fields += base._fields
        # Build a list of fields, in the order they were listed in the class
        fields = base_fields + [item for item in attrs.items() if isinstance(item[1], Field)]
        fields.sort(key=lambda item: item[1].creation_counter)
        setattr(new_cls, '_fields', fields)
        return new_cls

    @classmethod
    def create_ad_hoc_model(cls, fields):
        # fields is a list of tuples (name, db_type)
        import fields as orm_fields
        attrs = {}
        for name, db_type in fields:
            field_class = db_type + 'Field'
            if not hasattr(orm_fields, field_class):
                raise NotImplementedError('No field class for %s' % db_type)
            attrs[name] = getattr(orm_fields, field_class)()
        return cls.__new__(cls, 'AdHocModel', (Model,), attrs)


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
        Unrecognized field names will cause an AttributeError.
        '''
        super(Model, self).__init__()
        # Assign field values from keyword arguments
        for name, value in kwargs.iteritems():
            field = self.get_field(name)
            if field:
                setattr(self, name, value)
            else:
                raise AttributeError('%s does not have a field called %s' % (self.__class__.__name__, name))
        # Assign default values for fields not included in the keyword arguments
        for name, field in self._fields:
            if name not in kwargs:
                setattr(self, name, field.default)

    def __setattr__(self, name, value):
        '''
        When setting a field value, converts the value to its Pythonic type and validates it.
        This may raise a ValueError.
        '''
        field = self.get_field(name)
        if field:
            value = field.to_python(value)
            field.validate(value)
        super(Model, self).__setattr__(name, value)

    def get_field(self, name):
        '''
        Get a Field instance given its name, or None if not found.
        '''
        field = getattr(self.__class__, name, None)
        return field if isinstance(field, Field) else None

    @classmethod
    def table_name(cls):
        '''
        Returns the model's database table name.
        '''
        return cls.__name__.lower()

    @classmethod
    def create_table_sql(cls, db_name):
        '''
        Returns the SQL command for creating a table for this model.
        '''
        parts = ['CREATE TABLE IF NOT EXISTS `%s`.`%s` (' % (db_name, cls.table_name())]
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
        '''
        Returns the SQL command for deleting this model's table.
        '''
        return 'DROP TABLE IF EXISTS `%s`.`%s`' % (db_name, cls.table_name())

    @classmethod
    def from_tsv(cls, line, field_names=None):
        '''
        Create a model instance from a tab-separated line. The line may or may not include a newline.
        The field_names list must match the fields defined in the model, but does not have to include all of them.
        If omitted, it is assumed to be the names of all fields in the model, in order of definition.
        '''
        field_names = field_names or [name for name, field in cls._fields]
        values = iter(parse_tsv(line))
        kwargs = {}
        for name in field_names:
            kwargs[name] = values.next()
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
