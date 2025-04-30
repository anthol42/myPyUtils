from fasthtml.common import *

def ChartType(session, path: str):
    if "datagrid" in session and "selected-rows" in session["datagrid"] and len(session["datagrid"]["selected-rows"]) > 0:
        runIDs = session["datagrid"]["selected-rows"]
        runIDs = ','.join([str(i) for i in runIDs])
    else:
        print("Warning: no selected lines")
        runIDs = ""

    if "chart_type" not in session["scalars"]:
        session["scalars"]["chart_type"] = "step"
    type = session["scalars"]["chart_type"]
    return Div(
        H2("Step/Duration", cls="setup-title"),
        Input(type="checkbox", name="Step chart", id=f"chart-type-step-{runIDs}", value="step", cls="chart-type-checkbox",
              checked=type == "step", hx_get=f"{path}/change_chart?runIDs={runIDs}&step={type == 'step'}",
              hx_swap="outerHTML", hx_target="#chart-type-selector"),
        style="display: flex; flex-direction: row; align-items: center; justify-content: space-between; width: 100%;",
        id="chart-type-selector"
    )