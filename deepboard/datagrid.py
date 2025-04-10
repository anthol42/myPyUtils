from fasthtml.common import *
from datetime import datetime
def Header(name: str, col_id: str, sort_dir: str = None):
    if sort_dir == "asc":
        return Th(
            Div(name, Span("↑", cls='sort-icon'), hx_get=f'/sort?by={col_id}&order=desc', target_id='experiment-table',
                hx_swap='outerHTML',
                cls='sortable',
                id=f"grid-header-{col_id}"
                ),
            data_col=col_id
        ),
    elif sort_dir == "desc":
        return Th(
            Div(name, Span("↓", cls='sort-icon'), hx_get=f'/sort?by={col_id}&order=', target_id='experiment-table',
                hx_swap='outerHTML',
                cls='sortable',
                id=f"grid-header-{col_id}"),
            data_col=col_id
        ),
    else:
        return Th(
            Div(name, Span('⇅', cls='sort-icon'), hx_get=f'/sort?by={col_id}&order=asc', target_id='experiment-table',
                hx_swap='outerHTML',
                cls='sortable',
                id=f"grid-header-{col_id}"),
            data_col=col_id
        ),

def HeaderRename(name: str, col_id: str):
    return Th(
        Input(
            type="text",
            value=name,
            name="new_name",
            hx_post=f'/rename_col?col_id={col_id}',
            hx_target='#experiment-table',
            hx_swap='outerHTML',
            id=f"grid-header-{col_id}",
            cls="rename-input"
        )
    ),

def format_value(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value
def Row(data):
    return Tr(
        *[Td(format_value(value)) for value in data]
    )

def DataGrid(rename_col: str = None, sort_by: str = None, sort_order: str = None):
    from __main__ import rTable
    columns, col_ids, data = rTable.get_results()
    if sort_by is not None and sort_order is not None:
        data = sorted(data, key=lambda x: x[col_ids.index(sort_by)], reverse=(sort_order == "desc"))
    return Div(
        Table(
            # We put the headers in a form so that we can sort them using htmx
            Thead(
                Tr(
                    *[
                        HeaderRename(col_name, col_id) if col_id == rename_col else Header(
                            col_name,
                            col_id,
                            sort_order if col_id == sort_by else None)
                        for col_name, col_id in zip(columns, col_ids)],
                    id="column-header-row"
                )
                ),
            Tbody(
                *[Row(row) for row in data]
            ),
            id="experiment-table",
        ),
        cls="table-container"
    ),


def SortableColumnsJs():
    src = """
        import { Sortable } from 'https://cdn.jsdelivr.net/npm/sortablejs/+esm';
        
        document.addEventListener('DOMContentLoaded', function() {
            initSortable();
        });

        function initSortable() {
            const headerRow = document.getElementById('column-header-row');
            
            if (!headerRow) return;

            // Initialize SortableJS on the header row
            new Sortable(headerRow, {
                animation: 150,
                ghostClass: 'sortable-ghost',
                onEnd: function(evt) {
                    // Get the new column order
                    const headers = Array.from(headerRow.children);
                    const columnOrder = headers.map(header => 
                        header.getAttribute('data-col'));
                    
                    // Send the new order to the server using htmx as a POST request
                    htmx.ajax('POST', '/reorder_columns', {
                        target: '#experiment-table',
                        swap: 'outerHTML',
                        values: {
                            order: columnOrder.join(',')
                        }
                    });
                }
            });
        }

        // Re-initialize Sortable after HTMX content swaps
        document.body.addEventListener('htmx:afterSwap', function(evt) {
            if (evt.detail.target.id === 'experiment-table') {
                initSortable();
            }
        });
        """
    return Script(src, type='module')

def build_datagrid_endpoints(rt):
    rt("/hide")(hide_column)
    rt("/show")(show_column)
    rt("/rename_col_datagrid")(get_rename_column)
    rt("/rename_col", methods=["POST"])(post_rename_column)
    rt("/sort")(sort)
    rt("/reorder_columns", methods=["POST"])(reorder_columns)

# ---------------------------------------------------------------------------------------------------------------------
# Right click menu
# ---------------------------------------------------------------------------------------------------------------------
def right_click_handler(elementId: str, top: int, left: int):
    from __main__ import rTable
    clicked_col = elementId.replace("grid-header-", "")
    hidden_columns = [(key, alias) for key, (order, alias) in rTable.result_columns.items() if order is None]
    return Div(
        Ul(
            Li('Hide', hx_get=f"/hide?col={clicked_col}", hx_target='#experiment-table', hx_swap="outerHTML", cls="menu-item"),
            Li('Rename', hx_get=f'/rename_col_datagrid?col={clicked_col}', hx_target='#experiment-table', hx_swap="outerHTML", cls="menu-item"),
            Li(
                Div(A('Add', href="#", cls="has-submenu"), Span("►"),
                    style="display: flex; flex-direction: row; justify-content: space-between;"),
                Ul(
                    *[Li(alias, hx_get=f"/show?col={col_name}&after={clicked_col}", hx_target='#experiment-table', hx_swap="outerHTML", cls="menu-item")
                      for col_name, alias in hidden_columns],
                    cls="submenu"
                ),
                cls="menu-item has-submenu-wrapper"
            ),
            cls='dropdown-menu'
        ),
        id='custom-menu',
        style=f'visibility: visible; top: {top}px; left: {left}px;',
    )


async def hide_column(col: str):
    print(f"Hide column: {col}")
    from __main__ import rTable
    rTable.hide_column(col)

    # Return the datagrid
    return DataGrid()

async def show_column(col: str, after: str):
    from __main__ import rTable
    cols = rTable.result_columns
    if after not in cols:
        print(f"[WARNING]: Did not find column: {after}")
        return DataGrid()
    pos = cols[after][0] + 1
    print(f"Show column: {col} after {after} position {pos}")
    rTable.show_column(col, pos)

    # Return the datagrid
    return DataGrid()

async def get_rename_column(col: str):
    from __main__ import rTable
    if col not in rTable.result_columns:
        print(f"[WARNING]: Did not find column: {col}")
        return DataGrid()
    return DataGrid(rename_col=col)

async def post_rename_column(col_id: str, new_name: str):
    from __main__ import rTable
    if col_id not in rTable.result_columns:
        print(f"[WARNING]: Did not find column: {col_id}")
        return DataGrid()
    rTable.set_column_alias({col_id: new_name})

    # Return the datagrid
    return DataGrid()

async def sort(by: str, order: str):
    if order == "" or order is None: # Sorting has been deactivated
        return DataGrid()
    return DataGrid(sort_by=by, sort_order=order) # Sort by the column given the order

async def reorder_columns(order: str):
    from __main__ import rTable
    order = order.split(",")
    prep_order = {col_id: i + 1 for i, col_id in enumerate(order)}
    print(prep_order)
    rTable.set_column_order(prep_order)
    return DataGrid()
