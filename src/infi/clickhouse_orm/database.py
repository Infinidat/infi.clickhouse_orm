import requests
from collections import namedtuple
from models import ModelBase
from utils import escape, parse_tsv, import_submodules
from math import ceil
import datetime
import logging
from string import Template


Page = namedtuple('Page', 'objects number_of_objects pages_total number page_size')


class DatabaseException(Exception):
    pass


class Database(object):

    def __init__(self, db_name, db_url='http://localhost:8123/', username=None, password=None):
        self.db_name = db_name
        self.db_url = db_url
        self.username = username
        self.password = password
        self._send('CREATE DATABASE IF NOT EXISTS `%s`' % db_name)

    def create_table(self, model_class):
        # TODO check that model has an engine
        self._send(model_class.create_table_sql(self.db_name))

    def drop_table(self, model_class):
        self._send(model_class.drop_table_sql(self.db_name))

    def drop_database(self):
        self._send('DROP DATABASE `%s`' % self.db_name)

    def insert(self, model_instances):
        i = iter(model_instances)
        try:
            first_instance = i.next()
        except StopIteration:
            return # model_instances is empty
        model_class = first_instance.__class__
        def gen():
            yield self._substitute('INSERT INTO $table FORMAT TabSeparated\n', model_class)
            yield first_instance.to_tsv()
            yield '\n'
            for instance in i:
                yield instance.to_tsv()
                yield '\n'
        self._send(gen())

    def count(self, model_class, conditions=None):
        query = 'SELECT count() FROM $table'
        if conditions:
            query += ' WHERE ' + conditions
        query = self._substitute(query, model_class)
        r = self._send(query)
        return int(r.text) if r.text else 0

    def select(self, query, model_class=None, settings=None):
        query += ' FORMAT TabSeparatedWithNamesAndTypes'
        query = self._substitute(query, model_class)
        r = self._send(query, settings, True)
        lines = r.iter_lines()
        field_names = parse_tsv(next(lines))
        field_types = parse_tsv(next(lines))
        model_class = model_class or ModelBase.create_ad_hoc_model(zip(field_names, field_types))
        for line in lines:
            yield model_class.from_tsv(line, field_names)

    def paginate(self, model_class, order_by, page_num=1, page_size=100, conditions=None, settings=None):
        count = self.count(model_class, conditions)
        pages_total = int(ceil(count / float(page_size)))
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
        from migrations import MigrationHistory
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
        from migrations import MigrationHistory
        self.create_table(MigrationHistory)
        query = "SELECT module_name from $table WHERE package_name = '%s'" % migrations_package_name
        query = self._substitute(query, MigrationHistory)
        return set(obj.module_name for obj in self.select(query))

    def _send(self, data, settings=None, stream=False):
        params = self._build_params(settings)
        r = requests.post(self.db_url, params=params, data=data, stream=stream)
        if r.status_code != 200:
            raise DatabaseException(r.text)
        return r

    def _build_params(self, settings):
        params = dict(settings or {})
        if self.username:
            params['username'] = username
        if self.password:
            params['password'] = password
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
