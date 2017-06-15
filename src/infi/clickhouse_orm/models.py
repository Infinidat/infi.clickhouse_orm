from logging import getLogger

from six import with_metaclass
import pytz

from .fields import Field
from .utils import parse_tsv
from .query import QuerySet

logger = getLogger('clickhouse_orm')


class ModelBase(type):
    '''
    A metaclass for ORM models. It adds the _fields list to model classes.
    '''

    ad_hoc_model_cache = {}

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
        setattr(new_cls, '_writable_fields', [f for f in fields if not f[1].readonly])
        return new_cls

    @classmethod
    def create_ad_hoc_model(cls, fields, model_name='AdHocModel'):
        # fields is a list of tuples (name, db_type)
        # Check if model exists in cache
        fields = list(fields)
        cache_key = str(fields)
        if cache_key in cls.ad_hoc_model_cache:
            return cls.ad_hoc_model_cache[cache_key]
        # Create an ad hoc model class
        attrs = {}
        for name, db_type in fields:
            attrs[name] = cls.create_ad_hoc_field(db_type)
        model_class = cls.__new__(cls, model_name, (Model,), attrs)
        # Add the model class to the cache
        cls.ad_hoc_model_cache[cache_key] = model_class
        return model_class

    @classmethod
    def create_ad_hoc_field(cls, db_type):
        import infi.clickhouse_orm.fields as orm_fields
        # Enums
        if db_type.startswith('Enum'):
            return orm_fields.BaseEnumField.create_ad_hoc_field(db_type)
        # Arrays
        if db_type.startswith('Array'):
            inner_field = cls.create_ad_hoc_field(db_type[6 : -1])
            return orm_fields.ArrayField(inner_field)
        # FixedString
        if db_type.startswith('FixedString'):
            length = int(db_type[12 : -1])
            return orm_fields.FixedStringField(length)
        # Simple fields
        name = db_type + 'Field'
        if not hasattr(orm_fields, name):
            raise NotImplementedError('No field class for %s' % db_type)
        return getattr(orm_fields, name)()


class Model(with_metaclass(ModelBase)):
    '''
    A base class for ORM models. Each model class represent a ClickHouse table. For example:
        
        class CPUStats(Model):
            timestamp = DateTimeField()
            cpu_id = UInt16Field()
            cpu_percent = Float32Field()
            engine = Memory()
    '''

    engine = None
    readonly = False

    def __init__(self, **kwargs):
        '''
        Creates a model instance, using keyword arguments as field values.
        Since values are immediately converted to their Pythonic type,
        invalid values will cause a `ValueError` to be raised.
        Unrecognized field names will cause an `AttributeError`.
        '''
        super(Model, self).__init__()

        self._database = None

        # Assign field values from keyword arguments
        for name, value in kwargs.items():
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
        This may raise a `ValueError`.
        '''
        field = self.get_field(name)
        if field:
            value = field.to_python(value, pytz.utc)
            field.validate(value)
        super(Model, self).__setattr__(name, value)

    def set_database(self, db):
        '''
        Sets the `Database` that this model instance belongs to. 
        This is done automatically when the instance is read from the database or written to it.
        '''
        # This can not be imported globally due to circular import
        from .database import Database
        assert isinstance(db, Database), "database must be database.Database instance"
        self._database = db

    def get_database(self):
        '''
        Gets the `Database` that this model instance belongs to. 
        Returns `None` unless the instance was read from the database or written to it.
        '''
        return self._database

    def get_field(self, name):
        '''
        Gets a `Field` instance given its name, or `None` if not found.
        '''
        field = getattr(self.__class__, name, None)
        return field if isinstance(field, Field) else None

    @classmethod
    def table_name(cls):
        '''
        Returns the model's database table name. By default this is the
        class name converted to lowercase. Override this if you want to use
        a different table name.
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
            cols.append('    %s %s' % (name, field.get_sql()))
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
    def from_tsv(cls, line, field_names=None, timezone_in_use=pytz.utc, database=None):
        '''
        Create a model instance from a tab-separated line. The line may or may not include a newline.
        The `field_names` list must match the fields defined in the model, but does not have to include all of them.
        If omitted, it is assumed to be the names of all fields in the model, in order of definition.

        - `line`: the TSV-formatted data.
        - `field_names`: names of the model fields in the data.
        - `timezone_in_use`: the timezone to use when parsing dates and datetimes.
        - `database`: if given, sets the database that this instance belongs to.
        '''
        from six import next
        field_names = field_names or [name for name, field in cls._fields]
        values = iter(parse_tsv(line))
        kwargs = {}
        for name in field_names:
            field = getattr(cls, name)
            kwargs[name] = field.to_python(next(values), timezone_in_use)

        obj = cls(**kwargs)
        if database is not None:
            obj.set_database(database)

        return obj

    def to_tsv(self, include_readonly=True):
        '''
        Returns the instance's column values as a tab-separated line. A newline is not included.

        - `include_readonly`: if false, returns only fields that can be inserted into database.
        '''
        data = self.__dict__
        fields = self._fields if include_readonly else self._writable_fields
        return '\t'.join(field.to_db_string(data[name], quote=False) for name, field in fields)

    def to_dict(self, include_readonly=True, field_names=None):
        '''
        Returns the instance's column values as a dict.
        
        - `include_readonly`: if false, returns only fields that can be inserted into database.
        - `field_names`: an iterable of field names to return (optional)
        '''
        fields = self._fields if include_readonly else self._writable_fields

        if field_names is not None:
            fields = [f for f in fields if f[0] in field_names]

        data = self.__dict__
        return {name: data[name] for name, field in fields}

    @classmethod
    def objects_in(cls, database):
        '''
        Returns a `QuerySet` for selecting instances of this model class.
        '''
        return QuerySet(cls, database)

        
class BufferModel(Model):

    @classmethod
    def create_table_sql(cls, db_name):
        '''
        Returns the SQL command for creating a table for this model.
        '''
        parts = ['CREATE TABLE IF NOT EXISTS `%s`.`%s` AS `%s`.`%s`' % (db_name, cls.table_name(), db_name, cls.engine.main_model.table_name())]
        engine_str = cls.engine.create_table_sql(db_name)
        parts.append(engine_str)
        return ' '.join(parts)
