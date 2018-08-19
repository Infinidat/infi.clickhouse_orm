from __future__ import unicode_literals
import unittest

from infi.clickhouse_orm.database import Database
from infi.clickhouse_orm.models import Model
from infi.clickhouse_orm.fields import *
from infi.clickhouse_orm.engines import *


class DateFieldsTest(unittest.TestCase):

    def setUp(self):
        self.database = Database('test-db')
        self.database.create_table(ModelWithDate)

    def tearDown(self):
        self.database.drop_database()

    def test_ad_hoc_model(self):
        self.database.insert([
            ModelWithDate(date_field='2016-08-30', datetime_field='2016-08-30 03:50:00'),
            ModelWithDate(date_field='2016-08-31', datetime_field='2016-08-31 01:30:00')
        ])

        # toStartOfHour returns DateTime('Asia/Yekaterinburg') in my case, so I test it here to
        query = 'SELECT toStartOfHour(datetime_field) as hour_start, * from $db.modelwithdate ORDER BY date_field'
        results = list(self.database.select(query))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].date_field, datetime.date(2016, 8, 30))
        self.assertEqual(results[0].datetime_field, datetime.datetime(2016, 8, 30, 3, 50, 0, tzinfo=pytz.UTC))
        self.assertEqual(results[0].hour_start, datetime.datetime(2016, 8, 30, 3, 0, 0, tzinfo=pytz.UTC))
        self.assertEqual(results[1].date_field, datetime.date(2016, 8, 31))
        self.assertEqual(results[1].datetime_field, datetime.datetime(2016, 8, 31, 1, 30, 0, tzinfo=pytz.UTC))
        self.assertEqual(results[1].hour_start, datetime.datetime(2016, 8, 31, 1, 0, 0, tzinfo=pytz.UTC))


class ModelWithDate(Model):

    date_field = DateField()
    datetime_field = DateTimeField()

    engine = MergeTree('date_field', ('date_field',))
