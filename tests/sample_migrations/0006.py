from __future__ import annotations

from clickhouse_orm import migrations

from ..test_migrations import *

operations = [migrations.CreateTable(EnumModel1)]
