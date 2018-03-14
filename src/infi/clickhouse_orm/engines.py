from __future__ import unicode_literals

import six

from .utils import comma_join


class Engine(object):

    def create_table_sql(self):
        raise NotImplementedError()   # pragma: no cover


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
        return '%s(%s)' % (name, comma_join(params))

    def _build_sql_params(self):
        params = []
        if self.replica_name:
            params += ["'%s'" % self.replica_table_path, "'%s'" % self.replica_name]
        params.append(self.date_col)
        if self.sampling_expr:
            params.append(self.sampling_expr)
        params.append('(%s)' % comma_join(self.key_cols))
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
            params.append('(%s)' % comma_join(self.summing_cols))
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


class Merge(Engine):
    """
    The Merge engine (not to be confused with MergeTree) does not store data itself,
    but allows reading from any number of other tables simultaneously.
    Writing to a table is not supported
    https://clickhouse.yandex/docs/en/single/index.html#document-table_engines/merge
    """

    def __init__(self, table_regex):
        assert isinstance(table_regex, six.string_types), "'table_regex' parameter must be string"

        self.table_regex = table_regex

        # Use current database as default
        self.db_name = None

    def create_table_sql(self):
        db_name = ("`%s`" % self.db_name) if self.db_name else 'currentDatabase()'
        return "Merge(%s, '%s')" % (db_name, self.table_regex)

    def set_db_name(self, db_name):
        assert isinstance(db_name, six.string_types), "'db_name' parameter must be string"
        self.db_name = db_name


class Distributed(Engine):
    """
    The Distributed engine by itself does not store data,
    but allows distributed query processing on multiple servers.
    Reading is automatically parallelized.
    During a read, the table indexes on remote servers are used, if there are any.

    See full documentation here
    https://clickhouse.yandex/docs/en/table_engines/distributed.html
    """
    def __init__(self, cluster, table=None, db_name=None, sharding_key=None):
        """
        :param cluster: what cluster to access data from
        :param table: underlying table that actually stores data.
        If you are not specifying any table here, ensure that it can be inferred
        from your model's superclass (see models.DistributedModel.fix_engine_table)
        :param db_name: which database to access data from
        By default it is 'currentDatabase()'
        :param sharding_key: how to distribute data among shards when inserting
        straightly into Distributed table, optional
        """
        self.cluster = cluster
        self.table = table
        self.db_name = db_name
        self.sharding_key = sharding_key

    @property
    def table_name(self):
        # TODO: circular import is bad
        from .models import ModelBase

        table = self.table

        if isinstance(table, ModelBase):
            return table.table_name()

        return table

    def set_db_name(self, db_name):
        assert isinstance(db_name, six.string_types), "'db_name' parameter must be string"
        self.db_name = db_name

    def create_table_sql(self):
        name = self.__class__.__name__
        params = self._build_sql_params()
        return '%s(%s)' % (name, ', '.join(params))

    def _build_sql_params(self):
        db_name = ("`%s`" % self.db_name) if self.db_name else 'currentDatabase()'

        if self.table_name is None:
            raise ValueError("Cannot create {} engine: specify an underlying table".format(
                self.__class__.__name__))

        params = [self.cluster, db_name, self.table_name]
        if self.sharding_key:
            params.append(self.sharding_key)
        return params
