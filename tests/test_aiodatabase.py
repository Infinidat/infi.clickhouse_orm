# -*- coding: utf-8 -*-
import unittest
import datetime

from clickhouse_orm.database import ServerError, DatabaseException
from clickhouse_orm.query import Q
from clickhouse_orm.funcs import F
from tests.base_test_with_data import *


class DatabaseTestCase(TestCaseWithAsyncData):

    async def test_insert__generator(self):
        await self._insert_and_check(self._sample_data(), len(data))

    async def test_insert__list(self):
        await self._insert_and_check(list(self._sample_data()), len(data))

    async def test_insert__iterator(self):
        await self._insert_and_check(iter(self._sample_data()), len(data))

    async def test_insert__empty(self):
        await self._insert_and_check([], 0)

    async def test_insert__small_batches(self):
        await self._insert_and_check(self._sample_data(), len(data), batch_size=10)

    async def test_insert__medium_batches(self):
        await self._insert_and_check(self._sample_data(), len(data), batch_size=100)

    async def test_insert__funcs_as_default_values(self):
        if self.database.server_version < (20, 1, 2, 4):
            raise unittest.SkipTest('Buggy in server versions before 20.1.2.4')

        class TestModel(Model):
            a = DateTimeField(default=datetime.datetime(2020, 1, 1))
            b = DateField(default=F.toDate(a))
            c = Int32Field(default=7)
            d = Int32Field(default=c * 5)
            engine = Memory()
        await self.database.create_table(TestModel)
        await self.database.insert([TestModel()])
        with self.assertRaises(TypeError):
            # AioDatabase does not support queryset object value by index
            obj = TestModel.objects_in(self.database)[0]
        async for t in TestModel.objects_in(self.database):
            self.assertEqual(str(t.b), '2020-01-01')
            self.assertEqual(t.d, 35)

    async def test_count(self):
        await self.database.insert(self._sample_data())
        self.assertEqual(await self.database.count(Person), 100)
        # Conditions as string
        self.assertEqual(await self.database.count(Person, "first_name = 'Courtney'"), 2)
        self.assertEqual(await self.database.count(Person, "birthday > '2000-01-01'"), 22)
        self.assertEqual(await self.database.count(Person, "birthday < '1970-03-01'"), 0)
        # Conditions as expression
        self.assertEqual(
            await self.database.count(Person, Person.birthday > datetime.date(2000, 1, 1)), 22
        )
        # Conditions as Q object
        self.assertEqual(
            await self.database.count(Person, Q(birthday__gt=datetime.date(2000, 1, 1))), 22
        )

    async def test_select(self):
        await self._insert_and_check(self._sample_data(), len(data))
        query = "SELECT * FROM `test-db`.person WHERE first_name = 'Whitney' ORDER BY last_name"
        results = [person async for person in self.database.select(query, Person)]
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].last_name, 'Durham')
        self.assertEqual(results[0].height, 1.72)
        self.assertEqual(results[1].last_name, 'Scott')
        self.assertEqual(results[1].height, 1.70)
        self.assertEqual(results[0].get_database(), self.database)
        self.assertEqual(results[1].get_database(), self.database)

    async def test_dollar_in_select(self):
        query = "SELECT * FROM $table WHERE first_name = '$utm_source'"
        [_ async for _ in self.database.select(query, Person)]

    async def test_select_partial_fields(self):
        await self._insert_and_check(self._sample_data(), len(data))
        query = "SELECT first_name, last_name FROM `test-db`.person WHERE first_name = 'Whitney' ORDER BY last_name"
        results = [person async for person in self.database.select(query, Person)]
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].last_name, 'Durham')
        self.assertEqual(results[0].height, 0) # default value
        self.assertEqual(results[1].last_name, 'Scott')
        self.assertEqual(results[1].height, 0) # default value
        self.assertEqual(results[0].get_database(), self.database)
        self.assertEqual(results[1].get_database(), self.database)

    async def test_select_ad_hoc_model(self):
        await self._insert_and_check(self._sample_data(), len(data))
        query = "SELECT * FROM `test-db`.person WHERE first_name = 'Whitney' ORDER BY last_name"
        results = [person async for person in self.database.select(query)]
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].__class__.__name__, 'AdHocModel')
        self.assertEqual(results[0].last_name, 'Durham')
        self.assertEqual(results[0].height, 1.72)
        self.assertEqual(results[1].last_name, 'Scott')
        self.assertEqual(results[1].height, 1.70)
        self.assertEqual(results[0].get_database(), self.database)
        self.assertEqual(results[1].get_database(), self.database)

    async def test_select_with_totals(self):
        await self._insert_and_check(self._sample_data(), len(data))
        query = "SELECT last_name, sum(height) as height FROM `test-db`.person GROUP BY last_name WITH TOTALS"
        results = [person async for person in self.database.select(query)]
        total = sum(r.height for r in results[:-1])
        # Last line has an empty last name, and total of all heights
        self.assertFalse(results[-1].last_name)
        self.assertEqual(total, results[-1].height)

    async def test_pagination(self):
        await self._insert_and_check(self._sample_data(), len(data))
        # Try different page sizes
        for page_size in (1, 2, 7, 10, 30, 100, 150):
            # Iterate over pages and collect all intances
            page_num = 1
            instances = set()
            while True:
                page = await self.database.paginate(Person, 'first_name, last_name', page_num, page_size)
                self.assertEqual(page.number_of_objects, len(data))
                self.assertGreater(page.pages_total, 0)
                [instances.add(obj.to_tsv()) for obj in page.objects]
                if page.pages_total == page_num:
                    break
                page_num += 1
            # Verify that all instances were returned
            self.assertEqual(len(instances), len(data))

    async def test_pagination_last_page(self):
        await self._insert_and_check(self._sample_data(), len(data))
        # Try different page sizes
        for page_size in (1, 2, 7, 10, 30, 100, 150):
            # Ask for the last page in two different ways and verify equality
            page_a = await self.database.paginate(Person, 'first_name, last_name', -1, page_size)
            page_b = await self.database.paginate(Person, 'first_name, last_name',
                                                  page_a.pages_total, page_size)
            self.assertEqual(page_a[1:], page_b[1:])
            self.assertEqual(
                [obj.to_tsv() for obj in page_a.objects], [obj.to_tsv() for obj in page_b.objects]
            )

    async def test_pagination_empty_page(self):
        for page_num in (-1, 1, 2):
            page = await self.database.paginate(
                Person, 'first_name, last_name', page_num, 10, conditions="first_name = 'Ziggy'"
            )
            self.assertEqual(page.number_of_objects, 0)
            self.assertEqual(page.objects, [])
            self.assertEqual(page.pages_total, 0)
            self.assertEqual(page.number, max(page_num, 1))

    async def test_pagination_invalid_page(self):
        await self._insert_and_check(self._sample_data(), len(data))
        for page_num in (0, -2, -100):
            with self.assertRaises(ValueError):
                await self.database.paginate(Person, 'first_name, last_name', page_num, 100)

    async def test_pagination_with_conditions(self):
        await self._insert_and_check(self._sample_data(), len(data))
        # Conditions as string
        page = await self.database.paginate(
            Person, 'first_name, last_name', 1, 100, conditions="first_name < 'Ava'"
        )
        self.assertEqual(page.number_of_objects, 10)
        # Conditions as expression
        page = await self.database.paginate(
            Person, 'first_name, last_name', 1, 100, conditions=Person.first_name < 'Ava'
        )
        self.assertEqual(page.number_of_objects, 10)
        # Conditions as Q object
        page = await self.database.paginate(
            Person, 'first_name, last_name', 1, 100, conditions=Q(first_name__lt='Ava')
        )
        self.assertEqual(page.number_of_objects, 10)

    async def test_special_chars(self):
        s = u'אבגד \\\'"`,.;éåäöšž\n\t\0\b\r'
        p = Person(first_name=s)
        await self.database.insert([p])
        p = [_ async for _ in self.database.select("SELECT * from $table", Person)][0]
        self.assertEqual(p.first_name, s)

    async def test_raw(self):
        await self._insert_and_check(self._sample_data(), len(data))
        query = "SELECT * FROM `test-db`.person WHERE first_name = 'Whitney' ORDER BY last_name"
        results = await self.database.raw(query)
        self.assertEqual(results, "Whitney\tDurham\t1977-09-15\t1.72\t\\N\nWhitney\tScott\t1971-07-04\t1.7\t\\N\n")

    async def test_not_init(self):
        with self.assertRaises(DatabaseException) as cm:
            db = AioDatabase(self.database.db_name)
            await db.create_table(Person)

        exc = cm.exception
        self.assertTrue(exc.args[0].startswith('The AioDatabase object must execute the init'))

    async def test_read_only(self):
        with self.assertRaises(DatabaseException) as cm:
            db = AioDatabase('test-db-2', readonly=True)
            await db.init()

        exc = cm.exception
        self.assertTrue(exc.args[0].startswith('Database does not exist'))

    async def test_invalid_user(self):
        with self.assertRaises(ServerError) as cm:
            db = AioDatabase(self.database.db_name, username='default', password='wrong')
            await db.init()

        exc = cm.exception
        print(exc.code, exc.message)
        if exc.code == 193:  # ClickHouse version < 20.3
            self.assertTrue(exc.message.startswith('Wrong password for user default'))
        elif exc.code == 516:  # ClickHouse version >= 20.3
            self.assertTrue(exc.message.startswith('default: Authentication failed'))
        else:
            raise Exception('Unexpected error code - %s %s' % (exc.code, exc.message))

    async def test_nonexisting_db(self):
        db = AioDatabase('db_not_here', auto_create=False)
        await db.init()
        with self.assertRaises(ServerError) as cm:
            await db.create_table(Person)
        exc = cm.exception
        self.assertEqual(exc.code, 81)
        self.assertTrue(exc.message.startswith("Database db_not_here doesn't exist"))
        # Create and delete the db twice, to ensure db_exists gets updated
        for i in range(2):
            # Now create the database - should succeed
            await db.create_database()
            self.assertTrue(db.db_exists)
            await db.create_table(Person)
            # Drop the database
            await db.drop_database()
            self.assertFalse(db.db_exists)

    async def test_preexisting_db(self):
        db = AioDatabase(self.database.db_name, auto_create=False)
        await db.init()
        await db.count(Person)

    async def test_missing_engine(self):
        class EnginelessModel(Model):
            float_field = Float32Field()
        with self.assertRaises(DatabaseException) as cm:
            await self.database.create_table(EnginelessModel)
        self.assertEqual(str(cm.exception), 'EnginelessModel class must define an engine')

    async def test_potentially_problematic_field_names(self):
        class Model1(Model):
            system = StringField()
            readonly = StringField()
            engine = Memory()
        instance = Model1(system='s', readonly='r')
        self.assertEqual(instance.to_dict(), dict(system='s', readonly='r'))
        await self.database.create_table(Model1)
        await self.database.insert([instance])
        instance = [_ async for _ in Model1.objects_in(self.database)[0:10]][0]
        self.assertEqual(instance.to_dict(), dict(system='s', readonly='r'))

    async def test_does_table_exist(self):
        class Person2(Person):
            pass
        self.assertTrue(await self.database.does_table_exist(Person))
        self.assertFalse(await self.database.does_table_exist(Person2))

    async def test_add_setting(self):
        # Non-string setting name should not be accepted
        with self.assertRaises(AssertionError):
            self.database.add_setting(0, 1)
        # Add a setting and see that it makes the query fail
        self.database.add_setting('max_columns_to_read', 1)
        with self.assertRaises(ServerError):
            [_ async for _ in self.database.select('SELECT * from system.tables')]
        # Remove the setting and see that now it works
        self.database.add_setting('max_columns_to_read', None)
        [_ async for _ in self.database.select('SELECT * from system.tables')]

    async def test_create_ad_hoc_field(self):
        # Tests that create_ad_hoc_field works for all column types in the database
        from clickhouse_orm.models import ModelBase
        query = "SELECT DISTINCT type FROM system.columns"
        async for row in self.database.select(query):
            if row.type.startswith('Map'):
                continue  # Not supported yet
            ModelBase.create_ad_hoc_field(row.type)

    async def test_get_model_for_table(self):
        # Tests that get_model_for_table works for a non-system model
        model = await self.database.get_model_for_table('person')
        self.assertFalse(model.is_system_model())
        self.assertFalse(model.is_read_only())
        self.assertEqual(model.table_name(), 'person')
        # Read a few records
        [_ async for _ in model.objects_in(self.database)[:10]]
        # Inserts should work too
        await self.database.insert([
            model(first_name='aaa', last_name='bbb', height=1.77)
        ])

    async def test_get_model_for_table__system(self):
        # Tests that get_model_for_table works for all system tables
        query = "SELECT name FROM system.tables WHERE database='system'"
        async for row in self.database.select(query):
            print(row.name)
            if row.name in ('distributed_ddl_queue',):
                continue  # Not supported
            try:
                model = await self.database.get_model_for_table(row.name, system_table=True)
            except NotImplementedError:
                continue  # Table contains an unsupported field type
            self.assertTrue(model.is_system_model())
            self.assertTrue(model.is_read_only())
            self.assertEqual(model.table_name(), row.name)
            # Read a few records
            try:
                [_ async for _ in model.objects_in(self.database)[:10]]
            except ServerError as e:
                if 'Not enough privileges' in e.message:
                    pass
                elif 'no certificate file has been specified' in e.message:
                    pass
                elif 'table must contain condition' in e.message:
                    pass
                else:
                    raise
