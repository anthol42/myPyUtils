from datetime import datetime, date, timedelta
import sqlite3
from typing import *
import pandas as pd
import plotly.graph_objects as go
from decimal import Decimal, ROUND_HALF_UP
import yaml
import os

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

def ema(values, alpha):
    """
    Compute the Exponential Moving Average (EMA) of a list of values.

    Parameters:
    - values (list or numpy array): The data series.
    - alpha (float): Smoothing factor (between 0 and 1).

    Returns:
    - list: EMA-smoothed values.
    """
    return values.ewm(alpha=alpha, adjust=False).mean()

def make_fig(lines, type: str = "step", smoothness: float = 0.):
    from __main__ import CONFIG
    fig = go.Figure()

    for label, steps, values, color, epochs in lines:
        # Smooth the values
        if smoothness > 0:
            values = ema(values, 1.01 - smoothness / 100)
        if epochs is not None:
            additional_setup = dict(hovertext=values, customdata=[[e, label] for e in epochs],
                                    hovertemplate="%{customdata[1]} : %{y:.4f} | Epoch: %{customdata[0]}<extra></extra>")
        else:
            additional_setup = dict(hovertext=values, customdata=[[label] for _ in values],
                                    hovertemplate="%{customdata[0]} : %{y:.4f}<extra></extra>")

        if type == "time":
            steps = [datetime(1970, 1, 1) + timedelta(seconds=s) for s in steps]
        fig.add_trace(go.Scatter(
            x=steps,
            y=values,
            mode='lines',
            name=label,
            line=dict(color=color),
            **additional_setup
        ))

    if type == "step":
        fig.update_layout(
            CONFIG.PLOTLY_THEME,
            xaxis_title="Step",
            yaxis_title="Value",
            hovermode="x unified",
            showlegend=False,
            autosize=True,
            height=None,  # Let CSS control it
            width=None,  # Let CSS control it
            margin=dict(l=0, r=0, t=15, b=0)
        )
    elif type == "time":
        fig.update_layout(
            CONFIG.PLOTLY_THEME,
            xaxis_title="Duration",
            yaxis_title="Value",
            hovermode="x unified",
            showlegend=False,
            xaxis_tickformat="%H:%M:%S",  # format the ticks like 01:23:45
            autosize=True,
            height=None,  # Let CSS control it
            width=None,  # Let CSS control it
            margin=dict(l=0, r=0, t=15, b=0)
        )
    else:
        raise ValueError(f"Unknown plotting type: {type}")
    return fig


def smart_round(val, decimals=4):
    """
    Round a float to the given number of decimal places. However, if the float already has less decimal, noting is done!
    :param val: The value to round.
    :param decimals: The maximum number of decimal places to round.
    :return: The rounded value.
    """
    quantizer = Decimal('1').scaleb(-decimals)
    d = Decimal(str(val)).quantize(quantizer, rounding=ROUND_HALF_UP)
    return float(d.normalize())

class Config:
    COLORS = [
        "#1f77b4",  # muted blue
        "#ff7f0e",  # vivid orange
        "#2ca02c",  # medium green
        "#d62728",  # brick red
        "#9467bd",  # muted purple
        "#8c564b",  # brownish pink
        "#e377c2",  # pink
        "#7f7f7f",  # gray
        "#bcbd22",  # lime yellow
        "#17becf",  # cyan
    ]
    HIDDEN_COLOR = "#333333"  # gray for hidden lines

    PLOTLY_THEME = dict(
        plot_bgcolor='#111111',  # dark background for the plotting area
        paper_bgcolor='#111111',  # dark background for the full figure
        font=dict(color='white'),  # white text everywhere (axes, legend, etc.)
        xaxis=dict(
            gridcolor='#333333',  # subtle dark grid lines
            zerolinecolor='#333333'
        ),
        yaxis=dict(
            gridcolor='#333333',
            zerolinecolor='#333333'
        ),
    )

    MAX_DEC = 4 # Maximum number of decimals

    @classmethod
    def FromFile(cls, path: str):
        self = cls()
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
            self._update_theme(data)
        else:
            print("NO theme found, using default theme")
        return self

    def _update_theme(self, data: dict):
        for key, value in data.items():
            if not isinstance(value, dict):
                setattr(self, key, value)
            else:
                self._merge_dict(getattr(self, key), value)

    def _merge_dict(self, d, u):
        for k, v in u.items():
            if isinstance(v, dict) and isinstance(d.get(k), dict):
                self._merge_dict(d[k], v)
            else:
                d[k] = v
        return d