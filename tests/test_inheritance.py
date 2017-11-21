from __future__ import unicode_literals
import unittest
import datetime
import pytz

from infi.clickhouse_orm.models import Model
from infi.clickhouse_orm.fields import *
from infi.clickhouse_orm.engines import *


class InheritanceTestCase(unittest.TestCase):

    def assertFieldNames(self, model_class, names):
        self.assertEquals(names, list(model_class.fields()))

    def test_field_inheritance(self):
        self.assertFieldNames(ParentModel, ['date_field', 'int_field'])
        self.assertFieldNames(Model1, ['date_field', 'int_field', 'string_field'])
        self.assertFieldNames(Model2, ['date_field', 'int_field', 'float_field'])

    def test_create_table_sql(self):
        sql1 = ParentModel.create_table_sql('default')
        sql2 = Model1.create_table_sql('default')
        sql3 = Model2.create_table_sql('default')
        self.assertNotEqual(sql1, sql2)
        self.assertNotEqual(sql1, sql3)
        self.assertNotEqual(sql2, sql3)

    def test_get_field(self):
        self.assertIsNotNone(ParentModel().get_field('date_field'))
        self.assertIsNone(ParentModel().get_field('string_field'))
        self.assertIsNotNone(Model1().get_field('date_field'))
        self.assertIsNotNone(Model1().get_field('string_field'))
        self.assertIsNone(Model1().get_field('float_field'))


class ParentModel(Model):

    date_field = DateField()
    int_field = Int32Field()

    engine = MergeTree('date_field', ('int_field', 'date_field'))


class Model1(ParentModel):

    string_field = StringField()


class Model2(ParentModel):

    float_field = Float32Field()
