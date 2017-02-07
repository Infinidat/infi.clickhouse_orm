from six import string_types, text_type, binary_type
import datetime
import pytz
import time

from .utils import escape, parse_array


class Field(object):

    creation_counter = 0
    class_default = 0
    db_type = None

    def __init__(self, default=None):
        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1
        self.default = self.class_default if default is None else default

    def to_python(self, value):
        '''
        Converts the input value into the expected Python data type, raising ValueError if the
        data can't be converted. Returns the converted value. Subclasses should override this.
        '''
        return value

    def validate(self, value):
        '''
        Called after to_python to validate that the value is suitable for the field's database type.
        Subclasses should override this.
        '''
        pass

    def _range_check(self, value, min_value, max_value):
        '''
        Utility method to check that the given value is between min_value and max_value.
        '''
        if value < min_value or value > max_value:
            raise ValueError('%s out of range - %s is not between %s and %s' % (self.__class__.__name__, value, min_value, max_value))

    def to_db_string(self, value, quote=True):
        '''
        Returns the field's value prepared for writing to the database.
        When quote is true, strings are surrounded by single quotes.
        '''
        return escape(value, quote)

    def get_sql(self, with_default=True):
        '''
        Returns an SQL expression describing the field (e.g. for CREATE TABLE).
        '''
        if with_default:
            default = self.to_db_string(self.default)
            return '%s DEFAULT %s' % (self.db_type, default)
        else:
            return self.db_type


class StringField(Field):

    class_default = ''
    db_type = 'String'

    def to_python(self, value):
        if isinstance(value, text_type):
            return value
        if isinstance(value, binary_type):
            return value.decode('UTF-8')
        raise ValueError('Invalid value for %s: %r' % (self.__class__.__name__, value))


class DateField(Field):

    min_value = datetime.date(1970, 1, 1)
    max_value = datetime.date(2038, 1, 19)
    class_default = min_value
    db_type = 'Date'

    def to_python(self, value):
        if isinstance(value, datetime.date):
            return value
        if isinstance(value, int):
            return DateField.class_default + datetime.timedelta(days=value)
        if isinstance(value, string_types):
            if value == '0000-00-00':
                return DateField.min_value
            return datetime.datetime.strptime(value, '%Y-%m-%d').date()
        raise ValueError('Invalid value for %s - %r' % (self.__class__.__name__, value))

    def validate(self, value):
        self._range_check(value, DateField.min_value, DateField.max_value)

    def to_db_string(self, value, quote=True):
        return escape(value.isoformat(), quote)


class DateTimeField(Field):

    class_default = datetime.datetime.fromtimestamp(0, pytz.timezone('Asia/Shanghai'))
    db_type = 'DateTime'

    def to_python(self, value):
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime(value.year, value.month, value.day)
        if isinstance(value, int):
            return datetime.datetime.fromtimestamp(value, pytz.timezone('Asia/Shanghai'))
        if isinstance(value, string_types):
            if value == '0000-00-00 00:00:00':
                return self.class_default
            return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        raise ValueError('Invalid value for %s - %r' % (self.__class__.__name__, value))

    def to_db_string(self, value, quote=True):
        return escape(int(time.mktime(value.timetuple())), quote)


class BaseIntField(Field):

    def to_python(self, value):
        try:
            return int(value)
        except:
            raise ValueError('Invalid value for %s - %r' % (self.__class__.__name__, value))

    def validate(self, value):
        self._range_check(value, self.min_value, self.max_value)


class UInt8Field(BaseIntField):

    min_value = 0
    max_value = 2**8 - 1
    db_type = 'UInt8'


class UInt16Field(BaseIntField):

    min_value = 0
    max_value = 2**16 - 1
    db_type = 'UInt16'


class UInt32Field(BaseIntField):

    min_value = 0
    max_value = 2**32 - 1
    db_type = 'UInt32'


class UInt64Field(BaseIntField):

    min_value = 0
    max_value = 2**64 - 1
    db_type = 'UInt64'


class Int8Field(BaseIntField):

    min_value = -2**7
    max_value = 2**7 - 1
    db_type = 'Int8'


class Int16Field(BaseIntField):

    min_value = -2**15
    max_value = 2**15 - 1
    db_type = 'Int16'


class Int32Field(BaseIntField):

    min_value = -2**31
    max_value = 2**31 - 1
    db_type = 'Int32'


class Int64Field(BaseIntField):

    min_value = -2**63
    max_value = 2**63 - 1
    db_type = 'Int64'


class BaseFloatField(Field):

    def to_python(self, value):
        try:
            return float(value)
        except:
            raise ValueError('Invalid value for %s - %r' % (self.__class__.__name__, value))


class Float32Field(BaseFloatField):

    db_type = 'Float32'


class Float64Field(BaseFloatField):

    db_type = 'Float64'


class BaseEnumField(Field):

    def __init__(self, enum_cls, default=None):
        self.enum_cls = enum_cls
        if default is None:
            default = list(enum_cls)[0]
        super(BaseEnumField, self).__init__(default)

    def to_python(self, value):
        if isinstance(value, self.enum_cls):
            return value
        try:
            if isinstance(value, text_type):
                return self.enum_cls[value]
            if isinstance(value, binary_type):
                return self.enum_cls[value.decode('UTF-8')]
            if isinstance(value, int):
                return self.enum_cls(value)
        except (KeyError, ValueError):
            pass
        raise ValueError('Invalid value for %s: %r' % (self.enum_cls.__name__, value))

    def to_db_string(self, value, quote=True):
        return escape(value.name, quote)

    def get_sql(self, with_default=True):
        values = ['%s = %d' % (escape(item.name), item.value) for item in self.enum_cls]
        sql = '%s(%s)' % (self.db_type, ' ,'.join(values))
        if with_default:
            default = self.to_db_string(self.default)
            sql = '%s DEFAULT %s' % (sql, default)
        return sql

    @classmethod
    def create_ad_hoc_field(cls, db_type):
        '''
        Give an SQL column description such as "Enum8('apple' = 1, 'banana' = 2, 'orange' = 3)"
        this method returns a matching enum field.
        '''
        import re
        try:
            Enum # exists in Python 3.4+
        except NameError:
            from enum import Enum # use the enum34 library instead
        members = {}
        for match in re.finditer("'(\w+)' = (\d+)", db_type):
            members[match.group(1)] = int(match.group(2))
        enum_cls = Enum('AdHocEnum', members)
        field_class = Enum8Field if db_type.startswith('Enum8') else Enum16Field
        return field_class(enum_cls)


class Enum8Field(BaseEnumField):

    db_type = 'Enum8'


class Enum16Field(BaseEnumField):

    db_type = 'Enum16'


class ArrayField(Field):

    class_default = []

    def __init__(self, inner_field, default=None):
        self.inner_field = inner_field
        super(ArrayField, self).__init__(default)

    def to_python(self, value):
        if isinstance(value, text_type):
            value = parse_array(value)
        elif isinstance(value, binary_type):
            value = parse_array(value.decode('UTF-8'))
        elif not isinstance(value, (list, tuple)):
            raise ValueError('ArrayField expects list or tuple, not %s' % type(value))
        return [self.inner_field.to_python(v) for v in value]

    def validate(self, value):
        for v in value:
            self.inner_field.validate(v)

    def to_db_string(self, value, quote=True):
        array = [self.inner_field.to_db_string(v, quote=True) for v in value]
        return '[' + ', '.join(array) + ']'

    def get_sql(self, with_default=True):
        from .utils import escape
        return 'Array(%s)' % self.inner_field.get_sql(with_default=False)
