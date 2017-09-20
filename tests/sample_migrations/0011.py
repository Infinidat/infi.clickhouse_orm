import datetime

from infi.clickhouse_orm import migrations
from test_migrations import Model3


def forward(database):
    database.insert([
        Model3(date=datetime.date(2016, 1, 4), f1=4, f3=1, f4='test4')
    ])


operations = [
    migrations.RunPython(forward)
]