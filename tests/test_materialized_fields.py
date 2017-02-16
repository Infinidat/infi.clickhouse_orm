import unittest
from datetime import date

from infi.clickhouse_orm.database import Database
from infi.clickhouse_orm.models import Model
from infi.clickhouse_orm.fields import *
from infi.clickhouse_orm.engines import *


class MaterializedFieldsTest(unittest.TestCase):

    def setUp(self):
        self.database = Database('test-db')
        self.database.create_table(ModelWithMaterializedFields)

    def tearDown(self):
        self.database.drop_database()

    def test_insert_and_select(self):
        instance = ModelWithMaterializedFields(
            date_time_field='2016-08-30 11:00:00',
            int_field=-10,
            str_field='TEST'
        )
        self.database.insert([instance])
        # We can't select * from table, as it doesn't select materialized and alias fields
        query = 'SELECT date_time_field, int_field, str_field, mat_int, mat_date, mat_str' \
                ' FROM $db.%s ORDER BY mat_date' % ModelWithMaterializedFields.table_name()
        for model_cls in (ModelWithMaterializedFields, None):
            results = list(self.database.select(query, model_cls))
            self.assertEquals(len(results), 1)
            self.assertEquals(results[0].date_time_field, instance.date_time_field)
            self.assertEquals(results[0].int_field, instance.int_field)
            self.assertEquals(results[0].str_field, instance.str_field)
            self.assertEquals(results[0].mat_int, abs(instance.int_field))
            self.assertEquals(results[0].mat_str, instance.str_field.lower())
            self.assertEquals(results[0].mat_date, instance.date_time_field.date())

    def test_assignment_error(self):
        # I can't prevent assigning at all, in case db.select statements with model provided sets model fields.
        instance = ModelWithMaterializedFields()
        for value in ('x', [date.today()], ['aaa'], [None]):
            with self.assertRaises(ValueError):
                instance.mat_date = value

    def test_wrong_field(self):
        with self.assertRaises(AssertionError):
            StringField(materialized=123)

    def test_duplicate_default(self):
        with self.assertRaises(AssertionError):
            StringField(materialized='str_field', default='with default')

        with self.assertRaises(AssertionError):
            StringField(materialized='str_field', alias='str_field')


class ModelWithMaterializedFields(Model):
    int_field = Int32Field()
    date_time_field = DateTimeField()
    str_field = StringField()

    mat_str = StringField(materialized='lower(str_field)')
    mat_int = Int32Field(materialized='abs(int_field)')
    mat_date = DateField(materialized='toDate(date_time_field)')

    engine = MergeTree('mat_date', ('mat_date',))


