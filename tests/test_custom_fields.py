from __future__ import unicode_literals
import unittest
import six
from uuid import UUID
from infi.clickhouse_orm.database import Database
from infi.clickhouse_orm.fields import Field, Int16Field
from infi.clickhouse_orm.models import Model
from infi.clickhouse_orm.engines import Memory
from infi.clickhouse_orm.utils import escape


class CustomFieldsTest(unittest.TestCase):

    def setUp(self):
        self.database = Database('test-db')

    def tearDown(self):
        self.database.drop_database()

    def test_boolean_field(self):
        # Create a model
        class TestModel(Model):
            i = Int16Field()
            f = BooleanField()
            engine = Memory()
        self.database.create_table(TestModel)
        # Check valid values
        for index, value in enumerate([1, '1', True, 0, '0', False]):
            rec = TestModel(i=index, f=value)
            self.database.insert([rec])
        self.assertEqual([rec.f for rec in TestModel.objects_in(self.database).order_by('i')],
                          [True, True, True, False, False, False])
        # Check invalid values
        for value in [None, 'zzz', -5, 7]:
            with self.assertRaises(ValueError):
                TestModel(i=1, f=value)

    def test_uuid_field(self):
        # Create a model
        class TestModel(Model):
            i = Int16Field()
            f = UUIDField()
            engine = Memory()
        self.database.create_table(TestModel)
        # Check valid values (all values are the same UUID)
        values = [
            '{12345678-1234-5678-1234-567812345678}',
            '12345678123456781234567812345678',
            'urn:uuid:12345678-1234-5678-1234-567812345678',
            '\x12\x34\x56\x78'*4,
            (0x12345678, 0x1234, 0x5678, 0x12, 0x34, 0x567812345678),
            0x12345678123456781234567812345678,
        ]
        for index, value in enumerate(values):
            rec = TestModel(i=index, f=value)
            self.database.insert([rec])
        for rec in TestModel.objects_in(self.database):
            self.assertEqual(rec.f, UUID(values[0]))
        # Check that ClickHouse encoding functions are supported
        for rec in self.database.select("SELECT i, UUIDNumToString(f) AS f FROM testmodel", TestModel):
            self.assertEqual(rec.f, UUID(values[0]))
        for rec in self.database.select("SELECT 1 as i, UUIDStringToNum('12345678-1234-5678-1234-567812345678') AS f", TestModel):
            self.assertEqual(rec.f, UUID(values[0]))
        # Check invalid values
        for value in [None, 'zzz', -1, '123']:
            with self.assertRaises(ValueError):
                TestModel(i=1, f=value)


class BooleanField(Field):

    # The ClickHouse column type to use
    db_type = 'UInt8'

    # The default value if empty
    class_default = False

    def to_python(self, value, timezone_in_use):
        # Convert valid values to bool
        if value in (1, '1', True):
            return True
        elif value in (0, '0', False):
            return False
        else:
            raise ValueError('Invalid value for BooleanField: %r' % value)

    def to_db_string(self, value, quote=True):
        # The value was already converted by to_python, so it's a bool
        return '1' if value else '0'


class UUIDField(Field):

    # The ClickHouse column type to use
    db_type = 'FixedString(16)'

    # The default value if empty
    class_default = UUID(int=0)

    def to_python(self, value, timezone_in_use):
        # Convert valid values to UUID instance
        if isinstance(value, UUID):
            return value
        elif isinstance(value, six.string_types):
            return UUID(bytes=value.encode('latin1')) if len(value) == 16 else UUID(value)
        elif isinstance(value, six.integer_types):
            return UUID(int=value)
        elif isinstance(value, tuple):
            return UUID(fields=value)
        else:
            raise ValueError('Invalid value for UUIDField: %r' % value)

    def to_db_string(self, value, quote=True):
        # The value was already converted by to_python, so it's a UUID instance
        val = value.bytes
        if six.PY3:
            val = str(val, 'latin1')
        return escape(val, quote)

