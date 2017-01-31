import unittest
from datetime import date

import os
import shutil
from infi.clickhouse_orm.database import Database
from infi.clickhouse_orm.engines import *
from infi.clickhouse_orm.fields import *
from infi.clickhouse_orm.models import Model
from infi.clickhouse_orm.system_models import SystemPart


class SystemPartTest(unittest.TestCase):
    BACKUP_DIR = '/opt/clickhouse/shadow/'

    def setUp(self):
        self.database = Database('test-db')
        self.database.create_table(TestTable)
        self.database.insert([TestTable(date_field=date.today())])

    def tearDown(self):
        self.database.drop_database()

    def _get_backups_count(self):
        _, dirnames, _ = next(os.walk(self.BACKUP_DIR))
        return len(dirnames)

    def test_get_all(self):
        parts = SystemPart.all(self.database)
        self.assertEqual(len(list(parts)), 1)

    def test_get_active(self):
        parts = list(SystemPart.get_active(self.database))
        self.assertEqual(len(parts), 1)
        parts[0].detach(self.database)
        self.assertEqual(len(list(SystemPart.get_active(self.database))), 0)

    def test_attach_detach(self):
        parts = list(SystemPart.get_active(self.database))
        self.assertEqual(len(parts), 1)
        parts[0].detach(self.database)
        self.assertEqual(len(list(SystemPart.get_active(self.database))), 0)
        parts[0].attach(self.database)
        self.assertEqual(len(list(SystemPart.get_active(self.database))), 1)

    def test_drop(self):
        parts = list(SystemPart.get_active(self.database))
        parts[0].drop(self.database)
        self.assertEqual(len(list(SystemPart.get_active(self.database))), 0)

    def test_freeze(self):
        parts = list(SystemPart.all(self.database))
        # There can be other backups in the folder
        backups_count = self._get_backups_count()
        parts[0].freeze(self.database)
        backup_number = self._get_backups_count()
        self.assertEqual(backup_number, backups_count + 1)
        # Clean created backup
        shutil.rmtree(self.BACKUP_DIR + '{0}'.format(backup_number))

    def test_fetch(self):
        # TODO Not tested, as I have no replication set
        pass


class TestTable(Model):
    date_field = DateField()

    engine = MergeTree('date_field', ('date_field',))
