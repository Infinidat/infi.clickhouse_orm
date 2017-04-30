# -*- coding: utf-8 -*-
import json
import datetime

from src.Common.Tools.DictKey import find_value_fromdict_singlekey


class Builder(object):

    def __init__(self, conf):

        self.config = conf
        self.comparison_keys = dict([(key, self.config["keys"][key][0]) for key in self.config["keys"]])
        self.apply_keys = dict([(key, self.config["keys"][key][1]) for key in self.config["keys"]])

    # 日志接收日期
    def set_access_day(self, day):
        self.day = day.replace("-", "")

    def build(self, line):
        # type(line) == str
        # json.dumps(value, ensure_ascii=False).encode('utf-8')
        data = line if isinstance(line, dict) else json.loads(line)
        result = {}
        for key in data:
            if key not in self.comparison_keys:
                continue
            value = find_value_fromdict_singlekey(data, key)
            if key in self.apply_keys:
                value = getattr(self, self.apply_keys.get(key, "not_cast"))(value)
            result.setdefault(self.comparison_keys[key], value)
        return result

    def not_cast(self, value):
        return value

    def none_cast(self, value):
        if isinstance(value, str) or isinstance(value, unicode):
            if value.lower() == "null":
                return None
        if not value:
            return None
        return value

    def timestamp_cast(self, value, ts_len = 13):
        value_str = str(value)
        if "." in value_str:
            head, tail = value_str.split(".")
        else:
            head = value_str
            tail = ""

        if len(head) == ts_len:
            return int(head)

        if isinstance(value, float):
            ts_msec = int(value * 1000)
            if len(str(ts_msec)) == ts_len:
                return ts_msec
            else:
                return int(value)
        elif isinstance(value, int):
            if len(str(value)) == ts_len:
                return value
            return value
        elif isinstance(value, unicode) or isinstance(value, str):
            self.timestamp_cast(self.float_cast(value))

    def float_cast(self, value):
        try:
            return float(value)
        except:
            return 0.0

    def int_cast(self, value):
        return int(self.float_cast(value))

    def datetime_cast(self, value):
        value = value.replace("-", "").replace(" ", "").replace(":", "")
        try:
            result = datetime.datetime.strptime(value, "%Y%m%d%H%M%S")
        except:
            try:
                result = datetime.datetime.strptime(value, "%Y%m%d")
            except:
                result = datetime.datetime.now()
        return result

    def date_cast(self, value):
        result = self.datetime_cast(value).date()
        return result

    def str_cast(self, value):
        value = self.none_cast(value)
        if value is None:
            return ""
        if isinstance(value, str) or isinstance(value, unicode):
            return value.strip()
        elif isinstance(value, dict) or isinstance(value, list):
            try:
                return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            except:
                return json.dumps(value, separators=(',', ':'))
        else:
            return str(value).strip()


if __name__ == "__main__":
    pass