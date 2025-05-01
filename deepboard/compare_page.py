from fasthtml.common import *
from datetime import datetime
from deepboard.components import Legend, ChartType, Smoother


def SplitCard(session, split: str, metrics: List[str], opened: bool = True):
    from __main__ import rTable
    runIDs = sorted([int(rid) for rid in session["compare"]["selected-rows"]])
    sockets = [rTable.load_run(runID) for runID in runIDs]

    if opened:
        return Li(
            Div(
                H1(split, cls=".split-card-title"),
                Button(
                    I(cls="fas fa-chevron-down"),
                    hx_get=f"/compare/toggle_accordion?split={split}&metrics={','.join(metrics)}&open=false",
                    hx_target=f"#split-card-{split}",
                    hx_swap="outerHTML",
                    cls="accordion-toggle"
                ),
                cls="split-card-header"
            ),
            Div(
                cls="two-charts-container"
            ),
            cls="split-card",
            id=f"split-card-{split}",
        )
    else:
        return Li(
            Div(
                H1(split, cls=".split-card-title"),
                Button(
                    I(cls="fas fa-chevron-down"),
                    hx_get=f"/compare/toggle_accordion?split={split}&metrics={','.join(metrics)}&open=true",
                    hx_target=f"#split-card-{split}",
                    hx_swap="outerHTML",
                    cls="accordion-toggle rotated"
                ),

                cls="split-card-header"
            ),
            cls="split-card closed",
            id=f"split-card-{split}",
        )

def ChartCardList(session):
    runIDs = sorted([int(rid) for rid in session["compare"]["selected-rows"]])
    from __main__ import rTable
    sockets = [rTable.load_run(runID) for runID in runIDs]
    keys = {key for socket in sockets for key in socket.formatted_scalars}
    splits = {split for split, metric in keys}
    splits = sorted(splits)
    metrics = {split: [metric for sp, metric in keys if sp == split] for split in splits}

    return Ul(
                *[SplitCard(session, split, metrics[split]) for split in splits],
                cls="comparison-list"
            )




def CompareSetup(session, swap: bool = False):
    from __main__ import CONFIG
    if "hidden_lines" in session["compare"]:
        hidden_lines = session["compare"]["hidden_lines"]
    else:
        hidden_lines = []
    raw_labels = [int(txt) for txt in session["compare"]["selected-rows"]]
    raw_labels = sorted(raw_labels)
    labels = [(str(label), CONFIG.COLORS[i % len(CONFIG.COLORS)], str(label) in hidden_lines) for i, label in enumerate(raw_labels)]
    return Div(
        H1("Setup", cls="chart-scalar-title"),
        Legend(session, labels, path="/compare", selected_rows_key="compare"),
        ChartType(session, path="/compare", selected_rows_key="compare", session_path="compare"),
        Smoother(session, path="/compare", selected_rows_key="compare", session_path="compare"),
        cls="setup-card",
        id="setup-card",
        hx_swap_oob="true" if swap else None,
    )

def build_compare_routes(rt):
    rt("/compare/toggle_accordion")(toggle_accordion)
    rt("/compare/change_chart")(change_chart_type)
    rt("/compare/hide_line")(hide_line)
    rt("/compare/show_line")(show_line)
    rt("/compare/change_smoother")(change_smoother)

# Routes
def toggle_accordion(session, split: str, metrics: str, open: bool):
    return SplitCard(session, split, opened=open, metrics=metrics.split(","))

def change_chart_type(session, runIDs: str, step: bool):
    new_type = "time" if step else "step"
    session["compare"]["chart_type"] = new_type
    return ChartType(session, path="/compare", session_path="compare", selected_rows_key="compare") # We want to toggle it

def hide_line(session, runIDs: str, label: str):
    if 'hidden_lines' not in session["compare"]:
        session["compare"]['hidden_lines'] = []
    session["compare"]['hidden_lines'].append(label)
    return CompareSetup(session, swap=True)


def show_line(session, runIDs: str, label: str):
    if 'hidden_lines' not in session["compare"]:
        session["compare"]['hidden_lines'] = []
    if label in session["compare"]['hidden_lines']:
        session["compare"]['hidden_lines'].remove(label)

    return CompareSetup(session, swap=True)

def change_smoother(session, runIDs: str, smoother: int):
    session["compare"]["smoother_value"] = smoother
    return CompareSetup(session, swap=True)