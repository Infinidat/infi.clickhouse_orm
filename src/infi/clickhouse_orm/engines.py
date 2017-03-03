
class Engine(object):

    def create_table_sql(self):
        raise NotImplementedError()


class MergeTree(Engine):

    def __init__(self, date_col, key_cols, sampling_expr=None,
                 index_granularity=8192, replica_table_path=None, replica_name=None):
        self.date_col = date_col
        self.key_cols = key_cols
        self.sampling_expr = sampling_expr
        self.index_granularity = index_granularity
        self.replica_table_path = replica_table_path
        self.replica_name = replica_name
        # TODO verify that both replica fields are either present or missing

    def create_table_sql(self):
        name = self.__class__.__name__
        if self.replica_name:
            name = 'Replicated' + name
        params = self._build_sql_params()
        return '%s(%s)' % (name, ', '.join(params))

    def _build_sql_params(self):
        params = []
        if self.replica_name:
            params += ["'%s'" % self.replica_table_path, "'%s'" % self.replica_name]
        params.append(self.date_col)
        if self.sampling_expr:
            params.append(self.sampling_expr)
        params.append('(%s)' % ', '.join(self.key_cols))
        params.append(str(self.index_granularity))
        return params


class CollapsingMergeTree(MergeTree):

    def __init__(self, date_col, key_cols, sign_col, sampling_expr=None,
                 index_granularity=8192, replica_table_path=None, replica_name=None):
        super(CollapsingMergeTree, self).__init__(date_col, key_cols, sampling_expr, index_granularity, replica_table_path, replica_name)
        self.sign_col = sign_col

    def _build_sql_params(self):
        params = super(CollapsingMergeTree, self)._build_sql_params()
        params.append(self.sign_col)
        return params


class SummingMergeTree(MergeTree):

    def __init__(self, date_col, key_cols, summing_cols=None, sampling_expr=None,
                 index_granularity=8192, replica_table_path=None, replica_name=None):
        super(SummingMergeTree, self).__init__(date_col, key_cols, sampling_expr, index_granularity, replica_table_path, replica_name)
        self.summing_cols = summing_cols

    def _build_sql_params(self):
        params = super(SummingMergeTree, self)._build_sql_params()
        if self.summing_cols:
            params.append('(%s)' % ', '.join(self.summing_cols))
        return params


class Merge(Engine):

    def __init__(self, database, tablePattern):
        from .utils import escape
        self.database = escape(database, True)
        self.tablePattern = escape(tablePattern, True)

    def create_table_sql(self):
        name = self.__class__.__name__
        params = self._build_sql_params()
        return '%s(%s)' % (name, ', '.join(params))

    def _build_sql_params(self):
        params = [str(self.database), str(self.tablePattern)]
        return params


class ReplacingMergeTree(Engine):

    def __init__(self, date_col, key_cols, ver_col, index_granularity=8192):
        self.date_col = date_col
        self.key_cols = key_cols
        self.ver_col = ver_col
        self.index_granularity = index_granularity

    def create_table_sql(self):
        '''
        return demo: ReplacingMergeTree(EventDate, (OrderID, EventDate, BannerID, ...), 8192, ver)
        :return:
        '''
        # MergeTree(EventDate, intHash32(UserID), (CounterID, EventDate, intHash32(UserID)), 8192)
        name = self.__class__.__name__
        params = self._build_sql_params()
        return '%s(%s)' % (name, ', '.join(params))

    def _build_sql_params(self):
        params = []
        params.append(self.date_col)
        params.append('(%s)' % ', '.join(self.key_cols))
        params.append(str(self.index_granularity))
        params.append(str(self.ver_col))
        return params

if __name__ == "__main__":
    # tester = Merge("test", "^user_event")
    tester = ReplacingMergeTree("partition", ("jhd_userkey", "jhd_opTime"), "jhd_userkey")
    print(tester.create_table_sql())



