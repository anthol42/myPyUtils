from datetime import datetime, date
import sqlite3
from typing import *
import pandas as pd

def _adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 date."""
    return val.isoformat()


def _adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.isoformat()

def _convert_date(val):
    """Convert ISO 8601 date to datetime.date object."""
    return date.fromisoformat(val.decode())


def _convert_datetime(val):
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return datetime.fromisoformat(val.decode())

def prepare_db():

    sqlite3.register_adapter(datetime.date, _adapt_date_iso)
    sqlite3.register_adapter(datetime, _adapt_datetime_iso)


    sqlite3.register_converter("date", _convert_date)
    sqlite3.register_converter("datetime", _convert_datetime)

def make_df(socket, tag: Tuple[str, str]) -> Tuple[pd.DataFrame, List[int], List[int]]:
    scalars = socket.read_scalar("/".join(tag))
    steps = [scalar.step for scalar in scalars]
    value = [scalar.value for scalar in scalars]
    repetition = [scalar.run_rep for scalar in scalars]
    walltime = [scalar.wall_time for scalar in scalars]
    epochs = [scalar.epoch for scalar in scalars]
    df = pd.DataFrame({
        "step": steps,
        "value": value,
        "repetition": repetition,
        "duration": walltime,
        "epoch": epochs
    })
    available_rep = df["repetition"].unique()
    available_epochs = df["epoch"].unique()
    df = df.set_index(["step", "repetition"])
    return df, available_rep, available_epochs

def get_lines(socket, split, metric, key: Literal["step", "duration"]):
    out = []
    df, available_rep, available_epochs = make_df(socket, (split, metric))
    for rep in available_rep:
        rep_df = df.loc[(slice(None), rep), :]
        out.append({
            "index": rep_df.index.get_level_values("step"),
            "value": rep_df["value"],
            "epoch": rep_df["epoch"].values if len(available_epochs) > 1 else None,
        })
    return out