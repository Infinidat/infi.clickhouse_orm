# -*- coding: utf-8 -*-
import __init__
import datetime
import json
import uuid

from src.Computing.ComputingHandler import ProcessHandle
from src.infi.clickhouse_orm.database import Database
from src.Mode.ModeDemo import ModeDemo


class InsertDemo(ProcessHandle):

    def __init__(self, db_name):
        super(InsertDemo, self).__init__(db_name)
        self.mode = "table_insert_demo"

    def pipeline(self):
        i = 0
        while i < 1000:
            yield {
                'partition': datetime.datetime.today().strptime("%Y-%m-%d"),
                'attr1': i
            }
            i += 1





if __name__ == "__main__":
    tester = InsertDemo("test_db")