import sys; sys.path.append('..')
from fasthtml.common import *
from datagrid import DataGrid, build_datagrid_endpoints
from datagrid import right_click_handler as right_click_handler_dg
from utils import prepare_db
from pyutils.resultTable import ResultTable

DATABASE = "../pyutils/results/result_table.db"

prepare_db()

rTable = ResultTable(DATABASE)

def _not_found(req, exc): return Titled('Oh no!', Div('We could not find that page :('))

app = FastHTMLWithLiveReload(
    exception_handlers={404: _not_found},
    hdrs=(
        Link(rel='stylesheet', href='assets/theme.css', type='text/css'),
        Script(src="assets/base.js")
    ),
    static_path='assets'
)

rt = app.route
@rt("/assets/{fname:path}.{ext:static}")
async def get(fname:str, ext:str):
    print(f"\n\nServing static file: {fname}.{ext}")
    return FileResponse(f'assets/{fname}.{ext}')


def ExperimentRow(name: str):
    return Div(
        H3(name),
        cls="exp_row"
    )




# DataGrid


@rt("/")
def get():
    return (Title("Main page"),
            Div(id="custom-menu"),
            Div(
                DataGrid(),
                Div(
                    P('Select an item to see the image.'),
                    id='image-area',
                    cls='image-area'
                ),
                cls='container'
            )
            )



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

serve()