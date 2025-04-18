from typing import *
from datetime import datetime, timedelta
from fasthtml.common import *
from markupsafe import Markup

def HParamsView(runID: int):
    from __main__ import rTable
    socket = rTable.load_run(runID)
    hparams = socket.get_hparams()
    return Div(
        Table(
            Tr(
                Th('Parameter'),
                Th('Value'),
            ),
            *[
                Tr(
                    Td(key),
                    Td(value),
                )
                for key, value in hparams.items()
            ],
            cls="hparams-table",
        )
    )