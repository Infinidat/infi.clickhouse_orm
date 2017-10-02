from infi.clickhouse_orm import migrations
from ..test_migrations import *

operations = [
    migrations.AlterTableWithBuffer(Model4Buffer_changed)
]
