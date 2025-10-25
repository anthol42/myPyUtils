# Logger
This module allow you to log messages formatted using colors and different styles, in order to make them more readable.
Here, we will explore the basic usage, with the out of the box config, then how to customize the logger formatting.
```python
from pyutils import logger

logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.critical("This is a critical message")
```

## Customize
Let's say you don't like the default formatting, you can  customize it to your liking. To do so, you can access the 
`formatter` attributes of the logger, then the desired logger level to change, and set a new config. The config is 
called `FormatterConfig, and usually takes one parameter: the format string. The format string can use multiple special 
names that will be formatted by default:
- `msg`: The message to log
- `name`: The name of the logger module.globalpath
- `level`: The level of the log message (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `time`: The time of the log message formatted as `YY-mm-dd HH:MM:SS`
- `origin`: The origin of the log message (file name and line number)

Here is an example of how to customize the debug logger to have a different format:
```python
from pyutils import logger
from pyutils.logger import FormatterConfig

logger.formater.debug_config = FormatterConfig('[{level}] {msg} -- {name}')
```

Let's say you want to add new variables that can be formatted, you can do so by passing a dictionary of callbacks as a 
second parameter. The callback must take a `logging.LogRecord` object as parameter, and return the formatted string. Here is an 
example of how to add a `thread` variable that will log the thread name:
```python
from pyutils import logger
from pyutils.logger import FormatterConfig, BASE_FORMATTERS

custom_vars = {
    "thread": lambda record: record.threadName
}
logger.formater.info_config = FormatterConfig('[{level} - {thread}] {msg} -- {name}', BASE_FORMATTERS | custom_vars)
```

Note that we pass the `BASE_FORMATTERS` to keep the default formatters (previously available variables), and add our 
custom one.


## Filtering logs
You can log only logs that have a priority over a certain threshold. By default, its set to `WARNING`, but you can 
change it to log everything with:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

In other words, since its integrated with the standard python logging module, you can use all the features of it. However,
you cannot set the `BasiceConfig` as it will result in logging everything twice.
