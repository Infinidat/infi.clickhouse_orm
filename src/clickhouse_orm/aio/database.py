from __future__ import annotations
import datetime
import logging
from io import BytesIO
from math import ceil
from typing import Optional, AsyncGenerator

import httpx
import pytz

from clickhouse_orm.models import MODEL, ModelBase
from clickhouse_orm.utils import parse_tsv, import_submodules
from clickhouse_orm.database import Database, ServerError, DatabaseException, logger, Page


# pylint: disable=C0116


class AioDatabase(Database):
    _client_class = httpx.AsyncClient

    async def init(self):
        if self._init:
            return
        self.db_exists = await self._is_existing_database()
        if self._readonly:
            if not self.db_exists:
                raise DatabaseException(
                    "Database does not exist, and cannot be created under readonly connection"
                )
            self.connection_readonly = await self._is_connection_readonly()
            self.readonly = True
        elif self.auto_create and not self.db_exists:
            await self.create_database()
        self.server_version = await self._get_server_version()
        if self.server_version > (1, 1, 53981):
            self.server_timezone = await self._get_server_timezone()
        else:
            self.server_timezone = pytz.utc
        self.has_codec_support = self.server_version >= (19, 1, 16)
        self.has_low_cardinality_support = self.server_version >= (19, 0)
        self._init = True

    async def close(self):
        await self.request_session.aclose()

    async def _send(
        self, data: str | bytes | AsyncGenerator, settings: dict = None, stream: bool = False
    ):
        r = await super()._send(data, settings, stream)
        if r.status_code != 200:
            await r.aread()
            raise ServerError(r.text)
        return r

    async def count(self, model_class: type[MODEL], conditions=None) -> int:
        """
        Counts the number of records in the model's table.

        - `model_class`: the model to count.
        - `conditions`: optional SQL conditions (contents of the WHERE clause).
        """
        from clickhouse_orm.query import Q

        if not self._init:
            raise DatabaseException(
                "The AioDatabase object must execute the init method before it can be used"
            )

        query = "SELECT count() FROM $table"
        if conditions:
            if isinstance(conditions, Q):
                conditions = conditions.to_sql(model_class)
            query += " WHERE " + str(conditions)
        query = self._substitute(query, model_class)
        r = await self._send(query)
        return int(r.text) if r.text else 0

    async def create_database(self):
        """
        Creates the database on the ClickHouse server if it does not already exist.
        """
        await self._send(
            "CREATE DATABASE IF NOT EXISTS `%s` ENGINE = %s"
            % (self.db_name, self.engine.create_database_sql())
        )
        self.db_exists = True

    async def drop_database(self):
        """
        Deletes the database on the ClickHouse server.
        """
        await self._send("DROP DATABASE `%s`" % self.db_name)
        self.db_exists = False

    async def create_table(self, model_class: type[MODEL]) -> None:
        """
        Creates a table for the given model class, if it does not exist already.
        """
        if not self._init:
            raise DatabaseException(
                "The AioDatabase object must execute the init method before it can be used"
            )
        if model_class.is_system_model():
            raise DatabaseException("You can't create system table")
        if model_class.is_temporary_model() and self.session_id is None:
            raise DatabaseException(
                "Creating a temporary table must be within the lifetime of a session "
            )
        if getattr(model_class, "engine") is None:
            raise DatabaseException(f"%s class must define an engine" % model_class.__name__)
        await self._send(model_class.create_table_sql(self))

    async def create_temporary_table(self, model_class: type[MODEL], table_name: str = None):
        """
        Creates a temporary table for the given model class, if it does not exist already.
        And you can specify the temporary table name explicitly.
        """
        if not self._init:
            raise DatabaseException(
                "The AioDatabase object must execute the init method before it can be used"
            )

        await self._send(model_class.create_temporary_table_sql(self, table_name))

    async def drop_table(self, model_class: type[MODEL]) -> None:
        """
        Drops the database table of the given model class, if it exists.
        """
        if not self._init:
            raise DatabaseException(
                "The AioDatabase object must execute the init method before it can be used"
            )

        if model_class.is_system_model():
            raise DatabaseException("You can't drop system table")
        await self._send(model_class.drop_table_sql(self))

    async def does_table_exist(self, model_class: type[MODEL]) -> bool:
        """
        Checks whether a table for the given model class already exists.
        Note that this only checks for existence of a table with the expected name.
        """
        if not self._init:
            raise DatabaseException(
                "The AioDatabase object must execute the init method before it can be used"
            )

        sql = "SELECT count() FROM system.tables WHERE database = '%s' AND name = '%s'"
        r = await self._send(sql % (self.db_name, model_class.table_name()))
        return r.text.strip() == "1"

    async def get_model_for_table(self, table_name: str, system_table: bool = False):
        """
        Generates a model class from an existing table in the database.
        This can be used for querying tables which don't have a corresponding model class,
        for example system tables.

        - `table_name`: the table to create a model for
        - `system_table`: whether the table is a system table, or belongs to the current database
        """
        db_name = "system" if system_table else self.db_name
        sql = "DESCRIBE `%s`.`%s` FORMAT TSV" % (db_name, table_name)
        lines = await self._send(sql)
        fields = [parse_tsv(line)[:2] async for line in lines.aiter_lines()]
        model = ModelBase.create_ad_hoc_model(fields, table_name)
        if system_table:
            model._system = model._readonly = True
        return model

    async def insert(self, model_instances, batch_size=1000):
        """
        Insert records into the database.

        - `model_instances`: any iterable containing instances of a single model class.
        - `batch_size`: number of records to send per chunk (use a lower number if your records are very large).
        """
        i = iter(model_instances)
        try:
            first_instance = next(i)
        except StopIteration:
            return  # model_instances is empty
        model_class = first_instance.__class__

        if first_instance.is_read_only() or first_instance.is_system_model():
            raise DatabaseException("You can't insert into read only and system tables")

        fields_list = ",".join(["`%s`" % name for name in first_instance.fields(writable=True)])
        fmt = "TSKV" if model_class.has_funcs_as_defaults() else "TabSeparated"
        query = "INSERT INTO $table (%s) FORMAT %s\n" % (fields_list, fmt)

        async def gen():
            buf = BytesIO()
            buf.write(self._substitute(query, model_class).encode("utf-8"))
            first_instance.set_database(self)
            buf.write(first_instance.to_db_string())
            # Collect lines in batches of batch_size
            lines = 2
            for instance in i:
                instance.set_database(self)
                buf.write(instance.to_db_string())
                lines += 1
                if lines >= batch_size:
                    # Return the current batch of lines
                    yield buf.getvalue()
                    # Start a new batch
                    buf = BytesIO()
                    lines = 0
            # Return any remaining lines in partial batch
            if lines:
                yield buf.getvalue()

        await self._send(gen())

    async def select(
        self, query: str, model_class: Optional[type[MODEL]] = None, settings: Optional[dict] = None
    ) -> AsyncGenerator[MODEL, None]:
        """
        Performs a query and returns a generator of model instances.

        - `query`: the SQL query to execute.
        - `model_class`: the model class matching the query's table,
          or `None` for getting back instances of an ad-hoc model.
        - `settings`: query settings to send as HTTP GET parameters
        """
        query += " FORMAT TabSeparatedWithNamesAndTypes"
        query = self._substitute(query, model_class)
        r = await self._send(query, settings, True)
        try:
            field_names, field_types = None, None
            async for line in r.aiter_lines():
                # skip blank line left by WITH TOTALS modifier
                if not field_names:
                    field_names = parse_tsv(line)
                elif not field_types:
                    field_types = parse_tsv(line)
                    model_class = model_class or ModelBase.create_ad_hoc_model(
                        zip(field_names, field_types)
                    )
                elif line.strip():
                    yield model_class.from_tsv(line, field_names, self.server_timezone, self)
        except StopIteration:
            return
        finally:
            await r.aclose()

    async def raw(self, query: str, settings: Optional[dict] = None, stream: bool = False) -> str:
        """
        Performs a query and returns its output as text.

        - `query`: the SQL query to execute.
        - `settings`: query settings to send as HTTP GET parameters
        - `stream`: if true, the HTTP response from ClickHouse will be streamed.
        """
        query = self._substitute(query, None)
        return (await self._send(query, settings=settings, stream=stream)).text

    async def paginate(
        self,
        model_class: type[MODEL],
        order_by: str,
        page_num: int = 1,
        page_size: int = 100,
        conditions=None,
        settings: Optional[dict] = None,
    ):
        """
        Selects records and returns a single page of model instances.

        - `model_class`: the model class matching the query's table,
          or `None` for getting back instances of an ad-hoc model.
        - `order_by`: columns to use for sorting the query (contents of the ORDER BY clause).
        - `page_num`: the page number (1-based), or -1 to get the last page.
        - `page_size`: number of records to return per page.
        - `conditions`: optional SQL conditions (contents of the WHERE clause).
        - `settings`: query settings to send as HTTP GET parameters

        The result is a namedtuple containing `objects` (list), `number_of_objects`,
        `pages_total`, `number` (of the current page), and `page_size`.
        """
        from clickhouse_orm.query import Q

        count = await self.count(model_class, conditions)
        pages_total = int(ceil(count / float(page_size)))
        if page_num == -1:
            page_num = max(pages_total, 1)
        elif page_num < 1:
            raise ValueError("Invalid page number: %d" % page_num)
        offset = (page_num - 1) * page_size
        query = "SELECT * FROM $table"
        if conditions:
            if isinstance(conditions, Q):
                conditions = conditions.to_sql(model_class)
            query += " WHERE " + str(conditions)
        query += " ORDER BY %s" % order_by
        query += " LIMIT %d, %d" % (offset, page_size)
        query = self._substitute(query, model_class)
        return Page(
            objects=[r async for r in self.select(query, model_class, settings)] if count else [],
            number_of_objects=count,
            pages_total=pages_total,
            number=page_num,
            page_size=page_size,
        )

    async def migrate(self, migrations_package_name, up_to=9999):
        """
        Executes schema migrations.

        - `migrations_package_name` - fully qualified name of the Python package
          containing the migrations.
        - `up_to` - number of the last migration to apply.
        """
        from ..migrations import MigrationHistory

        logger = logging.getLogger("migrations")
        applied_migrations = await self._get_applied_migrations(migrations_package_name)
        modules = import_submodules(migrations_package_name)
        unapplied_migrations = set(modules.keys()) - applied_migrations
        for name in sorted(unapplied_migrations):
            logger.info("Applying migration %s...", name)
            for operation in modules[name].operations:
                operation.apply(self)
            await self.insert(
                [
                    MigrationHistory(
                        package_name=migrations_package_name,
                        module_name=name,
                        applied=datetime.date.today(),
                    )
                ]
            )
            if int(name[:4]) >= up_to:
                break

    async def _is_existing_database(self):
        r = await self._send(
            "SELECT count() FROM system.databases WHERE name = '%s'" % self.db_name
        )
        return r.text.strip() == "1"

    async def _is_connection_readonly(self):
        r = await self._send("SELECT value FROM system.settings WHERE name = 'readonly'")
        return r.text.strip() != "0"

    async def _get_server_timezone(self):
        try:
            r = await self._send("SELECT timezone()")
            return pytz.timezone(r.text.strip())
        except ServerError as err:
            logger.exception("Cannot determine server timezone (%s), assuming UTC", err)
            return pytz.utc

    async def _get_server_version(self, as_tuple=True):
        try:
            r = await self._send("SELECT version();")
            ver = r.text
        except ServerError as err:
            logger.exception("Cannot determine server version (%s), assuming 1.1.0", err)
            ver = "1.1.0"
        return tuple(int(n) for n in ver.split(".") if n.isdigit()) if as_tuple else ver

    async def _get_applied_migrations(self, migrations_package_name):
        from ..migrations import MigrationHistory

        await self.create_table(MigrationHistory)
        query = "SELECT module_name from $table WHERE package_name = '%s'" % migrations_package_name
        query = self._substitute(query, MigrationHistory)
        return set(obj.module_name async for obj in self.select(query))


__all__ = [AioDatabase]
