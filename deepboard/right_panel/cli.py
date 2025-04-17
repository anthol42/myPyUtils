from typing import *
from datetime import datetime, timedelta
from fasthtml.common import *
from markupsafe import Markup

def CliView(runID: int):
    from __main__ import rTable
    row = rTable.fetch_experiment(runID)
    cli = {keyvalue.split("=")[0]:"=".join(keyvalue.split("=")[1:]) for keyvalue in row[4].split(" ")}
    print(cli)
    lines = [P(Markup(f"- {key}: {value}"), cls="config-part") for key, value in cli.items()]
    return Div(
        *lines,
        cls="file-view",
    )