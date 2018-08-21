from __future__ import unicode_literals
import unittest

from infi.clickhouse_orm.database import Database
from infi.clickhouse_orm.models import Model, BufferModel
from infi.clickhouse_orm.fields import *
from infi.clickhouse_orm.engines import *
from infi.clickhouse_orm.migrations import MigrationHistory

# Add tests to path so that migrations will be importable
import sys, os
sys.path.append(os.path.dirname(__file__))

try:
    Enum # exists in Python 3.4+
except NameError:
    from enum import Enum # use the enum34 library instead

import logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logging.getLogger("requests").setLevel(logging.WARNING)


class MigrationsTestCase(unittest.TestCase):

    def setUp(self):
        self.database = Database('test-db')
        self.database.drop_table(MigrationHistory)

    def tearDown(self):
        self.database.drop_database()

    def tableExists(self, model_class):
        query = "EXISTS TABLE $db.`%s`" % model_class.table_name()
        return next(self.database.select(query)).result == 1

    def getTableFields(self, model_class):
        query = "DESC `%s`.`%s`" % (self.database.db_name, model_class.table_name())
        return [(row.name, row.type) for row in self.database.select(query)]

    def test_migrations(self):
        # Creation and deletion of table
        self.database.migrate('tests.sample_migrations', 1)
        self.assertTrue(self.tableExists(Model1))
        self.database.migrate('tests.sample_migrations', 2)
        self.assertFalse(self.tableExists(Model1))
        self.database.migrate('tests.sample_migrations', 3)
        self.assertTrue(self.tableExists(Model1))
        # Adding, removing and altering simple fields
        self.assertEqual(self.getTableFields(Model1), [('date', 'Date'), ('f1', 'Int32'), ('f2', 'String')])
        self.database.migrate('tests.sample_migrations', 4)
        self.assertEqual(self.getTableFields(Model2), [('date', 'Date'), ('f1', 'Int32'), ('f3', 'Float32'), ('f2', 'String'), ('f4', 'String'), ('f5', 'Array(UInt64)')])
        self.database.migrate('tests.sample_migrations', 5)
        self.assertEqual(self.getTableFields(Model3), [('date', 'Date'), ('f1', 'Int64'), ('f3', 'Float64'), ('f4', 'String')])
        # Altering enum fields
        self.database.migrate('tests.sample_migrations', 6)
        self.assertTrue(self.tableExists(EnumModel1))
        self.assertEqual(self.getTableFields(EnumModel1),
                          [('date', 'Date'), ('f1', "Enum8('dog' = 1, 'cat' = 2, 'cow' = 3)")])
        self.database.migrate('tests.sample_migrations', 7)
        self.assertTrue(self.tableExists(EnumModel1))
        self.assertEqual(self.getTableFields(EnumModel2),
                          [('date', 'Date'), ('f1', "Enum16('dog' = 1, 'cat' = 2, 'horse' = 3, 'pig' = 4)")])
        # Materialized fields and alias fields
        self.database.migrate('tests.sample_migrations', 8)
        self.assertTrue(self.tableExists(MaterializedModel))
        self.assertEqual(self.getTableFields(MaterializedModel),
                          [('date_time', "DateTime"), ('date', 'Date')])
        self.database.migrate('tests.sample_migrations', 9)
        self.assertTrue(self.tableExists(AliasModel))
        self.assertEqual(self.getTableFields(AliasModel),
                          [('date', 'Date'), ('date_alias', "Date")])
        # Buffer models creation and alteration
        self.database.migrate('tests.sample_migrations', 10)
        self.assertTrue(self.tableExists(Model4))
        self.assertTrue(self.tableExists(Model4Buffer))
        self.assertEqual(self.getTableFields(Model4), [('date', 'Date'), ('f1', 'Int32'), ('f2', 'String')])
        self.assertEqual(self.getTableFields(Model4Buffer), [('date', 'Date'), ('f1', 'Int32'), ('f2', 'String')])
        self.database.migrate('tests.sample_migrations', 11)
        self.assertEqual(self.getTableFields(Model4), [('date', 'Date'), ('f3', 'DateTime'), ('f2', 'String')])
        self.assertEqual(self.getTableFields(Model4Buffer), [('date', 'Date'), ('f3', 'DateTime'), ('f2', 'String')])

        self.database.migrate('tests.sample_migrations', 12)
        self.assertEqual(self.database.count(Model3), 3)
        data = [item.f1 for item in self.database.select('SELECT f1 FROM $table ORDER BY f1', model_class=Model3)]
        self.assertListEqual(data, [1, 2, 3])

        self.database.migrate('tests.sample_migrations', 13)
        self.assertEqual(self.database.count(Model3), 4)
        data = [item.f1 for item in self.database.select('SELECT f1 FROM $table ORDER BY f1', model_class=Model3)]
        self.assertListEqual(data, [1, 2, 3, 4])

        self.database.migrate('tests.sample_migrations', 14)
        self.assertTrue(self.tableExists(MaterializedModel1))
        self.assertEqual(self.getTableFields(MaterializedModel1),
                          [('date_time', "DateTime"), ('int_field', 'Int8'), ('date', 'Date')])
        self.assertTrue(self.tableExists(AliasModel1))
        self.assertEqual(self.getTableFields(AliasModel1),
                          [('date', 'Date'), ('int_field', 'Int8'), ('date_alias', "Date")])


# Several different models with the same table name, to simulate a table that changes over time

class Model1(Model):

    date = DateField()
    f1 = Int32Field()
    f2 = StringField()

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'mig'


class Model2(Model):

    date = DateField()
    f1 = Int32Field()
    f3 = Float32Field()
    f2 = StringField()
    f4 = StringField()
    f5 = ArrayField(UInt64Field()) # addition of an array field

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'mig'


class Model3(Model):

    date = DateField()
    f1 = Int64Field() # changed from Int32
    f3 = Float64Field() # changed from Float32
    f4 = StringField()

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'mig'


class EnumModel1(Model):

    date = DateField()
    f1 = Enum8Field(Enum('SomeEnum1', 'dog cat cow'))

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'enum_mig'


class EnumModel2(Model):

    date = DateField()
    f1 = Enum16Field(Enum('SomeEnum2', 'dog cat horse pig')) # changed type and values

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'enum_mig'


class MaterializedModel(Model):
    date_time = DateTimeField()
    date = DateField(materialized='toDate(date_time)')

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'materalized_date'


class MaterializedModel1(Model):
    date_time = DateTimeField()
    date = DateField(materialized='toDate(date_time)')
    int_field = Int8Field()

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'materalized_date'


class AliasModel(Model):
    date = DateField()
    date_alias = DateField(alias='date')

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'alias_date'


class AliasModel1(Model):
    date = DateField()
    date_alias = DateField(alias='date')
    int_field = Int8Field()

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'alias_date'


class Model4(Model):

    date = DateField()
    f1 = Int32Field()
    f2 = StringField()

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'model4'


class Model4Buffer(BufferModel, Model4):

    engine = Buffer(Model4)

    @classmethod
    def table_name(cls):
        return 'model4buffer'


class Model4_changed(Model):

    date = DateField()
    f3 = DateTimeField()
    f2 = StringField()

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'model4'


class Model4Buffer_changed(BufferModel, Model4_changed):

    engine = Buffer(Model4_changed)

    @classmethod
    def table_name(cls):
        return 'model4buffer'
