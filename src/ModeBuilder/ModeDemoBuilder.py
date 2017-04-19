# -*- coding: utf-8 -*-
import __init__
from collections import OrderedDict
from Builder import Builder

from src.Mode.ModeDemo import ModeDemo


class ModeDemoBuilder(Builder):

    def __init__(self, appoint_conf="default"):
        configs = {
            "default": {
                "keys": OrderedDict([
                    # 日志字段名称：[替换名称（把不同日志的字段名称转化为模型统一的字段名称）， 指定类型转换方法（在基类中定义）]
                    ("partition", ["partition", "date_cast"]),
                    ("attr1", ["attr1", "str_cast"]),
                ]),
            }
        }
        super(ModeDemoBuilder, self).__init__(configs[appoint_conf])

    # 初始化模型对象并返回
    def build(self, line_jsom, tablename = None, add_kwargs = None):
        '''
        :param line_jsom: json格式日志
        :param tablename: 入库表名
        :param add_kwargs: 添加属性
        :return:
        '''
        if add_kwargs is None:
            add_kwargs = {}
        result = super(ModeDemoBuilder, self).build(line)
        result.update(**add_kwargs)
        add_kwargs = None
        return ModeDemo(tablename=tablename, **result)


if __name__ == "__main__":
    line = '''{"jhd_auth": "on", "jhd_sdk_type": "android", "jhd_ua": "hm_note_1s", "jhd_map": {"jhd_start": "direct"}, "jhd_loc": "null", "jhd_pushid": "6d8eb571eb5f49d2b32b29b072450f25", "jhd_opTime": "20170108235920", "jhd_eventId": "null", "jhd_ip": "182.118.113.25", "jhd_pb": "QQ_MARKET", "jhd_userkey": "cef6a4e9-1add-3607-941c-8f1a438e06610", "jhd_os": "android_4.4.4", "jhd_opType": "in", "jhd_sdk_version": "1.0.1", "jhd_netType": "wifi", "jhd_vr": "3.0.0", "jhd_ts": "1483891160105", "jhd_interval": "null", "jhd_datatype": "caiyu_ad"}'''
    tester = ModeDemoBuilder(day="2016-12-31")



