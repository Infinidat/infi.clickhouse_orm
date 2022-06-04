import unittest
from datetime import date

import os

from clickhouse_orm.database import Database, DatabaseException, ServerError
from clickhouse_orm.engines import Memory, MergeTree
from clickhouse_orm.fields import UUIDField, DateField
from clickhouse_orm.models import TemporaryModel, Model
from clickhouse_orm.session import in_session


class TemporaryTest(unittest.TestCase):

    def setUp(self):
        self.database = Database('test-db', log_statements=True)

    def tearDown(self):
        self.database.drop_database()

    def test_create_table(self):
        with self.assertRaises(ServerError):
            self.database.create_table(TemporaryTable)
        with self.assertRaises(AssertionError):
            self.database.create_table(TemporaryTable2)
        with in_session():
            self.database.create_table(TemporaryTable)
            count = TemporaryTable.objects_in(self.database).count()
            self.assertEqual(count, 0)
        # Check if temporary table is cleaned up
        with self.assertRaises(ServerError):
            TemporaryTable.objects_in(self.database).count()


class TemporaryTable(TemporaryModel):
    date_field = DateField()
    uuid = UUIDField()

    engine = Memory()


class TemporaryTable2(TemporaryModel):
    date_field = DateField()
    uuid = UUIDField()

    engine = MergeTree('date_field', ('date_field',))
