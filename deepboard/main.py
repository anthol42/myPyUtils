import sys; sys.path.append('..')
from fasthtml.common import *
from datagrid import DataGrid, build_datagrid_endpoints, SortableColumnsJs, CompareButton
from datagrid import right_click_handler as right_click_handler_dg
from utils import prepare_db
from pyutils.resultTable import ResultTable
from right_panel import RightPanel, build_right_panel_routes, reset_scalar_session
from compare_page import ChartCardList, CompareSetup, build_compare_routes
from fh_plotly import plotly_headers

class Config:
    COLORS = [
        "#1f77b4",  # muted blue
        "#ff7f0e",  # vivid orange
        "#2ca02c",  # medium green
        "#d62728",  # brick red
        "#9467bd",  # muted purple
        "#8c564b",  # brownish pink
        "#e377c2",  # pink
        "#7f7f7f",  # gray
        "#bcbd22",  # lime yellow
        "#17becf",  # cyan
    ]
    HIDDEN_COLOR = "#333333"  # gray for hidden lines

    PLOTLY_THEME = dict(
        plot_bgcolor='#111111',  # dark background for the plotting area
        paper_bgcolor='#111111',  # dark background for the full figure
        font=dict(color='white'),  # white text everywhere (axes, legend, etc.)
        xaxis=dict(
            gridcolor='#333333',  # subtle dark grid lines
            zerolinecolor='#333333'
        ),
        yaxis=dict(
            gridcolor='#333333',
            zerolinecolor='#333333'
        ),
    )

CONFIG = Config()
DATABASE = "../pyutils/results/result_table.db"

prepare_db()

rTable = ResultTable(DATABASE)

def _not_found(req, exc): return Titled('Oh no!', Div('We could not find that page :('))

app = FastHTMLWithLiveReload(
    exception_handlers={404: _not_found},
    hdrs=(
        Link(rel='stylesheet', href='assets/theme.css', type='text/css'),
        Link(rel='stylesheet', href='assets/right_panel.css', type='text/css'),
        Link(rel='stylesheet', href='assets/charts.css', type='text/css'),
        Link(rel='stylesheet', href='assets/fileview.css', type='text/css'),
        Link(rel='stylesheet', href='assets/compare.css', type='text/css'),
        Link(href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css", rel="stylesheet"),
        plotly_headers,
        Script(src="assets/base.js"),
        SortableColumnsJs(),
    ),
    static_path='assets'
)

rt = app.route
@rt("/assets/{fname:path}.{ext:static}")
async def get(fname:str, ext:str):
    print(f"\n\nServing static file: {fname}.{ext}")
    return FileResponse(f'assets/{fname}.{ext}')

# DataGrid


@rt("/")
def get(session):
    return (Title("Table"),
            Div(id="custom-menu"),
            Div(
                Div(
                    DataGrid(session, wrapincontainer=True),
                    CompareButton(session),
                    cls="table-container"
                ),
                RightPanel(session),
                cls='container',
                id="container",
            )
            )

@rt("/compare")
def get(session, run_ids: str):
    run_ids = run_ids.split(",")
    session["compare"] = {"selected-rows": run_ids}
    return (Title("Compare"),
            Div(id="custom-menu"),
            Div(
                Div(
                    CompareSetup(session),
                    cls="compare-setup-container"
                ),
                Div(
                    ChartCardList(session),
                    cls="cards-list-container"
                ),
                cls="compare-container"
            )
            )

@rt("/reset")
def get(session):
    session["datagrid"] = dict()
    return Div(
                Div(
                    DataGrid(session, wrapincontainer=True),
                    CompareButton(session),
                    cls="table-container"
                ),
                RightPanel(session),
                cls='container',
                id="container",
                hx_swap_oob="true"
            )

# Choose a row in the datagrid
@rt("/click_row")
def get(session, run_id: int):
    reset_scalar_session(session)
    if "datagrid" not in session:
        session["datagrid"] = dict()
    session["datagrid"]["selected-rows"] = [run_id]
    # Return the image
    return DataGrid(session), CompareButton(session, swap=True), RightPanel(session)


# Dropdown menu when right-cliked
@rt("/get-context-menu")
def get(elementId: str, top: int, left: int):
    if elementId.startswith("grid-header"):
        return right_click_handler_dg(elementId, top, left)
    else:
        return Div(
            Div(
                Div('Option 1', hx_post='/copy', hx_target='this', cls="menu-item"),
                Div('Option 2', hx_post='/copy', hx_target='this', cls="menu-item"),
                cls='dropdown-menu'
            ),
            id='custom-menu',
            style=f'visibility: visible; top: {top}px; left: {left}px;',
        )

build_datagrid_endpoints(rt)
build_right_panel_routes(rt)
build_compare_routes(rt)

serve()