# -*- coding: utf-8 -*-

import unittest

from infi.clickhouse_orm.database import Database
from .base_test_with_data import *
import logging
from datetime import date, datetime

try:
    Enum # exists in Python 3.4+
except NameError:
    from enum import Enum # use the enum34 library instead


class QuerySetTestCase(TestCaseWithData):

    def setUp(self):
        super(QuerySetTestCase, self).setUp()
        self.database.insert(self._sample_data())

    def _test_qs(self, qs, expected_count):
        logging.info(qs.as_sql())
        for instance in qs:
            logging.info('\t%s' % instance.to_dict())
        self.assertEquals(qs.count(), expected_count)

    def test_no_filtering(self):
        qs = Person.objects_in(self.database)
        self._test_qs(qs, len(data))

    def test_truthiness(self):
        qs = Person.objects_in(self.database)
        self.assertTrue(qs.filter(first_name='Connor'))
        self.assertFalse(qs.filter(first_name='Willy'))

    def test_filter_string_field(self):
        qs = Person.objects_in(self.database)
        self._test_qs(qs.filter(first_name='Ciaran'), 2)
        self._test_qs(qs.filter(first_name='ciaran'), 0) # case sensitive
        self._test_qs(qs.filter(first_name__iexact='ciaran'), 2) # case insensitive
        self._test_qs(qs.filter(first_name__gt='Whilemina'), 4)
        self._test_qs(qs.filter(first_name__gte='Whilemina'), 5)
        self._test_qs(qs.filter(first_name__lt='Adam'), 1)
        self._test_qs(qs.filter(first_name__lte='Adam'), 2)
        self._test_qs(qs.filter(first_name__in=('Connor', 'Courtney')), 3) # in tuple
        self._test_qs(qs.filter(first_name__in=['Connor', 'Courtney']), 3) # in list
        self._test_qs(qs.filter(first_name__in="'Connor', 'Courtney'"), 3) # in string
        self._test_qs(qs.filter(first_name__not_in="'Connor', 'Courtney'"), 97)
        self._test_qs(qs.filter(first_name__contains='sh'), 3) # case sensitive
        self._test_qs(qs.filter(first_name__icontains='sh'), 6) # case insensitive
        self._test_qs(qs.filter(first_name__startswith='le'), 0) # case sensitive
        self._test_qs(qs.filter(first_name__istartswith='Le'), 2) # case insensitive
        self._test_qs(qs.filter(first_name__istartswith=''), 100) # empty prefix
        self._test_qs(qs.filter(first_name__endswith='IA'), 0) # case sensitive
        self._test_qs(qs.filter(first_name__iendswith='ia'), 3) # case insensitive
        self._test_qs(qs.filter(first_name__iendswith=''), 100) # empty suffix

    def test_filter_unicode_string(self):
        self.database.insert([
            Person(first_name=u'דונלד', last_name=u'דאק')
        ])
        qs = Person.objects_in(self.database)
        self._test_qs(qs.filter(first_name=u'דונלד'), 1)

    def test_filter_float_field(self):
        qs = Person.objects_in(self.database)
        self._test_qs(qs.filter(height__gt=2), 0)
        self._test_qs(qs.filter(height__lt=1.61), 4)
        self._test_qs(qs.filter(height__lt='1.61'), 4)
        self._test_qs(qs.exclude(height__lt='1.61'), 96)
        self._test_qs(qs.filter(height__gt=0), 100)
        self._test_qs(qs.exclude(height__gt=0), 0)

    def test_filter_date_field(self):
        qs = Person.objects_in(self.database)
        self._test_qs(qs.filter(birthday='1970-12-02'), 1)
        self._test_qs(qs.filter(birthday__eq='1970-12-02'), 1)
        self._test_qs(qs.filter(birthday__ne='1970-12-02'), 99)
        self._test_qs(qs.filter(birthday=date(1970, 12, 2)), 1)
        self._test_qs(qs.filter(birthday__lte=date(1970, 12, 2)), 3)

    def test_only(self):
        qs = Person.objects_in(self.database).only('first_name', 'last_name')
        for person in qs:
            self.assertTrue(person.first_name)
            self.assertTrue(person.last_name)
            self.assertFalse(person.height)
            self.assertEquals(person.birthday, date(1970, 1, 1))

    def test_order_by(self):
        qs = Person.objects_in(self.database)
        self.assertFalse('ORDER BY' in qs.as_sql())
        self.assertFalse(qs.order_by_as_sql())
        person = list(qs.order_by('first_name', 'last_name'))[0]
        self.assertEquals(person.first_name, 'Abdul')
        person = list(qs.order_by('-first_name', '-last_name'))[0]
        self.assertEquals(person.first_name, 'Yolanda')
        person = list(qs.order_by('height'))[0]
        self.assertEquals(person.height, 1.59)
        person = list(qs.order_by('-height'))[0]
        self.assertEquals(person.height, 1.8)

    def test_in_subquery(self):
        qs = Person.objects_in(self.database)
        self._test_qs(qs.filter(height__in='SELECT max(height) FROM $table'), 2)
        self._test_qs(qs.filter(first_name__in=qs.only('last_name')), 2)
        self._test_qs(qs.filter(first_name__not_in=qs.only('last_name')), 98)

    def _insert_sample_model(self):
        self.database.create_table(SampleModel)
        now = datetime.now()
        self.database.insert([
            SampleModel(timestamp=now, num=1, color=Color.red),
            SampleModel(timestamp=now, num=2, color=Color.red),
            SampleModel(timestamp=now, num=3, color=Color.blue),
            SampleModel(timestamp=now, num=4, color=Color.white),
        ])

    def test_filter_enum_field(self):
        self._insert_sample_model()
        qs = SampleModel.objects_in(self.database)
        self._test_qs(qs.filter(color=Color.red), 2)
        self._test_qs(qs.exclude(color=Color.white), 3)
        # Different ways to specify blue
        self._test_qs(qs.filter(color__gt=Color.blue), 1)
        self._test_qs(qs.filter(color__gt='blue'), 1)
        self._test_qs(qs.filter(color__gt=2), 1)

    def test_filter_int_field(self):
        self._insert_sample_model()
        qs = SampleModel.objects_in(self.database)
        self._test_qs(qs.filter(num=1), 1)
        self._test_qs(qs.filter(num__eq=1), 1)
        self._test_qs(qs.filter(num__ne=1), 3)
        self._test_qs(qs.filter(num__gt=1), 3)
        self._test_qs(qs.filter(num__gte=1), 4)
        self._test_qs(qs.filter(num__in=(1, 2, 3)), 3)
        self._test_qs(qs.filter(num__in=range(1, 4)), 3)

    def test_slicing(self):
        db = Database('system')
        numbers = list(range(100))
        qs = Numbers.objects_in(db)
        self.assertEquals(qs[0].number, numbers[0])
        self.assertEquals(qs[5].number, numbers[5])
        self.assertEquals([row.number for row in qs[:1]], numbers[:1])
        self.assertEquals([row.number for row in qs[:10]], numbers[:10])
        self.assertEquals([row.number for row in qs[3:10]], numbers[3:10])
        self.assertEquals([row.number for row in qs[9:10]], numbers[9:10])
        self.assertEquals([row.number for row in qs[10:10]], numbers[10:10])

    def test_invalid_slicing(self):
        db = Database('system')
        qs = Numbers.objects_in(db)
        with self.assertRaises(AssertionError):
            qs[3:10:2]
        with self.assertRaises(AssertionError):
            qs[-5]
        with self.assertRaises(AssertionError):
            qs[:-5]
        with self.assertRaises(AssertionError):
            qs[50:1]

    def test_pagination(self):
        qs = Person.objects_in(self.database).order_by('first_name', 'last_name')
        # Try different page sizes
        for page_size in (1, 2, 7, 10, 30, 100, 150):
            # Iterate over pages and collect all intances
            page_num = 1
            instances = set()
            while True:
                page = qs.paginate(page_num, page_size)
                self.assertEquals(page.number_of_objects, len(data))
                self.assertGreater(page.pages_total, 0)
                [instances.add(obj.to_tsv()) for obj in page.objects]
                if page.pages_total == page_num:
                    break
                page_num += 1
            # Verify that all instances were returned
            self.assertEquals(len(instances), len(data))

    def test_pagination_last_page(self):
        qs = Person.objects_in(self.database).order_by('first_name', 'last_name')
        # Try different page sizes
        for page_size in (1, 2, 7, 10, 30, 100, 150):
            # Ask for the last page in two different ways and verify equality
            page_a = qs.paginate(-1, page_size)
            page_b = qs.paginate(page_a.pages_total, page_size)
            self.assertEquals(page_a[1:], page_b[1:])
            self.assertEquals([obj.to_tsv() for obj in page_a.objects],
                              [obj.to_tsv() for obj in page_b.objects])

    def test_pagination_invalid_page(self):
        qs = Person.objects_in(self.database).order_by('first_name', 'last_name')
        for page_num in (0, -2, -100):
            with self.assertRaises(ValueError):
                qs.paginate(page_num, 100)

    def test_pagination_with_conditions(self):
        qs = Person.objects_in(self.database).order_by('first_name', 'last_name').filter(first_name__lt='Ava')
        page = qs.paginate(1, 100)
        self.assertEquals(page.number_of_objects, 10)


class AggregateTestCase(TestCaseWithData):

    def setUp(self):
        super(AggregateTestCase, self).setUp()
        self.database.insert(self._sample_data())

    def test_aggregate_no_grouping(self):
        qs = Person.objects_in(self.database).aggregate(average_height='avg(height)', count='count()')
        print(qs.as_sql())
        self.assertEquals(qs.count(), 1)
        for row in qs:
            self.assertAlmostEqual(row.average_height, 1.6923, places=4)
            self.assertEquals(row.count, 100)

    def test_aggregate_with_filter(self):
        # When filter comes before aggregate
        qs = Person.objects_in(self.database).filter(first_name='Warren').aggregate(average_height='avg(height)', count='count()')
        print(qs.as_sql())
        self.assertEquals(qs.count(), 1)
        for row in qs:
            self.assertAlmostEqual(row.average_height, 1.675, places=4)
            self.assertEquals(row.count, 2)
        # When filter comes after aggregate
        qs = Person.objects_in(self.database).aggregate(average_height='avg(height)', count='count()').filter(first_name='Warren')
        print(qs.as_sql())
        self.assertEquals(qs.count(), 1)
        for row in qs:
            self.assertAlmostEqual(row.average_height, 1.675, places=4)
            self.assertEquals(row.count, 2)

    def test_aggregate_with_implicit_grouping(self):
        qs = Person.objects_in(self.database).aggregate('first_name', average_height='avg(height)', count='count()')
        print(qs.as_sql())
        self.assertEquals(qs.count(), 94)
        total = 0
        for row in qs:
            self.assertTrue(1.5 < row.average_height < 2)
            self.assertTrue(0 < row.count < 3)
            total += row.count
        self.assertEquals(total, 100)

    def test_aggregate_with_explicit_grouping(self):
        qs = Person.objects_in(self.database).aggregate(weekday='toDayOfWeek(birthday)', count='count()').group_by('weekday')
        print(qs.as_sql())
        self.assertEquals(qs.count(), 7)
        total = 0
        for row in qs:
            total += row.count
        self.assertEquals(total, 100)

    def test_aggregate_with_order_by(self):
        qs = Person.objects_in(self.database).aggregate(weekday='toDayOfWeek(birthday)', count='count()').group_by('weekday')
        days = [row.weekday for row in qs.order_by('weekday')]
        self.assertEquals(days, list(range(1, 8)))

    def test_aggregate_with_indexing(self):
        qs = Person.objects_in(self.database).aggregate(weekday='toDayOfWeek(birthday)', count='count()').group_by('weekday')
        total = 0
        for i in range(7):
            total += qs[i].count
        self.assertEquals(total, 100)

    def test_aggregate_with_slicing(self):
        qs = Person.objects_in(self.database).aggregate(weekday='toDayOfWeek(birthday)', count='count()').group_by('weekday')
        total = sum(row.count for row in qs[:3]) + sum(row.count for row in qs[3:])
        self.assertEquals(total, 100)

    def test_aggregate_with_pagination(self):
        qs = Person.objects_in(self.database).aggregate(weekday='toDayOfWeek(birthday)', count='count()').group_by('weekday')
        total = 0
        page_num = 1
        while True:
            page = qs.paginate(page_num, page_size=3)
            self.assertEquals(page.number_of_objects, 7)
            total += sum(row.count for row in page.objects)
            if page.pages_total == page_num:
                break
            page_num += 1
        self.assertEquals(total, 100)

    def test_aggregate_with_wrong_grouping(self):
        with self.assertRaises(AssertionError):
            Person.objects_in(self.database).aggregate(weekday='toDayOfWeek(birthday)', count='count()').group_by('first_name')

    def test_aggregate_with_no_calculated_fields(self):
        with self.assertRaises(AssertionError):
            Person.objects_in(self.database).aggregate()

    def test_aggregate_with_only(self):
        # Cannot put only() after aggregate()
        with self.assertRaises(NotImplementedError):
            Person.objects_in(self.database).aggregate(weekday='toDayOfWeek(birthday)', count='count()').only('weekday')
        # When only() comes before aggregate(), it gets overridden
        qs = Person.objects_in(self.database).only('last_name').aggregate(average_height='avg(height)', count='count()')
        self.assertTrue('last_name' not in qs.as_sql())

    def test_aggregate_on_aggregate(self):
        with self.assertRaises(NotImplementedError):
            Person.objects_in(self.database).aggregate(weekday='toDayOfWeek(birthday)', count='count()').aggregate(s='sum(height)')

    def test_filter_on_calculated_field(self):
        # This is currently not supported, so we expect it to fail
        with self.assertRaises(AttributeError):
            qs = Person.objects_in(self.database).aggregate(weekday='toDayOfWeek(birthday)', count='count()').group_by('weekday')
            qs = qs.filter(weekday=1)
            self.assertEquals(qs.count(), 1)


Color = Enum('Color', u'red blue green yellow brown white black')


class SampleModel(Model):

    timestamp = DateTimeField()
    materialized_date = DateField(materialized='toDate(timestamp)')
    num = Int32Field()
    color = Enum8Field(Color)

    engine = MergeTree('materialized_date', ('materialized_date',))


class Numbers(Model):

    number = UInt64Field()
