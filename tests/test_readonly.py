# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from infi.clickhouse_orm.database import DatabaseException, ServerError
from .base_test_with_data import *


class ReadonlyTestCase(TestCaseWithData):

    def _test_readonly_db(self, username):
        self._insert_and_check(self._sample_data(), len(data))
        orig_database = self.database
        try:
            self.database = Database(orig_database.db_name, username=username, readonly=True)
            with self.assertRaises(ServerError) as cm:
                self._insert_and_check(self._sample_data(), len(data))
            self._check_db_readonly_err(cm.exception)

            self.assertEquals(self.database.count(Person), 100)
            list(self.database.select('SELECT * from $table', Person))
            with self.assertRaises(ServerError) as cm:
                self.database.drop_table(Person)
            self._check_db_readonly_err(cm.exception, drop_table=True)

            with self.assertRaises(ServerError) as cm:
                self.database.drop_database()
            self._check_db_readonly_err(cm.exception, drop_table=True)
        except ServerError as e:
            if e.code == 192 and e.message.startswith('Unknown user'):
                raise unittest.SkipTest('Database user "%s" is not defined' % username)
            else:
                raise
        finally:
            self.database = orig_database

    def _check_db_readonly_err(self, exc, drop_table=None):
        self.assertEqual(exc.code, 164)
        if drop_table:
            self.assertEqual(exc.message, 'Cannot drop table in readonly mode')
        else:
            self.assertEqual(exc.message, 'Cannot insert into table in readonly mode')

    def test_readonly_db_with_default_user(self):
        self._test_readonly_db('default')

    def test_readonly_db_with_readonly_user(self):
        self._test_readonly_db('readonly')

    def test_insert_readonly(self):
        m = ReadOnlyModel(name='readonly')
        with self.assertRaises(DatabaseException):
            self.database.insert([m])

    def test_create_readonly_table(self):
        self.database.create_table(ReadOnlyModel)

    def test_drop_readonly_table(self):
        self.database.drop_table(ReadOnlyModel)


class ReadOnlyModel(Model):
    readonly = True

    name = StringField()
    date = DateField()
    engine = MergeTree('date', ('name',))
