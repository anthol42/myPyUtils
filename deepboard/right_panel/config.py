from typing import *
from datetime import datetime, timedelta
from fasthtml.common import *
from markupsafe import Markup

def ConfigView(runID: int):
    from __main__ import rTable
    cfg_text = rTable.load_config(runID)
    cfg_parts = cfg_text.splitlines()
    cfg = []
    for part in cfg_parts:
        cfg.append(P(Markup(part), cls="config-part"))
    return Div(
        *cfg,
        cls="file-view",
    )