# -*- coding: utf-8 -*-
import datetime
import time


class DatetimeStr(object):

    def __init__(self):
        pass

    @classmethod
    def to_datetime(cls, datetime_str):
        if not (isinstance(datetime_str, str) or isinstance(datetime_str, unicode)):
            raise ValueError('Invalid type for %s - %r' % (cls.__class__.__name__, datetime_str))
        datetime_str = datetime_str.replace("-", "").replace(" ", "").replace("+", "")
        if len(datetime_str) == 8:
            tm = datetime.datetime.strptime(datetime_str, "%Y%m%d").date()
            return tm
        elif len(datetime_str) == 10:
            tm = datetime.datetime.strptime(datetime_str, "%Y%m%d%H")
            return tm
        elif len(datetime_str) == 12:
            tm = datetime.datetime.strptime(datetime_str, "%Y%m%d%H%M").date()
            return tm

    @classmethod
    def datetype(cls, datetime_str):
        if not (isinstance(datetime_str, str) or isinstance(datetime_str, unicode)):
            raise ValueError('Invalid type for %s - %r' % (cls.__class__.__name__, datetime_str))
        datetime_str = datetime_str.replace("-", "").replace(" ", "").replace("+", "")
        if len(datetime_str) == 8:
            tm = datetime.datetime.strptime(datetime_str, "%Y%m%d").date()
            return "day"
        elif len(datetime_str) == 10:
            tm = datetime.datetime.strptime(datetime_str, "%Y%m%d%H")
            return "hour"
        elif len(datetime_str) == 12:
            tm = datetime.datetime.strptime(datetime_str, "%Y%m%d%H%M").date()
            return "minute"

    @classmethod
    def get_yyyymmdd(cls, datetime_str, strformat="%Y%m%d"):
        if not (isinstance(datetime_str, str) or isinstance(datetime_str, unicode)):
            raise ValueError('Invalid type for %s - %r' % (cls.__class__.__name__, datetime_str))
        datetime_str = datetime_str.replace("-", "").replace(" ", "").replace("+", "").replace(":", "")
        if len(datetime_str) == 8:
            tm = datetime.datetime.strptime(datetime_str, "%Y%m%d").date()
            result = tm.strftime(strformat)
            return result
        elif len(datetime_str) == 10:
            tm = datetime.datetime.strptime(datetime_str, "%Y%m%d%H")
            result = tm.strftime(strformat)
            return result
        elif len(datetime_str) == 12:
            tm = datetime.datetime.strptime(datetime_str, "%Y%m%d%H%M").date()
            result = tm.strftime(strformat)
            return result

    @classmethod
    def get_yyyymmddhh(cls, datetime_str):
        if not (isinstance(datetime_str, str) or isinstance(datetime_str, unicode)):
            raise ValueError('Invalid type for %s - %r' % (cls.__class__.__name__, datetime_str))
        datetime_str = datetime_str.replace("-", "").replace(" ", "").replace("+", "").replace(":", "")
        if len(datetime_str) == 8:
            tm = datetime.datetime.strptime(datetime_str, "%Y%m%d").date()
            return datetime_str[:8] + "??"
        elif len(datetime_str) == 10:
            tm = datetime.datetime.strptime(datetime_str, "%Y%m%d%H")
            return datetime_str[:10]
        elif len(datetime_str) == 12:
            tm = datetime.datetime.strptime(datetime_str, "%Y%m%d%H%M").date()
            return datetime_str[:10]

    @classmethod
    def get_yyyymmddhhmm(cls, datetime_str):
        if not (isinstance(datetime_str, str) or isinstance(datetime_str, unicode)):
            raise ValueError('Invalid type for %s - %r' % (cls.__class__.__name__, datetime_str))
        datetime_str = datetime_str.replace("-", "").replace(" ", "").replace("+", "").replace(":", "")
        if len(datetime_str) == 8:
            tm = datetime.datetime.strptime(datetime_str, "%Y%m%d").date()
            return datetime_str[:8] + "??"*2
        elif len(datetime_str) == 10:
            tm = datetime.datetime.strptime(datetime_str, "%Y%m%d%H")
            return datetime_str[:10] + "??"
        elif len(datetime_str) == 12:
            tm = datetime.datetime.strptime(datetime_str, "%Y%m%d%H%M").date()
            return datetime_str[:12]

if __name__ == "__main__":
    print DatetimeStr.get_yyyymmdd("2017-01-10", "%Y-%m-%d %H%M")