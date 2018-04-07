from __future__ import unicode_literals
import unittest

from infi.clickhouse_orm.database import Database, DatabaseException
from infi.clickhouse_orm.models import Model, MergeModel
from infi.clickhouse_orm.fields import *
from infi.clickhouse_orm.engines import *

import logging
logging.getLogger("requests").setLevel(logging.WARNING)


class EnginesTestCase(unittest.TestCase):

    def setUp(self):
        self.database = Database('test-db')

    def tearDown(self):
        self.database.drop_database()

    def _create_and_insert(self, model_class):
        self.database.create_table(model_class)
        self.database.insert([
            model_class(date='2017-01-01', event_id=23423, event_group=13, event_count=7, event_version=1)
        ])

    def test_merge_tree(self):
        class TestModel(SampleModel):
            engine = MergeTree('date', ('date', 'event_id', 'event_group'))
        self._create_and_insert(TestModel)

    def test_merge_tree_with_sampling(self):
        class TestModel(SampleModel):
            engine = MergeTree('date', ('date', 'event_id', 'event_group', 'intHash32(event_id)'), sampling_expr='intHash32(event_id)')
        self._create_and_insert(TestModel)

    def test_merge_tree_with_granularity(self):
        class TestModel(SampleModel):
            engine = MergeTree('date', ('date', 'event_id', 'event_group'), index_granularity=4096)
        self._create_and_insert(TestModel)

    def test_replicated_merge_tree(self):
        engine = MergeTree('date', ('date', 'event_id', 'event_group'), replica_table_path='/clickhouse/tables/{layer}-{shard}/hits', replica_name='{replica}')
        expected = "ReplicatedMergeTree('/clickhouse/tables/{layer}-{shard}/hits', '{replica}', date, (date, event_id, event_group), 8192)"
        self.assertEquals(engine.create_table_sql(), expected)

    def test_collapsing_merge_tree(self):
        class TestModel(SampleModel):
            engine = CollapsingMergeTree('date', ('date', 'event_id', 'event_group'), 'event_version')
        self._create_and_insert(TestModel)

    def test_summing_merge_tree(self):
        class TestModel(SampleModel):
            engine = SummingMergeTree('date', ('date', 'event_group'), ('event_count',))
        self._create_and_insert(TestModel)

    def test_replacing_merge_tree(self):
        class TestModel(SampleModel):
            engine = ReplacingMergeTree('date', ('date', 'event_id', 'event_group'), 'event_uversion')
        self._create_and_insert(TestModel)

    def test_tiny_log(self):
        class TestModel(SampleModel):
            engine = TinyLog()
        self._create_and_insert(TestModel)

    def test_log(self):
        class TestModel(SampleModel):
            engine = Log()
        self._create_and_insert(TestModel)

    def test_memory(self):
        class TestModel(SampleModel):
            engine = Memory()
        self._create_and_insert(TestModel)

    def test_merge(self):
        class TestModel1(SampleModel):
            engine = TinyLog()

        class TestModel2(SampleModel):
            engine = TinyLog()

        class TestMergeModel(MergeModel, SampleModel):
            engine = Merge('^testmodel')

        self.database.create_table(TestModel1)
        self.database.create_table(TestModel2)
        self.database.create_table(TestMergeModel)

        # Insert operations are restricted for this model type
        with self.assertRaises(DatabaseException):
            self.database.insert([
                TestMergeModel(date='2017-01-01', event_id=23423, event_group=13, event_count=7, event_version=1)
            ])

        # Testing select
        self.database.insert([
            TestModel1(date='2017-01-01', event_id=1, event_group=1, event_count=1, event_version=1)
        ])
        self.database.insert([
            TestModel2(date='2017-01-02', event_id=2, event_group=2, event_count=2, event_version=2)
        ])
        # event_uversion is materialized field. So * won't select it and it will be zero
        res = self.database.select('SELECT *, event_uversion FROM $table ORDER BY event_id', model_class=TestMergeModel)
        res = [row for row in res]
        self.assertEqual(2, len(res))
        self.assertDictEqual({
            '_table': 'testmodel1',
            'date': datetime.date(2017, 1, 1),
            'event_id': 1,
            'event_group': 1,
            'event_count': 1,
            'event_version': 1,
            'event_uversion': 1
        }, res[0].to_dict(include_readonly=True))
        self.assertDictEqual({
            '_table': 'testmodel2',
            'date': datetime.date(2017, 1, 2),
            'event_id': 2,
            'event_group': 2,
            'event_count': 2,
            'event_version': 2,
            'event_uversion': 2
        }, res[1].to_dict(include_readonly=True))


class SampleModel(Model):

    date            = DateField()
    event_id        = UInt32Field()
    event_group     = UInt32Field()
    event_count     = UInt16Field()
    event_version   = Int8Field()
    event_uversion  = UInt8Field(materialized='abs(event_version)')
