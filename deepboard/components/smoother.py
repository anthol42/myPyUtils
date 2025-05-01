from fasthtml.common import *

def Smoother(session, path: str, selected_rows_key: str, session_path: str):
    if selected_rows_key in session and "selected-rows" in session[selected_rows_key] and len(session[selected_rows_key]["selected-rows"]) > 0:
        runIDs = session[selected_rows_key]["selected-rows"]
    else:
        print("Warning: no selected lines")
        runIDs = []
    if "smoother_value" not in session[session_path]:
        session[session_path]["smoother_value"] = 1
    value = session[session_path]["smoother_value"]
    return Div(
        H2("Smoother", cls="setup-title"),
        Div(
            P(f"{value - 1}%"),
            Input(type="range", min=1, max=101, value=value, id=f"chart-smoother", name="smoother",
                  hx_get=f"{path}/change_smoother?runIDs={','.join(str(i) for i in runIDs)}", hx_trigger="change"),
            cls="chart-smoother-container",
        ),
        cls="chart-toolbox",
    )