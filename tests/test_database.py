# -*- coding: utf-8 -*-

import unittest

from infi.clickhouse_orm.database import Database, DatabaseException
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

    def test_count(self):
        self.database.insert(self._sample_data())
        self.assertEquals(self.database.count(Person), 100)
        self.assertEquals(self.database.count(Person, "first_name = 'Courtney'"), 2)
        self.assertEquals(self.database.count(Person, "birthday > '2000-01-01'"), 22)
        self.assertEquals(self.database.count(Person, "birthday < '1970-03-01'"), 0)

    def test_select(self):
        self._insert_and_check(self._sample_data(), len(data))
        query = "SELECT * FROM `test-db`.person WHERE first_name = 'Whitney' ORDER BY last_name"
        results = list(self.database.select(query, Person))
        self.assertEquals(len(results), 2)
        self.assertEquals(results[0].last_name, 'Durham')
        self.assertEquals(results[0].height, 1.72)
        self.assertEquals(results[1].last_name, 'Scott')
        self.assertEquals(results[1].height, 1.70)
        self.assertEqual(results[0].get_database(), self.database)
        self.assertEqual(results[1].get_database(), self.database)

    def test_select_partial_fields(self):
        self._insert_and_check(self._sample_data(), len(data))
        query = "SELECT first_name, last_name FROM `test-db`.person WHERE first_name = 'Whitney' ORDER BY last_name"
        results = list(self.database.select(query, Person))
        self.assertEquals(len(results), 2)
        self.assertEquals(results[0].last_name, 'Durham')
        self.assertEquals(results[0].height, 0) # default value
        self.assertEquals(results[1].last_name, 'Scott')
        self.assertEquals(results[1].height, 0) # default value
        self.assertEqual(results[0].get_database(), self.database)
        self.assertEqual(results[1].get_database(), self.database)

    def test_select_ad_hoc_model(self):
        self._insert_and_check(self._sample_data(), len(data))
        query = "SELECT * FROM `test-db`.person WHERE first_name = 'Whitney' ORDER BY last_name"
        results = list(self.database.select(query))
        self.assertEquals(len(results), 2)
        self.assertEquals(results[0].__class__.__name__, 'AdHocModel')
        self.assertEquals(results[0].last_name, 'Durham')
        self.assertEquals(results[0].height, 1.72)
        self.assertEquals(results[1].last_name, 'Scott')
        self.assertEquals(results[1].height, 1.70)
        self.assertEqual(results[0].get_database(), self.database)
        self.assertEqual(results[1].get_database(), self.database)

    def test_select_with_totals(self):
        self._insert_and_check(self._sample_data(), len(data))
        query = "SELECT last_name, sum(height) as height FROM `test-db`.person GROUP BY last_name WITH TOTALS"
        results = list(self.database.select(query))
        total = sum(r.height for r in results[:-1])
        # Last line has an empty last name, and total of all heights
        self.assertFalse(results[-1].last_name)
        self.assertEquals(total, results[-1].height)

    def test_pagination(self):
        self._insert_and_check(self._sample_data(), len(data))
        # Try different page sizes
        for page_size in (1, 2, 7, 10, 30, 100, 150):
            # Iterate over pages and collect all intances
            page_num = 1
            instances = set()
            while True:
                page = self.database.paginate(Person, 'first_name, last_name', page_num, page_size)
                self.assertEquals(page.number_of_objects, len(data))
                self.assertGreater(page.pages_total, 0)
                [instances.add(obj.to_tsv()) for obj in page.objects]
                if page.pages_total == page_num:
                    break
                page_num += 1
            # Verify that all instances were returned
            self.assertEquals(len(instances), len(data))

    def test_pagination_last_page(self):
        self._insert_and_check(self._sample_data(), len(data))
        # Try different page sizes
        for page_size in (1, 2, 7, 10, 30, 100, 150):
            # Ask for the last page in two different ways and verify equality
            page_a = self.database.paginate(Person, 'first_name, last_name', -1, page_size)
            page_b = self.database.paginate(Person, 'first_name, last_name', page_a.pages_total, page_size)
            self.assertEquals(page_a[1:], page_b[1:])
            self.assertEquals([obj.to_tsv() for obj in page_a.objects], 
                              [obj.to_tsv() for obj in page_b.objects])

    def test_pagination_invalid_page(self):
        self._insert_and_check(self._sample_data(), len(data))
        for page_num in (0, -2, -100):
            with self.assertRaises(ValueError):
                self.database.paginate(Person, 'first_name, last_name', page_num, 100)

    def test_pagination_with_conditions(self):
        self._insert_and_check(self._sample_data(), len(data))
        page = self.database.paginate(Person, 'first_name, last_name', 1, 100, conditions="first_name < 'Ava'")
        self.assertEquals(page.number_of_objects, 10)

    def test_special_chars(self):
        s = u'אבגד \\\'"`,.;éåäöšž\n\t\0\b\r'
        p = Person(first_name=s)
        self.database.insert([p])
        p = list(self.database.select("SELECT * from $table", Person))[0]
        self.assertEquals(p.first_name, s)

    def test_raw(self):
        self._insert_and_check(self._sample_data(), len(data))
        query = "SELECT * FROM `test-db`.person WHERE first_name = 'Whitney' ORDER BY last_name"
        results = self.database.raw(query)
        self.assertEqual(results, "Whitney\tDurham\t1977-09-15\t1.72\nWhitney\tScott\t1971-07-04\t1.7\n")

    def test_invalid_user(self):
        with self.assertRaises(DatabaseException):
            Database(self.database.db_name, username='default', password='wrong')