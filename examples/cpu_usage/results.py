from infi.clickhouse_orm import Database, F
from models import CPUStats


db = Database('demo')
queryset = CPUStats.objects_in(db)
total = queryset.filter(CPUStats.cpu_id == 1).count()
busy = queryset.filter(CPUStats.cpu_id == 1, CPUStats.cpu_percent > 95).count()
print('CPU 1 was busy {:.2f}% of the time'.format(busy * 100.0 / total))

# Calculate the average usage per CPU
for row in queryset.aggregate(CPUStats.cpu_id, average=F.avg(CPUStats.cpu_percent)):
    print('CPU {row.cpu_id}: {row.average:.2f}%'.format(row=row))
