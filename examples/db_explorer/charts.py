import pygal
from pygal.style import RotateStyle
from jinja2.filters import do_filesizeformat


# Formatting functions
number_formatter = lambda v: '{:,}'.format(v)
bytes_formatter = lambda v: do_filesizeformat(v, True)


def tables_piechart(db, by_field, value_formatter):
    '''
    Generate a pie chart of the top n tables in the database.
    `db` - the database instance
    `by_field` - the field name to sort by
    `value_formatter` - a function to use for formatting the numeric values
    '''
    Tables = db.get_model_for_table('tables', system_table=True)
    qs = Tables.objects_in(db).filter(database=db.db_name, is_temporary=False).exclude(engine='Buffer')
    tuples = [(getattr(table, by_field), table.name) for table in qs]
    return _generate_piechart(tuples, value_formatter)


def columns_piechart(db, tbl_name, by_field, value_formatter):
    '''
    Generate a pie chart of the top n columns in the table.
    `db` - the database instance
    `tbl_name` - the table name
    `by_field` - the field name to sort by
    `value_formatter` - a function to use for formatting the numeric values
    '''
    ColumnsTable = db.get_model_for_table('columns', system_table=True)
    qs = ColumnsTable.objects_in(db).filter(database=db.db_name, table=tbl_name)
    tuples = [(getattr(col, by_field), col.name) for col in qs]
    return _generate_piechart(tuples, value_formatter)


def _get_top_tuples(tuples, n=15):
    '''
    Given a list of tuples (value, name), this function sorts
    the list and returns only the top n results. All other tuples
    are aggregated to a single "others" tuple.
    '''
    non_zero_tuples = [t for t in tuples if t[0]]
    sorted_tuples = sorted(non_zero_tuples, reverse=True)
    if len(sorted_tuples) > n:
        others = (sum(t[0] for t in sorted_tuples[n:]), 'others')
        sorted_tuples = sorted_tuples[:n] + [others]
    return sorted_tuples


def _generate_piechart(tuples, value_formatter):
    '''
    Generates a pie chart.
    `tuples` - a list of (value, name) tuples to include in the chart
    `value_formatter` - a function to use for formatting the values
    '''
    style = RotateStyle('#9e6ffe', background='white', legend_font_family='Roboto', legend_font_size=18, tooltip_font_family='Roboto', tooltip_font_size=24)
    chart = pygal.Pie(style=style, margin=0, title=' ', value_formatter=value_formatter, truncate_legend=-1)
    for t in _get_top_tuples(tuples):
        chart.add(t[1], t[0])
    return chart.render(is_unicode=True, disable_xml_declaration=True)
