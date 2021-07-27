import datetime

from test_migrations import Model3

from clickhouse_orm import migrations


def forward(database):
    database.insert([Model3(date=datetime.date(2016, 1, 4), f1=4, f3=1, f4="test4")])


operations = [migrations.RunPython(forward)]
