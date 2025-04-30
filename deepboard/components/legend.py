from fasthtml.common import *

def LegendLine(session, runIDs: str, label: str, color: str, hidden: bool, path):
    from __main__ import CONFIG
    if hidden:
        return Li(
            Span(cls="legend-icon", style=f"background-color: {CONFIG.HIDDEN_COLOR};"),
            A(label, cls="legend-label", style=f"color: {CONFIG.HIDDEN_COLOR};"),
            hx_get=f"{path}/show_line?runIDs={runIDs}&label={label}",
            cls="legend-line"
        )
    else:
        return Li(
            Span(cls="legend-icon", style=f"background-color: {color};"),
            A(label, cls="legend-label"),
            hx_get=f"{path}/hide_line?runIDs={runIDs}&label={label}",
            cls="legend-line"
        )
def Legend(session, labels: list[tuple], path: str, session_path: str):
    if session_path in session and "selected-rows" in session[session_path] and len(session[session_path]["selected-rows"]) > 0:
        runIDs = session[session_path]["selected-rows"]
        runIDs = ','.join([str(i) for i in runIDs])
    else:
        print("Warning: no selected lines")
        runIDs = ""
    return Div(
        H2("Legend", cls="chart-legend-title"),
        Ul(
            *[LegendLine(session, runIDs, label, color, hidden, path=path) for label, color, hidden in labels],
            cls="chart-legend",
            id=f"chart-legend-{runIDs}"
        ),
        cls="chart-toolbox",
    )