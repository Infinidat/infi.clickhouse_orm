from clickhouse_orm import migrations

from ..test_migrations import *

operations = [migrations.CreateTable(ModelWithIndex)]
