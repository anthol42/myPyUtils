# Logger
This module can help you create callbacks as drop-in replacement for print, but that can be easily customized to print 
additional information sucha as the date and time, the origin of the print, etc. It is also possible to create multiple
loggers with different formatting rules. Here is an example of the loggers that I use in my projects:
```python
from pyutils import logger, Colors, ResetColor

# Available loggers: log, warn, error

log = logger.Logger(T=logger.LoggerType.INFO, name="INFO", logColor=None)
warn = logger.Logger(T=logger.LoggerType.WARNING, name="WARNING", logColor=None)
error = logger.Logger(T=logger.LoggerType.ERROR, name="ERROR", logColor=Colors.error)

def config_loggers_with_verbose(verbose: int = 3):
    log.config(show_name=True, show_time=True, show_type=False, show_origin=False,
               name_formatter=f"<CAPS>{Colors.success}[{'{}'}]{ResetColor()}",
               time_formatter=lambda x: (f'{Colors.darken}[{x.strftime("%Y-%m-%d %H:%M:%S")}]{ResetColor()}', True),
               start_sep=" ", end_sep="   ", console=verbose >= 2)

    warn.config(show_name=True, show_time=True, show_type=False, show_origin=True,
                name_formatter=f"<CAPS>{Colors.warning}[{'{}'}]{ResetColor()}",
                time_formatter=lambda x: (f'{Colors.darken}{x.strftime("%Y-%m-%d %H:%M:%S")}{ResetColor()}', False),
                start_sep="\n\t", origin_formatter=f"{Colors.darken} |  From: {'{}'} -- line no {'{}'}{ResetColor()}",
                console=verbose >= 1)

    error.config(show_name=True, show_time=True, show_type=False, show_origin=True,
                 name_formatter=f"<CAPS>{Colors.error}[{'{}'}]{ResetColor()}",
                 time_formatter=lambda x: (f'{Colors.darken}{x.strftime("%Y-%m-%d %H:%M:%S")}{ResetColor()}', False),
                 start_sep="\n\t", origin_formatter=f"{Colors.darken} |  From: {'{}'} -- line no {'{}'}{ResetColor()}",
                 console=verbose >= 1)

config_loggers_with_verbose()
```
I put this code in a bin file, then import everything from this bin file:
```python
from bin import *
...
log("This is a log")
warn("This is a warning")
error("This is a non-fatal error")
```

I can also configure the verbosity with the ```config_loggers_with_verbose()```. Let's say I only want to see error messages,
I can call the function with the argument 1 in my main scrip:
```python
from bin import *

...
if __name__ == "__main__":
    config_loggers_with_verbose(1)
    ...
```
This will only show the error messages. If I want to see all the messages, I can call the function with the argument 3, and so on.