from fasthtml.common import *
from datetime import datetime
from deepboard.utils import smart_round

def Header(name: str, col_id: str, sort_dir: str = None):
    if sort_dir == "asc":
        return Th(
            Div(name, Span("↑", cls='sort-icon'), hx_get=f'/sort?by={col_id}&order=desc', target_id='experiment-table',
                hx_swap='innerHTML',
                cls='sortable',
                id=f"grid-header-{col_id}"
                ),
            data_col=col_id
        ),
    elif sort_dir == "desc":
        return Th(
            Div(name, Span("↓", cls='sort-icon'), hx_get=f'/sort?by={col_id}&order=', target_id='experiment-table',
                hx_swap='innerHTML',
                cls='sortable',
                id=f"grid-header-{col_id}"),
            data_col=col_id
        ),
    else:
        return Th(
            Div(name, Span('⇅', cls='sort-icon'), hx_get=f'/sort?by={col_id}&order=asc', target_id='experiment-table',
                hx_swap='innerHTML',
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
            hx_swap='innerHTML',
            id=f"grid-header-{col_id}",
            cls="rename-input"
        )
    ),

def format_value(value, decimals: int = 4):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(value, float):
        return smart_round(value, decimals)
    return value

def Row(data, run_id, selected: bool, hidden: bool, max_decimals: int):
    cls = "table-row"
    if selected:
        cls += " table-row-selected"

    if hidden:
        cls += " table-row-hidden"

    return Tr(
        *[Td(format_value(value, decimals=max_decimals)) for value in data],
        hx_get=f"/click_row?run_id={run_id}",  # HTMX will GET this URL
        hx_trigger="click[!event.shiftKey]",
        hx_target="#experiment-table",  # Target DOM element to update
        hx_swap="innerHTML",  # Optional: how to replace content
        id=f"grid-row-{run_id}",
        cls=cls,
    )

def DataGrid(session, rename_col: str = None, wrapincontainer: bool = False):
    from __main__ import rTable, CONFIG

    if "datagrid" not in session:
        session["datagrid"] = dict()
    show_hidden = session.get("show_hidden", False)
    rows_selected = session["datagrid"].get("selected-rows") or []
    sort_by: Optional[str] = session["datagrid"].get("sort_by", None)
    sort_order: Optional[str] = session["datagrid"].get("sort_order", None)
    columns, col_ids, data = rTable.get_results(show_hidden=show_hidden)
    # If the columns to sort by is hidden, we reset it
    if sort_by is not None and sort_by not in col_ids:
        session["datagrid"]["sort_by"] = sort_by = None
        session["datagrid"]["sort_order"] = sort_order = None

    if sort_by is not None and sort_order is not None:
        data = sorted(
            data,
            key=lambda x: (
                x[col_ids.index(sort_by)] is None,  # True = 1, False = 0 — Nones last
                x[col_ids.index(sort_by)]
            ),
            reverse=(sort_order == "desc")
        )

    run_ids = [row[col_ids.index("run_id")] for row in data]
    rows_hidden = rTable.get_hidden_runs() if show_hidden else []
    table = Table(
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
                    *[Row(row, run_id, max_decimals=CONFIG.MAX_DEC, selected=run_id in rows_selected, hidden=run_id in rows_hidden) for row, run_id in zip(data, run_ids)],
                ),
                cls="data-grid"
            ),

    if wrapincontainer:
        return Div(
                table,
                cls="scroll-container",
                id="experiment-table",
            ),
    else:
        return table



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
                        swap: 'innerHTML',
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


def CompareButton(session, swap: bool = False):
    show = "datagrid" in session and "selected-rows" in session["datagrid"] and len(session["datagrid"]["selected-rows"]) > 1
    run_ids = session["datagrid"].get("selected-rows") or []
    url = f"/compare?run_ids={','.join([str(i) for i in run_ids])}"
    return Div(
        Button(
            "Compare",
            cls="compare-button",
            style="display: block;" if show else "display: none;",
            onclick=f"window.open('{url}', '_blank')",
            hx_get="/reset",
            hx_target="#container",
        ),
        cls="compare-button-container",
        id="compare-button-container",
        hx_swap_oob="true" if swap else "false",
    )


def build_datagrid_endpoints(rt):
    rt("/hide")(hide_column)
    rt("/show")(show_column)
    rt("/rename_col_datagrid")(get_rename_column)
    rt("/rename_col", methods=["POST"])(post_rename_column)
    rt("/sort")(sort)
    rt("/reorder_columns", methods=["POST"])(reorder_columns)
    rt("/shift_click_row")(shift_click_row) # Endpoint is called in the javascript file
    rt("/hide_run")(hide_run)
    rt("/show_run")(show_run)
    rt("/show_hidden")(show_hidden)
    rt("/hide_hidden")(hide_hidden)


# ---------------------------------------------------------------------------------------------------------------------
# Right click menu
# ---------------------------------------------------------------------------------------------------------------------
def right_click_handler(elementIds: List[str], top: int, left: int):
    from __main__ import rTable
    elementId = [elem for elem in elementIds if elem.startswith("grid-header-")][0]
    clicked_col = elementId.replace("grid-header-", "")
    hidden_columns = [(key, alias) for key, (order, alias) in rTable.result_columns.items() if order is None]
    return Div(
        Ul(
            Li('Hide', hx_get=f"/hide?col={clicked_col}", hx_target='#experiment-table', hx_swap="innerHTML", cls="menu-item"),
            Li('Rename', hx_get=f'/rename_col_datagrid?col={clicked_col}', hx_target='#experiment-table', hx_swap="innerHTML", cls="menu-item"),
            Li(
                Div(A('Add', href="#", cls="has-submenu"), Span("►"),
                    style="display: flex; flex-direction: row; justify-content: space-between;"),
                Ul(
                    *[Li(alias, hx_get=f"/show?col={col_name}&after={clicked_col}", hx_target='#experiment-table', hx_swap="innerHTML", cls="menu-item")
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
def right_click_handler_row(session, elementIds: List[str], top: int, left: int):
    from __main__ import rTable
    elementId = [elem for elem in elementIds if elem.startswith("grid-row-")][0]
    clicked_row = int(elementId.replace("grid-row-", ""))
    hidden_runs = rTable.get_hidden_runs()
    if clicked_row in hidden_runs:
        hideshow_button = Li('Show', hx_get=f"/show_run?run_id={clicked_row}", hx_target='#experiment-table',
                             hx_swap="innerHTML", cls="menu-item")
    else:
        hideshow_button = Li('Hide', hx_get=f"/hide_run?run_id={clicked_row}", hx_target='#experiment-table',
                             hx_swap="innerHTML",cls="menu-item")
    print(session)
    if session.get("show_hidden", False):
        toggle_visibility_button = Li('Hide Hidden', hx_get=f"/hide_hidden", hx_target='#experiment-table',
                                      hx_swap="innerHTML", cls="menu-item")
    else:
        toggle_visibility_button = Li('Show Hidden', hx_get=f"/show_hidden", hx_target='#experiment-table',
                                      hx_swap="innerHTML", cls="menu-item")
    return Div(
        Ul(
            hideshow_button,
            toggle_visibility_button,
            cls='dropdown-menu'
        ),
        id='custom-menu',
        style=f'visibility: visible; top: {top}px; left: {left}px;',
    )

async def hide_column(session, col: str):
    from __main__ import rTable
    rTable.hide_column(col)

    # Return the datagrid
    return DataGrid(session)

async def show_column(session, col: str, after: str):
    from __main__ import rTable
    cols = rTable.result_columns
    if after not in cols:
        print(f"[WARNING]: Did not find column: {after}")
        return DataGrid(session)
    pos = cols[after][0] + 1
    print(f"Show column: {col} after {after} position {pos}")
    rTable.show_column(col, pos)

    # Return the datagrid
    return DataGrid(session)

async def get_rename_column(session, col: str):
    from __main__ import rTable
    if col not in rTable.result_columns:
        print(f"[WARNING]: Did not find column: {col}")
        return DataGrid(session)
    return DataGrid(session, rename_col=col)

async def post_rename_column(session, col_id: str, new_name: str):
    from __main__ import rTable
    if col_id not in rTable.result_columns:
        print(f"[WARNING]: Did not find column: {col_id}")
        return DataGrid(session)
    rTable.set_column_alias({col_id: new_name})

    # Return the datagrid
    return DataGrid(session)

async def sort(session, by: str, order: str):
    if "datagrid" not in session:
        session["datagrid"] = dict(
            sort_by=None,
            sort_order=None
        )
    session["datagrid"]["sort_by"] = by
    session["datagrid"]["sort_order"] = order
    return DataGrid(session)

async def reorder_columns(session, order: str):
    from __main__ import rTable
    order = order.split(",")
    prep_order = {col_id: i + 1 for i, col_id in enumerate(order)}
    rTable.set_column_order(prep_order)
    return DataGrid(session)

async def shift_click_row(session, run_id: int):
    if "datagrid" not in session:
        session["datagrid"] = dict()

    session["datagrid"]["multiselection"] = True
    if "selected-rows" not in session["datagrid"]:
        session["datagrid"]["selected-rows"] = []

    if run_id in session["datagrid"]["selected-rows"]:
        session["datagrid"]["selected-rows"].remove(run_id)
    else:
        session["datagrid"]["selected-rows"].append(run_id)

    return DataGrid(session), CompareButton(session, swap=True)

async def hide_run(session, run_id: int):
    from __main__ import rTable
    rTable.hide_run(run_id)
    return DataGrid(session)

async def show_run(session, run_id: int):
    from __main__ import rTable
    rTable.show_run(run_id)
    return DataGrid(session)

async def show_hidden(session):
    session["show_hidden"] = True
    return DataGrid(session)

async def hide_hidden(session):
    session["show_hidden"] = False
    return DataGrid(session)
