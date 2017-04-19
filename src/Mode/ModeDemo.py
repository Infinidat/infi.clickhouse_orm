# -*- coding: utf-8 -*-
from src.infi.clickhouse_orm.models import CreateMergeMode
from src.infi.clickhouse_orm import fields
from src.infi.clickhouse_orm import engines

class ModeDemo(CreateMergeMode):

    # Partition Column
    partition = fields.DateField()
    # ATTRIBUTE
    attr1 = fields.StringField()

    engine = engines.MergeTree("partition", ("attr1", ), "attr1")

if __name__ == "__main__":
    # tester = UserEvent("666table")
    tester = ModeDemo(tablename="tttt_444")
    print tester.create_merge_table_sql(db_name="test_database")
    print tester.create_table_sql(db_name="test_database")