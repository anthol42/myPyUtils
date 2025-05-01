from fasthtml.common import *
from datetime import datetime
from deepboard.components import Legend, ChartType, Smoother
from deepboard.utils import get_lines, make_fig
from fh_plotly import plotly2fasthtml
from typing import *

def make_lines(sockets, split: str, metric: str, runIDs: List[int], type: Literal["step", "duration"]):
    from __main__ import CONFIG
    lines = []
    all_reps = [socket.get_repetitions() for socket in sockets]
    multi_rep = any(len(rep) > 1 for rep in all_reps)
    for i, runID in enumerate(runIDs):
        reps = get_lines(sockets[i], split, metric, key=type)

        for rep_idx, rep in enumerate(reps):
            lines.append((
                f'{runID}.{rep_idx}' if multi_rep else f'{runID}',
                rep["index"],
                rep["value"],
                CONFIG.COLORS[i % len(CONFIG.COLORS)],
                rep["epoch"],
            ))
    return lines

def Chart(session, split: str, metric: str, type: Literal["step", "duration"], running: bool = False):
    from __main__ import rTable
    runIDs = [int(txt) for txt in session["compare"]["selected-rows"]]
    sockets = [rTable.load_run(runID) for runID in runIDs]
    hidden_lines = session["compare"]["hidden_lines"] if "hidden_lines" in session["compare"] else []
    smoothness = session["compare"]["smoother_value"] - 1 if "smoother_value" in session["compare"] else 0
    lines = make_lines(sockets, split, metric, runIDs, type)

    # # Sort lines by label
    lines.sort(key=lambda x: x[0])
    # Hide lines if needed
    lines = [line for line in lines if line[0] not in hidden_lines]
    fig = make_fig(lines, type=type, smoothness=smoothness)

    if running:
        update_params = dict(
            hx_get=f"/compare/chart?split={split}&metric={metric}&type={type}&running={running}",
            hx_target=f"#chart-container-{split}-{metric}",
            hx_trigger="every 10s",
            hx_swap="outerHTML",
        )
    else:
        update_params = {}
    return  Div(
            plotly2fasthtml(fig, js_options=dict(responsive=True)),
            cls="chart-container",
            id=f"chart-container-{split}-{metric}",
            **update_params
        ),

def LoadingChart(session, split: str, metric: str, type: Literal["step", "duration"], running: bool = False):
    return Div(
            Div(
                H1(metric, cls="chart-title"),
                cls="chart-header",
                id=f"chart-header-{split}-{metric}"
            ),
        Div(
            cls="chart-container",
            id=f"chart-container-{split}-{metric}",
            hx_get=f"/compare/chart?split={split}&metric={metric}&type={type}&running={running}",
            hx_target=f"#chart-container-{split}-{metric}",
            hx_trigger="load",
        ),
        cls = "chart",
        id = f"chart-{split}-{metric}",
    )

def SplitCard(session, split: str, metrics: List[str]):
    from __main__ import rTable
    runIDs = sorted([int(rid) for rid in session["compare"]["selected-rows"]])
    sockets = [rTable.load_run(runID) for runID in runIDs]
    running = any([socket.status == "running" for socket in sockets])
    metrics = sorted(metrics)
    chart_type = session["compare"]["chart_type"] if "chart_type" in session["compare"] else "step"

    opened = session["compare"]["cards-state"][split] if "cards-state" in session["compare"] and split in session["compare"]["cards-state"] else True
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
                *[LoadingChart(session, split, metric, type=chart_type, running=running) for metric in metrics],
                cls="multi-charts-container"
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

def ChartCardList(session, swap: bool = False):
    runIDs = sorted([int(rid) for rid in session["compare"]["selected-rows"]])
    from __main__ import rTable
    sockets = [rTable.load_run(runID) for runID in runIDs]
    keys = {key for socket in sockets for key in socket.formatted_scalars}
    splits = {split for split, metric in keys}
    splits = sorted(splits)
    metrics = {split: [metric for sp, metric in keys if sp == split] for split in splits}

    return Ul(
                *[SplitCard(session, split, metrics[split]) for split in splits],
                cls="comparison-list",
                id="chart-card-list",
                hx_swap_oob="true" if swap else None
            )




def CompareSetup(session, swap: bool = False):
    from __main__ import CONFIG
    from __main__ import rTable
    if "hidden_lines" in session["compare"]:
        hidden_lines = session["compare"]["hidden_lines"]
    else:
        hidden_lines = []
    raw_labels = [int(txt) for txt in session["compare"]["selected-rows"]]
    raw_labels = sorted(raw_labels)
    sockets = [rTable.load_run(runID) for runID in raw_labels]
    repetitions = [socket.get_repetitions() for socket in sockets]
    if any(len(rep) > 1 for rep in repetitions):
        labels = [(f"{label}.{rep}", CONFIG.COLORS[i % len(CONFIG.COLORS)], f"{label}.{rep}" in hidden_lines) for i, label in enumerate(raw_labels) for rep in sockets[i].get_repetitions()]
    else:
        labels = [(f"{label}", CONFIG.COLORS[i % len(CONFIG.COLORS)], f"{label}" in hidden_lines) for
                  i, label in enumerate(raw_labels)]
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
    rt("/compare/chart")(load_chart)

# Routes
def toggle_accordion(session, split: str, metrics: str, open: bool):
    if "cards-state" not in session["compare"]:
        session["compare"]["cards-state"] = {}
    session["compare"]["cards-state"][split] = open
    return SplitCard(session, split, metrics=metrics.split(","))

def change_chart_type(session, runIDs: str, step: bool):
    new_type = "time" if step else "step"
    session["compare"]["chart_type"] = new_type
    return (ChartType(session, path="/compare", session_path="compare", selected_rows_key="compare"), # We want to toggle it
            ChartCardList(session, swap=True)
    )

def hide_line(session, runIDs: str, label: str):
    if 'hidden_lines' not in session["compare"]:
        session["compare"]['hidden_lines'] = []
    session["compare"]['hidden_lines'].append(label)
    return CompareSetup(session, swap=True), ChartCardList(session, swap=True)


def show_line(session, runIDs: str, label: str):
    if 'hidden_lines' not in session["compare"]:
        session["compare"]['hidden_lines'] = []
    if label in session["compare"]['hidden_lines']:
        session["compare"]['hidden_lines'].remove(label)

    return CompareSetup(session, swap=True), ChartCardList(session, swap=True)

def change_smoother(session, runIDs: str, smoother: int):
    session["compare"]["smoother_value"] = smoother
    return CompareSetup(session, swap=True), ChartCardList(session, swap=True)

def load_chart(session, split: str, metric: str, type: str, running: bool):
    return Chart(session, split, metric, type, running)