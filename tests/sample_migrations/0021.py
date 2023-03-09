from infi.clickhouse_orm import migrations
from ..test_migrations import *

operations = [
    migrations.ModifyTTL(ModelWithTTLs,
        [
            "date_two + INTERVAL 24 MONTH DELETE",
            "date_two + INTERVAL 1 YEAR TO DISK 'default'"
        ]
    )
]
