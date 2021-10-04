import logging
import unittest

from clickhouse_orm import Database, F, Memory, Model, StringField, UInt64Field


class DictionaryTestMixin:
    def setUp(self):
        self.database = Database("test-db", log_statements=True)
        if self.database.server_version < (20, 1, 11, 73):
            raise unittest.SkipTest("ClickHouse version too old")
        self._create_dictionary()

    def tearDown(self):
        self.database.drop_database()

    def _call_func(self, func):
        sql = "SELECT %s AS value" % func.to_sql()
        logging.info(sql)
        result = list(self.database.select(sql))
        logging.info("\t==> %s", result[0].value if result else "<empty>")
        return result

    def _test_func(self, func, expected_value):
        result = self._call_func(func)
        print("Comparing %s to %s" % (result[0].value, expected_value))
        assert result[0].value == expected_value


class SimpleDictionaryTest(DictionaryTestMixin, unittest.TestCase):
    def _create_dictionary(self):
        # Create a table to be used as source for the dictionary
        self.database.create_table(NumberName)
        self.database.insert(
            NumberName(number=i, name=name)
            for i, name in enumerate("Zero One Two Three Four Five Six Seven Eight Nine Ten".split())
        )
        # Create the dictionary
        self.database.raw(
            """
            CREATE DICTIONARY numbers_dict(
              number UInt64,
              name String DEFAULT '?'
            )
            PRIMARY KEY number
            SOURCE(CLICKHOUSE(
                HOST 'localhost' PORT 9000 USER 'default' PASSWORD '' DB 'test-db' TABLE 'numbername'
            ))
            LIFETIME(100)
            LAYOUT(HASHED());
        """
        )
        self.dict_name = "test-db.numbers_dict"

    def test_dictget(self):
        self._test_func(F.dictGet(self.dict_name, "name", F.toUInt64(3)), "Three")
        self._test_func(F.dictGet(self.dict_name, "name", F.toUInt64(99)), "?")

    def test_dictgetordefault(self):
        self._test_func(F.dictGetOrDefault(self.dict_name, "name", F.toUInt64(3), "n/a"), "Three")
        self._test_func(F.dictGetOrDefault(self.dict_name, "name", F.toUInt64(99), "n/a"), "n/a")

    def test_dicthas(self):
        self._test_func(F.dictHas(self.dict_name, F.toUInt64(3)), 1)
        self._test_func(F.dictHas(self.dict_name, F.toUInt64(99)), 0)


class HierarchicalDictionaryTest(DictionaryTestMixin, unittest.TestCase):
    def _create_dictionary(self):
        # Create a table to be used as source for the dictionary
        self.database.create_table(Region)
        self.database.insert(
            [
                Region(region_id=1, parent_region=0, region_name="Russia"),
                Region(region_id=2, parent_region=1, region_name="Moscow"),
                Region(region_id=3, parent_region=2, region_name="Center"),
                Region(region_id=4, parent_region=0, region_name="Great Britain"),
                Region(region_id=5, parent_region=4, region_name="London"),
            ]
        )
        # Create the dictionary
        self.database.raw(
            """
            CREATE DICTIONARY regions_dict(
              region_id UInt64,
              parent_region UInt64 HIERARCHICAL,
              region_name String DEFAULT '?'
            )
            PRIMARY KEY region_id
            SOURCE(CLICKHOUSE(
                HOST 'localhost' PORT 9000 USER 'default' PASSWORD '' DB 'test-db' TABLE 'region'
            ))
            LIFETIME(100)
            LAYOUT(HASHED());
        """
        )
        self.dict_name = "test-db.regions_dict"

    def test_dictget(self):
        self._test_func(F.dictGet(self.dict_name, "region_name", F.toUInt64(3)), "Center")
        self._test_func(F.dictGet(self.dict_name, "parent_region", F.toUInt64(3)), 2)
        self._test_func(F.dictGet(self.dict_name, "region_name", F.toUInt64(99)), "?")

    def test_dictgetordefault(self):
        self._test_func(
            F.dictGetOrDefault(self.dict_name, "region_name", F.toUInt64(3), "n/a"),
            "Center",
        )
        self._test_func(
            F.dictGetOrDefault(self.dict_name, "region_name", F.toUInt64(99), "n/a"),
            "n/a",
        )

    def test_dicthas(self):
        self._test_func(F.dictHas(self.dict_name, F.toUInt64(3)), 1)
        self._test_func(F.dictHas(self.dict_name, F.toUInt64(99)), 0)

    def test_dictgethierarchy(self):
        self._test_func(F.dictGetHierarchy(self.dict_name, F.toUInt64(3)), [3, 2, 1])
        # Default behaviour changed in CH, but we're not really testing that
        default = self._call_func(F.dictGetHierarchy(self.dict_name, F.toUInt64(99)))
        assert isinstance(default, list)
        assert len(default) <= 1  # either [] or [99]

    def test_dictisin(self):
        self._test_func(F.dictIsIn(self.dict_name, F.toUInt64(3), F.toUInt64(1)), 1)
        self._test_func(F.dictIsIn(self.dict_name, F.toUInt64(3), F.toUInt64(4)), 0)
        self._test_func(F.dictIsIn(self.dict_name, F.toUInt64(99), F.toUInt64(4)), 0)


class NumberName(Model):
    """A table to act as a source for the dictionary"""

    number = UInt64Field()
    name = StringField()

    engine = Memory()


class Region(Model):

    region_id = UInt64Field()
    parent_region = UInt64Field()
    region_name = StringField()

    engine = Memory()
