import time
from datetime import datetime, timedelta
from .color import BaseColor, Color, Colors, ResetColor
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

def pretty_time_format(seconds: float):
    """
    Format the seconds like: 1h 30m or 30m 20s or 20s
    :param seconds: The seconds to format
    :return: The formatted string
    """
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds // 60:.0f}m {seconds % 60:.0f}s"
    else:
        return f"{seconds // 3600:.0f}h {(seconds % 3600) // 60:.0f}m"

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
    return "  ".join([f"{k}: {v:.4f}" for k, v in self.added_values.items() if isinstance(v, float) or isinstance(v, int)])

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


# --------------------- DL progress bar CB--------------------- #
def format_time_per_step(self: 'progress'):
    """
    Format in this style: 2ms/step
    """
    color = self.done_color if self.iter_ended else Colors.green
    if color is None:
        color = Colors.green
    if self.ema == 0:
        return f"{color}NA/step{ResetColor()}"
    else:
        time_per_step = self.ema
        if time_per_step < 1e-6:
            time_per_step *= 1e9
            return f"{color}{time_per_step:.2f} ns/step{ResetColor()}"
        elif time_per_step < 1e-3:
            time_per_step *= 1e6
            return f"{color}{time_per_step:.2f} µs/step{ResetColor()}"
        elif time_per_step < 1:
            time_per_step *= 1e3
            return f"{color}{time_per_step:.2f} ms/step{ResetColor()}"
        else:
            return f"{color}{time_per_step:.2f} s/step{ResetColor()}"

def format_dl_eta(self: 'progress'):
    """
    While training, the eta is shown: 9s; when done, it shows the elapsed time: 1h 30m
    """
    if self.ema == 0:
        return f"{Colors.accent}NA{ResetColor()}"
    elapsed = (datetime.now() - self.start_time).total_seconds()
    if self.iter_ended:
        if self.done_color is not None:
            return f"{self.done_color}{pretty_time_format(elapsed)}{ResetColor()}"
        else:
            return f"{Colors.accent}{pretty_time_format(elapsed)}{ResetColor()}"
    else:
        eta = (self.total - self.count) * self.ema
        return f"{Colors.accent}{pretty_time_format(eta)}{ResetColor()}"

def format_sep(self: 'progress'):
    """
    Format a separator: ' | ' that appears only if there are added values
    """
    if len(self.added_values) == 0:
        return ""
    else:
        return " | "
class ProgressConfig:
    """
    The configuration class for the progress bar. Each config is an instance of this object.
    You should not interact directly with this class, but rather use the `progress.set_config` method.
    """
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
                 color: Optional[BaseColor] = None,
                 done_color: Optional[BaseColor] = None):
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
    """
    The progress bar class. This class can be used as a replacement to tqdm. I believe it is more flexible than tqdm, and,
    as you will see, pretty handy. The code is also short with less than 500 lines. I believe its most important feature
    is its customizability. You can almost change everything in the progress bar, so you can easily make your own
    personal progress bar.

    # Customization
    To understand how to customoze the bar, you need to understand a design choice concept. Everything except the bar itself
    is a widget. Widgets are a callback function that takes a progress object as parameter and return a string. I will
    explain more about widgets shortly. The progress bar itself can be modified with different parameters. You can specify
    which characters you want to use for the bar.

    The widgets, or callback functions are used to display information complementary to the progress bar. For example,
    the tqdm progress bar displays the percentage, the total, the eta, etc. These are widgets. You can add your own
    widgets. There are two parameters that accept widgets: `pre_cb` and `post_cb`. The `pre_cb` widgets are displayed
    before the progress bar, and the `post_cb` widgets are displayed after the progress bar. You can add as many widgets
    as you want. The widgets are called with the progress object as parameter and must return a string.

    If you would like to see example on how to customize the progress bar, take a look at the end of this file,
    two types of progress bar are implemented: `pip` and `dl`. The `pip` progress bar is a progress bar that is similar
    to the one used in pip. The `dl` progress bar is a progress bar that is more suited for deep learning tasks.

    ## More than one configuration
    You can use as many configuration as you like, without overwriting the default configuration. To do so, you can specify
    the type parameter of the `set_config` method. Then, to use the configuration you want, you can specify the type parameter
    of the progress object. For example, if you have a configuration named `dl`, you can use it like this:
    ```
    for i in progress(range(100), type="dl"):
        ... // computations
    ```
    """
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
                   color: Optional[BaseColor] = None,
                   done_color: Optional[BaseColor] = None,
                   pre_cb: Optional[Sequence[Callable[['progress'], str]]] = None,
                   post_cb: Optional[Sequence[Callable[['progress'], str]]] = None):
        """
        Set the configuration of the progress bar. Set a new type name to create a new configuration. If the type already
        exists, it will overwrite the previous configuration.
        :param type: The name of the configuration
        :param desc: The default description of the progress bar
        :param cu: The upstream character of the progress bar (left)
        :param cd: The downstream character of the progress bar (right)
        :param max_width: The maximum width of the progress bar (Number of characters). By default, if the terminal window
        is smaller than the max width, the progress bar will shrink to fit the terminal window. If you want to disable
        this behavior, you can set the `ignore_term_width` parameter to True.
        :param delim: The delimiters of the progress bar top left and top right characters
        :param done_delim: The delimiters of the done progress bar top left and top right characters, but when the progress
        bar is done. (you can have a different style or color for the done progress bar)
        :param done_charac: The character used to fill the progress bar when the progress bar is done
        :param cursors: A sequence of characters that are used to fill the progress bar. The progress bar is filled with
        the cursor that corresponds to the remainder of the progress. Using multiple characters in the sequence will make
        a smoother progress bar.
        :param refresh_rate: The refresh rate of the progress bar in seconds In other words, it is the minimum delay between
        each display update of the progress bar. If the progress bar is updated too frequently, it can slow down the program.
        :param end: The character that is added at the end of the progress bar when it is completed. By default, it is
        a newline character.
        :param enum: If set t true, it will return the index of the iteration bar. It is equivalent to do:
        for i, x in enumerate(progress(...)):

        You can also set the enum parameter by calling the enum() method. Example:
        for i, x in progress(...).enum():
        :param ref: It will return a reference to the progress bar in the for loop. Example:
        for prg, x in progress(..., ref=True):

        You can also set the ref parameter by calling the ref() method. Example:
        for prg, x in progress(...).ref():
        :param ignore_term_width: If set to true, the progress bar will not shrink to fit the terminal window. It will be
        fixed to the max width.
        :param color: The color of the progress bar. By default, the default terminal color is used.
        :param done_color: The color of the progress bar when it is done. By default, the default terminal color is used.
        :param pre_cb: The ordered list of callback functions that are called before the progress bar. The callback functions
        must take a progress object as parameter and return a string. The strings are concatenated to form the preline.
        :param post_cb: The ordered list of callback functions that are called after the progress bar. The callback functions
        must take a progress object as parameter and return a string. The strings are concatenated to form the postline.
        :return: None
        """
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
                 color: Optional[BaseColor] = None,
                 done_color: Optional[BaseColor] = None,
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
        self.smoothing_factor = 2/(1 + self.total) if self.total is not None else 2/(1+100)

        # Callbacks
        self.pre_cb = pre_cb if pre_cb is not None else config.pre_cb
        self.post_cb = post_cb if post_cb is not None else config.post_cb

        self.added_values = kwargs
        self.count = 0
        self.last_count: Optional[int] = None
        self.has_initialized = False
        self.iter_ended = False

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
            self.iter_ended = True
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
        color = self.done_color if self.iter_ended else self.color
        if color is None:
            color = ResetColor()
        post = []
        for cb in self.post_cb:
            post.append(str(color) + cb(self))

        return " ".join(post)

def prange(*args, **kwargs):
    return progress(range(*args), **kwargs)


progress.set_config(
    done_color=Colors.darken,
    type="dl",
    cursors=(f">{Colors.darken}", ),
    cu="=",
    cd="-",
    max_width=40,
    # refresh_rate=0.01,
    ignore_term_width="PYCHARM_HOSTED" in os.environ,
    delim=(f"[{Colors.orange}", f"{ResetColor()}]"),
    done_delim=(f"[{Colors.success}", f"{Colors.darken}]"),
    done_charac=f"=",
    end="",
    post_cb=(
            format_total,
            format_dl_eta,
            format_time_per_step,
            format_sep,
            format_added_values
        )
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
