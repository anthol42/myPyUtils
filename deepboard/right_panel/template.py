from fasthtml.common import *
from datetime import datetime
from .scalars import ScalarTab
from .config import ConfigView

def RightPanelContent(session, run_id: int, active_tab: str):
    if active_tab == 'scalars':
        tab_content = ScalarTab(session, run_id)
    else:
        tab_content = ConfigView(run_id)
    return Div(
        H1(f"Run Id: {run_id}"),
        Div(
            Div('Scalars', cls='tab active' if active_tab == 'scalars' else 'tab',
                hx_get=f'/fillpanel?run_id={run_id}&tab=scalars', hx_target='#right-panel-content',
                hx_swap='outerHTML'),
            Div('Config', cls='tab active' if active_tab == 'config' else 'tab',
                hx_get=f'/fillpanel?run_id={run_id}&tab=config', hx_target='#right-panel-content', hx_swap='outerHTML'),
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

def RightPanel(session, run_id: int = None):
    if run_id is None:
        placeholder_text = 'Select an item to see the content.'
    else:
        placeholder_text = f'Row {run_id} selected'
    return Div(
        Button(
            I(cls="fas fa-times"),
            hx_get="/reset",
            hx_target="#container",
            cls="close-button",
        ) if run_id is not None else None,
        Div(P(placeholder_text, cls="right-panel-placeholder")) if run_id is None else OpenPanel(session, run_id),
        id='right-panel',
        hx_swap_oob='outerHTML'
    ),


def fill_panel(session, run_id: int, tab: str):
    return RightPanelContent(session, run_id, tab)


# 418 682 1744
