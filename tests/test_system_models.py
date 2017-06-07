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

    def _get_backups(self):
        if not os.path.exists(self.BACKUP_DIR):
            return []
        _, dirnames, _ = next(os.walk(self.BACKUP_DIR))
        return dirnames

    def test_get_all(self):
        parts = SystemPart.get(self.database)
        self.assertEqual(len(list(parts)), 1)

    def test_get_active(self):
        parts = list(SystemPart.get_active(self.database))
        self.assertEqual(len(parts), 1)
        parts[0].detach()
        self.assertEqual(len(list(SystemPart.get_active(self.database))), 0)

    def test_get_conditions(self):
        parts = list(SystemPart.get(self.database, conditions="table='testtable'"))
        self.assertEqual(len(parts), 1)
        parts = list(SystemPart.get(self.database, conditions=u"table='othertable'"))
        self.assertEqual(len(parts), 0)

    def test_attach_detach(self):
        parts = list(SystemPart.get_active(self.database))
        self.assertEqual(len(parts), 1)
        parts[0].detach()
        self.assertEqual(len(list(SystemPart.get_active(self.database))), 0)
        parts[0].attach()
        self.assertEqual(len(list(SystemPart.get_active(self.database))), 1)

    def test_drop(self):
        parts = list(SystemPart.get_active(self.database))
        parts[0].drop()
        self.assertEqual(len(list(SystemPart.get_active(self.database))), 0)

    def test_freeze(self):
        parts = list(SystemPart.get(self.database))
        # There can be other backups in the folder
        prev_backups = set(self._get_backups())
        parts[0].freeze()
        backups = set(self._get_backups())
        self.assertEqual(len(backups), len(prev_backups) + 1)
        # Clean created backup
        shutil.rmtree(self.BACKUP_DIR + '{0}'.format(list(backups - prev_backups)[0]))

    def test_fetch(self):
        # TODO Not tested, as I have no replication set
        pass


class TestTable(Model):
    date_field = DateField()

    engine = MergeTree('date_field', ('date_field',))
