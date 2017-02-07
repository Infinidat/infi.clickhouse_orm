# -*- coding: utf-8 -*-
from infi.clickhouse_orm.database import Database


# 扩展create_merge_table方法
class SubDatabase(Database):

    def create_merge_table(self, model_class):
        self._send(model_class.create_merge_table_sql(self.db_name))