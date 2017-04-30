# -*- coding: utf-8 -*-
import logging
import sys
reload(sys)

from LoadIter import LoadIter
from src.infi.clickhouse_orm.database import Database
from src.Common.Tools.FNDecorator import fn_timer
from src.Computing.ProcessDemo import ProcessDemo
from src.ModeBuilder.ModeDemoBuilder import ModeDemoBuilder

sys.setdefaultencoding("utf-8")

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')


class ModeProcess(object):

    def __init__(self, mode_builder_name):
        self.mode_builder_register()
        self.process_hanlder = self.modebuilders[mode_builder_name][0]

    @fn_timer
    def load(self, db_name, *args, **kwargs):
        hanlder = self.process_hanlder(db_name=db_name)
        hanlder.process(*args, **kwargs)

    # 模型注册函数
    def mode_builder_register(self):
        self.modebuilders = {
            "ProcessDemo": [ProcessDemo],
        }

if __name__ == "__main__":
    tester = ModeProcess("ProcessDemo")
    tester.load("20170417", day='2017-04-18')
