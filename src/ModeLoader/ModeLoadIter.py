# -*- coding: utf-8 -*-
import logging
import sys
reload(sys)

from LoadIter import LoadIter
from src.infi.clickhouse_orm.database import Database
from src.Common.Tools.FNDecorator import fn_timer
from src.Computing.InsertDemo import InsertDemo
from src.ModeBuilder.ModeDemoBuilder import ModeDemoBuilder

sys.setdefaultencoding("utf-8")

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')


class ModeLoaderIter(LoadIter):

    def __init__(self, mode_builder_name):
        self.mode_builder_register()
        mode_builder = self.modebuilders[mode_builder_name][0]
        super(ModeLoaderIter, self).__init__(mode_builder)
        self.insert_hanlder = self.modebuilders[mode_builder_name][1]

    @fn_timer
    def load(self, db_name, mode_name):
        data_creator = self.insert_hanlder(db_name=db_name)
        mode_iter = self.loderIter(data_creator.pipeline(), mode_name, add_kwargs=None)
        data_creator.insert_mode(db_name, mode_iter)

    # 模型注册函数
    def mode_builder_register(self):
        self.modebuilders = {
            "ModeDemoBuilder": [ModeDemoBuilder(), InsertDemo],
        }

if __name__ == "__main__":
    tester = ModeLoaderIter("UserSession_ncf")
    tester.load("20170417", "ncf_ws", "usersession")
