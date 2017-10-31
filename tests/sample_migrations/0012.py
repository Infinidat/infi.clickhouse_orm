from infi.clickhouse_orm import migrations

operations = [
    migrations.RunSQL("INSERT INTO `mig` (date, f1, f3, f4) VALUES ('2016-01-01', 1, 1, 'test') "),
    migrations.RunSQL([
        "INSERT INTO `mig` (date, f1, f3, f4) VALUES ('2016-01-02', 2, 2, 'test2') ",
        "INSERT INTO `mig` (date, f1, f3, f4) VALUES ('2016-01-03', 3, 3, 'test3') ",
    ])
]
