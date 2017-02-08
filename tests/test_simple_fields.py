import unittest
from infi.clickhouse_orm.fields import *
from datetime import date, datetime
import pytz


class SimpleFieldsTest(unittest.TestCase):

    def test_date_field(self):
        f = DateField()
        # Valid values
        for value in (date(1970, 1, 1), datetime(1970, 1, 1), '1970-01-01', '0000-00-00', 0):
            self.assertEquals(f.to_python(value, pytz.utc), date(1970, 1, 1))
        # Invalid values
        for value in ('nope', '21/7/1999', 0.5):
            with self.assertRaises(ValueError):
                f.to_python(value, pytz.utc)
        # Range check
        for value in (date(1900, 1, 1), date(2900, 1, 1)):
            with self.assertRaises(ValueError):
                f.validate(value)

    def test_datetime_field(self):
        f = DateTimeField()
        epoch = datetime(1970, 1, 1, tzinfo=pytz.utc)
        # Valid values
        for value in (date(1970, 1, 1), datetime(1970, 1, 1), epoch, 
                      epoch.astimezone(pytz.timezone('US/Eastern')), epoch.astimezone(pytz.timezone('Asia/Jerusalem')),
                      '1970-01-01 00:00:00', '0000-00-00 00:00:00', 0):
            dt = f.to_python(value, pytz.utc)
            self.assertEquals(dt.tzinfo, pytz.utc)
            self.assertEquals(dt, epoch)
            # Verify that conversion to and from db string does not change value
            dt2 = f.to_python(int(f.to_db_string(dt)), pytz.utc)
            self.assertEquals(dt, dt2)
        # Invalid values
        for value in ('nope', '21/7/1999', 0.5):
            with self.assertRaises(ValueError):
                f.to_python(value, pytz.utc)

    def test_date_field(self):
        f = DateField()
        epoch = date(1970, 1, 1)
        # Valid values
        for value in (datetime(1970, 1, 1), epoch, '1970-01-01', '0000-00-00', 0):
            d = f.to_python(value, pytz.utc)
            self.assertEquals(d, epoch)
            # Verify that conversion to and from db string does not change value
            d2 = f.to_python(f.to_db_string(d, quote=False), pytz.utc)
            self.assertEquals(d, d2)
        # Invalid values
        for value in ('nope', '21/7/1999', 0.5):
            with self.assertRaises(ValueError):
                f.to_python(value, pytz.utc)

    def test_date_field_timezone(self):
        # Verify that conversion of timezone-aware datetime is correct
        f = DateField()
        dt = datetime(2017, 10, 5, tzinfo=pytz.timezone('Asia/Jerusalem'))
        self.assertEquals(f.to_python(dt, pytz.utc), date(2017, 10, 4))

    def test_uint8_field(self):
        f = UInt8Field()
        # Valid values
        for value in (17, '17', 17.0):
            self.assertEquals(f.to_python(value, pytz.utc), 17)
        # Invalid values
        for value in ('nope', date.today()):
            with self.assertRaises(ValueError):
                f.to_python(value, pytz.utc)
        # Range check
        for value in (-1, 1000):
            with self.assertRaises(ValueError):
                f.validate(value)