import plotly.graph_objects as go
import pandas as pd
from typing import *
from datetime import datetime, timedelta
from fasthtml.common import *
from fh_plotly import plotly2fasthtml

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

def ema(values, alpha):
    """
    Compute the Exponential Moving Average (EMA) of a list of values.

    Parameters:
    - values (list or numpy array): The data series.
    - alpha (float): Smoothing factor (between 0 and 1).

    Returns:
    - list: EMA-smoothed values.
    """
    return values.ewm(alpha=alpha, adjust=False).mean()

def make_fig(lines, type: str = "step", smoothness: float = 0.):
    fig = go.Figure()

    for label, steps, values, color, epochs in lines:
        # Smooth the values
        if smoothness > 0:
            values = ema(values, 1.01 - smoothness / 100)
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



def LegendLine(session, runID: int, label: str, color: str, hidden: bool):
    if hidden:
        return Li(
            Span(cls="legend-icon", style=f"background-color: {HIDDEN_COLOR};"),
            A(label, cls="legend-label", style=f"color: {HIDDEN_COLOR};"),
            hx_get=f"/scalars/show_line?runID={runID}&label={label}",
            cls="legend-line"
        )
    else:
        return Li(
            Span(cls="legend-icon", style=f"background-color: {color};"),
            A(label, cls="legend-label"),
            hx_get=f"/scalars/hide_line?runID={runID}&label={label}",
            cls="legend-line"
        )
def Legend(session, runID: int, labels: list[tuple]):
    return Div(
        H2("Legend", cls="chart-legend-title"),
        Ul(
            *[LegendLine(session, runID, label, color, hidden) for label, color, hidden in labels],
            cls="chart-legend",
            id=f"chart-legend-{runID}"
        ),
        cls="chart-toolbox",
    )

def Smoother(session, runID: int):
    if "smoother_value" not in session["scalars"]:
        session["scalars"]["smoother_value"] = 1
    value = session["scalars"]["smoother_value"]
    return Div(
        H2("Smoother", cls="setup-title"),
        Div(
            P(f"{value - 1}%"),
            Input(type="range", min=1, max=101, value=value, id=f"chart-smoother", name="smoother",
                  hx_get=f"/scalars/change_smoother?runID={runID}", hx_trigger="change"),
            cls="chart-smoother-container",
        ),
        cls="chart-toolbox",
    )

def ChartType(session, runID: int):
    if "chart_type" not in session["scalars"]:
        session["scalars"]["chart_type"] = "step"
    type = session["scalars"]["chart_type"]
    return Div(
        H2("Step/Duration", cls="setup-title"),
        Input(type="checkbox", name="Step chart", id=f"chart-type-step-{runID}", value="step", cls="chart-type-checkbox",
              checked=type == "step", hx_get=f"/scalars/change_chart?runID={runID}&step={type == 'step'}",
              hx_swap="outerHTML", hx_target="#chart-type-selector"),
        style="display: flex; flex-direction: row; align-items: center; justify-content: space-between; width: 100%;",
        id="chart-type-selector"
    )

def Status(session, runID: int, status: Literal["running", "finished", "failed"]):
    return Div(
        H2("Status", cls="setup-title"),
        Select(
            Option("Running", value="running", selected=status == "running", cls="run-status-option running"),
            Option("Finished", value="finished", selected=status == "finished", cls="run-status-option finished"),
            Option("Failed", value="failed", selected=status == "failed", cls="run-status-option failed"),
            id=f"runstatus-select",
            name="run_status",
            hx_get=f"/scalars/change_status?runID={runID}",
            hx_target="#scalar-tab",
            hx_trigger="change",
            hx_swap="outerHTML",
            hx_params="*",
            cls="run-status-select" + " " + status,
        ),
        style="display: flex; flex-direction: row; align-items: center; justify-content: space-between; width: 100%;",
        id="chart-type-selector"
    )
def Setup(session, runID: int, labels: list[tuple], status: Literal["running", "finished", "failed"]):
    return Div(
        H1("Setup", cls="chart-scalar-title"),
        Div(
            Div(
                Smoother(session, runID),
                ChartType(session, runID),
                Status(session, runID, status),
                style="width: 100%; margin-right: 1em; display: flex; flex-direction: column; align-items: flex-start",
            ),
            Legend(session, runID, labels),
            cls="chart-setup-container",
        ),
        cls="chart-setup",
    )
# Components
def Chart(session, runID: int, metric: str, type: str = "step", running: bool = False):
    from __main__ import rTable
    socket = rTable.load_run(runID)
    keys = socket.formatted_scalars
    # metrics = {label for split, label in keys}
    splits = {split for split, label in keys}
    hidden_lines = session["scalars"]["hidden_lines"] if "hidden_lines" in session["scalars"] else []
    smoothness = session["scalars"]["smoother_value"] - 1 if "smoother_value" in session["scalars"] else 0
    if type == "step":
        lines = make_step_lines(socket, splits, metric, keys)
    elif type == "time":
        lines = make_time_lines(socket, splits, metric, keys)
    else:
        raise ValueError(f"Unknown plotting type: {type}")

    # # Sort lines by label
    lines.sort(key=lambda x: x[0])
    # Hide lines if needed
    lines = [line for line in lines if line[0] not in hidden_lines]
    fig = make_fig(lines, type=type, smoothness=smoothness)

    if running:
        update_params = dict(
            hx_get=f"/scalars/chart?runID={runID}&metric={metric}&type={type}&running={running}",
            hx_target=f"#chart-container-{runID}-{metric}",
            hx_trigger="every 10s",
            hx_swap="outerHTML",
        )
    else:
        update_params = {}
    return Div(
            plotly2fasthtml(fig, js_options=dict(responsive=True)),
            cls="chart-container",
            id=f"chart-container-{runID}-{metric}",
            **update_params
        )

def LoadingChart(session, runID: int, metric: str, type: str, running: bool = False):
    return Div(
        Div(
            H1(metric, cls="chart-title"),
            cls="chart-header",
            id=f"chart-header-{runID}-{metric}"
        ),
        Div(
            cls="chart-container",
            id=f"chart-container-{runID}-{metric}",
            hx_get=f"/scalars/chart?runID={runID}&metric={metric}&type={type}&running={running}",
            hx_target=f"#chart-container-{runID}-{metric}",
            hx_trigger="load",
        ),
        cls="chart",
        id=f"chart-{runID}-{metric}",
    )

def Charts(session, runID: int, swap: bool = False, status: Literal["running", "finished", "failed"] = "running"):
    from __main__ import rTable
    socket = rTable.load_run(runID)
    keys = socket.formatted_scalars
    metrics = {label for split, label in keys}
    type = session["scalars"]["chart_type"] if "chart_type" in session["scalars"] else "step"
    out = Div(
            H1("Charts", cls="chart-scalar-title"),
        Ul(
            *[
                Li(LoadingChart(session, runID, metric, type=type, running=status == "running"), cls="chart-list-item")
                for metric in metrics
            ],
            cls="chart-list",
        ),
        cls="chart-section",
        id=f"charts-section",
        hx_swap_oob="true" if swap else None,
    )
    return out

def ScalarTab(session, runID, swap: bool = False):
    if 'hidden_lines' not in session:
        session["scalars"]['hidden_lines'] = []
    from __main__ import rTable
    socket = rTable.load_run(runID)
    keys = socket.formatted_scalars
    splits = {split for split, label in keys}
    # Get repetitions
    available_rep = socket.get_repetitions()
    line_names = [(f'{split}_{rep}', COLORS[i % len(COLORS)], f'{split}_{rep}' in session["scalars"]['hidden_lines']) for i, split in enumerate(splits) for rep in
                  available_rep]
    # Sort lines by label
    line_names.sort(key=lambda x: x[0])
    status = socket.status
    return Div(
        Setup(session, runID, line_names, status),
        Charts(session, runID, status=status),
        style="display; flex; width: 40vw; flex-direction: column; align-items: center; justify-content: center;",
        id="scalar-tab",
        hx_swap_oob="true" if swap else None,
    )


def build_scalar_routes(rt):
    rt("/scalars/change_chart")(change_chart_type)
    rt("/scalars/hide_line")(hide_line)
    rt("/scalars/show_line")(show_line)
    rt("/scalars/change_smoother")(change_smoother)
    rt("/scalars/chart")(load_chart)
    rt("/scalars/change_status")(change_status)


# Interactive Routes
def change_chart_type(session, runID: int, step: bool):
    new_type = "time" if step else "step"
    session["scalars"]["chart_type"] = new_type
    return (
        ChartType(session, runID), # We want to toggle it
        Charts(session, runID, swap=True)
            )

def hide_line(session, runID: int, label: str):
    if 'hidden_lines' not in session["scalars"]:
        session["scalars"]['hidden_lines'] = []

    session["scalars"]['hidden_lines'].append(label)
    return ScalarTab(session, runID, swap=True)


def show_line(session, runID: int, label: str):
    if 'hidden_lines' not in session["scalars"]:
        session["scalars"]['hidden_lines'] = []

    if label in session["scalars"]['hidden_lines']:
        session["scalars"]['hidden_lines'].remove(label)

    return ScalarTab(session, runID, swap=True)

def change_smoother(session, runID: int, smoother: int):
    session["scalars"]["smoother_value"] = smoother
    return ScalarTab(session, runID, swap=True)

def load_chart(session, runID: int, metric: str, type: str, running: bool):
    return Chart(session, runID, metric, type, running)

def change_status(session, runID: int, run_status: str):
    from __main__ import rTable
    socket = rTable.load_run(runID)
    socket.set_status(run_status)
    return ScalarTab(session, runID, swap=True)