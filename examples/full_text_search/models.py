from clickhouse_orm.engines import MergeTree
from clickhouse_orm.fields import LowCardinalityField, StringField, UInt64Field
from clickhouse_orm.models import Index, Model


class Fragment(Model):

    language = LowCardinalityField(StringField(), default="EN")
    document = LowCardinalityField(StringField())
    idx = UInt64Field()
    word = StringField()
    stem = StringField()

    # An index for faster search by document and fragment idx
    index = Index((document, idx), type=Index.minmax(), granularity=1)

    # The primary key allows efficient lookup of stems
    engine = MergeTree(order_by=(stem, document, idx), partition_key=("language",))
