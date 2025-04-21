from typing import *
from datetime import datetime, timedelta
from fasthtml.common import *
from markupsafe import Markup

def ConfigView(runID: int):
    from __main__ import rTable

    # Config
    cfg_text = rTable.load_config(runID)
    cfg_parts = cfg_text.splitlines()
    cfg = []
    for part in cfg_parts:
        cfg.append(P(Markup(part), cls="config-part"))

    # Cli
    row = rTable.fetch_experiment(runID)
    if row[4] == "":
        lines = [P(Markup(""), cls="config-part")]
    else:
        cli = {keyvalue.split("=")[0]: "=".join(keyvalue.split("=")[1:]) for keyvalue in row[4].split(" ")}
        lines = [P(Markup(f"- {key}: {value}"), cls="config-part") for key, value in cli.items()]
    return Div(
        Div(
            H2("Configuration"),
            Div(
                *cfg,
                cls="file-view",
            )
        ),
        Div(
            H2("Cli"),
            Div(
                *lines,
                cls="file-view",
            )
        )
    )