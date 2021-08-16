from clickhouse_orm import DateTimeField, Float32Field, Memory, Model, UInt16Field


class CPUStats(Model):

    timestamp = DateTimeField()
    cpu_id = UInt16Field()
    cpu_percent = Float32Field()

    engine = Memory()
