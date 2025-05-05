import os.path
import sys; sys.path.append('..')
from fasthtml.common import *
from datagrid import DataGrid, build_datagrid_endpoints, SortableColumnsJs, CompareButton, right_click_handler_row
from datagrid import right_click_handler as right_click_handler_dg
from utils import prepare_db, Config
from pyutils.resultTable import ResultTable
from right_panel import RightPanel, build_right_panel_routes, reset_scalar_session
from compare_page import ChartCardList, CompareSetup, build_compare_routes
from fh_plotly import plotly_headers
import shutil

if not os.path.exists(os.path.expanduser('~/.config/deepboard')):
    os.makedirs(os.path.expanduser('~/.config/deepboard'))

if not os.path.exists(os.path.expanduser('~/.config/deepboard/THEME.yml')):
    shutil.copy("./THEME.yml", os.path.expanduser('~/.config/deepboard/THEME.yml'))

if not os.path.exists(os.path.expanduser('~/.config/deepboard/THEME.css')):
    shutil.copy("assets/theme.css", os.path.expanduser('~/.config/deepboard/THEME.css'))

CONFIG = Config.FromFile(os.path.expanduser('~/.config/deepboard/THEME.yml'))
DATABASE = "../pyutils/results/result_table.db"

prepare_db()

rTable = ResultTable(DATABASE)

def _not_found(req, exc): return Titled('Oh no!', Div('We could not find that page :('))

app = FastHTMLWithLiveReload(
    exception_handlers={404: _not_found},
    hdrs=(
        Link(rel='stylesheet', href='assets/base.css', type='text/css'),
        Link(rel='stylesheet', href='assets/datagrid.css', type='text/css'),
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
    if fname == "theme" and ext == "css":
        if os.path.exists(os.path.expanduser('~/.config/deepboard/theme.css')):
            return FileResponse(os.path.expanduser('~/.config/deepboard/THEME.css'))

    return FileResponse(f'assets/{fname}.{ext}')

# DataGrid


@rt("/")
def get(session):
    if "show_hidden" not in session:
        session["show_hidden"] = False
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
    if "show_hidden" not in session:
        session["show_hidden"] = False
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
def get(session, elementIds: str, top: int, left: int):
    elementIds = elementIds.split(",")
    if any(elementId.startswith("grid-header") for elementId in elementIds):
        return right_click_handler_dg(elementIds, top, left)
    elif any(elementId.startswith("grid-row") for elementId in elementIds):
        return right_click_handler_row(session, elementIds, top, left)
    else:
        return Div(
            # Div(
            #     cls='dropdown-menu'
            # ),
            id='custom-menu',
            style=f'visibility: visible; top: {top}px; left: {left}px;',
        )

build_datagrid_endpoints(rt)
build_right_panel_routes(rt)
build_compare_routes(rt)

serve()