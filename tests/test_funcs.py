import unittest
from .base_test_with_data import *
from .test_querysets import SampleModel
from datetime import date, datetime, tzinfo, timedelta
from infi.clickhouse_orm.database import ServerError


class FuncsTestCase(TestCaseWithData):

    def setUp(self):
        super(FuncsTestCase, self).setUp()
        self.database.insert(self._sample_data())

    def _test_qs(self, qs, expected_count):
        logger.info(qs.as_sql())
        count = 0
        for instance in qs:
            count += 1
            logger.info('\t[%d]\t%s' % (count, instance.to_dict()))
        self.assertEqual(count, expected_count)
        self.assertEqual(qs.count(), expected_count)

    def _test_func(self, func, expected_value=None):
        sql = 'SELECT %s AS value' % func.to_sql()
        logger.info(sql)
        result = list(self.database.select(sql))
        logger.info('\t==> %s', result[0].value if result else '<empty>')
        if expected_value is not None:
            self.assertEqual(result[0].value, expected_value)

    def test_func_to_sql(self):
        # No args
        self.assertEqual(F('func').to_sql(), 'func()')
        # String args
        self.assertEqual(F('func', "Wendy's", u"Wendy's").to_sql(), "func('Wendy\\'s', 'Wendy\\'s')")
        # Numeric args
        self.assertEqual(F('func', 1, 1.1, Decimal('3.3')).to_sql(), "func(1, 1.1, 3.3)")
        # Date args
        self.assertEqual(F('func', date(2018, 12, 31)).to_sql(), "func(toDate('2018-12-31'))")
        # Datetime args
        self.assertEqual(F('func', datetime(2018, 12, 31)).to_sql(), "func(toDateTime('1546214400'))")
        # Boolean args
        self.assertEqual(F('func', True, False).to_sql(), "func(1, 0)")
        # Timezone args
        self.assertEqual(F('func', pytz.utc).to_sql(), "func('UTC')")
        self.assertEqual(F('func', pytz.timezone('Europe/Athens')).to_sql(), "func('Europe/Athens')")
        # Null args
        self.assertEqual(F('func', None).to_sql(), "func(NULL)")
        # Fields as args
        self.assertEqual(F('func', SampleModel.color).to_sql(), "func(`color`)")
        # Funcs as args
        self.assertEqual(F('func', F('sqrt', 25)).to_sql(), 'func(sqrt(25))')
        # Iterables as args
        x = [1, 'z', F('foo', 17)]
        for y in [x, tuple(x), iter(x)]:
            self.assertEqual(F('func', y, 5).to_sql(), "func([1, 'z', foo(17)], 5)")
        self.assertEqual(F('func', [(1, 2), (3, 4)]).to_sql(), "func([[1, 2], [3, 4]])")
        # Binary operator functions
        self.assertEqual(F.plus(1, 2).to_sql(), "(1 + 2)")
        self.assertEqual(F.lessOrEquals(1, 2).to_sql(), "(1 <= 2)")

    def test_filter_float_field(self):
        qs = Person.objects_in(self.database)
        # Height > 2
        self._test_qs(qs.filter(F.greater(Person.height, 2)), 0)
        self._test_qs(qs.filter(Person.height > 2), 0)
        # Height > 1.61
        self._test_qs(qs.filter(F.greater(Person.height, 1.61)), 96)
        self._test_qs(qs.filter(Person.height > 1.61), 96)
        # Height < 1.61
        self._test_qs(qs.filter(F.less(Person.height, 1.61)), 4)
        self._test_qs(qs.filter(Person.height < 1.61), 4)

    def test_filter_date_field(self):
        qs = Person.objects_in(self.database)
        # People born on the 30th
        self._test_qs(qs.filter(F('equals', F('toDayOfMonth', Person.birthday), 30)), 3)
        self._test_qs(qs.filter(F('toDayOfMonth', Person.birthday) == 30), 3)
        self._test_qs(qs.filter(F.toDayOfMonth(Person.birthday) == 30), 3)
        # People born on Sunday
        self._test_qs(qs.filter(F('equals', F('toDayOfWeek', Person.birthday), 7)), 18)
        self._test_qs(qs.filter(F('toDayOfWeek', Person.birthday) == 7), 18)
        self._test_qs(qs.filter(F.toDayOfWeek(Person.birthday) == 7), 18)
        # People born on 1976-10-01
        self._test_qs(qs.filter(F('equals', Person.birthday, '1976-10-01')), 1)
        self._test_qs(qs.filter(F('equals', Person.birthday, date(1976, 10, 01))), 1)
        self._test_qs(qs.filter(Person.birthday == date(1976, 10, 01)), 1)

    def test_func_as_field_value(self):
        qs = Person.objects_in(self.database)
        self._test_qs(qs.filter(height__gt=F.plus(1, 0.61)), 96)
        self._test_qs(qs.exclude(birthday=F.today()), 100)
        self._test_qs(qs.filter(birthday__between=['1970-01-01', F.today()]), 100)

    def test_comparison_operators(self):
        one = F.plus(1, 0)
        two = F.plus(1, 1)
        self._test_func(one > one, 0)
        self._test_func(two > one, 1)
        self._test_func(one >= two, 0)
        self._test_func(one >= one, 1)
        self._test_func(one < one, 0)
        self._test_func(one < two, 1)
        self._test_func(two <= one, 0)
        self._test_func(one <= one, 1)
        self._test_func(one == two, 0)
        self._test_func(one == one, 1)
        self._test_func(one != one, 0)
        self._test_func(one != two, 1)

    def test_arithmetic_operators(self):
        one = F.plus(1, 0)
        two = F.plus(1, 1)
        # +
        self._test_func(one + two, 3)
        self._test_func(one + 2, 3)
        self._test_func(2 + one, 3)
        # -
        self._test_func(one - two, -1)
        self._test_func(one - 2, -1)
        self._test_func(1 - two, -1)
        # *
        self._test_func(one * two, 2)
        self._test_func(one * 2, 2)
        self._test_func(1 * two, 2)
        # /
        self._test_func(one / two, 0.5)
        self._test_func(one / 2, 0.5)
        self._test_func(1 / two, 0.5)
        # %
        self._test_func(one % two, 1)
        self._test_func(one % 2, 1)
        self._test_func(1 % two, 1)
        # sign
        self._test_func(-one, -1)
        self._test_func(--one, 1)
        self._test_func(+one, 1)

    def test_logical_operators(self):
        one = F.plus(1, 0)
        two = F.plus(1, 1)
        # &
        self._test_func(one & two, 1)
        self._test_func(one & two, 1)
        self._test_func(one & 0, 0)
        self._test_func(0 & one, 0)
        # |
        self._test_func(one | two, 1)
        self._test_func(one | 0, 1)
        self._test_func(0 | one, 1)
        # ^
        self._test_func(one ^ one, 0)
        self._test_func(one ^ 0, 1)
        self._test_func(0 ^ one, 1)
        # ~
        self._test_func(~one, 0)
        self._test_func(~~one, 1)
        # compound
        self._test_func(one & 0 | two, 1)
        self._test_func(one & 0 & two, 0)
        self._test_func(one & 0 | 0, 0)
        self._test_func((one | 0) & two, 1)

    def test_date_functions(self):
        d = date(2018, 12, 31)
        dt = datetime(2018, 12, 31, 11, 22, 33)
        self._test_func(F.toYear(d), 2018)
        self._test_func(F.toYear(dt), 2018)
        self._test_func(F.toMonth(d), 12)
        self._test_func(F.toMonth(dt), 12)
        self._test_func(F.toDayOfMonth(d), 31)
        self._test_func(F.toDayOfMonth(dt), 31)
        self._test_func(F.toDayOfWeek(d), 1)
        self._test_func(F.toDayOfWeek(dt), 1)
        self._test_func(F.toHour(dt), 11)
        self._test_func(F.toMinute(dt), 22)
        self._test_func(F.toSecond(dt), 33)
        self._test_func(F.toMonday(d), d)
        self._test_func(F.toMonday(dt), d)
        self._test_func(F.toStartOfMonth(d), date(2018, 12, 1))
        self._test_func(F.toStartOfMonth(dt), date(2018, 12, 1))
        self._test_func(F.toStartOfQuarter(d), date(2018, 10, 1))
        self._test_func(F.toStartOfQuarter(dt), date(2018, 10, 1))
        self._test_func(F.toStartOfYear(d), date(2018, 1, 1))
        self._test_func(F.toStartOfYear(dt), date(2018, 1, 1))
        self._test_func(F.toStartOfMinute(dt), datetime(2018, 12, 31, 11, 22, 0, tzinfo=pytz.utc))
        self._test_func(F.toStartOfFiveMinute(dt), datetime(2018, 12, 31, 11, 20, 0, tzinfo=pytz.utc))
        self._test_func(F.toStartOfFifteenMinutes(dt), datetime(2018, 12, 31, 11, 15, 0, tzinfo=pytz.utc))
        self._test_func(F.toStartOfHour(dt), datetime(2018, 12, 31, 11, 0, 0, tzinfo=pytz.utc))
        self._test_func(F.toStartOfDay(dt), datetime(2018, 12, 31, 0, 0, 0, tzinfo=pytz.utc))
        self._test_func(F.toTime(dt), datetime(1970, 1, 2, 11, 22, 33, tzinfo=pytz.utc))
        self._test_func(F.toTime(dt, pytz.utc), datetime(1970, 1, 2, 11, 22, 33, tzinfo=pytz.utc))
        self._test_func(F.toTime(dt, 'Europe/Athens'), datetime(1970, 1, 2, 13, 22, 33, tzinfo=pytz.utc))
        self._test_func(F.toTime(dt, pytz.timezone('Europe/Athens')), datetime(1970, 1, 2, 13, 22, 33, tzinfo=pytz.utc))
        self._test_func(F.toRelativeYearNum(dt), 2018)
        self._test_func(F.toRelativeYearNum(dt, 'Europe/Athens'), 2018)
        self._test_func(F.toRelativeMonthNum(dt), 2018 * 12 + 12)
        self._test_func(F.toRelativeMonthNum(dt, 'Europe/Athens'), 2018 * 12 + 12)
        self._test_func(F.toRelativeWeekNum(dt), 2557)
        self._test_func(F.toRelativeWeekNum(dt, 'Europe/Athens'), 2557)
        self._test_func(F.toRelativeDayNum(dt), 17896)
        self._test_func(F.toRelativeDayNum(dt, 'Europe/Athens'), 17896)
        self._test_func(F.toRelativeHourNum(dt), 429515)
        self._test_func(F.toRelativeHourNum(dt, 'Europe/Athens'), 429515)
        self._test_func(F.toRelativeMinuteNum(dt), 25770922)
        self._test_func(F.toRelativeMinuteNum(dt, 'Europe/Athens'), 25770922)
        self._test_func(F.toRelativeSecondNum(dt), 1546255353)
        self._test_func(F.toRelativeSecondNum(dt, 'Europe/Athens'), 1546255353)
        self._test_func(F.now(), datetime.utcnow().replace(tzinfo=pytz.utc, microsecond=0))
        self._test_func(F.today(), date.today())
        self._test_func(F.yesterday(), date.today() - timedelta(days=1))
        self._test_func(F.timeSlot(dt), datetime(2018, 12, 31, 11, 0, 0, tzinfo=pytz.utc))
        self._test_func(F.timeSlots(dt, 300), [datetime(2018, 12, 31, 11, 0, 0, tzinfo=pytz.utc)])
        self._test_func(F.formatDateTime(dt, '%D %T'), '12/31/18 11:22:33')
        self._test_func(F.formatDateTime(dt, '%D %T', 'Europe/Athens'), '12/31/18 13:22:33')

    def test_type_conversion_functions(self):
        for f in (F.toUInt8, F.toUInt16, F.toUInt32, F.toUInt64, F.toInt8, F.toInt16, F.toInt32, F.toInt64, F.toFloat32, F.toFloat64):
            self._test_func(f(17), 17)
            self._test_func(f('17'), 17)
        for f in (F.toUInt8OrZero, F.toUInt16OrZero, F.toUInt32OrZero, F.toUInt64OrZero, F.toInt8OrZero, F.toInt16OrZero, F.toInt32OrZero, F.toInt64OrZero, F.toFloat32OrZero, F.toFloat64OrZero):
            self._test_func(f('17'), 17)
            self._test_func(f('a'), 0)
        for f in (F.toDecimal32, F.toDecimal64, F.toDecimal128):
            self._test_func(f(17.17, 2), Decimal('17.17'))
            self._test_func(f('17.17', 2), Decimal('17.17'))
        self._test_func(F.toDate('2018-12-31'), date(2018, 12, 31))
        self._test_func(F.toDateTime('2018-12-31 11:22:33'), datetime(2018, 12, 31, 11, 22, 33, tzinfo=pytz.utc))
        self._test_func(F.toString(123), '123')
        self._test_func(F.toFixedString('123', 5), '123')
        self._test_func(F.toStringCutToZero('123\0'), '123')
        self._test_func(F.CAST(17, 'String'), '17')

    def test_string_functions(self):
        self._test_func(F.empty(''), 1)
        self._test_func(F.empty('x'), 0)
        self._test_func(F.notEmpty(''), 0)
        self._test_func(F.notEmpty('x'), 1)
        self._test_func(F.length('x'), 1)
        self._test_func(F.lengthUTF8('x'), 1)
        self._test_func(F.lower('Ab'), 'ab')
        self._test_func(F.upper('Ab'), 'AB')
        self._test_func(F.lowerUTF8('Ab'), 'ab')
        self._test_func(F.upperUTF8('Ab'), 'AB')
        self._test_func(F.reverse('Ab'), 'bA')
        self._test_func(F.reverseUTF8('Ab'), 'bA')
        self._test_func(F.concat('Ab', 'Cd', 'Ef'), 'AbCdEf')
        self._test_func(F.substring('123456', 3, 2), '34')
        self._test_func(F.substringUTF8('123456', 3, 2), '34')
        self._test_func(F.appendTrailingCharIfAbsent('Hello', '!'), 'Hello!')
        self._test_func(F.appendTrailingCharIfAbsent('Hello!', '!'), 'Hello!')
        self._test_func(F.convertCharset(F.convertCharset('Hello', 'latin1', 'utf16'), 'utf16', 'latin1'), 'Hello')

    def test_base64_functions(self):
        try:
            self._test_func(F.base64Decode(F.base64Encode('Hello')), 'Hello')
            self._test_func(F.tryBase64Decode(F.base64Encode('Hello')), 'Hello')
            self._test_func(F.tryBase64Decode('zzz'), None)
        except ServerError as e:
            # ClickHouse version that doesn't support these functions
            raise unittest.SkipTest(e.message)
