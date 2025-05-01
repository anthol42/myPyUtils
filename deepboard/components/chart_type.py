from fasthtml.common import *

def ChartType(session, path: str, selected_rows_key: str, session_path: str):
    if selected_rows_key in session and "selected-rows" in session[selected_rows_key] and len(session[selected_rows_key]["selected-rows"]) > 0:
        runIDs = session[selected_rows_key]["selected-rows"]
        runIDs = ','.join([str(i) for i in runIDs])
    else:
        print("Warning: no selected lines")
        runIDs = ""
        print(session)

    if "chart_type" not in session[session_path]:
        session[session_path]["chart_type"] = "step"
    type = session[session_path]["chart_type"]
    return Div(
        H2("Step/Duration", cls="setup-title"),
        Input(type="checkbox", name="Step chart", id=f"chart-type-step-{runIDs}", value="step", cls="chart-type-checkbox",
              checked=type == "step", hx_get=f"{path}/change_chart?runIDs={runIDs}&step={type == 'step'}",
              hx_swap="outerHTML", hx_target="#chart-type-selector"),
        style="display: flex; flex-direction: row; align-items: center; justify-content: space-between; width: 100%;",
        id="chart-type-selector"
    )