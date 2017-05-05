
class Engine(object):

    def create_table_sql(self):
        raise NotImplementedError()


class TinyLog(Engine):

    def create_table_sql(self):
        return 'TinyLog'


class Log(Engine):

    def create_table_sql(self):
        return 'Log'


class Memory(Engine):

    def create_table_sql(self):
        return 'Memory'


class MergeTree(Engine):

    def __init__(self, date_col, key_cols, sampling_expr=None,
                 index_granularity=8192, replica_table_path=None, replica_name=None):
        assert type(key_cols) in (list, tuple), 'key_cols must be a list or tuple'
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
        assert type is None or type(summing_cols) in (list, tuple), 'summing_cols must be a list or tuple'
        self.summing_cols = summing_cols

    def _build_sql_params(self):
        params = super(SummingMergeTree, self)._build_sql_params()
        if self.summing_cols:
            params.append('(%s)' % ', '.join(self.summing_cols))
        return params


class ReplacingMergeTree(MergeTree):

    def __init__(self, date_col, key_cols, ver_col=None, sampling_expr=None,
                 index_granularity=8192, replica_table_path=None, replica_name=None):
        super(ReplacingMergeTree, self).__init__(date_col, key_cols, sampling_expr, index_granularity, replica_table_path, replica_name)
        self.ver_col = ver_col

    def _build_sql_params(self):
        params = super(ReplacingMergeTree, self)._build_sql_params()
        if self.ver_col:
            params.append(self.ver_col)
        return params


class Buffer(Engine):
    """
    Buffers the data to write in RAM, periodically flushing it to another table.
    Must be used in conjuction with a `BufferModel`.
    Read more [here](https://clickhouse.yandex/reference_en.html#Buffer).
    """
    
    #Buffer(database, table, num_layers, min_time, max_time, min_rows, max_rows, min_bytes, max_bytes)
    def __init__(self, main_model, num_layers=16, min_time=10, max_time=100, min_rows=10000, max_rows=1000000, min_bytes=10000000, max_bytes=100000000):
        self.main_model = main_model
        self.num_layers = num_layers
        self.min_time = min_time
        self.max_time = max_time
        self.min_rows = min_rows
        self.max_rows = max_rows
        self.min_bytes = min_bytes
        self.max_bytes = max_bytes


    def create_table_sql(self, db_name):
        # Overriden create_table_sql example: 
        #sql = 'ENGINE = Buffer(merge, hits, 16, 10, 100, 10000, 1000000, 10000000, 100000000)'
        sql = 'ENGINE = Buffer(`%s`, `%s`, %d, %d, %d, %d, %d, %d, %d)' % (
                   db_name, self.main_model.table_name(), self.num_layers,
                   self.min_time, self.max_time, self.min_rows,
                   self.max_rows, self.min_bytes, self.max_bytes
              )
        return sql
