from pyutils.resultTable import ResultTable
import plotly.graph_objects as go
import pandas as pd
from typing import *
from datetime import datetime, timedelta
from fasthtml.common import *
from fh_plotly import plotly_headers, plotly2fasthtml

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

PLOTLY_THEME = dict(
        plot_bgcolor='#111111',     # dark background for the plotting area
        paper_bgcolor='#111111',    # dark background for the full figure
        font=dict(color='white'),   # white text everywhere (axes, legend, etc.)
        xaxis=dict(
            gridcolor='#333333',    # subtle dark grid lines
            zerolinecolor='#333333'
        ),
        yaxis=dict(
            gridcolor='#333333',
            zerolinecolor='#333333'
        ),
)

def make_df(socket, tag) -> Tuple[pd.DataFrame, List[int], List[int]]:
    scalars = socket.read_scalar("/".join(tag))
    steps = [scalar.step for scalar in scalars]
    value = [scalar.value for scalar in scalars]
    repetition = [scalar.run_rep for scalar in scalars]
    walltime = [scalar.wall_time for scalar in scalars]
    epochs = [scalar.epoch for scalar in scalars]
    df = pd.DataFrame({
        "step": steps,
        "value": value,
        "repetition": repetition,
        "walltime": walltime,
        "epoch": epochs
    })
    available_rep = df["repetition"].unique()
    available_epochs = df["epoch"].unique()
    df = df.set_index(["step", "repetition"])
    return df, available_rep, available_epochs

def make_step_lines(socket, splits: set[str], metric: str, keys: set[tuple[str, str]]):
    lines = []
    for i, split in enumerate(splits):
        tag = (split, metric)
        if tag in keys:
            df, available_rep, available_epochs = make_df(socket, tag)
            for rep in available_rep:
                rep_df = df.loc[(slice(None), rep), :]
                lines.append((
                    f'{split}_{rep}',
                    rep_df.index.get_level_values("step"),
                    rep_df["value"],
                    COLORS[i % len(COLORS)],
                    rep_df["epoch"].values if len(available_epochs) > 1 else None,
                ))
    return lines

def make_time_lines(socket, splits: set[str], metric: str, keys: set[tuple[str, str]]):
    lines = []
    for i, split in enumerate(splits):
        tag = (split, metric)
        if tag in keys:
            df, available_rep, available_epochs = make_df(socket, tag)
            for rep in available_rep:
                rep_df = df.loc[(slice(None), rep), :]
                lines.append((
                    f'{split}_{rep}',
                    rep_df["walltime"],
                    rep_df["value"],
                    COLORS[i % len(COLORS)],
                    rep_df["epoch"].values if len(available_epochs) > 1 else None,
                ))
    return lines

def make_fig(lines, type: str = "step"):
    fig = go.Figure()

    for label, steps, values, color, epochs in lines:
        if epochs is not None:
            additional_setup = dict(hovertext=values, customdata=[[e, label] for e in epochs],
                                    hovertemplate="%{customdata[1]} : %{y:.4f} | Epoch: %{customdata[0]}<extra></extra>")
        else:
            additional_setup = dict(hovertext=values, customdata=[[label] for _ in values],
                                    hovertemplate="%{customdata[0]} : %{y:.4f}<extra></extra>")

        if type == "time":
            steps = [datetime(1970, 1, 1) + timedelta(seconds=s) for s in steps]
        fig.add_trace(go.Scatter(
            x=steps,
            y=values,
            mode='lines',
            name=label,
            line=dict(color=color),
            **additional_setup
        ))

    if type == "step":
        fig.update_layout(
            PLOTLY_THEME,
            xaxis_title="Step",
            yaxis_title="Value",
            hovermode="x unified",
            showlegend=False,
            autosize=True,
            height=None,  # Let CSS control it
            width=None,  # Let CSS control it
            margin=dict(l=0, r=0, t=15, b=0)
        )
    elif type == "time":
        fig.update_layout(
            PLOTLY_THEME,
            xaxis_title="Duration",
            yaxis_title="Value",
            hovermode="x unified",
            showlegend=False,
            xaxis_tickformat="%H:%M:%S",  # format the ticks like 01:23:45
            autosize=True,
            height=None,  # Let CSS control it
            width=None,  # Let CSS control it
            margin=dict(l=0, r=0, t=15, b=0)
        )
    else:
        raise ValueError(f"Unknown plotting type: {type}")
    return fig



def LegendLine(label: str, color: str):
    return Li(
        Span(cls="legend-icon", style=f"background-color: {color};"),
        A(label, cls="legend-label"),
        cls="legend-line"
    )
def Legend(runID: int, labels: list[tuple]):
    return Div(
        H2("Legend", cls="chart-legend-title"),
        Ul(
            *[LegendLine(label, color) for label, color in labels],
            cls="chart-legend",
            id=f"chart-legend-{runID}"
        ),
        cls="chart-toolbox",
    )

def Smoother(value: float):
    return Div(
        H2("Smoother", cls="setup-title"),
        Div(
            P(value),
            Input(type="range", min=0, max=100, value=1, id=f"chart-smoother"),
            cls="chart-smoother-container",
        ),
        cls="chart-toolbox",
    )

def ChartType(runID: int, type: str):
    return Div(
        H2("Step/Duration", cls="setup-title"),
        Input(type="checkbox", name="Step chart", id=f"chart-type-step-{runID}", value="step", cls="chart-type-checkbox",
              checked=type == "step", hx_get=f"/scalars/change_chart?runID={runID}&step={type == 'step'}",
              hx_swap="outerHTML", hx_target="#chart-type-selector"),
        style="display: flex; flex-direction: row; align-items: center; justify-content: space-between; width: 100%;",
        id="chart-type-selector"
    )

def Setup(runID: int, labels: list[tuple], smooth: float):
    return Div(
        H1("Setup", cls="chart-scalar-title"),
        Div(
            Div(
                Smoother(smooth),
                ChartType(runID, type="step"),
                style="width: 100%; margin-right: 1em; display: flex; flex-direction: column; align-items: flex-start",
            ),
            Legend(runID, labels),
            cls="chart-setup-container",
        ),
        cls="chart-setup",
    )
# Components
def Chart(runID: int, metric: str, type: str = "step"):
    from __main__ import rTable
    socket = rTable.load_run(runID)
    keys = socket.formatted_scalars
    # metrics = {label for split, label in keys}
    splits = {split for split, label in keys}

    if type == "step":
        lines = make_step_lines(socket, splits, metric, keys)
    elif type == "time":
        lines = make_time_lines(socket, splits, metric, keys)
    else:
        raise ValueError(f"Unknown plotting type: {type}")

    # # Sort lines by label
    lines.sort(key=lambda x: x[0])
    fig = make_fig(lines, type=type)

    return Div(
        Div(
            H1(metric, cls="chart-title"),
            cls="chart-header",
            id=f"chart-header-{runID}-{metric}"
        ),
        Div(
            plotly2fasthtml(fig, js_options=dict(responsive=True)),
            cls="chart-container",
            id=f"chart-container-{runID}-{metric}"
        ),
        cls="chart",
        id=f"chart-{runID}-{metric}",
    )

def Charts(runID: int, type: str = "step", swap: bool = False):
    from __main__ import rTable
    socket = rTable.load_run(runID)
    keys = socket.formatted_scalars
    metrics = {label for split, label in keys}
    out = Div(
            H1("Charts", cls="chart-scalar-title"),
        Ul(
            *[
                Li(Chart(runID, metric, type=type), cls="chart-list-item")
                for metric in metrics
            ],
            cls="chart-list",
        ),
        cls="chart-section",
        id=f"charts-section",
        hx_swap_oob="true" if swap else None,
    )
    return out

def ScalarTab(runID, hidden_lines: List[str] = None):
    from __main__ import rTable
    socket = rTable.load_run(runID)
    keys = socket.formatted_scalars
    splits = {split for split, label in keys}
    # Get repetitions
    available_rep = socket.get_repetitions()
    line_names = [(f'{split}_{rep}', COLORS[i % len(COLORS)]) for i, split in enumerate(splits) for rep in
                  available_rep]
    # Sort lines by label
    line_names.sort(key=lambda x: x[0])
    if hidden_lines is not None:
        line_names = [line for line in line_names if line[0] not in hidden_lines]
    return Div(
        Setup(runID, line_names, smooth=0.),
        Charts(runID),
        style="display; flex; width: 40vw; flex-direction: column; align-items: center; justify-content: center;",
    )


def build_scalar_routes(rt):
    rt("/scalars/change_chart")(change_chart_type)


# Interactive Routes
def change_chart_type(runID: int, step: bool):
    return (
        ChartType(runID, type="time" if step else "step"), # We want to toggle it
        Charts(runID, type="time" if step else "step", swap=True)
            )
