from fasthtml.common import *

def LegendLine(session, runID: int, label: str, color: str, hidden: bool, path):
    from __main__ import CONFIG
    if hidden:
        return Li(
            Span(cls="legend-icon", style=f"background-color: {CONFIG.HIDDEN_COLOR};"),
            A(label, cls="legend-label", style=f"color: {CONFIG.HIDDEN_COLOR};"),
            hx_get=f"{path}/show_line?runID={runID}&label={label}",
            cls="legend-line"
        )
    else:
        return Li(
            Span(cls="legend-icon", style=f"background-color: {color};"),
            A(label, cls="legend-label"),
            hx_get=f"{path}/hide_line?runID={runID}&label={label}",
            cls="legend-line"
        )
def Legend(session, runID: int, labels: list[tuple], path: str):
    return Div(
        H2("Legend", cls="chart-legend-title"),
        Ul(
            *[LegendLine(session, runID, label, color, hidden, path=path) for label, color, hidden in labels],
            cls="chart-legend",
            id=f"chart-legend-{runID}"
        ),
        cls="chart-toolbox",
    )