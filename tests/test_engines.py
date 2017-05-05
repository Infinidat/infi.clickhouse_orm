import unittest

from infi.clickhouse_orm.database import Database, DatabaseException
from infi.clickhouse_orm.models import Model
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
            engine = MergeTree('date', ('date', 'event_id', 'event_group'), sampling_expr='intHash32(event_id)')
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


class SampleModel(Model):

    date            = DateField()
    event_id        = UInt32Field()
    event_group     = UInt32Field()
    event_count     = UInt16Field()
    event_version   = Int8Field()
    event_uversion  = UInt8Field(materialized='abs(event_version)')
