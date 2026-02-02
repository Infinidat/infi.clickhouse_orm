from __future__ import annotations

import json
import unittest

from clickhouse_orm import database, engines, fields, models


class JoinTest(unittest.TestCase):
    def setUp(self):
        self.database = database.Database("test-db", log_statements=True)
        self.database.create_table(Foo)
        self.database.create_table(Bar)
        self.database.insert([Foo(id=i) for i in range(3)])
        self.database.insert([Bar(id=i, b=i * i) for i in range(3)])

    def print_res(self, query):
        print(query)
        print(json.dumps([row.to_dict() for row in self.database.select(query)]))

    def test_without_db_name(self):
        self.print_res(f"SELECT * FROM {Foo.table_name()}")
        self.print_res(f"SELECT * FROM {Bar.table_name()}")
        self.print_res(f"SELECT b FROM {Foo.table_name()} ALL LEFT JOIN {Bar.table_name()} USING id")

    def test_with_db_name(self):
        self.print_res(f"SELECT * FROM $db.{Foo.table_name()}")
        self.print_res(f"SELECT * FROM $db.{Bar.table_name()}")
        self.print_res(f"SELECT b FROM $db.{Foo.table_name()} ALL LEFT JOIN $db.{Bar.table_name()} USING id")

    def test_with_subquery(self):
        self.print_res(
            f"SELECT b FROM {Foo.table_name()} ALL LEFT JOIN (SELECT * from {Bar.table_name()}) subquery USING id"
        )
        self.print_res(
            f"SELECT b FROM $db.{Foo.table_name()} ALL LEFT JOIN (SELECT * from $db.{Bar.table_name()}) subquery USING id"
        )


class Foo(models.Model):
    id = fields.UInt8Field()
    engine = engines.Memory()


class Bar(Foo):
    b = fields.UInt8Field()
