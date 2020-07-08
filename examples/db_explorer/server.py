from infi.clickhouse_orm import Database, F
from charts import tables_piechart, columns_piechart, number_formatter, bytes_formatter
from flask import Flask
from flask import render_template
import sys


app = Flask(__name__)


@app.route('/')
def homepage_view():
    db = _get_db('system')
    DatabasesTable = db.get_model_for_table('databases', system_table=True)
    databases = DatabasesTable.objects_in(db).exclude(name='system').order_by(F.lower(DatabasesTable.name))
    return render_template('homepage.html', db=db, databases=databases)


@app.route('/<db_name>/')
def database_view(db_name):
    db = _get_db(db_name)
    ColumnsTable = db.get_model_for_table('columns', system_table=True)
    tables = ColumnsTable.objects_in(db).filter(database=db_name).aggregate(ColumnsTable.table,
        compressed_size=F.sum(ColumnsTable.data_compressed_bytes),
        uncompressed_size=F.sum(ColumnsTable.data_uncompressed_bytes),
        ratio=F.sum(ColumnsTable.data_uncompressed_bytes) / F.sum(ColumnsTable.data_compressed_bytes)
        ).order_by(F.lower(ColumnsTable.table))
    return render_template('database.html',
        db=db,
        tables=tables,
        tables_piechart_by_rows=tables_piechart(db, 'total_rows', value_formatter=number_formatter),
        tables_piechart_by_size=tables_piechart(db, 'total_bytes', value_formatter=bytes_formatter),
    )


@app.route('/<db_name>/<tbl_name>/')
def table_view(db_name, tbl_name):
    db = _get_db(db_name)
    TablesTable = db.get_model_for_table('tables', system_table=True)
    tbl_info = TablesTable.objects_in(db).filter(database=db_name, name=tbl_name)[0]
    create_table_sql = db.raw('SHOW CREATE TABLE %s FORMAT TabSeparatedRaw' % tbl_name)
    ColumnsTable = db.get_model_for_table('columns', system_table=True)
    columns = ColumnsTable.objects_in(db).filter(database=db_name, table=tbl_name)
    return render_template('table.html',
        db=db,
        tbl_name=tbl_name,
        tbl_info=tbl_info,
        create_table_sql=create_table_sql,
        columns=columns,
        piechart=columns_piechart(db, tbl_name, 'data_compressed_bytes', value_formatter=bytes_formatter),
    )


def _get_db(db_name):
    db_url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8123/'
    username = sys.argv[2] if len(sys.argv) > 2 else None
    password = sys.argv[3] if len(sys.argv) > 3 else None
    return Database(db_name, db_url, username, password, readonly=True)


if __name__ == '__main__':
    _get_db('system') # fail early on db connection problems
    app.run(debug=True)
