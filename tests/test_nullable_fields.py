from __future__ import unicode_literals
import unittest
import pytz

from infi.clickhouse_orm.database import Database
from infi.clickhouse_orm.models import Model
from infi.clickhouse_orm.fields import *
from infi.clickhouse_orm.engines import *

from datetime import date, datetime


class NullableFieldsTest(unittest.TestCase):

    def setUp(self):
        self.database = Database('test-db')
        self.database.create_table(ModelWithNullable)

    def tearDown(self):
        self.database.drop_database()

    def test_nullable_datetime_field(self):
        f = NullableField(DateTimeField())
        epoch = datetime(1970, 1, 1, tzinfo=pytz.utc)
        # Valid values
        for value in (date(1970, 1, 1),
                      datetime(1970, 1, 1),
                      epoch,
                      epoch.astimezone(pytz.timezone('US/Eastern')),
                      epoch.astimezone(pytz.timezone('Asia/Jerusalem')),
                      '1970-01-01 00:00:00',
                      '1970-01-17 00:00:17',
                      '0000-00-00 00:00:00',
                      0,
                      '\\N'):
            dt = f.to_python(value, pytz.utc)
            if value == '\\N':
                self.assertIsNone(dt)
            else:
                self.assertEqual(dt.tzinfo, pytz.utc)
            # Verify that conversion to and from db string does not change value
            dt2 = f.to_python(f.to_db_string(dt, quote=False), pytz.utc)
            self.assertEqual(dt, dt2)
        # Invalid values
        for value in ('nope', '21/7/1999', 0.5):
            with self.assertRaises(ValueError):
                f.to_python(value, pytz.utc)

    def test_nullable_uint8_field(self):
        f = NullableField(UInt8Field())
        # Valid values
        for value in (17, '17', 17.0, '\\N'):
            python_value = f.to_python(value, pytz.utc)
            if value == '\\N':
                self.assertIsNone(python_value)
                self.assertEqual(value, f.to_db_string(python_value))
            else:
                self.assertEqual(python_value, 17)

        # Invalid values
        for value in ('nope', date.today()):
            with self.assertRaises(ValueError):
                f.to_python(value, pytz.utc)

    def test_nullable_string_field(self):
        f = NullableField(StringField())
        # Valid values
        for value in ('\\\\N', 'N', 'some text', '\\N'):
            python_value = f.to_python(value, pytz.utc)
            if value == '\\N':
                self.assertIsNone(python_value)
                self.assertEqual(value, f.to_db_string(python_value))
            else:
                self.assertEqual(python_value, value)

    def test_isinstance(self):
        for field in (StringField, UInt8Field, Float32Field, DateTimeField):
            f = NullableField(field())
            self.assertTrue(f.isinstance(field))
            self.assertTrue(f.isinstance(NullableField))
        for field in (Int8Field, Int16Field, Int32Field, Int64Field, UInt8Field, UInt16Field, UInt32Field, UInt64Field):
            f = NullableField(field())
            self.assertTrue(f.isinstance(BaseIntField))
        for field in (Float32Field, Float64Field):
            f = NullableField(field())
            self.assertTrue(f.isinstance(BaseFloatField))
        f = NullableField(NullableField(UInt32Field()))
        self.assertTrue(f.isinstance(BaseIntField))
        self.assertTrue(f.isinstance(NullableField))
        self.assertFalse(f.isinstance(BaseFloatField))

    def _insert_sample_data(self):
        dt = date(1970, 1, 1)
        self.database.insert([
            ModelWithNullable(date_field='2016-08-30', null_str='', null_int=42, null_date=dt),
            ModelWithNullable(date_field='2016-08-30', null_str='nothing', null_int=None, null_date=None),
            ModelWithNullable(date_field='2016-08-31', null_str=None, null_int=42, null_date=dt),
            ModelWithNullable(date_field='2016-08-31', null_str=None, null_int=None, null_date=None)
        ])

    def _assert_sample_data(self, results):
        dt = date(1970, 1, 1)
        self.assertEqual(len(results), 4)
        self.assertIsNone(results[0].null_str)
        self.assertEqual(results[0].null_int, 42)
        self.assertEqual(results[0].null_date, dt)
        self.assertIsNone(results[1].null_date)
        self.assertEqual(results[1].null_str, 'nothing')
        self.assertIsNone(results[1].null_date)
        self.assertIsNone(results[2].null_str)
        self.assertEqual(results[2].null_date, dt)
        self.assertEqual(results[2].null_int, 42)
        self.assertIsNone(results[3].null_int)
        self.assertIsNone(results[3].null_str)
        self.assertIsNone(results[3].null_date)

    def test_insert_and_select(self):
        self._insert_sample_data()
        query = 'SELECT * from $table ORDER BY date_field'
        results = list(self.database.select(query, ModelWithNullable))
        self._assert_sample_data(results)

    def test_ad_hoc_model(self):
        self._insert_sample_data()
        query = 'SELECT * from $db.modelwithnullable ORDER BY date_field'
        results = list(self.database.select(query))
        self._assert_sample_data(results)


class ModelWithNullable(Model):

    date_field = DateField()
    null_str = NullableField(StringField(), extra_null_values={''})
    null_int = NullableField(Int32Field())
    null_date = NullableField(DateField())

    engine = MergeTree('date_field', ('date_field',))
