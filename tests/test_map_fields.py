import unittest
from datetime import date

from clickhouse_orm.database import Database
from clickhouse_orm.models import Model
from clickhouse_orm.fields import MapField, DateField, StringField, Int32Field, Float64Field
from clickhouse_orm.engines import MergeTree


class TupleFieldsTest(unittest.TestCase):

    def setUp(self):
        self.database = Database('test-db', log_statements=True)
        self.database.create_table(ModelWithTuple)

    def tearDown(self):
        self.database.drop_database()

    def test_insert_and_select(self):
        instance = ModelWithTuple(
            date_field='2022-06-26',
            map1={"k1": "v1", "k2": "v2"},
            map2={"v1": 1, "v2": 2},
            map3={"f1": 1.1, "f2": 2.0},
            map4={"2022-06-25": "ok", "2022-06-26": "today"}
        )
        self.database.insert([instance])
        query = 'SELECT * from $db.modelwithtuple ORDER BY date_field'
        for model_cls in (ModelWithTuple, None):
            results = list(self.database.select(query, model_cls))
            self.assertEqual(len(results), 1)
            self.assertIn("k1", results[0].map1)
            self.assertEqual(results[0].map1["k2"], "v2")
            self.assertEqual(results[0].map2["v1"], 1)
            self.assertEqual(results[0].map3["f2"], 2.0)
            self.assertEqual(results[0].map4[date(2022, 6, 26)], "today")

    def test_conversion(self):
        instance = ModelWithTuple(
            map2="{'1': '2'}"
        )
        self.assertEqual(instance.map2['1'], 2)

    def test_assignment_error(self):
        instance = ModelWithTuple()
        for value in (7, 'x', [date.today()], ['aaa'], [None]):
            with self.assertRaises(ValueError):
                instance.map1 = value


class ModelWithTuple(Model):

    date_field = DateField()
    map1 = MapField(StringField(), StringField())
    map2 = MapField(StringField(), Int32Field())
    map3 = MapField(StringField(), Float64Field())
    map4 = MapField(DateField(), StringField())

    engine = MergeTree('date_field', ('date_field',))
