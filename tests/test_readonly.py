# -*- coding: utf-8 -*-

import unittest

from infi.clickhouse_orm.database import Database, DatabaseException
from infi.clickhouse_orm.models import Model
from infi.clickhouse_orm.fields import *
from infi.clickhouse_orm.engines import *
from .base_test_with_data import *


class ReadonlyTestCase(TestCaseWithData):

    def test_readonly(self):
        orig_database = self.database
        self.database = Database(orig_database.db_name, readonly=True)
        with self.assertRaises(DatabaseException):
            self._insert_and_check(self._sample_data(), len(data))
        self.assertEquals(self.database.count(Person), 0)
        with self.assertRaises(DatabaseException):
            self.database.drop_table(Person)
        with self.assertRaises(DatabaseException):
            self.database.drop_database()
        self.database = orig_database

    def test_insert_readonly(self):
        m = ReadOnlyModel(name='readonly')
        with self.assertRaises(DatabaseException):
            self.database.insert([m])

    def test_create_readonly_table(self):
        with self.assertRaises(DatabaseException):
            self.database.create_table(ReadOnlyModel)

    def test_drop_readonly_table(self):
        with self.assertRaises(DatabaseException):
            self.database.drop_table(ReadOnlyModel)


class ReadOnlyModel(Model):
    readonly = True

    name = StringField()

