from fasthtml.common import *
DATABASE = "../pyutils/results/result_table.db"

db = database(DATABASE)

experiments, results, logs = db.t.Experiments, db.t.Results, db.t.Logs

if experiments not in db.t:
    raise RuntimeError("Expect a valid database: Experiment table not found")
if results not in db.t:
    raise RuntimeError("Expect a valid database: Results table not found")
if logs not in db.t:
    raise RuntimeError("Expect a valid database: Logs table not found")

def _not_found(req, exc): return Titled('Oh no!', Div('We could not find that page :('))

app = FastHTMLWithLiveReload(
    exception_handlers={404: _not_found},
    hdrs=(
        Link(rel='stylesheet', href='static/theme.css', type='text/css'),
        Script(src="static/base.js")
    ),
    static_path='static'
)

rt = app.route
@rt("/static/{fname:path}.{ext:static}")
async def get(fname:str, ext:str):
    return FileResponse(f'static/{fname}.{ext}')


def ExperimentRow(name: str):
    return Div(
        H3(name),
        cls="exp_row"
    )
@rt("/")
def get():
    return (Title("Main page"),
            Div(
                Div(
                    Table(
                        Thead(
                            Tr(
                                Th(
                                    Span('RunId', hx_get='/sort?by=RunId', hx_target='tbody', hx_swap='outerHTML',
                                         cls='sortable'),
                                    Span('⇅', cls='sort-icon')
                                ),
                                Th(
                                    Span('Experiment', hx_get='/sort?by=Experiment', hx_target='tbody',
                                         hx_swap='outerHTML', cls='sortable'),
                                    Span('⇅', cls='sort-icon')
                                ),
                                Th(
                                    Span('RunTime', hx_get='/sort?by=RunTime', hx_target='tbody', hx_swap='outerHTML',
                                         cls='sortable'),
                                    Span('⇅', cls='sort-icon')
                                ),
                                Th(
                                    Span('Loss', hx_get='/sort?by=Loss', hx_target='tbody', hx_swap='outerHTML',
                                         cls='sortable'),
                                    Span('⇅', cls='sort-icon')
                                ),
                                Th(
                                    Span('Accuracy', hx_get='/sort?by=Accuracy', hx_target='tbody', hx_swap='outerHTML',
                                         cls='sortable'),
                                    Span('⇅', cls='sort-icon')
                                )
                            )
                        ),
                        Tbody(
                            Tr(
                                Td('001'),
                                Td('baseline'),
                                Td('12m 35s'),
                                Td('0.342'),
                                Td('88.5%')
                            ),
                            Tr(
                                Td('002'),
                                Td('dropout_0.3'),
                                Td('13m 10s'),
                                Td('0.289'),
                                Td('90.1%')
                            ),
                            Tr(
                                Td('003'),
                                Td('batchnorm_on'),
                                Td('12m 47s'),
                                Td('0.301'),
                                Td('89.3%')
                            )
                        )
                    ),
                    cls="table-container"
                ),
                Div(
                    P('Select an item to see the image.'),
                    id='image-area',
                    cls='image-area'
                ),
                cls='container'
            )
            )

serve()