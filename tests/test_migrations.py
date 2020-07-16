import unittest

from infi.clickhouse_orm.database import Database, ServerError
from infi.clickhouse_orm.models import Model, BufferModel, Constraint, Index
from infi.clickhouse_orm.fields import *
from infi.clickhouse_orm.engines import *
from infi.clickhouse_orm.migrations import MigrationHistory

from enum import Enum
# Add tests to path so that migrations will be importable
import sys, os
sys.path.append(os.path.dirname(__file__))


import logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logging.getLogger("requests").setLevel(logging.WARNING)


class MigrationsTestCase(unittest.TestCase):

    def setUp(self):
        self.database = Database('test-db', log_statements=True)
        self.database.drop_table(MigrationHistory)

    def tearDown(self):
        self.database.drop_database()

    def table_exists(self, model_class):
        query = "EXISTS TABLE $db.`%s`" % model_class.table_name()
        return next(self.database.select(query)).result == 1

    def get_table_fields(self, model_class):
        query = "DESC `%s`.`%s`" % (self.database.db_name, model_class.table_name())
        return [(row.name, row.type) for row in self.database.select(query)]

    def get_table_def(self, model_class):
        return self.database.raw('SHOW CREATE TABLE $db.`%s`' % model_class.table_name())

    def test_migrations(self):
        # Creation and deletion of table
        self.database.migrate('tests.sample_migrations', 1)
        self.assertTrue(self.table_exists(Model1))
        self.database.migrate('tests.sample_migrations', 2)
        self.assertFalse(self.table_exists(Model1))
        self.database.migrate('tests.sample_migrations', 3)
        self.assertTrue(self.table_exists(Model1))
        # Adding, removing and altering simple fields
        self.assertEqual(self.get_table_fields(Model1), [('date', 'Date'), ('f1', 'Int32'), ('f2', 'String')])
        self.database.migrate('tests.sample_migrations', 4)
        self.assertEqual(self.get_table_fields(Model2), [('date', 'Date'), ('f1', 'Int32'), ('f3', 'Float32'), ('f2', 'String'), ('f4', 'String'), ('f5', 'Array(UInt64)')])
        self.database.migrate('tests.sample_migrations', 5)
        self.assertEqual(self.get_table_fields(Model3), [('date', 'Date'), ('f1', 'Int64'), ('f3', 'Float64'), ('f4', 'String')])
        # Altering enum fields
        self.database.migrate('tests.sample_migrations', 6)
        self.assertTrue(self.table_exists(EnumModel1))
        self.assertEqual(self.get_table_fields(EnumModel1),
                          [('date', 'Date'), ('f1', "Enum8('dog' = 1, 'cat' = 2, 'cow' = 3)")])
        self.database.migrate('tests.sample_migrations', 7)
        self.assertTrue(self.table_exists(EnumModel1))
        self.assertEqual(self.get_table_fields(EnumModel2),
                          [('date', 'Date'), ('f1', "Enum16('dog' = 1, 'cat' = 2, 'horse' = 3, 'pig' = 4)")])
        # Materialized fields and alias fields
        self.database.migrate('tests.sample_migrations', 8)
        self.assertTrue(self.table_exists(MaterializedModel))
        self.assertEqual(self.get_table_fields(MaterializedModel),
                          [('date_time', "DateTime"), ('date', 'Date')])
        self.database.migrate('tests.sample_migrations', 9)
        self.assertTrue(self.table_exists(AliasModel))
        self.assertEqual(self.get_table_fields(AliasModel),
                          [('date', 'Date'), ('date_alias', "Date")])
        # Buffer models creation and alteration
        self.database.migrate('tests.sample_migrations', 10)
        self.assertTrue(self.table_exists(Model4))
        self.assertTrue(self.table_exists(Model4Buffer))
        self.assertEqual(self.get_table_fields(Model4), [('date', 'Date'), ('f1', 'Int32'), ('f2', 'String')])
        self.assertEqual(self.get_table_fields(Model4Buffer), [('date', 'Date'), ('f1', 'Int32'), ('f2', 'String')])
        self.database.migrate('tests.sample_migrations', 11)
        self.assertEqual(self.get_table_fields(Model4), [('date', 'Date'), ('f3', 'DateTime'), ('f2', 'String')])
        self.assertEqual(self.get_table_fields(Model4Buffer), [('date', 'Date'), ('f3', 'DateTime'), ('f2', 'String')])

        self.database.migrate('tests.sample_migrations', 12)
        self.assertEqual(self.database.count(Model3), 3)
        data = [item.f1 for item in self.database.select('SELECT f1 FROM $table ORDER BY f1', model_class=Model3)]
        self.assertListEqual(data, [1, 2, 3])

        self.database.migrate('tests.sample_migrations', 13)
        self.assertEqual(self.database.count(Model3), 4)
        data = [item.f1 for item in self.database.select('SELECT f1 FROM $table ORDER BY f1', model_class=Model3)]
        self.assertListEqual(data, [1, 2, 3, 4])

        self.database.migrate('tests.sample_migrations', 14)
        self.assertTrue(self.table_exists(MaterializedModel1))
        self.assertEqual(self.get_table_fields(MaterializedModel1),
                          [('date_time', 'DateTime'), ('int_field', 'Int8'), ('date', 'Date'), ('int_field_plus_one', 'Int8')])
        self.assertTrue(self.table_exists(AliasModel1))
        self.assertEqual(self.get_table_fields(AliasModel1),
                          [('date', 'Date'), ('int_field', 'Int8'), ('date_alias', 'Date'), ('int_field_plus_one', 'Int8')])
        # Codecs and low cardinality
        self.database.migrate('tests.sample_migrations', 15)
        self.assertTrue(self.table_exists(Model4_compressed))
        if self.database.has_low_cardinality_support:
            self.assertEqual(self.get_table_fields(Model2LowCardinality),
                             [('date', 'Date'), ('f1', 'LowCardinality(Int32)'), ('f3', 'LowCardinality(Float32)'),
                              ('f2', 'LowCardinality(String)'), ('f4', 'LowCardinality(Nullable(String))'), ('f5', 'Array(LowCardinality(UInt64))')])
        else:
            logging.warning('No support for low cardinality')
            self.assertEqual(self.get_table_fields(Model2),
                             [('date', 'Date'), ('f1', 'Int32'), ('f3', 'Float32'), ('f2', 'String'), ('f4', 'Nullable(String)'),
                              ('f5', 'Array(UInt64)')])

        if self.database.server_version >= (19, 14, 3, 3):
            # Creating constraints
            self.database.migrate('tests.sample_migrations', 16)
            self.assertTrue(self.table_exists(ModelWithConstraints))
            self.database.insert([ModelWithConstraints(f1=101, f2='a')])
            with self.assertRaises(ServerError):
                self.database.insert([ModelWithConstraints(f1=99, f2='a')])
            with self.assertRaises(ServerError):
                self.database.insert([ModelWithConstraints(f1=101, f2='x')])
            # Modifying constraints
            self.database.migrate('tests.sample_migrations', 17)
            self.database.insert([ModelWithConstraints(f1=99, f2='a')])
            with self.assertRaises(ServerError):
                self.database.insert([ModelWithConstraints(f1=101, f2='a')])
            with self.assertRaises(ServerError):
                self.database.insert([ModelWithConstraints(f1=99, f2='x')])

        if self.database.server_version >= (20, 1, 2, 4):
            # Creating indexes
            self.database.migrate('tests.sample_migrations', 18)
            self.assertTrue(self.table_exists(ModelWithIndex))
            self.assertIn('INDEX index ', self.get_table_def(ModelWithIndex))
            self.assertIn('INDEX another_index ', self.get_table_def(ModelWithIndex))
            # Modifying indexes
            self.database.migrate('tests.sample_migrations', 19)
            self.assertNotIn('INDEX index ', self.get_table_def(ModelWithIndex))
            self.assertIn('INDEX index2 ', self.get_table_def(ModelWithIndex))
            self.assertIn('INDEX another_index ', self.get_table_def(ModelWithIndex))


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
    int_field_plus_one = Int8Field(materialized='int_field + 1')

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
    int_field_plus_one = Int8Field(alias='int_field + 1')

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


class Model4_compressed(Model):

    date = DateField()
    f3 = DateTimeField(codec='Delta,ZSTD(10)')
    f2 = StringField(codec='LZ4HC')

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'model4'


class Model2LowCardinality(Model):
    date = DateField()
    f1 = LowCardinalityField(Int32Field())
    f3 = LowCardinalityField(Float32Field())
    f2 = LowCardinalityField(StringField())
    f4 = LowCardinalityField(NullableField(StringField()))
    f5 = ArrayField(LowCardinalityField(UInt64Field()))

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'mig'


class ModelWithConstraints(Model):

    date = DateField()
    f1 = Int32Field()
    f2 = StringField()

    constraint = Constraint(f2.isIn(['a', 'b', 'c'])) # check reserved keyword as constraint name
    f1_constraint = Constraint(f1 > 100)

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'modelwithconstraints'


class ModelWithConstraints2(Model):

    date = DateField()
    f1 = Int32Field()
    f2 = StringField()

    constraint = Constraint(f2.isIn(['a', 'b', 'c']))
    f1_constraint_new = Constraint(f1 < 100)

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'modelwithconstraints'


class ModelWithIndex(Model):

    date = DateField()
    f1 = Int32Field()
    f2 = StringField()

    index = Index(f1, type=Index.minmax(), granularity=1)
    another_index = Index(f2, type=Index.set(0), granularity=1)

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'modelwithindex'


class ModelWithIndex2(Model):

    date = DateField()
    f1 = Int32Field()
    f2 = StringField()

    index2 = Index(f1, type=Index.bloom_filter(), granularity=2)
    another_index = Index(f2, type=Index.set(0), granularity=1)

    engine = MergeTree('date', ('date',))

    @classmethod
    def table_name(cls):
        return 'modelwithindex'

