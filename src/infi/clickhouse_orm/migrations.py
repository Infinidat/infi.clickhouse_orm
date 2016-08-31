from .models import Model
from .fields import DateField, StringField
from .engines import MergeTree
from .utils import escape

from six.moves import zip

import logging
logger = logging.getLogger('migrations')


class Operation(object):
    '''
    Base class for migration operations.
    '''

    def apply(self, database):
        raise NotImplementedError()


class CreateTable(Operation):
    '''
    A migration operation that creates a table for a given model class.
    '''

    def __init__(self, model_class):
        self.model_class = model_class

    def apply(self, database):
        logger.info('    Create table %s', self.model_class.table_name())
        database.create_table(self.model_class)


class AlterTable(Operation):
    '''
    A migration operation that compares the table of a given model class to
    the model's fields, and alters the table to match the model. The operation can:
      - add new columns
      - drop obsolete columns
      - modify column types
    Default values are not altered by this operation.
    '''

    def __init__(self, model_class):
        self.model_class = model_class

    def _get_table_fields(self, database):
        query = "DESC `%s`.`%s`" % (database.db_name, self.model_class.table_name())
        return [(row.name, row.type) for row in database.select(query)]

    def _alter_table(self, database, cmd):
        cmd = "ALTER TABLE `%s`.`%s` %s" % (database.db_name, self.model_class.table_name(), cmd)
        logger.debug(cmd)
        database._send(cmd)

    def apply(self, database):
        logger.info('    Alter table %s', self.model_class.table_name())
        table_fields = dict(self._get_table_fields(database))
        # Identify fields that were deleted from the model
        deleted_fields = set(table_fields.keys()) - set(name for name, field in self.model_class._fields)
        for name in deleted_fields:
            logger.info('        Drop column %s', name)
            self._alter_table(database, 'DROP COLUMN %s' % name)
            del table_fields[name]
        # Identify fields that were added to the model
        prev_name = None
        for name, field in self.model_class._fields:
            if name not in table_fields:
                logger.info('        Add column %s', name)
                assert prev_name, 'Cannot add a column to the beginning of the table'
                cmd = 'ADD COLUMN %s %s AFTER %s' % (name, field.get_sql(), prev_name)
                self._alter_table(database, cmd)
            prev_name = name
        # Identify fields whose type was changed
        model_fields = [(name, field.get_sql(with_default=False)) for name, field in self.model_class._fields]
        for model_field, table_field in zip(model_fields, self._get_table_fields(database)):
            assert model_field[0] == table_field[0], 'Model fields and table columns in disagreement'
            if model_field[1] != table_field[1]:
                logger.info('        Change type of column %s from %s to %s', table_field[0], table_field[1], model_field[1])
                self._alter_table(database, 'MODIFY COLUMN %s %s' % model_field)


class DropTable(Operation):
    '''
    A migration operation that drops the table of a given model class.
    '''

    def __init__(self, model_class):
        self.model_class = model_class

    def apply(self, database):
        logger.info('    Drop table %s', self.model_class.__name__)
        database.drop_table(self.model_class)


class MigrationHistory(Model):
    '''
    A model for storing which migrations were already applied to the containing database.
    '''

    package_name = StringField()
    module_name = StringField()
    applied = DateField()

    engine = MergeTree('applied', ('package_name', 'module_name'))

    @classmethod
    def table_name(cls):
        return 'infi_clickhouse_orm_migrations'
