from __future__ import unicode_literals, annotations

import logging
from typing import TYPE_CHECKING, Optional, Union

from .utils import comma_join, get_subclass_names


if TYPE_CHECKING:
    from clickhouse_orm.database import Database
    from clickhouse_orm.models import Model
    from clickhouse_orm.funcs import F

logger = logging.getLogger("clickhouse_orm")


class TableEngine:
    def create_table_sql(self, db: Database) -> str:
        raise NotImplementedError()  # pragma: no cover


class DatabaseEngine:
    def create_database_sql(self) -> str:
        raise NotImplementedError()  # pragma: no cover


class Atomic(DatabaseEngine):
    """
    It supports non-blocking DROP TABLE and RENAME TABLE queries and atomic EXCHANGE TABLES queries.
    Atomic database engine is used by default.
    """

    def create_database_sql(self) -> str:
        return "Atomic"


class Lazy(DatabaseEngine):
    """
    Keeps tables in RAM only expiration_time_in_seconds seconds after last access.
    Can be used only with *Log tables.

    It’s optimized for storing many small *Log tables,
    for which there is a long time interval between accesses.
    """

    def __init__(self, expiration_time_in_seconds: int):
        self.expiration_time_in_seconds = expiration_time_in_seconds

    def create_database_sql(self) -> str:
        return f"Lazy({self.expiration_time_in_seconds})"


class MySQL(DatabaseEngine):
    """
    Allows to connect to databases on a remote MySQL server and perform INSERT and
    SELECT queries to exchange data between ClickHouse and MySQL.

    The MySQL database engine translate queries to the MySQL server so you can perform operations
    such as SHOW TABLES or SHOW CREATE TABLE.
    """

    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        """
        - `host`: MySQL server address.
        - `port`: MySQL server port.
        - `database`: Remote database name.
        - `user`: MySQL user.
        - `password`: User password.
        """
        self.host_port = f"{host}:{port}"
        self.database = database
        self.user = user
        self.password = password

    def create_database_sql(self) -> str:
        return f"MySQL('{self.host_port}', '{self.database}', '{self.user}', '{self.password}')"


class PostgreSQL(DatabaseEngine):
    """
    Allows to connect to databases on a remote PostgreSQL server. Supports read and write operations
     (SELECT and INSERT queries) to exchange data between ClickHouse and PostgreSQL.

    Gives the real-time access to table list and table structure from
    remote PostgreSQL with the help of SHOW TABLES and DESCRIBE TABLE queries.

    Supports table structure modifications (ALTER TABLE ... ADD|DROP COLUMN).
    If use_table_cache parameter (see the Engine Parameters below) it set to 1,
    the table structure is cached and not checked for being modified,
    but can be updated with DETACH and ATTACH queries.
    """

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        schema: str = None,
        use_table_cache: int = None,
    ):
        """
        - `host`: PostgreSQL server address.
        - `port`: PostgreSQL server port.
        - `database`: Remote database name.
        - `user`: PostgreSQL user.
        - `password`: User password.
        - `schema`: PostgreSQL schema.
        - `use_table_cache`: Defines if the database table structure is cached or not.
        """
        self.host_port = f"{host}:{port}"
        self.database = database
        self.user = user
        self.password = password
        self.schema = schema
        self.use_table_cache = use_table_cache
        self._params = [
            f"'{self.password}'",
            f"'{self.database}'",
            f"'{self.user}'",
            f"'{self.password}'",
        ]
        if self.schema is not None:
            self._params.append(f"'{self.schema}'")
        if self.use_table_cache is not None:
            self._params.append(str(self.use_table_cache))

    def create_database_sql(self) -> str:
        return f"PostgreSQL({','.join(self._params)})"


class SQLite(DatabaseEngine):
    """
    Allows to connect to SQLite database and perform INSERT and SELECT queries to
    exchange data between ClickHouse and SQLite.
    """
    def __init__(self, db_path: str):
        """
        - `db_path`: Path to a file with SQLite database.
        """
        self.db_path = db_path

    def create_database_sql(self) -> str:
        return f"SQLite('{self.db_path}')"


class TinyLog(TableEngine):
    def create_table_sql(self, db):
        return "TinyLog"


class Log(TableEngine):
    def create_table_sql(self, db):
        return "Log"


class Memory(TableEngine):
    def create_table_sql(self, db):
        return "Memory"


class MergeTree(TableEngine):
    def __init__(
        self,
        date_col: Optional[str] = None,
        order_by: Union[list, tuple] = (),
        sampling_expr: Optional[F] = None,
        index_granularity: int = 8192,
        replica_table_path: Optional[str] = None,
        replica_name: Optional[str] = None,
        partition_key: Optional[Union[list, tuple]] = None,
        primary_key: Optional[Union[list, tuple]] = None,
    ):
        assert type(order_by) in (list, tuple), "order_by must be a list or tuple"
        assert date_col is None or isinstance(date_col, str), "date_col must be string if present"
        assert primary_key is None or type(primary_key) in (
            list,
            tuple,
        ), "primary_key must be a list or tuple"
        assert partition_key is None or type(partition_key) in (
            list,
            tuple,
        ), "partition_key must be tuple or list if present"
        assert (replica_table_path is None) == (
            replica_name is None
        ), "both replica_table_path and replica_name must be specified"

        # These values conflict with each other (old and new syntax of table engines.
        # So let's control only one of them is given.
        assert date_col or partition_key, "You must set either date_col or partition_key"
        self.date_col = date_col
        self.partition_key = partition_key if partition_key else ("toYYYYMM(`%s`)" % date_col,)
        self.primary_key = primary_key

        self.order_by = order_by
        self.sampling_expr = sampling_expr
        self.index_granularity = index_granularity
        self.replica_table_path = replica_table_path
        self.replica_name = replica_name

    # I changed field name for new reality and syntax
    @property
    def key_cols(self):
        logger.warning(
            "`key_cols` attribute is deprecated and may be removed in future. "
            "Use `order_by` attribute instead"
        )
        return self.order_by

    @key_cols.setter
    def key_cols(self, value):
        logger.warning(
            "`key_cols` attribute is deprecated and may be removed in future. "
            "Use `order_by` attribute instead"
        )
        self.order_by = value

    def create_table_sql(self, db: Database) -> str:
        name = self.__class__.__name__
        if self.replica_name:
            name = "Replicated" + name

        # In ClickHouse 1.1.54310 custom partitioning key was introduced
        # https://clickhouse.tech/docs/en/table_engines/custom_partitioning_key/
        # Let's check version and use new syntax if available
        if db.server_version >= (1, 1, 54310):
            partition_sql = "PARTITION BY (%s) ORDER BY (%s)" % (
                comma_join(self.partition_key, stringify=True),
                comma_join(self.order_by, stringify=True),
            )

            if self.primary_key:
                partition_sql += " PRIMARY KEY (%s)" % comma_join(self.primary_key, stringify=True)

            if self.sampling_expr:
                partition_sql += " SAMPLE BY %s" % self.sampling_expr

            partition_sql += " SETTINGS index_granularity=%d" % self.index_granularity

        elif not self.date_col:
            # Can't import it globally due to circular import
            from clickhouse_orm.database import DatabaseException

            raise DatabaseException(
                "Custom partitioning is not supported before ClickHouse 1.1.54310. "
                "Please update your server or use date_col syntax."
                "https://clickhouse.tech/docs/en/table_engines/custom_partitioning_key/"
            )
        else:
            partition_sql = ""

        params = self._build_sql_params(db)
        return "%s(%s) %s" % (name, comma_join(params), partition_sql)

    def _build_sql_params(self, db: Database) -> list[str]:
        params = []
        if self.replica_name:
            params += ["'%s'" % self.replica_table_path, "'%s'" % self.replica_name]

        # In ClickHouse 1.1.54310 custom partitioning key was introduced
        # https://clickhouse.tech/docs/en/table_engines/custom_partitioning_key/
        # These parameters are process in create_table_sql directly.
        # In previous ClickHouse versions this this syntax does not work.
        if db.server_version < (1, 1, 54310):
            params.append(self.date_col)
            if self.sampling_expr:
                params.append(self.sampling_expr)
            params.append("(%s)" % comma_join(self.order_by, stringify=True))
            params.append(str(self.index_granularity))

        return params


class CollapsingMergeTree(MergeTree):
    def __init__(
        self,
        date_col=None,
        order_by=(),
        sign_col="sign",
        sampling_expr=None,
        index_granularity=8192,
        replica_table_path=None,
        replica_name=None,
        partition_key=None,
        primary_key=None,
    ):
        super(CollapsingMergeTree, self).__init__(
            date_col,
            order_by,
            sampling_expr,
            index_granularity,
            replica_table_path,
            replica_name,
            partition_key,
            primary_key,
        )
        self.sign_col = sign_col

    def _build_sql_params(self, db: Database) -> list[str]:
        params = super()._build_sql_params(db)
        params.append(self.sign_col)
        return params


class SummingMergeTree(MergeTree):
    def __init__(
        self,
        date_col=None,
        order_by=(),
        summing_cols=None,
        sampling_expr=None,
        index_granularity=8192,
        replica_table_path=None,
        replica_name=None,
        partition_key=None,
        primary_key=None,
    ):
        super(SummingMergeTree, self).__init__(
            date_col,
            order_by,
            sampling_expr,
            index_granularity,
            replica_table_path,
            replica_name,
            partition_key,
            primary_key,
        )
        assert type is None or type(summing_cols) in (
            list,
            tuple,
        ), "summing_cols must be a list or tuple"
        self.summing_cols = summing_cols

    def _build_sql_params(self, db: Database) -> list[str]:
        params = super(SummingMergeTree, self)._build_sql_params(db)
        if self.summing_cols:
            params.append("(%s)" % comma_join(self.summing_cols))
        return params


class ReplacingMergeTree(MergeTree):
    def __init__(
        self,
        date_col=None,
        order_by=(),
        ver_col=None,
        sampling_expr=None,
        index_granularity=8192,
        replica_table_path=None,
        replica_name=None,
        partition_key=None,
        primary_key=None,
    ):
        super(ReplacingMergeTree, self).__init__(
            date_col,
            order_by,
            sampling_expr,
            index_granularity,
            replica_table_path,
            replica_name,
            partition_key,
            primary_key,
        )
        self.ver_col = ver_col

    def _build_sql_params(self, db: Database) -> list[str]:
        params = super(ReplacingMergeTree, self)._build_sql_params(db)
        if self.ver_col:
            params.append(self.ver_col)
        return params


class Buffer(TableEngine):
    """
    Buffers the data to write in RAM, periodically flushing it to another table.
    Must be used in conjuction with a `BufferModel`.
    Read more [here](https://clickhouse.tech/docs/en/engines/table-engines/special/buffer/).
    """

    def __init__(
        self,
        main_model: type[Model],
        num_layers: int = 16,
        min_time: int = 10,
        max_time: int = 100,
        min_rows: int = 10000,
        max_rows: int = 1000000,
        min_bytes: int = 10000000,
        max_bytes: int = 100000000,
    ):
        self.main_model = main_model
        self.num_layers = num_layers
        self.min_time = min_time
        self.max_time = max_time
        self.min_rows = min_rows
        self.max_rows = max_rows
        self.min_bytes = min_bytes
        self.max_bytes = max_bytes

    def create_table_sql(self, db: Database) -> str:
        # Overriden create_table_sql example:
        # sql = 'ENGINE = Buffer(merge, hits, 16, 10, 100, 10000, 1000000, 10000000, 100000000)'
        sql = "ENGINE = Buffer(`%s`, `%s`, %d, %d, %d, %d, %d, %d, %d)" % (
            db.db_name,
            self.main_model.table_name(),
            self.num_layers,
            self.min_time,
            self.max_time,
            self.min_rows,
            self.max_rows,
            self.min_bytes,
            self.max_bytes,
        )
        return sql


class Merge(TableEngine):
    """
    The Merge engine (not to be confused with MergeTree) does not store data itself,
    but allows reading from any number of other tables simultaneously.
    Writing to a table is not supported
    https://clickhouse.tech/docs/en/engines/table-engines/special/merge/
    """

    def __init__(self, table_regex: str):
        assert isinstance(table_regex, str), "'table_regex' parameter must be string"
        self.table_regex = table_regex

    def create_table_sql(self, db: Database) -> str:
        return "Merge(`%s`, '%s')" % (db.db_name, self.table_regex)


class Distributed(TableEngine):
    """
    The Distributed engine by itself does not store data,
    but allows distributed query processing on multiple servers.
    Reading is automatically parallelized.
    During a read, the table indexes on remote servers are used, if there are any.

    See full documentation here
    https://clickhouse.tech/docs/en/engines/table-engines/special/distributed/
    """

    def __init__(self, cluster, table=None, sharding_key=None):
        """
        - `cluster`: what cluster to access data from
        - `table`: underlying table that actually stores data.
        If you are not specifying any table here, ensure that it can be inferred
        from your model's superclass (see models.DistributedModel.fix_engine_table)
        - `sharding_key`: how to distribute data among shards when inserting
        straightly into Distributed table, optional
        """
        self.cluster = cluster
        self.table = table
        self.sharding_key = sharding_key

    @property
    def table_name(self) -> str:
        from clickhouse_orm.models import ModelBase

        table = self.table

        if isinstance(table, ModelBase):
            return table.table_name()

        return table

    def create_table_sql(self, db: Database) -> str:
        name = self.__class__.__name__
        params = self._build_sql_params(db)
        return "%s(%s)" % (name, ", ".join(params))

    def _build_sql_params(self, db: Database) -> list[str]:
        if self.table_name is None:
            raise ValueError(
                "Cannot create {} engine: specify an underlying table".format(
                    self.__class__.__name__
                )
            )

        params = ["`%s`" % p for p in [self.cluster, db.db_name, self.table_name]]
        if self.sharding_key:
            params.append(self.sharding_key)
        return params


# Expose only relevant classes in import *
__all__ = get_subclass_names(locals(), TableEngine)
