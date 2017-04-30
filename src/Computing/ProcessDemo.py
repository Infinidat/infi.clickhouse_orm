# -*- coding: utf-8 -*-

from ComputingHandler import ProcessHandle


class ProcessDemo(ProcessHandle):

    def __init__(self, db_name = "ncf_common"):
        super(ProcessDemo, self).__init__(db_name)
        self.mode = "table_demo"

    def build_table(self, *args, **kwargs):
        yyyymmdd = kwargs["day"].replace('-', '')
        query = "drop table %(db_name)s.usercharge_%(day)s" % {
            "day": yyyymmdd,
            "db_name": self.db_name,
        }
        return query

    def query(self, *args, **kwargs):
        day = kwargs["day"]

        yyyymmdd = day.replace('-', '')

        query_format = "create table %(db_name)s.usercharge_%(yyyymmdd)s engine = MergeTree(partition, pushid, (pushid), 8192) as " \
                       "select partition, pushid, firstLoginTime, today_charge_num, total_charge_num, total_charge_day, (today_charge_num > 0 and today_charge_num = total_charge_num) is_new_charge, (today_charge_num > 0 and today_charge_num < total_charge_num) is_recharge, (toDate(firstLoginTime) = partition) is_new_user " \
                       "from ( " \
                       "select partition, pushid, countIf(toDate(rechargeTime) != '0000-00-00') today_charge_num from ncf_common.user_pushid where partition = '%(day)s' group by partition, pushid) " \
                       "any left join ( " \
                       "select pushid, min(opTime) firstLoginTime, length(groupUniqArrayIf(rechargeTime, toDate(rechargeTime) != '0000-00-00')) total_charge_num, length(groupUniqArrayIf(toDate(rechargeTime), toDate(rechargeTime) != '0000-00-00')) total_charge_day " \
                       "from ncf_common.user_pushid where partition <= '%(day)s' group by pushid) " \
                       "using pushid"

        query = query_format % {
            "day": day,
            "db_name": self.db_name,
            "yyyymmdd": yyyymmdd
        }

        return query

if __name__ == "__main__":
    tester = ProcessDemo()
    print tester.build_table(day='2017-03-27')
    print tester.cmd(day='2017-03-28')