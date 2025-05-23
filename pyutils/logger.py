from .color import BaseColor, ResetColor
from enum import Enum
from typing import *
import sys
import inspect
from datetime import datetime

# Static var counting the number of loggers
NUM_LOGGERS = 0
class LoggerType(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"    # Non fatal error


class LogKwargs:
    def __init__(self, sep: str = ' ', start: str = '',
                 end: str = '\n', file=sys.stdout, flush=False, color: Optional[BaseColor] = None):
        self.sep = sep
        self.end = end
        self.start = start
        self.file = file
        self.flush = flush
        self.color = color

    def get(self):
        return {"sep": self.sep, "end": self.end, "file": self.file, "flush": self.flush}

def get_frames():
    current_frame = inspect.currentframe()
    frames = [current_frame]
    while current_frame.f_back is not None:
        current_frame = current_frame.f_back
        frames.append(current_frame)

    return frames
class LogConfig:
    def __init__(self, **kwargs):
        self.init(**kwargs)

    def init(self, console: bool = True, show_name: bool = True, show_type: bool = True, show_time: bool = True,
                 show_origin: bool = True,
                 name_formatter: str = "<CAPS>{}", type_formatter: str = "<CAPS>[{}]",
                 time_formatter: Callable[[datetime], Tuple[str, bool]] = lambda x: (f'[{x}]', False),
                 origin_formatter: str = "<END>From: {} -- line no {}",
                 start_sep: str = " -- ", end_sep: str = " | "):
        self.console = console
        self.show_name = show_name
        self.show_type = show_type
        self.show_time = show_time
        self.show_origin = show_origin
        self.name_formatter = name_formatter
        self.type_formatter = type_formatter
        self.time_formatter = time_formatter
        self.origin_formatter = origin_formatter
        self.start_sep = start_sep
        self.end_sep = end_sep

    @staticmethod
    def get_modifiers(s: str):
        mods = {
            "caps": False,
            "end": False
        }
        if "<CAPS>" in s:
            mods["caps"] = True
        if "<END>" in s:
            mods["end"] = True
        return mods
    @staticmethod
    def clear_modifiers(s: str):
        return s.replace("<CAPS>", "").replace("<END>", "")
    @staticmethod
    def apply_mods(s, mods):
        s = s.upper() if mods["caps"] else s
        return s

    def format_string(self, s, formatter) -> Tuple[str, bool]:
        """
        Format the name attribute
        Returns: The formated name, boolean representing whether it should be appended (END)
        """
        mods = self.get_modifiers(formatter)
        formatter = self.clear_modifiers(formatter)
        s = self.apply_mods(s, mods)
        return formatter.format(s), mods["end"]

    def format_time(self, time: datetime) -> Tuple[str, bool]:
        """
        Format the time attribute
        Returns: The formated time, boolean representing whether it should be appended (END)
        """
        return self.time_formatter(time)
    def format_origin(self) -> Tuple[str, bool]:
        # Get the frames
        frames = get_frames()
        caller_frame = frames[4] # Number is the level
        filename = caller_frame.f_code.co_filename
        line_number = caller_frame.f_lineno

        # Format the string
        formatter = self.origin_formatter
        mods = self.get_modifiers(formatter)
        formatter = self.clear_modifiers(formatter)
        file = self.apply_mods(filename, mods)
        line = self.apply_mods(str(line_number), mods)
        s = formatter.format(file, line)
        return s, mods["end"]

class FatalFailure(Exception):
    pass
class Logger:
    """
    Class to create a callback function that has a similar interface to the print function. However, you can customize
    how it prints the data. You can also log to a file if needed, where all the logs are stored.
    """
    def __init__(self, T: LoggerType, logfile: Optional[str] = None, name: Optional[str] = None,
                 logColor: Optional[BaseColor] = None):
        """
        Initialize the logger
        :param T: The type of the logger
        :param logfile: The file to log to, if None, it will not log to a file
        :param name: The name of the logger. If None, it will be Logger_{NUM_LOGGERS}
        :param logColor: The color to log the text, by default.
        """
        global NUM_LOGGERS
        self.T = T
        self.logfile = logfile
        self.console_file = sys.stdout
        if name is None:
            name = f"Logger_{NUM_LOGGERS}"
        self.name = name
        self.logColor = logColor
        self.CONFIG = LogConfig()

        NUM_LOGGERS += 1

    def config(self, show_name: bool = True, show_type: bool = True, show_time: bool = True, show_origin: bool = False,
               name_formatter: str = "<CAPS>{}", type_formatter: str = "<CAPS>[{}]",
               time_formatter: Callable[[datetime], Tuple[str, bool]] = lambda x: (f'[{x}]', False),
               origin_formatter: str = "<END>From: {} -- line no {}",
               start_sep: str = " -- ", end_sep: str = " | ", console: bool = True):
        """
        Configure the logger.
        # Formatters
        You can specify formatters for the name, type, time, and origin of the logger. The formatters are strings
        that can contains special keywords that will define how the string is formatted. The special keywords are:
        - <CAPS>: Capitalize the string
        - <END>: Append the string to the end of the log
        :param show_name: Show the name of the logger
        :param show_type: Show the type of the logger
        :param show_time: Show the time of the log
        :param show_origin: Show the origin of the log: The file and the line number
        :param name_formatter: The format of the name of the logger
        :param type_formatter: The format of the type of the logger
        :param time_formatter: The format of the time of the logger
        :param origin_formatter: The format of the origin of the logger
        :param start_sep: The separator between the generic info such as the name, the date, etc, and the start of the log
        :param end_sep: The separator between the log and the generic info that are appended.
        :param console: Whether to print to the console or not.
        :return: None
        """
        self.CONFIG.init(console, show_name, show_type, show_time, show_origin, name_formatter, type_formatter, time_formatter,
                        origin_formatter, start_sep, end_sep)
    def decorate(self, s: str):
        inserts, appends = [], []
        if self.CONFIG.show_name:
            name, end = self.CONFIG.format_string(self.name, self.CONFIG.name_formatter)
            if end:
                appends.append(name)
            else:
                inserts.append(name)
        if self.CONFIG.show_type:
            type, end = self.CONFIG.format_string(self.T.value, self.CONFIG.type_formatter)
            if end:
                appends.append(type)
            else:
                inserts.append(type)
        if self.CONFIG.show_time:
            time, end = self.CONFIG.format_time(datetime.now())
            if end:
                appends.append(time)
            else:
                inserts.append(time)
        if self.CONFIG.show_origin:
            origin, end = self.CONFIG.format_origin()
            if end:
                appends.append(origin)
            else:
                inserts.append(origin)

        s = " ".join(inserts) + self.CONFIG.start_sep + s
        if len(appends) > 0:
            s = s + self.CONFIG.end_sep + " ".join(appends)
        return s

    def __call__(self, *args, **kwargs):
        """
        Same signature as the print function.
        Will print the log to the console and to the file if needed, according to the configuration format.
        """
        kwargs = LogKwargs(**kwargs)

        # Format the string
        original_string = kwargs.start + kwargs.sep.join([str(arg) for arg in args])
        # Color the string if needed
        if self.logColor is not None:
            colored_string = f"{self.logColor}{original_string}{ResetColor()}"
        else:
            colored_string = original_string

        s_colored = self.decorate(colored_string) + kwargs.end
        s = self.decorate(original_string) + kwargs.end

        # Log to console if needed
        if self.CONFIG.console:
            if self.T == LoggerType.ERROR:
                print(s_colored, sep="", end="", flush=kwargs.flush, file=sys.stderr)
            else:
                print(s_colored, sep="", end="", flush=kwargs.flush)

        if self.logfile is not None:
            with open(self.logfile, "a") as f:
                f.write(s)