from __future__ import unicode_literals
import unittest

from infi.clickhouse_orm.database import ServerError


class ServerErrorTest(unittest.TestCase):

    def test_old_format(self):

        code, msg = ServerError.get_error_code_msg("Code: 81, e.displayText() = DB::Exception: Database db_not_here doesn't exist, e.what() = DB::Exception (from [::1]:33458)")
        self.assertEquals(code, 81)
        self.assertEquals(msg, "Database db_not_here doesn't exist")

        code, msg = ServerError.get_error_code_msg("Code: 161, e.displayText() = DB::Exception: Limit for number of columns to read exceeded. Requested: 11, maximum: 1, e.what() = DB::Exception\n")
        self.assertEquals(code, 161)
        self.assertEquals(msg, "Limit for number of columns to read exceeded. Requested: 11, maximum: 1")


    def test_new_format(self):

        code, msg = ServerError.get_error_code_msg("Code: 164, e.displayText() = DB::Exception: Cannot drop table in readonly mode")
        self.assertEquals(code, 164)
        self.assertEquals(msg, "Cannot drop table in readonly mode")

        code, msg = ServerError.get_error_code_msg("Code: 48, e.displayText() = DB::Exception: Method write is not supported by storage Merge")
        self.assertEquals(code, 48)
        self.assertEquals(msg, "Method write is not supported by storage Merge")

        code, msg = ServerError.get_error_code_msg("Code: 60, e.displayText() = DB::Exception: Table default.zuzu doesn't exist.\n")
        self.assertEquals(code, 60)
        self.assertEquals(msg, "Table default.zuzu doesn't exist.")
