from fasthtml.common import *
from datetime import datetime

def Header(name: str):
    return Th(
        Div(name, Span('⇅', cls='sort-icon'), hx_get='/sort?by=RunId', target_id='experiment-table',
            hx_swap='outerHTML',
            cls='sortable',
            id=f"grid-header-{name}"),
    ),

def format_value(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value
def Row(data):
    return Tr(
        *[Td(format_value(value)) for value in data]
    )

def DataGrid(rtable: 'ResultTable'):
    columns, data = rtable.get_results()
    return Div(
        Table(
            Thead(
                Tr(Header(col_name) for col_name in columns)
            ),
            Tbody(
                *[Row(row) for row in data]
            ),
            id="experiment-table",
        ),
        cls="table-container"
    ),