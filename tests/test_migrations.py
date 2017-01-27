import unittest

from infi.clickhouse_orm.database import Database
from infi.clickhouse_orm.models import Model
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
        self.assertEquals(self.getTableFields(Model1), [('date', 'Date'), ('f1', 'Int32'), ('f2', 'String')])
        self.database.migrate('tests.sample_migrations', 4)
        self.assertEquals(self.getTableFields(Model2), [('date', 'Date'), ('f1', 'Int32'), ('f3', 'Float32'), ('f2', 'String'), ('f4', 'String')])
        self.database.migrate('tests.sample_migrations', 5)
        self.assertEquals(self.getTableFields(Model3), [('date', 'Date'), ('f1', 'Int64'), ('f3', 'Float64'), ('f4', 'String')])
        # Altering enum fields
        self.database.migrate('tests.sample_migrations', 6)
        self.assertTrue(self.tableExists(EnumModel1))
        self.assertEquals(self.getTableFields(EnumModel1), 
                          [('date', 'Date'), ('f1', "Enum8('dog' = 1, 'cat' = 2, 'cow' = 3)")])
        self.database.migrate('tests.sample_migrations', 7)
        self.assertTrue(self.tableExists(EnumModel1))
        self.assertEquals(self.getTableFields(EnumModel2), 
                          [('date', 'Date'), ('f1', "Enum16('dog' = 1, 'cat' = 2, 'horse' = 3, 'pig' = 4)")])
        self.database.migrate('tests.sample_migrations', 8)
        self.assertTrue(self.tableExists(MaterializedModel))
        self.assertEquals(self.getTableFields(MaterializedModel),
                          [('date_time', "DateTime"), ('date', 'Date')])
        self.database.migrate('tests.sample_migrations', 9)
        self.assertTrue(self.tableExists(AliasModel))
        self.assertEquals(self.getTableFields(AliasModel),
                          [('date', 'Date'), ('date_alias', "Date")])


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


class AliasModel(Model):
    date = DateField()
    date_alias = DateField(alias='date')

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'alias_date'