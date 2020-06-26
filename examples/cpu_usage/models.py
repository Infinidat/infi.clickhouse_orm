from infi.clickhouse_orm import Model, DateTimeField, UInt16Field, Float32Field, Memory


class CPUStats(Model):

    timestamp = DateTimeField()
    cpu_id = UInt16Field()
    cpu_percent = Float32Field()

    engine = Memory()

