from typing import *
from datetime import datetime, timedelta
from fasthtml.common import *
from markupsafe import Markup


def CopyToClipboard(text: str, cls):
    return Div(
        Span(
            I(cls=f'fas fa-copy copy-icon default-icon {cls}'),
            I(cls=f'fas fa-check copy-icon check-icon {cls}'),
            cls='copy-icon-container',
        ),
        Span(text, cls='copy-text' + ' ' + cls),
        onclick='copyToClipboard(this)',
        cls='copy-container'
    )

def Status(runID: int, status: Literal["running", "finished", "failed"], swap: bool = False):
    swap_oob = dict(swap_oob="true") if swap else {}
    return Select(
            Option("Running", value="running", selected=status == "running", cls="run-status-option running"),
            Option("Finished", value="finished", selected=status == "finished", cls="run-status-option finished"),
            Option("Failed", value="failed", selected=status == "failed", cls="run-status-option failed"),
            id=f"runstatus-select",
            name="run_status",
            hx_get=f"/runinfo/change_status?runID={runID}",
            hx_target="#runstatus-select",
            hx_trigger="change",
            hx_swap="outerHTML",
            hx_params="*",
            **swap_oob,
            cls="run-status-select" + " " + status,
        )

def DiffView(diff: Optional[str]):
    diff_parts = diff.splitlines() if diff else [""]
    dff = []
    for part in diff_parts:
        dff.append(P(Markup(part), cls="config-part"))
    return Div(
        H2("Diff"),
            Div(
                *dff,
                cls="file-view",
            )
        )


def InfoView(runID: int):
    from __main__ import rTable
    # Cli
    row = rTable.fetch_experiment(runID)
    # RunID, Exp name, cfg, cfg hash, cli, comment, start, status, commit, diff
    start: datetime = datetime.fromisoformat(row[6])
    status = row[7]
    commit = row[8]
    diff = row[9]
    return Div(
        Table(
            Tr(
                Td(H3("Start", cls="info-label")),
                Td(H3(start.strftime("%Y-%m-%d %H:%M:%S"), cls="info-value")),
            ),
            Tr(
                Td(H3("Status", cls="info-label")),
                Td(Status(runID, status), cls="align-right"),
            ),
            Tr(
                Td(H3("Commit", cls="info-label")),
                Td(CopyToClipboard(commit, cls="info-value"), cls="align-right"),
            ),
            cls="info-table",
        ),
        DiffView(diff)
    )



# Routes
def build_info_routes(rt):
    rt("/runinfo/change_status")(change_status)

def change_status(session, runID: int, run_status: str):
    from __main__ import rTable
    socket = rTable.load_run(runID)
    socket.set_status(run_status)
    return Status(runID, run_status, swap=True)