from clickhouse_orm import migrations

from ..test_migrations import *

operations = [migrations.AlterConstraints(ModelWithConstraints2)]
