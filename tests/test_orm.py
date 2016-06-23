import unittest

from infi.clickhouse_utils.database import Database
from infi.clickhouse_utils.models import Model
from infi.clickhouse_utils.fields import *
from infi.clickhouse_utils.engines import *


class ORMTestCase(unittest.TestCase):

    def setUp(self):
        self.database = Database('test_db')

    def tearDown(self):
        self.database.drop_database()

    def test_create_table(self):
        self.database.create_table(Person)
        self.database.drop_table(Person)


class Person(Model):

    first_name = StringField()
    last_name = StringField()
    birthday = DateField()
    height = Float32Field()

    engine = MergeTree('birthday', ('first_name', 'last_name', 'birthday'))



