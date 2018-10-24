# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import unittest

from infi.clickhouse_orm.database import ServerError, DatabaseException
from .base_test_with_data import *


class DatabaseTestCase(TestCaseWithData):

    def test_insert__generator(self):
        self._insert_and_check(self._sample_data(), len(data))

    def test_insert__list(self):
        self._insert_and_check(list(self._sample_data()), len(data))

    def test_insert__iterator(self):
        self._insert_and_check(iter(self._sample_data()), len(data))

    def test_insert__empty(self):
        self._insert_and_check([], 0)

    def test_insert__small_batches(self):
        self._insert_and_check(self._sample_data(), len(data), batch_size=10)

    def test_insert__medium_batches(self):
        self._insert_and_check(self._sample_data(), len(data), batch_size=100)

    def test_count(self):
        self.database.insert(self._sample_data())
        self.assertEqual(self.database.count(Person), 100)
        self.assertEqual(self.database.count(Person, "first_name = 'Courtney'"), 2)
        self.assertEqual(self.database.count(Person, "birthday > '2000-01-01'"), 22)
        self.assertEqual(self.database.count(Person, "birthday < '1970-03-01'"), 0)

    def test_select(self):
        self._insert_and_check(self._sample_data(), len(data))
        query = "SELECT * FROM `test-db`.person WHERE first_name = 'Whitney' ORDER BY last_name"
        results = list(self.database.select(query, Person))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].last_name, 'Durham')
        self.assertEqual(results[0].height, 1.72)
        self.assertEqual(results[1].last_name, 'Scott')
        self.assertEqual(results[1].height, 1.70)
        self.assertEqual(results[0].get_database(), self.database)
        self.assertEqual(results[1].get_database(), self.database)

    def test_dollar_in_select(self):
        query = "SELECT * FROM $table WHERE first_name = '$utm_source'"
        list(self.database.select(query, Person))

    def test_select_partial_fields(self):
        self._insert_and_check(self._sample_data(), len(data))
        query = "SELECT first_name, last_name FROM `test-db`.person WHERE first_name = 'Whitney' ORDER BY last_name"
        results = list(self.database.select(query, Person))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].last_name, 'Durham')
        self.assertEqual(results[0].height, 0) # default value
        self.assertEqual(results[1].last_name, 'Scott')
        self.assertEqual(results[1].height, 0) # default value
        self.assertEqual(results[0].get_database(), self.database)
        self.assertEqual(results[1].get_database(), self.database)

    def test_select_ad_hoc_model(self):
        self._insert_and_check(self._sample_data(), len(data))
        query = "SELECT * FROM `test-db`.person WHERE first_name = 'Whitney' ORDER BY last_name"
        results = list(self.database.select(query))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].__class__.__name__, 'AdHocModel')
        self.assertEqual(results[0].last_name, 'Durham')
        self.assertEqual(results[0].height, 1.72)
        self.assertEqual(results[1].last_name, 'Scott')
        self.assertEqual(results[1].height, 1.70)
        self.assertEqual(results[0].get_database(), self.database)
        self.assertEqual(results[1].get_database(), self.database)

    def test_select_with_totals(self):
        self._insert_and_check(self._sample_data(), len(data))
        query = "SELECT last_name, sum(height) as height FROM `test-db`.person GROUP BY last_name WITH TOTALS"
        results = list(self.database.select(query))
        total = sum(r.height for r in results[:-1])
        # Last line has an empty last name, and total of all heights
        self.assertFalse(results[-1].last_name)
        self.assertEqual(total, results[-1].height)

    def test_pagination(self):
        self._insert_and_check(self._sample_data(), len(data))
        # Try different page sizes
        for page_size in (1, 2, 7, 10, 30, 100, 150):
            # Iterate over pages and collect all intances
            page_num = 1
            instances = set()
            while True:
                page = self.database.paginate(Person, 'first_name, last_name', page_num, page_size)
                self.assertEqual(page.number_of_objects, len(data))
                self.assertGreater(page.pages_total, 0)
                [instances.add(obj.to_tsv()) for obj in page.objects]
                if page.pages_total == page_num:
                    break
                page_num += 1
            # Verify that all instances were returned
            self.assertEqual(len(instances), len(data))

    def test_pagination_last_page(self):
        self._insert_and_check(self._sample_data(), len(data))
        # Try different page sizes
        for page_size in (1, 2, 7, 10, 30, 100, 150):
            # Ask for the last page in two different ways and verify equality
            page_a = self.database.paginate(Person, 'first_name, last_name', -1, page_size)
            page_b = self.database.paginate(Person, 'first_name, last_name', page_a.pages_total, page_size)
            self.assertEqual(page_a[1:], page_b[1:])
            self.assertEqual([obj.to_tsv() for obj in page_a.objects],
                              [obj.to_tsv() for obj in page_b.objects])

    def test_pagination_invalid_page(self):
        self._insert_and_check(self._sample_data(), len(data))
        for page_num in (0, -2, -100):
            with self.assertRaises(ValueError):
                self.database.paginate(Person, 'first_name, last_name', page_num, 100)

    def test_pagination_with_conditions(self):
        self._insert_and_check(self._sample_data(), len(data))
        page = self.database.paginate(Person, 'first_name, last_name', 1, 100, conditions="first_name < 'Ava'")
        self.assertEqual(page.number_of_objects, 10)

    def test_special_chars(self):
        s = u'אבגד \\\'"`,.;éåäöšž\n\t\0\b\r'
        p = Person(first_name=s)
        self.database.insert([p])
        p = list(self.database.select("SELECT * from $table", Person))[0]
        self.assertEqual(p.first_name, s)

    def test_raw(self):
        self._insert_and_check(self._sample_data(), len(data))
        query = "SELECT * FROM `test-db`.person WHERE first_name = 'Whitney' ORDER BY last_name"
        results = self.database.raw(query)
        self.assertEqual(results, "Whitney\tDurham\t1977-09-15\t1.72\t\\N\nWhitney\tScott\t1971-07-04\t1.7\t\\N\n")

    def test_invalid_user(self):
        with self.assertRaises(ServerError) as cm:
            Database(self.database.db_name, username='default', password='wrong')

        exc = cm.exception
        self.assertEqual(exc.code, 193)
        self.assertEqual(exc.message, 'Wrong password for user default')

    def test_nonexisting_db(self):
        db = Database('db_not_here', autocreate=False)
        with self.assertRaises(ServerError) as cm:
            db.create_table(Person)
        exc = cm.exception
        self.assertEqual(exc.code, 81)
        self.assertEqual(exc.message, "Database db_not_here doesn't exist")
        # Now create the database - should succeed
        db.create_database()
        db.create_table(Person)
        db.drop_database()

    def test_preexisting_db(self):
        db = Database(self.database.db_name, autocreate=False)
        db.count(Person)

    def test_missing_engine(self):
        class EnginelessModel(Model):
            float_field = Float32Field()
        with self.assertRaises(DatabaseException) as cm:
            self.database.create_table(EnginelessModel)
        self.assertEqual(str(cm.exception), 'EnginelessModel class must define an engine')

    def test_potentially_problematic_field_names(self):
        class Model1(Model):
            system = StringField()
            readonly = StringField()
            engine = Memory()
        instance = Model1(system='s', readonly='r')
        self.assertEqual(instance.to_dict(), dict(system='s', readonly='r'))
        self.database.create_table(Model1)
        self.database.insert([instance])
        instance = Model1.objects_in(self.database)[0]
        self.assertEqual(instance.to_dict(), dict(system='s', readonly='r'))

    def test_does_table_exist(self):
        class Person2(Person):
            pass
        self.assertTrue(self.database.does_table_exist(Person))
        self.assertFalse(self.database.does_table_exist(Person2))

    def test_add_setting(self):
        # Non-string setting name should not be accepted
        with self.assertRaises(AssertionError):
            self.database.add_setting(0, 1)
        # Add a setting and see that it makes the query fail
        self.database.add_setting('max_columns_to_read', 1)
        with self.assertRaises(ServerError):
            list(self.database.select('SELECT * from system.tables'))
        # Remove the setting and see that now it works
        self.database.add_setting('max_columns_to_read', None)
        list(self.database.select('SELECT * from system.tables'))
