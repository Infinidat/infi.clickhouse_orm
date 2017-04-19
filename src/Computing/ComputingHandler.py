# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger(__name__)
from src.infi.clickhouse_orm.database import Database
from src.Common.Tools.FNDecorator import fn_timer


class ProcessHandle(object):

    def __init__(self, db_name):
        self.db_name = db_name

    def build_table(self):
        raise NotImplementedError()

    def query(self, *args, **kwargs):
        raise NotImplementedError()

    def pipeline(self, *args, **kwargs):
        raise NotImplementedError()

    def optimize(self, partition):

        query_format = "OPTIMIZE TABLE %(db_name)s.%(mode)s PARTITION %(partition)s FINAL"
        query = query_format % {
            "db_name": self.db_name,
            "mode": self.mode,
            "partition": partition,
        }
        logger.info(query)
        client = Database(self.db_name)
        client.submit(self.db_name, query)

    @fn_timer
    def process(self, *args, **kwargs):
        client = Database(self.db_name)
        try:
            build_query = self.build_table(*args, **kwargs)
            logger.info(build_query)
            client.submit(build_query)
        except:
            pass
        _query = self.query(*args, **kwargs)
        logger.info(_query)
        client.submit(_query)


    @fn_timer
    def insert_mode(self, db_name, mode_iter, bulksize=10000, create_merge=True, drop_table=True):
        client = Database(db_name)
        client.insert_try_best(mode_iter, bulksize=bulksize, create_merge=create_merge, drop_table=drop_table)