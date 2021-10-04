# -*- coding: utf-8 -*-
from clickhouse_orm.engines import Buffer
from clickhouse_orm.models import BufferModel

from .base_test_with_data import Person, TestCaseWithData, data


class BufferTestCase(TestCaseWithData):
    def _insert_and_check_buffer(self, data, count):
        self.database.insert(data)
        self.assertEqual(count, self.database.count(PersonBuffer))

    def _sample_buffer_data(self):
        for entry in data:
            yield PersonBuffer(**entry)

    def test_insert_buffer(self):
        self.database.create_table(PersonBuffer)
        self._insert_and_check_buffer(self._sample_buffer_data(), len(data))


class PersonBuffer(BufferModel, Person):

    engine = Buffer(Person)
