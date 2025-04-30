from fasthtml.common import *
from datetime import datetime
from deepboard.components import Legend, ChartType, Smoother


def SplitCard(session, split: str, opened: bool = True):
    if opened:
        return Li(
            Div(
                H1(split, cls=".split-card-title"),
                Button(
                    I(cls="fas fa-chevron-down"),
                    hx_get=f"/compare/toggle_accordion?split={split}&open=false",
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
                    hx_get=f"/compare/toggle_accordion?split={split}&open=true",
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
    return Ul(
                SplitCard(session, "Train"),
                    SplitCard(session, "Step"),
                    SplitCard(session, "Valid"),
                cls="comparison-list"
            )




def CompareSetup(session):
    from __main__ import CONFIG
    labels_text = session["compare"]["selected-rows"]
    labels = [(label, CONFIG.COLORS[i % len(CONFIG.COLORS)], False) for i, label in enumerate(labels_text)]
    return Div(
        H1("Setup", cls="chart-scalar-title"),
        Legend(session, labels, path="/compare", session_path="compare"),
        ChartType(session, path="/compare", session_path="compare"),
        Smoother(session, path="/compare", session_path="compare"),
        cls="setup-card"
    )

def build_compare_routes(rt):
    rt("/compare/toggle_accordion")(toggle_accordion)

# Routes
def toggle_accordion(session, split: str, open: bool):
    return SplitCard(session, split, opened=open)