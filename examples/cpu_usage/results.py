from __future__ import annotations

from models import CPUStats

from clickhouse_orm import Database, F

db = Database("demo")
queryset = CPUStats.objects_in(db)
total = queryset.filter(CPUStats.cpu_id == 1).count()
busy = queryset.filter(CPUStats.cpu_id == 1, CPUStats.cpu_percent > 95).count()
print(f"CPU 1 was busy {busy * 100.0 / total:.2f}% of the time")

# Calculate the average usage per CPU
for row in queryset.aggregate(CPUStats.cpu_id, average=F.avg(CPUStats.cpu_percent)):
    print(f"CPU {row.cpu_id}: {row.average:.2f}%")
