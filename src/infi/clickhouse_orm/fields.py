import datetime
import pytz
import time


class Field(object):

    creation_counter = 0
    class_default = 0
    db_type = None

    def __init__(self, default=None):
        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1
        self.default = default or self.class_default

    def to_python(self, value):
        """
        Converts the input value into the expected Python data type, raising ValueError if the
        data can't be converted. Returns the converted value. Subclasses should override this.
        """
        return value

    def get_db_prep_value(self, value):
        """
        Returns the field's value prepared for interacting with the database.
        """
        return value


class StringField(Field):

    class_default = ''
    db_type = 'String'

    def to_python(self, value):
        if isinstance(value, unicode):
            return value
        if isinstance(value, str):
            return value.decode('UTF-8')
        raise ValueError('Invalid value for %s: %r' % (self.__class__.__name__, value))

    def get_db_prep_value(self, value):
        if isinstance(value, unicode):
            return value.encode('UTF-8')
        return value


class DateField(Field):

    class_default = datetime.date(1970, 1, 1)
    db_type = 'Date'

    def to_python(self, value):
        if isinstance(value, datetime.date):
            return value
        if isinstance(value, int):
            return DateField.class_default + datetime.timedelta(days=value)
        if isinstance(value, basestring):
            return datetime.datetime.strptime(value, '%Y-%m-%d').date()
        raise ValueError('Invalid value for %s: %r' % (self.__class__.__name__, value))

    def get_db_prep_value(self, value):
        return value.isoformat()


class DateTimeField(Field):

    class_default = datetime.datetime.fromtimestamp(0, pytz.utc)
    db_type = 'DateTime'

    def to_python(self, value):
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime(value.year, value.month, value.day)
        if isinstance(value, int):
            return datetime.datetime.fromtimestamp(value, pytz.utc)
        if isinstance(value, basestring):
            return datetime.datetime.strptime(value, '%Y-%m-%d %H-%M-%S')
        raise ValueError('Invalid value for %s: %r' % (self.__class__.__name__, value))

    def get_db_prep_value(self, value):
        return int(time.mktime(value.timetuple()))


class BaseIntField(Field):

    def to_python(self, value):
        if isinstance(value, int):
            return value
        if isinstance(value, basestring):
            return int(value)
        raise ValueError('Invalid value for %s: %r' % (self.__class__.__name__, value))


class UInt8Field(BaseIntField):

    db_type = 'UInt8'


class UInt16Field(BaseIntField):

    db_type = 'UInt16'


class UInt32Field(BaseIntField):

    db_type = 'UInt32'


class UInt64Field(BaseIntField):

    db_type = 'UInt64'


class Int8Field(BaseIntField):

    db_type = 'Int8'


class Int16Field(BaseIntField):

    db_type = 'Int16'


class Int32Field(BaseIntField):

    db_type = 'Int32'


class Int64Field(BaseIntField):

    db_type = 'Int64'


class BaseFloatField(Field):

    def to_python(self, value):
        if isinstance(value, float):
            return value
        if isinstance(value, basestring) or isinstance(value, int):
            return float(value)
        raise ValueError('Invalid value for %s: %r' % (self.__class__.__name__, value))


class Float32Field(BaseFloatField):

    db_type = 'Float32'


class Float64Field(BaseFloatField):

    db_type = 'Float64'

