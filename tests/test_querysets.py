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
        self._test_qs(qs.filter(num__gt=1), 3)
        self._test_qs(qs.filter(num__gte=1), 4)
        self._test_qs(qs.filter(num__in=(1, 2, 3)), 3)
        self._test_qs(qs.filter(num__in=range(1, 4)), 3)


Color = Enum('Color', u'red blue green yellow brown white black')


class SampleModel(Model):

    timestamp = DateTimeField()
    materialized_date = DateField(materialized='toDate(timestamp)')
    num = Int32Field()
    color = Enum8Field(Color)

    engine = MergeTree('materialized_date', ('materialized_date',))