import requests
from collections import namedtuple
from models import ModelBase
from utils import escape, parse_tsv
from math import ceil


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
            yield 'INSERT INTO `%s`.`%s` FORMAT TabSeparated\n' % (self.db_name, model_class.table_name())
            yield first_instance.to_tsv()
            yield '\n'
            for instance in i:
                yield instance.to_tsv()
                yield '\n'
        self._send(gen())

    def count(self, model_class, conditions=None):
        query = 'SELECT count() FROM `%s`.`%s`' % (self.db_name, model_class.table_name())
        if conditions:
            query += ' WHERE ' + conditions
        r = self._send(query)
        return int(r.text) if r.text else 0

    def select(self, query, model_class=None, settings=None):
        query += ' FORMAT TabSeparatedWithNamesAndTypes'
        r = self._send(query, settings)
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
        query = 'SELECT * FROM `%s`.`%s`' % (self.db_name, model_class.table_name())
        if conditions:
            query += ' WHERE ' + conditions
        query += ' ORDER BY %s' % order_by
        query += ' LIMIT %d, %d' % (offset, page_size)
        return Page(
            objects=list(self.select(query, model_class, settings)),
            number_of_objects=count,
            pages_total=pages_total,
            number=page_num,
            page_size=page_size
        )

    def _send(self, data, settings=None):
        params = self._build_params(settings)
        r = requests.post(self.db_url, params=params, data=data, stream=True)
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
