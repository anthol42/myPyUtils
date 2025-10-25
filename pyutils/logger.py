import logging
import inspect
import sys
from typing import Callable
from datetime import datetime
from pyutils.color import Colors

BASE_FORMATTERS = {
    'name': lambda record: record.name,
    'level': lambda record: record.levelname,
    'time': lambda record: str(datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')),
    'origin': lambda record: f'from {record.pathname} -- line no {record.lineno}',
    'msg': lambda record: record.msg,
}

class FormatterConfig:
    def __init__(self, fmt: str, formatters: dict[str, Callable[[logging.LogRecord], str]] = BASE_FORMATTERS):
        self.fmt = fmt
        self.formatters = formatters

    def format(self, record: logging.LogRecord) -> str:
        formatted_parts = {}
        for name, cb in self.formatters.items():
            formatted_parts[name] = cb(record)
        return self.fmt.format(**formatted_parts)

class Formatter(logging.Formatter):
    def __init__(self):
        super().__init__("")
        self.debug_config = FormatterConfig(fmt=f'[{Colors.orange}{{level}}{Colors.reset} — {Colors.darken}{{time}}{Colors.reset}] {{msg}} {Colors.darken}({{name}})\n\t{{origin}}{Colors.reset}')
        self.info_config = FormatterConfig(fmt=f'{Colors.green}[{{level}}]{Colors.reset} {{msg}} [{Colors.darken}{{time}}{Colors.reset}]')
        self.warning_config = FormatterConfig(fmt=f'{Colors.warning}[{{level}}]{Colors.reset} {Colors.darken}{{time}}{Colors.reset} {{msg}}{Colors.darken} | {{name}}{Colors.reset}')
        self.error_config = FormatterConfig(fmt=f'{Colors.error}[{{level}}]{Colors.reset} {Colors.darken}{{time}}  |  {{origin}}{Colors.reset}\n\t {{msg}}')
        self.critical_config = self.error_config

    def format(self, record: logging.LogRecord):
        match record.levelno:
            case logging.DEBUG:
                return self.debug_config.format(record)
            case logging.INFO:
                return self.info_config.format(record)
            case logging.WARNING:
                return self.warning_config.format(record)
            case logging.ERROR:
                return self.error_config.format(record)
            case logging.CRITICAL:
                return self.critical_config.format(record)
            case _:
                return super().format(record)

formater = Formatter()

def _get_caller_qualname(level: int = 1):
    # Get caller's frame
    frame = inspect.currentframe()
    for _ in range(level):
        frame = frame.f_back
    code = frame.f_code
    module = inspect.getmodule(frame)
    module_name = module.__name__ if module else "<unknown>"

    # Get the function's qualified name (includes class + nested defs)
    qualname = code.co_qualname.replace(".<locals>", "")
    if qualname == "<module>":
        return module_name
    else:
        return f"{module_name}.{qualname}"

def _setup_logger(logger: logging.Logger):
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formater)
        logger.addHandler(handler)

def debug(msg: str):
    logger = logging.getLogger(_get_caller_qualname(2))
    _setup_logger(logger)
    logger.debug(msg, stacklevel=2)

def info(msg: str):
    logger = logging.getLogger(_get_caller_qualname(2))
    _setup_logger(logger)
    logger.info(msg, stacklevel=2)

def warning(msg: str):
    logger = logging.getLogger(_get_caller_qualname(2))
    _setup_logger(logger)
    logger.warning(msg, stacklevel=2)

def error(msg: str):
    logger = logging.getLogger(_get_caller_qualname(2))
    _setup_logger(logger)
    logger.error(msg, stacklevel=2)

def critical(msg: str):
    logger = logging.getLogger(_get_caller_qualname(2))
    _setup_logger(logger)
    logger.critical(msg, stacklevel=2)