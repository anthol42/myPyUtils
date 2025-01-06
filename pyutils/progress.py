import time
from datetime import datetime, timedelta
from .color import Color, ResetColor
import math
from typing import *
import shutil
from copy import deepcopy
import os

# --------------------- Default/tqdm progress bar CB--------------------- #
def format_seconds_to_hms(seconds):
    seconds = round(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours == 0:
        return f"{minutes:02}:{seconds:02}"
    else:
        return f"{hours:02}:{minutes:02}:{seconds:02}"

def format_percent(self: 'progress'):
    return f"{(self.count / self.total) * 100:.0f}%"

def format_desc(self: 'progress'):
    return f"{self.desc}:" if self.desc is not None and self.desc != "" else ""


def format_total(self: 'progress'):
    return f"{self.count}/{self.total}"

def format_eta(self: 'progress'):
    if self.ema == 0:
        return "[00:00<00:00, 0.00it/s]"
    elapsed = (datetime.now() - self.start_time).total_seconds()
    eta = (self.total - self.count) * self.ema
    it_per_sec = 1 / self.ema
    if it_per_sec < 1:
        return f"[{format_seconds_to_hms(elapsed)}<{format_seconds_to_hms(eta)}, {self.ema:.2f}s/it]"
    else:
        return f"[{format_seconds_to_hms(elapsed)}<{format_seconds_to_hms(eta)}, {it_per_sec:.2f}it/s]"

def format_added_values(self: 'progress'):
    return " ".join([f"{k}: {v:.3f}" for k, v in self.added_values.items() if isinstance(v, float) or isinstance(v, int)])

# --------------------- Pip progress bar CB--------------------- #

def format_pip_total(self: 'progress'):
    unit = self.added_values.get("unit", "it")
    if isinstance(self.total, int):
        return f"{Color(2)}{self.count}/{self.total} {unit}{ResetColor()}"
    else:
        return f"{Color(2)}{self.count:.2f}/{self.total:.2f} {unit}{ResetColor()}"

def format_speed(self: 'progress'):
    if self.ema == 0:
        return ""
    it_per_sec = 1 / self.ema
    unit = self.added_values.get("unit", "it")
    return f"{Color(1)}{it_per_sec:.2f} {unit}/s{ResetColor()}"

def format_pip_eta(self: 'progress'):
    if self.ema == 0:
        return "[00:00<00:00, 0.00it/s]"
    eta = (self.total - self.count) * self.ema
    return f"eta {Color(6)}{format_seconds_to_hms(eta)}{ResetColor()}"


class ProgressConfig:
    def __init__(self, desc: str = "", type: str = "default",
                 cu: str = "█", cd: str = " ", max_width: int = 50,
                 delim: Tuple[str, str] = ("|", "|"),
                 done_delim: Tuple[str, str] = ("|", "|"),
                 done_charac: str = "█",
                 cursors: Tuple[str] = (" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉"),
                 refresh_rate: float = 0.25,
                 end: str = "\n",
                 enum: bool = False,
                 ref: bool = False,
                 ignore_term_width: bool = False,
                 pre_cb: Sequence[Callable[['progress'], str]] = (
                         format_desc,
                         format_percent,
                 ),
                 post_cb: Sequence[Callable[['progress'], str]] = (
                         format_total,
                         format_eta,
                         format_added_values
                 ),
                 color: Optional[Color] = None,
                 done_color: Optional[Color] = None):
        self.desc = desc
        self.name = type
        self.cu = cu
        self.cd = cd
        self.max_width = max_width
        self.delim = delim
        self.done_delim = done_delim
        self.done_charac = done_charac
        self.cursors = cursors
        self.refresh_rate = refresh_rate
        self.end = end
        self.enum = enum
        self.ref = ref
        self.ignore_term_width = ignore_term_width
        self.pre_cb = pre_cb
        self.post_cb = post_cb
        self.color = color
        self.done_color = done_color




class progress:
    CONFIGS = {
        "default": ProgressConfig()
    }

    @classmethod
    def set_config(cls, type: str = "default",
                   desc: Optional[str] = None,
                   cu: Optional[str] = None,
                   cd: Optional[str] = None,
                   max_width: Optional[int] = None,
                   delim: Optional[Tuple[str, str]] = None,
                   done_delim: Optional[Tuple[str, str]] = None,
                   done_charac: Optional[str] = None,
                   cursors: Optional[Tuple[str]] = None,
                   refresh_rate: Optional[float] = None,
                   end: Optional[str] = None,
                   enum: Optional[bool] = None,
                   ref: Optional[bool] = None,
                   ignore_term_width: Optional[bool] = None,
                   color: Optional[Color] = None,
                   done_color: Optional[Color] = None,
                   pre_cb: Optional[Sequence[Callable[['progress'], str]]] = None,
                   post_cb: Optional[Sequence[Callable[['progress'], str]]] = None):
        def_cfg = deepcopy(cls.CONFIGS["default"])
        cls.CONFIGS[type] = ProgressConfig(
            desc=desc if desc is not None else def_cfg.desc,
            type=type,
            cu=cu if cu is not None else def_cfg.cu,
            cd=cd if cd is not None else def_cfg.cd,
            max_width=max_width if max_width is not None else def_cfg.max_width,
            delim=delim if delim is not None else def_cfg.delim,
            done_delim=done_delim if done_delim is not None else def_cfg.done_delim,
            done_charac=done_charac if done_charac is not None else def_cfg.done_charac,
            cursors=cursors if cursors is not None else def_cfg.cursors,
            refresh_rate=refresh_rate if refresh_rate is not None else def_cfg.refresh_rate,
            end=end if end is not None else def_cfg.end,
            enum=enum if enum is not None else def_cfg.enum,
            ref=ref if ref is not None else def_cfg.ref,
            ignore_term_width=ignore_term_width if ignore_term_width is not None else def_cfg.ignore_term_width,
            pre_cb=pre_cb if pre_cb is not None else def_cfg.pre_cb,
            post_cb=post_cb if post_cb is not None else def_cfg.post_cb,
            color=color if color is not None else def_cfg.color,
            done_color=done_color if done_color is not None else def_cfg.done_color
        )

    def __init__(self, it: Optional[Iterable] = None, *,
                 type: str = "default",
                 desc: Optional[str] = None,
                 total: Optional[int] = None,
                 cu: Optional[str] = None,
                 cd: Optional[str] = None,
                 max_width: Optional[int] = None,
                 delim: Optional[Tuple[str, str]] = None,
                 done_delim: Optional[Tuple[str, str]] = None,
                 done_charac: Optional[str] = None,
                 cursors: Optional[Tuple[str]] = None,
                 refresh_rate: Optional[float] = None,
                 end: Optional[str] = None,
                 enum: Optional[bool] = None,
                 ref: Optional[bool] = None,
                 ignore_term_width: Optional[bool] = None,
                 color: Optional[Color] = None,
                 done_color: Optional[Color] = None,
                 pre_cb: Optional[Sequence[Callable[['progress'], str]]] = None,
                 post_cb: Optional[Sequence[Callable[['progress'], str]]] = None,
                **kwargs):
        # Get the config
        if type not in self.CONFIGS:
            raise ValueError(f"Type {type} was not setup, hence doesn't exist.")
        config: ProgressConfig = self.CONFIGS[type]
        self.it = iter(it) if it is not None else None
        self.desc = desc if desc is not None else config.desc
        self.cu = cu if cu is not None else config.cu
        self.cd = cd if cd is not None else config.cd
        self.max_c = max_width if max_width is not None else config.max_width
        self.delim = delim if delim is not None else config.delim
        self.done_delim = done_delim if done_delim is not None else config.done_delim
        self.done_charac = done_charac if done_charac is not None else config.done_charac
        self.cursors = cursors if cursors is not None else config.cursors
        self.refresh_rate = refresh_rate if refresh_rate is not None else config.refresh_rate
        self.end = end if end is not None else config.end
        self._enum = enum if enum is not None else config.enum
        self._ref = ref if ref is not None else config.ref
        self.ignore_term_width = ignore_term_width if ignore_term_width is not None else config.ignore_term_width
        self.color = color if color is not None else config.color
        self.done_color = done_color if done_color is not None else config.done_color

        if total is None:
            try:
                self.total = len(it)
            except TypeError:
                self.total = None
        else:
            self.total = total

        # For timing
        self.start_time: Optional[datetime] = None
        self.prev_step: Optional[datetime] = None
        self.last_display: Optional[datetime] = None
        self.ema = 0
        self.smoothing_factor = 2/(1 + self.total / 10) if self.total is not None else 2/(1+100)

        # Callbacks
        self.pre_cb = pre_cb if pre_cb is not None else config.pre_cb
        self.post_cb = post_cb if post_cb is not None else config.post_cb

        self.added_values = kwargs
        self.count = 0
        self.last_count: Optional[int] = None
        self.has_initialized = False

    def __iter__(self):
        return self

    def __next__(self):
        try:
            # Loading next element
            ne = next(self.it)
            self.last_count = self.count
            self.count += 1

            # Measure the duration of each steps
            self.prep_step_duration()

            # Early return because we do not want to display the progress bar yet (If true)
            if (datetime.now() - self.last_display).total_seconds() < self.refresh_rate:
                return self.return_fn(ne)

            # Display progress bar
            self.display_loading_bar()
            return self.return_fn(ne)

        except StopIteration:
            # Display done bar
            self.display_done_bar()
            raise StopIteration

    def prep_step_duration(self):
        # Mean step duration (EMA)
        if not self.has_initialized:  # First step: INIT
            self.start_time = datetime.now()
            self.prev_step = datetime.now()
            # Epoch
            self.last_display = datetime.now() - timedelta(seconds=self.refresh_rate + 1)
            self.has_initialized = True
        else:
            # Get step duration
            elapsed_steps = self.count - self.last_count
            step_duration = (datetime.now() - self.prev_step).total_seconds() / elapsed_steps
            if self.ema == 0:  # Second step: INIT EMA
                self.ema = step_duration
            else:
                self.ema = self.smoothing_factor * step_duration + (1 - self.smoothing_factor) * self.ema
            self.prev_step = datetime.now()

    def display_loading_bar(self):
        preline = self.make_preline()
        postline = self.make_postline()
        line_width = self.get_term_width() - len(preline) - len(postline) - 5
        if line_width < 0:
            line_width = 0
        if line_width > self.max_c:
            line_width = self.max_c

        cursor_pos = int(((self.count) / self.total) * line_width)
        cursor_progress = (self.count / self.total) * line_width - cursor_pos
        cursor = self.cursors[math.floor(cursor_progress * len(self.cursors))]
        if self.count == self.total:
            cursor = self.cu

        self.last_display = datetime.now()
        line = f"{self.delim[0]}{self.cu * cursor_pos}{cursor}{self.cd * (line_width - cursor_pos)}{self.delim[1]}  {ResetColor()}"
        if self.color is not None:
            print(f"\r{self.color}" + preline + line + f"{self.color}" + postline, end=f"{ResetColor()}")
        else:
            print("\r" + preline + line + postline, end="")

    def display_done_bar(self):
        preline = self.make_preline()
        postline = self.make_postline()
        line_width = self.get_term_width() - len(preline) - len(postline) - 5
        if line_width < 0:
            line_width = 0
        if line_width > self.max_c:
            line_width = self.max_c
        line = f"{self.done_delim[0]}{self.done_charac * line_width}{self.done_charac}{self.done_delim[1]}  {ResetColor()}"
        if self.done_color is not None:
            print(f"\r{self.done_color}" + preline + line + f"{self.done_color}" + postline, end=f"{ResetColor()}{self.end}")
        else:
            print("\r" + preline + line + postline, end=self.end)

    def update(self, current: int, **kwargs):
        self.last_count = self.count
        self.count = current
        self.report(**kwargs)

        # Measure the duration of each steps
        self.prep_step_duration()

        # Display progress bar
        if self.count >= self.total:
            self.display_done_bar()
        else:
            self.display_loading_bar()

    def return_fn(self, ne):
        if self._enum and self._ref:
            return self.count - 1, self, ne
        elif self._enum:
            return self.count - 1, ne
        elif self._ref:
            return self, ne
        else:
            return ne

    def ref(self):
        self._ref = True
        return self

    def enum(self):
        self._enum = True
        return self

    def report(self, **kwargs):
        self.added_values.update(kwargs)

    def get_term_width(self):
        if self.ignore_term_width:
            return 1000
        else:
            return shutil.get_terminal_size().columns

    def make_preline(self):
        pre = []
        for cb in self.pre_cb:
            pre.append(cb(self))

        return " ".join(pre)

    def make_postline(self):
        post = []
        for cb in self.post_cb:
            post.append(cb(self))

        return " ".join(post)

def prange(*args, **kwargs):
    return progress(range(*args), **kwargs)


progress.set_config(
    done_color=Color(247),
    type="dl",
    cursors=(f">{Color(240)}", ),
    cu="=",
    cd="-",
    max_width=40,
    # refresh_rate=0.01,
    ignore_term_width="PYCHARM_HOSTED" in os.environ,
    delim=(f"[{Color(208)}", f"{ResetColor()}]"),
    done_delim=(f"[{Color(40)}", f"{Color(247)}]"),
    done_charac=f"=",
    end=""
)
progress.set_config(
    done_color=Color(247),
    type="pip",
    cursors=(f"{Color(8)}╺", f"╸{Color(8)}"),
    cu="━",
    cd="━",
    max_width=40,
    # refresh_rate=0.01,
    ignore_term_width="PYCHARM_HOSTED" in os.environ,
    delim=(f"   {Color(197)}", f"{ResetColor()}"),
    done_delim=(f"   {Color(10)}", f"{ResetColor()}"),
    done_charac=f"━",
    pre_cb=(
        format_desc,
    ),
    post_cb=(
        format_pip_total,
        format_speed,
        format_pip_eta
    )
)

if __name__ == "__main__":
    # a = [i for i in range(100)]
    print("Loading")
    for prg, a in prange(500, type="pip").ref():
        time.sleep(0.05)
        prg.report(value=a/100, test=-a)

    print("Epoch 2")
    for prg, a in prange(500, type="dl").ref():
        time.sleep(0.05)
        prg.report(value=a/100, test=-a)
