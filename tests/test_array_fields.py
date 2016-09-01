import unittest
from datetime import date

from infi.clickhouse_orm.database import Database
from infi.clickhouse_orm.models import Model
from infi.clickhouse_orm.fields import *
from infi.clickhouse_orm.engines import *


class ArrayFieldsTest(unittest.TestCase):

    def setUp(self):
        self.database = Database('test-db')
        self.database.create_table(ModelWithArrays)

    def tearDown(self):
        self.database.drop_database()

    def test_insert_and_select(self):
        instance = ModelWithArrays(
            date_field='2016-08-30', 
            arr_str=['goodbye,', 'cruel', 'world', 'special chars: ,"\\\'` \n\t\\[]'], 
            arr_date=['2010-01-01']
        )
        self.database.insert([instance])
        query = 'SELECT * from $db.modelwitharrays ORDER BY date_field'
        for model_cls in (ModelWithArrays, None):
            results = list(self.database.select(query, model_cls))
            self.assertEquals(len(results), 1)
            self.assertEquals(results[0].arr_str, instance.arr_str)
            self.assertEquals(results[0].arr_int, instance.arr_int)
            self.assertEquals(results[0].arr_date, instance.arr_date)

    def test_conversion(self):
        instance = ModelWithArrays(
            arr_int=('1', '2', '3'),
            arr_date=['2010-01-01']
        )
        self.assertEquals(instance.arr_str, [])
        self.assertEquals(instance.arr_int, [1, 2, 3])
        self.assertEquals(instance.arr_date, [date(2010, 1, 1)])

    def test_assignment_error(self):
        instance = ModelWithArrays()
        for value in (7, 'x', [date.today()], ['aaa'], [None]):
            with self.assertRaises(ValueError):
                instance.arr_int = value


class ModelWithArrays(Model):

    date_field = DateField()
    arr_str = ArrayField(StringField())
    arr_int = ArrayField(Int32Field())
    arr_date = ArrayField(DateField())

    engine = MergeTree('date_field', ('date_field',))

