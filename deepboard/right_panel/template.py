from fasthtml.common import *
from datetime import datetime
from .scalars import ScalarTab
from .config import ConfigView
from .hparams import HParamsView
from .run_info import InfoView

def reset_scalar_session(session):
    session["scalars"] = dict(
        hidden_lines=[],
        smoother_value=1,
        chart_type='step'
    )

def RightPanelContent(session, run_id: int, active_tab: str):
    if active_tab == 'scalars':
        tab_content = ScalarTab(session, run_id)
    elif active_tab == 'config':
        tab_content = ConfigView(run_id)
    elif active_tab == 'hparams':
        tab_content = HParamsView(run_id)
    elif active_tab == 'run_info':
        tab_content = InfoView(run_id)
    else:
        tab_content = Div(
            P("Invalid tab selected.", cls="error-message")
        )

    run_name = "DEBUG" if run_id == -1 else run_id
    return Div(
        H1(f"Run: {run_name}"),
        Div(
            Div('Scalars', cls='tab active' if active_tab == 'scalars' else 'tab',
                hx_get=f'/fillpanel?run_id={run_id}&tab=scalars', hx_target='#right-panel-content',
                hx_swap='outerHTML'),
            Div('Config', cls='tab active' if active_tab == 'config' else 'tab',
                hx_get=f'/fillpanel?run_id={run_id}&tab=config', hx_target='#right-panel-content', hx_swap='outerHTML'),
            Div('HParams', cls='tab active' if active_tab == 'hparams' else 'tab',
                hx_get=f'/fillpanel?run_id={run_id}&tab=hparams', hx_target='#right-panel-content', hx_swap='outerHTML'),
            Div('Info', cls='tab active' if active_tab == 'run_info' else 'tab',
                hx_get=f'/fillpanel?run_id={run_id}&tab=run_info', hx_target='#right-panel-content',
                hx_swap='outerHTML'),
            cls='tab-menu'
        ),
        Div(
            tab_content,
            id='tab-content', cls='tab-content'
        ),
        cls="right-panel-content",
        id="right-panel-content"
    ),

def OpenPanel(session, run_id: int, active_tab: str = 'scalars'):
    return Div(
        RightPanelContent(session, run_id, active_tab),
        cls="open-right-panel"
    )

def RightPanel(session):
    placeholder_text = [
        P("Select an item to see the run", cls="right-panel-placeholder"),
        P("Shift + click to compare runs", cls="right-panel-placeholder")
    ]
    if "datagrid" in session and session["datagrid"].get("selected-rows") and len(session["datagrid"]["selected-rows"]) == 1:
        run_id = session["datagrid"]["selected-rows"][0]
    else:
        run_id = None
    return Div(
        Button(
            I(cls="fas fa-times"),
            hx_get="/reset",
            hx_target="#container",
            hx_swap="outerHTML",
            cls="close-button",
        ) if run_id is not None else None,
        Div(*placeholder_text) if run_id is None else OpenPanel(session, run_id),
        id='right-panel',
        hx_swap_oob='true'
    ),


def fill_panel(session, run_id: int, tab: str):
    return RightPanelContent(session, run_id, tab)


# 418 682 1744
