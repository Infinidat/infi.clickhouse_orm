# -*- coding: utf-8 -*-
import ConfigParser
import logging
import sys
from SubDatabase import SubDatabase
# from infi.clickhouse_orm.database import Database
try:
    from __init__ import configPath
except:
    from ClickHouseClient.__init__ import configPath
logger = logging.getLogger(__name__)


class ClickHouseClient(object):
    cf = ConfigParser.ConfigParser()
    cf.read(configPath)
    DB_URL = cf.get("clickhouse", "db_url")
    PASSWORD = cf.get("clickhouse", "password")

    def __init__(self):
        pass
        # self.db = Database(db_name=db_name, db_url=self.__class__.DB_URL, password=self.__class__.PASSWORD)

    def database(self, db_name):
        db = SubDatabase(db_name=db_name, db_url=self.__class__.DB_URL, password=self.__class__.PASSWORD)
        return db

    # 封装insert方法
    def insert(self, db, model_instances, bulksize = 1000, is_create = False, insert_count = 0, first_recu = True):
        cache = []
        table_name = None
        for elem in model_instances:
            if is_create == False:
                db.create_table(elem)
                db.create_merge_table(elem)
                is_create = True
                table_name = elem.table_name()
            cache.append(elem)
            if len(cache) >= bulksize:
                try:
                    # 必须保证 batch_size >= bulksize,否则插入出错情况下二分插入失效
                    db.insert(cache, batch_size=bulksize)
                    insert_count += len(cache)
                    cache = []
                except:
                    # 二分插入
                    if len(cache) > 1:
                        self.insert(db, cache[:(len(cache) / 2)], bulksize = min(len(cache[:(len(cache) / 2)]), bulksize), is_create=is_create, insert_count=insert_count, first_recu=False)
                        self.insert(db, cache[(len(cache) / 2):], bulksize = min(len(cache[(len(cache) / 2):]), bulksize), is_create=is_create, insert_count=insert_count, first_recu=False)
                    elif len(cache) == 1:
                        # 输出报错日志
                        logger.error("%s" % (str(sys.exc_info()), ))
                    cache = []
        if cache:
            try:
                # 必须保证 batch_size >= bulksize,否则插入出错情况下二分插入失效
                db.insert(cache, batch_size=bulksize)
                insert_count += len(cache)
            except:
                # 二分插入
                if len(cache) > 1:
                    self.insert(db, cache[:(len(cache) / 2)], min(len(cache[:(len(cache) / 2)]) / 2, bulksize), is_create=is_create, insert_count=insert_count, first_recu=False)
                    self.insert(db, cache[(len(cache) / 2):], min(len(cache[(len(cache) / 2):]) / 2, bulksize), is_create=is_create, insert_count=insert_count, first_recu=False)
                elif len(cache) == 1:
                    logger.error("%s; LOG: %s" % (str(sys.exc_info()), ))
        if first_recu:
            logger.info("%(db_name)s.%(table_name)s insert %(count)d records." % {
                "db_name": db.db_name,
                "table_name": table_name,
                "count": insert_count,
            })


if __name__ == "__main__":
    tester = ClickHouseClient()
    print tester.database("ncf")