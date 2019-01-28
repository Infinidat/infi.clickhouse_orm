import six
from datetime import date, datetime, tzinfo
import functools

from .utils import is_iterable, comma_join
from .query import Cond


def binary_operator(func):
    """
    Decorates a function to mark it as a binary operator.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)
        ret.is_binary_operator = True
        return ret
    return wrapper


class FunctionOperatorsMixin(object):
    """
    A mixin for implementing Python operators using F objects.
    """

    # Comparison operators

    def __lt__(self, other):
        return F.less(self, other)

    def __le__(self, other):
        return F.lessOrEquals(self, other)

    def __eq__(self, other):
        return F.equals(self, other)

    def __ne__(self, other):
        return F.notEquals(self, other)

    def __gt__(self, other):
        return F.greater(self, other)

    def __ge__(self, other):
        return F.greaterOrEquals(self, other)

    # Arithmetic operators

    def __add__(self, other):
        return F.plus(self, other)

    def __radd__(self, other):
        return F.plus(other, self)

    def __sub__(self, other):
        return F.minus(self, other)

    def __rsub__(self, other):
        return F.minus(other, self)

    def __mul__(self, other):
        return F.multiply(self, other)

    def __rmul__(self, other):
        return F.multiply(other, self)

    def __div__(self, other):
        return F.divide(self, other)

    def __rdiv__(self, other):
        return F.divide(other, self)

    def __mod__(self, other):
        return F.modulo(self, other)

    def __rmod__(self, other):
        return F.modulo(other, self)

    def __neg__(self):
        return F.negate(self)

    def __pos__(self):
        return self

    # Logical operators

    def __and__(self, other):
        return F._and(self, other)

    def __rand__(self, other):
        return F._and(other, self)

    def __or__(self, other):
        return F._or(self, other)

    def __ror__(self, other):
        return F._or(other, self)

    def __xor__(self, other):
        return F._xor(self, other)

    def __rxor__(self, other):
        return F._xor(other, self)

    def __invert__(self):
        return F._not(self)


class F(Cond, FunctionOperatorsMixin):
    """
    Represents a database function call and its arguments.
    It doubles as a query condition when the function returns a boolean result.
    """
    def __init__(self, name, *args):
        self.name = name
        self.args = args
        self.is_binary_operator = False

    def to_sql(self, *args):
        """
        Generates an SQL string for this function and its arguments.
        For example if the function name is a symbol of a binary operator:
            (2.54 * `height`)
        For other functions:
            gcd(12, 300)
        """
        if self.is_binary_operator:
            prefix = ''
            sep = ' ' + self.name + ' '
        else:
            prefix = self.name
            sep = ', '
        arg_strs = (self.arg_to_sql(arg) for arg in self.args)
        return prefix + '(' + sep.join(arg_strs) + ')'

    def arg_to_sql(self, arg):
        """
        Converts a function argument to SQL string according to its type.
        Supports functions, model fields, strings, dates, datetimes, booleans,
        None, numbers, timezones, arrays/iterables.
        """
        from .fields import Field, StringField, DateTimeField, DateField
        if isinstance(arg, F):
            return arg.to_sql()
        if isinstance(arg, Field):
            return "`%s`" % arg.name
        if isinstance(arg, six.string_types):
            return StringField().to_db_string(arg)
        if isinstance(arg, datetime):
            return "toDateTime(%s)" % DateTimeField().to_db_string(arg)
        if isinstance(arg, date):
            return "toDate('%s')" % arg.isoformat()
        if isinstance(arg, bool):
            return six.text_type(int(arg))
        if isinstance(arg, tzinfo):
            return StringField().to_db_string(arg.tzname(None))
        if arg is None:
            return 'NULL'
        if is_iterable(arg):
            return '[' + comma_join(self.arg_to_sql(x) for x in arg) + ']'
        return six.text_type(arg)

    # Arithmetic functions

    @staticmethod
    @binary_operator
    def plus(a, b):
        return F('+', a, b)

    @staticmethod
    @binary_operator
    def minus(a, b):
        return F('-', a, b)

    @staticmethod
    @binary_operator
    def multiply(a, b):
        return F('*', a, b)

    @staticmethod
    @binary_operator
    def divide(a, b):
        return F('/', a, b)

    @staticmethod
    def intDiv(a, b):
        return F('intDiv', a, b)

    @staticmethod
    def intDivOrZero(a, b):
        return F('intDivOrZero', a, b)

    @staticmethod
    @binary_operator
    def modulo(a, b):
        return F('%', a, b)

    @staticmethod
    def negate(a):
        return F('negate', a)

    @staticmethod
    def abs(a):
        return F('abs', a)

    @staticmethod
    def gcd(a, b):
        return F('gcd',a, b)

    @staticmethod
    def lcm(a, b):
        return F('lcm', a, b)

    # Comparison functions

    @staticmethod
    @binary_operator
    def equals(a, b):
        return F('=', a, b)

    @staticmethod
    @binary_operator
    def notEquals(a, b):
        return F('!=', a, b)

    @staticmethod
    @binary_operator
    def less(a, b):
        return F('<', a, b)

    @staticmethod
    @binary_operator
    def greater(a, b):
        return F('>', a, b)

    @staticmethod
    @binary_operator
    def lessOrEquals(a, b):
        return F('<=', a, b)

    @staticmethod
    @binary_operator
    def greaterOrEquals(a, b):
        return F('>=', a, b)

    # Logical functions (should be used as python operators: & | ^ ~)

    @staticmethod
    @binary_operator
    def _and(a, b):
        return F('AND', a, b)

    @staticmethod
    @binary_operator
    def _or(a, b):
        return F('OR', a, b)

    @staticmethod
    def _xor(a, b):
        return F('xor', a, b)

    @staticmethod
    def _not(a):
        return F('not', a)

    # Functions for working with dates and times

    @staticmethod
    def toYear(d):
        return F('toYear', d)

    @staticmethod
    def toMonth(d):
        return F('toMonth', d)

    @staticmethod
    def toDayOfMonth(d):
        return F('toDayOfMonth', d)

    @staticmethod
    def toDayOfWeek(d):
        return F('toDayOfWeek', d)

    @staticmethod
    def toHour(d):
        return F('toHour', d)

    @staticmethod
    def toMinute(d):
        return F('toMinute', d)

    @staticmethod
    def toSecond(d):
        return F('toSecond', d)

    @staticmethod
    def toMonday(d):
        return F('toMonday', d)

    @staticmethod
    def toStartOfMonth(d):
        return F('toStartOfMonth', d)

    @staticmethod
    def toStartOfQuarter(d):
        return F('toStartOfQuarter', d)

    @staticmethod
    def toStartOfYear(d):
        return F('toStartOfYear', d)

    @staticmethod
    def toStartOfMinute(d):
        return F('toStartOfMinute', d)

    @staticmethod
    def toStartOfFiveMinute(d):
        return F('toStartOfFiveMinute', d)

    @staticmethod
    def toStartOfFifteenMinutes(d):
        return F('toStartOfFifteenMinutes', d)

    @staticmethod
    def toStartOfHour(d):
        return F('toStartOfHour', d)

    @staticmethod
    def toStartOfDay(d):
        return F('toStartOfDay', d)

    @staticmethod
    def toTime(d, timezone=''):
        return F('toTime', d, timezone)

    @staticmethod
    def toRelativeYearNum(d, timezone=''):
        return F('toRelativeYearNum', d, timezone)

    @staticmethod
    def toRelativeMonthNum(d, timezone=''):
        return F('toRelativeMonthNum', d, timezone)

    @staticmethod
    def toRelativeWeekNum(d, timezone=''):
        return F('toRelativeWeekNum', d, timezone)

    @staticmethod
    def toRelativeDayNum(d, timezone=''):
        return F('toRelativeDayNum', d, timezone)

    @staticmethod
    def toRelativeHourNum(d, timezone=''):
        return F('toRelativeHourNum', d, timezone)

    @staticmethod
    def toRelativeMinuteNum(d, timezone=''):
        return F('toRelativeMinuteNum', d, timezone)

    @staticmethod
    def toRelativeSecondNum(d, timezone=''):
        return F('toRelativeSecondNum', d, timezone)

    @staticmethod
    def now():
        return F('now')

    @staticmethod
    def today():
        return F('today')

    @staticmethod
    def yesterday():
        return F('yesterday')

    @staticmethod
    def timeSlot(d):
        return F('timeSlot', d)

    @staticmethod
    def timeSlots(start_time, duration):
        return F('timeSlots', start_time, F.toUInt32(duration))

    @staticmethod
    def formatDateTime(d, format, timezone=''):
        return F('formatDateTime', d, format, timezone)

    # Type conversion functions

    @staticmethod
    def toUInt8(x):
        return F('toUInt8', x)

    @staticmethod
    def toUInt16(x):
        return F('toUInt16', x)

    @staticmethod
    def toUInt32(x):
        return F('toUInt32', x)

    @staticmethod
    def toUInt64(x):
        return F('toUInt64', x)

    @staticmethod
    def toInt8(x):
        return F('toInt8', x)

    @staticmethod
    def toInt16(x):
        return F('toInt16', x)

    @staticmethod
    def toInt32(x):
        return F('toInt32', x)

    @staticmethod
    def toInt64(x):
        return F('toInt64', x)

    @staticmethod
    def toFloat32(x):
        return F('toFloat32', x)

    @staticmethod
    def toFloat64(x):
        return F('toFloat64', x)

    @staticmethod
    def toUInt8OrZero(x):
        return F('toUInt8OrZero', x)

    @staticmethod
    def toUInt16OrZero(x):
        return F('toUInt16OrZero', x)

    @staticmethod
    def toUInt32OrZero(x):
        return F('toUInt32OrZero', x)

    @staticmethod
    def toUInt64OrZero(x):
        return F('toUInt64OrZero', x)

    @staticmethod
    def toInt8OrZero(x):
        return F('toInt8OrZero', x)

    @staticmethod
    def toInt16OrZero(x):
        return F('toInt16OrZero', x)

    @staticmethod
    def toInt32OrZero(x):
        return F('toInt32OrZero', x)

    @staticmethod
    def toInt64OrZero(x):
        return F('toInt64OrZero', x)

    @staticmethod
    def toFloat32OrZero(x):
        return F('toFloat32OrZero', x)

    @staticmethod
    def toFloat64OrZero(x):
        return F('toFloat64OrZero', x)

    @staticmethod
    def toDecimal32(x, scale):
        return F('toDecimal32', x, scale)

    @staticmethod
    def toDecimal64(x, scale):
        return F('toDecimal64', x, scale)

    @staticmethod
    def toDecimal128(x, scale):
        return F('toDecimal128', x, scale)

    @staticmethod
    def toDate(x):
        return F('toDate', x)

    @staticmethod
    def toDateTime(x):
        return F('toDateTime', x)

    @staticmethod
    def toString(x):
        return F('toString', x)

    @staticmethod
    def toFixedString(s, length):
        return F('toFixedString', s, length)

    @staticmethod
    def toStringCutToZero(s):
        return F('toStringCutToZero', s)

    @staticmethod
    def CAST(x, type):
        return F('CAST', x, type)

    # Functions for working with strings

    @staticmethod
    def empty(s):
        return F('empty', s)

    @staticmethod
    def notEmpty(s):
        return F('notEmpty', s)

    @staticmethod
    def length(s):
        return F('length', s)

    @staticmethod
    def lengthUTF8(s):
        return F('lengthUTF8', s)

    @staticmethod
    def lower(s):
        return F('lower', s)

    @staticmethod
    def upper(s):
        return F('upper', s)

    @staticmethod
    def lowerUTF8(s):
        return F('lowerUTF8', s)

    @staticmethod
    def upperUTF8(s):
        return F('upperUTF8', s)

    @staticmethod
    def reverse(s):
        return F('reverse', s)

    @staticmethod
    def reverseUTF8(s):
        return F('reverseUTF8', s)

    @staticmethod
    def concat(*args):
        return F('concat', *args)

    @staticmethod
    def substring(s, offset, length):
        return F('substring', s, offset, length)

    @staticmethod
    def substringUTF8(s, offset, length):
        return F('substringUTF8', s, offset, length)

    @staticmethod
    def appendTrailingCharIfAbsent(s, c):
        return F('appendTrailingCharIfAbsent', s, c)

    @staticmethod
    def convertCharset(s, from_charset, to_charset):
        return F('convertCharset', s, from_charset, to_charset)

    @staticmethod
    def base64Encode(s):
        return F('base64Encode', s)

    @staticmethod
    def base64Decode(s):
        return F('base64Decode', s)

    @staticmethod
    def tryBase64Decode(s):
        return F('tryBase64Decode', s)

