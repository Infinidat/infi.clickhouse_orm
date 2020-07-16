import psutil, time, datetime
from infi.clickhouse_orm import Database
from models import CPUStats


db = Database('demo')
db.create_table(CPUStats)


psutil.cpu_percent(percpu=True) # first sample should be discarded

while True:
    time.sleep(1)
    stats = psutil.cpu_percent(percpu=True)
    timestamp = datetime.datetime.now()
    print(timestamp)
    db.insert([
        CPUStats(timestamp=timestamp, cpu_id=cpu_id, cpu_percent=cpu_percent)
        for cpu_id, cpu_percent in enumerate(stats)
    ])
