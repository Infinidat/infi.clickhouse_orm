import requests


class DatabaseException(Exception):
    pass


class Database(object):

    def __init__(self, db_name, db_url='http://localhost:8123/', username=None, password=None):
        self.db_name = db_name
        self.db_url = db_url
        self.username = username
        self.password = password
        self._send('CREATE DATABASE IF NOT EXISTS ' + db_name)

    def create_table(self, model_class):
        self._send(model_class.create_table_sql(self.db_name))

    def drop_table(self, model_class):
        self._send(model_class.drop_table_sql(self.db_name))

    def drop_database(self):
        self._send('DROP DATABASE ' + self.db_name)

    def _send(self, sql, settings=None):
        params = self._build_params(settings)
        r = requests.post(self.db_url, params=params, data=sql)
        if r.status_code != 200:
            raise DatabaseException(r.text)

    def _build_params(self, settings):
        params = dict(settings or {})
        if self.username:
            params['username'] = username
        if self.password:
            params['password'] = password
        return params
