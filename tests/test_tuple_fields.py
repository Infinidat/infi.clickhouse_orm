import unittest
from datetime import date

from clickhouse_orm.database import Database
from clickhouse_orm.models import Model
from clickhouse_orm.fields import TupleField, DateField, StringField, Int32Field, ArrayField
from clickhouse_orm.engines import MergeTree


class TupleFieldsTest(unittest.TestCase):

    def setUp(self):
        self.database = Database('test-db', log_statements=True)
        self.database.create_table(ModelWithTuple)

    def tearDown(self):
        self.database.drop_database()

    def test_insert_and_select(self):
        instance = ModelWithTuple(
            date_field='2016-08-30',
            tuple_str=['goodbye,', 'cruel'],
            tuple_date=['2010-01-01', '2020-01-01'],
        )
        self.database.insert([instance])
        query = 'SELECT * from $db.modelwithtuple ORDER BY date_field'
        for model_cls in (ModelWithTuple, None):
            results = list(self.database.select(query, model_cls))
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].tuple_str, instance.tuple_str)
            self.assertEqual(results[0].tuple_int, instance.tuple_int)
            self.assertEqual(results[0].tuple_date, instance.tuple_date)

    def test_conversion(self):
        instance = ModelWithTuple(
            tuple_int=('1', '2'),
            tuple_date=['2010-01-01', '2020-01-01']
        )
        self.assertEqual(instance.tuple_str, ('', ''))
        self.assertEqual(instance.tuple_int, (1, 2))
        self.assertEqual(instance.tuple_date, (date(2010, 1, 1), date(2020, 1, 1)))

    def test_assignment_error(self):
        instance = ModelWithTuple()
        for value in (7, 'x', [date.today()], ['aaa'], [None]):
            with self.assertRaises(ValueError):
                instance.tuple_int = value

    def test_invalid_inner_field(self):
        for x in ([('a', DateField)], [('b', None)], [('c', "")], [('d', ArrayField(StringField()))]):
            with self.assertRaises(AssertionError):
                TupleField(x)


class ModelWithTuple(Model):

    date_field = DateField()
    tuple_str = TupleField([('a', StringField()), ('b', StringField())])
    tuple_int = TupleField([('a', Int32Field()), ('b', Int32Field())])
    tuple_date = TupleField([('a', DateField()), ('b', DateField())])
    tuple_mix = TupleField([('a', StringField()), ('b', Int32Field()), ('c', DateField())])

    engine = MergeTree('date_field', ('date_field',))
