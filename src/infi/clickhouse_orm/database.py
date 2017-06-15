import requests
from collections import namedtuple
from .models import ModelBase
from .utils import escape, parse_tsv, import_submodules
from math import ceil
import datetime
from string import Template
from six import PY3, string_types
import pytz

import logging
logger = logging.getLogger('clickhouse_orm')


Page = namedtuple('Page', 'objects number_of_objects pages_total number page_size')


class DatabaseException(Exception):
    '''
    Raised when a database operation fails.
    '''
    pass


class Database(object):
    '''
    Database instances connect to a specific ClickHouse database for running queries, 
    inserting data and other operations.
    '''

    def __init__(self, db_name, db_url='http://localhost:8123/', 
                 username=None, password=None, readonly=False, autocreate=True):
        '''
        Initializes a database instance. Unless it's readonly, the database will be
        created on the ClickHouse server if it does not already exist.

        - `db_name`: name of the database to connect to.
        - `db_url`: URL of the ClickHouse server.
        - `username`: optional connection credentials.
        - `password`: optional connection credentials.
        - `readonly`: use a read-only connection.
        - `autocreate`: automatically create the database if does not exist (unless in readonly mode).
        '''
        self.db_name = db_name
        self.db_url = db_url
        self.username = username
        self.password = password
        self.readonly = False
        self.db_exists = True
        if readonly:
            self.connection_readonly = self._is_connection_readonly()
            self.readonly = True
        elif autocreate:
            self.db_exists = False
            self.create_database()
        self.server_timezone = self._get_server_timezone()

    def create_database(self):
        '''
        Creates the database on the ClickHouse server if it does not already exist.
        '''
        self._send('CREATE DATABASE IF NOT EXISTS `%s`' % self.db_name)
        self.db_exists = True

    def drop_database(self):
        '''
        Deletes the database on the ClickHouse server.
        '''
        self._send('DROP DATABASE `%s`' % self.db_name)

    def create_table(self, model_class):
        '''
        Creates a table for the given model class, if it does not exist already.
        '''
        # TODO check that model has an engine
        if model_class.readonly:
            raise DatabaseException("You can't create read only table")
        self._send(model_class.create_table_sql(self.db_name))

    def drop_table(self, model_class):
        '''
        Drops the database table of the given model class, if it exists.
        '''
        if model_class.readonly:
            raise DatabaseException("You can't drop read only table")
        self._send(model_class.drop_table_sql(self.db_name))

    def insert(self, model_instances, batch_size=1000):
        '''
        Insert records into the database.

        - `model_instances`: any iterable containing instances of a single model class.
        - `batch_size`: number of records to send per chunk (use a lower number if your records are very large).
        '''
        from six import next
        from io import BytesIO
        i = iter(model_instances)
        try:
            first_instance = next(i)
        except StopIteration:
            return  # model_instances is empty
        model_class = first_instance.__class__

        if first_instance.readonly:
            raise DatabaseException("You can't insert into read only table")

        def gen():
            buf = BytesIO()
            buf.write(self._substitute('INSERT INTO $table FORMAT TabSeparated\n', model_class).encode('utf-8'))
            first_instance.set_database(self)
            buf.write(first_instance.to_tsv(include_readonly=False).encode('utf-8'))
            buf.write('\n'.encode('utf-8'))
            # Collect lines in batches of batch_size
            lines = 2
            for instance in i:
                instance.set_database(self)
                buf.write(instance.to_tsv(include_readonly=False).encode('utf-8'))
                buf.write('\n'.encode('utf-8'))
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
        self._send(gen())

    def count(self, model_class, conditions=None):
        '''
        Counts the number of records in the model's table.

        - `model_class`: the model to count.
        - `conditions`: optional SQL conditions (contents of the WHERE clause).
        '''
        query = 'SELECT count() FROM $table'
        if conditions:
            query += ' WHERE ' + conditions
        query = self._substitute(query, model_class)
        r = self._send(query)
        return int(r.text) if r.text else 0

    def select(self, query, model_class=None, settings=None):
        '''
        Performs a query and returns a generator of model instances.

        - `query`: the SQL query to execute.
        - `model_class`: the model class matching the query's table,
          or `None` for getting back instances of an ad-hoc model.
        - `settings`: query settings to send as HTTP GET parameters
        '''
        query += ' FORMAT TabSeparatedWithNamesAndTypes'
        query = self._substitute(query, model_class)
        r = self._send(query, settings, True)
        lines = r.iter_lines()
        field_names = parse_tsv(next(lines))
        field_types = parse_tsv(next(lines))
        model_class = model_class or ModelBase.create_ad_hoc_model(zip(field_names, field_types))
        for line in lines:
            # skip blank line left by WITH TOTALS modifier
            if line:
                yield model_class.from_tsv(line, field_names, self.server_timezone, self)

    def raw(self, query, settings=None, stream=False):
        '''
        Performs a query and returns its output as text.

        - `query`: the SQL query to execute.
        - `settings`: query settings to send as HTTP GET parameters
        - `stream`: if true, the HTTP response from ClickHouse will be streamed.
        '''
        query = self._substitute(query, None)
        return self._send(query, settings=settings, stream=stream).text

    def paginate(self, model_class, order_by, page_num=1, page_size=100, conditions=None, settings=None):
        '''
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
        '''
        count = self.count(model_class, conditions)
        pages_total = int(ceil(count / float(page_size)))
        if page_num == -1:
            page_num = pages_total
        elif page_num < 1:
            raise ValueError('Invalid page number: %d' % page_num)
        offset = (page_num - 1) * page_size
        query = 'SELECT * FROM $table'
        if conditions:
            query += ' WHERE ' + conditions
        query += ' ORDER BY %s' % order_by
        query += ' LIMIT %d, %d' % (offset, page_size)
        query = self._substitute(query, model_class)
        return Page(
            objects=list(self.select(query, model_class, settings)),
            number_of_objects=count,
            pages_total=pages_total,
            number=page_num,
            page_size=page_size
        )

    def migrate(self, migrations_package_name, up_to=9999):
        '''
        Executes schema migrations.

        - `migrations_package_name` - fully qualified name of the Python package 
          containing the migrations.
        - `up_to` - number of the last migration to apply.
        '''
        from .migrations import MigrationHistory
        logger = logging.getLogger('migrations')
        applied_migrations = self._get_applied_migrations(migrations_package_name)
        modules = import_submodules(migrations_package_name)
        unapplied_migrations = set(modules.keys()) - applied_migrations
        for name in sorted(unapplied_migrations):
            logger.info('Applying migration %s...', name)
            for operation in modules[name].operations:
                operation.apply(self)
            self.insert([MigrationHistory(package_name=migrations_package_name, module_name=name, applied=datetime.date.today())])
            if int(name[:4]) >= up_to:
                break

    def _get_applied_migrations(self, migrations_package_name):
        from .migrations import MigrationHistory
        self.create_table(MigrationHistory)
        query = "SELECT module_name from $table WHERE package_name = '%s'" % migrations_package_name
        query = self._substitute(query, MigrationHistory)
        return set(obj.module_name for obj in self.select(query))

    def _send(self, data, settings=None, stream=False):
        if isinstance(data, string_types):
            data = data.encode('utf-8')
        params = self._build_params(settings)
        r = requests.post(self.db_url, params=params, data=data, stream=stream)
        if r.status_code != 200:
            raise DatabaseException(r.text)
        return r

    def _build_params(self, settings):
        params = dict(settings or {})
        if self.db_exists:
            params['database'] = self.db_name
        if self.username:
            params['user'] = self.username
        if self.password:
            params['password'] = self.password
        # Send the readonly flag, unless the connection is already readonly (to prevent db error)
        if self.readonly and not self.connection_readonly:
            params['readonly'] = '1'
        return params

    def _substitute(self, query, model_class=None):
        '''
        Replaces $db and $table placeholders in the query.
        '''
        if '$' in query:
            mapping = dict(db="`%s`" % self.db_name)
            if model_class:
                mapping['table'] = "`%s`.`%s`" % (self.db_name, model_class.table_name())
            query = Template(query).substitute(mapping)
        return query

    def _get_server_timezone(self):
        try:
            r = self._send('SELECT timezone()')
            return pytz.timezone(r.text.strip())
        except DatabaseException:
            logger.exception('Cannot determine server timezone, assuming UTC')
            return pytz.utc

    def _is_connection_readonly(self):
        r = self._send("SELECT value FROM system.settings WHERE name = 'readonly'")
        return r.text.strip() != '0'
