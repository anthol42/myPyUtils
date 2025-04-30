from fasthtml.common import *

def ChartType(session, runID: int, path: str):
    if "chart_type" not in session["scalars"]:
        session["scalars"]["chart_type"] = "step"
    type = session["scalars"]["chart_type"]
    return Div(
        H2("Step/Duration", cls="setup-title"),
        Input(type="checkbox", name="Step chart", id=f"chart-type-step-{runID}", value="step", cls="chart-type-checkbox",
              checked=type == "step", hx_get=f"{path}/change_chart?runID={runID}&step={type == 'step'}",
              hx_swap="outerHTML", hx_target="#chart-type-selector"),
        style="display: flex; flex-direction: row; align-items: center; justify-content: space-between; width: 100%;",
        id="chart-type-selector"
    )