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

    def get_db_prep_value(self, value):
        '''
        Returns the field's value prepared for interacting with the database.
        '''
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

    min_value = datetime.date(1970, 1, 1)
    max_value = datetime.date(2038, 1, 19)
    class_default = min_value
    db_type = 'Date'

    def to_python(self, value):
        if isinstance(value, datetime.date):
            return value
        if isinstance(value, int):
            return DateField.class_default + datetime.timedelta(days=value)
        if isinstance(value, basestring):
            if value == '0000-00-00':
                return DateField.min_value
            return datetime.datetime.strptime(value, '%Y-%m-%d').date()
        raise ValueError('Invalid value for %s - %r' % (self.__class__.__name__, value))

    def validate(self, value):
        self._range_check(value, DateField.min_value, DateField.max_value)

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
            return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        raise ValueError('Invalid value for %s - %r' % (self.__class__.__name__, value))

    def get_db_prep_value(self, value):
        return int(time.mktime(value.timetuple()))


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

