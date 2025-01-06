# Antho Utils
## Description
This package is a collection of useful helpers that I regularly use in my projects. It uses a single lightweight 
dependency: PyYAML. I made a public package because I think it might be helpful to others as well. The following presents
a short description of each module.

### Color
A zero dependencies api to add color to the terminal. It supports 256 colors and 24-bit colors (True color). It is also
possible to theme the colors, so you can use consistent colors in your project. It includes a traceback formatting tool
that automatically add colors to the traceback, in order to make it easier and quicker to read. (I use this function in 
all of my projects)

### ConfigFile
A simple api to load and parse configuration files. It supports YAML files. You can verify the configuration format with
a template with a single parameter.  This can be helpful when you have a long task, such as training a neural network,
and you access some keys in the config later. You do not want your long task to crash after few hours or even days 
because you have the wrong type on a missing key in your config.

It also supports different Profiles, so the same configuration file can be used on different machines or for different
, but analogous, tasks. For example, if I want a to run my script locally for quicker developpement, but I train on a 
HPC server, I do not want to make two configurations files that are almost identical, I can simply create two profiles 
in the same configuration file with different paths or values, and use the appropriate profile depending on the machine.

### Logger
A simple implementation of a logger that is easy to use, and is highly customizable. It integrates well with the Color 
api. I usually define three loggers: log, warning and error. The log logger is used for general information. The warning
logger is used for unusual patterns that could be bugs, but won't crash the program. Finally, the error logger is used 
for non-blocking errors that should be looked into. Each logger has its own formatting rules. You can create as many 
different loggers as you like.  Once created, a logger can be used just like python's print function. Example:
```python
log = Logger(...)
log("This is a log message")
```

### Progress
This module has a similar function - and usage synthax - to tqdm. However, I believe it is more customizable than tqdm, and more suitable for
deep learning progress bar. It also implements out of the box three different types of progress bars: a tqdm-like,
a deep-learning one (keras-like) and a pip-like progress bar. It is also possible, and easy to create your own 
progress bar. Let's look at an example:
```python
# tqdm-like
for i in progress(range(100)):
    time.sleep(0.1)
# keras-like, it will report the loss value in the progress bar in real-time
for bar, batch in progress(dataloader, type="dl").ref():
    time.sleep(0.1)
    bar.repport(loss=...)
# pip-like
for i in progress(range(100), type="pip"):
    time.sleep(0.1)
```

## Installation
It is as easy to install as:
```shell
pip install antho-utils
```

## Usage
For a basic usage, you can import everything from the package:
```python
from pyutils import *
```
or, you can also import the desired tools/modules:
```python
from pyutils.color import Colors, ResetColor, TraceBackColor, ConfigFile, Logger, LoggerType, progress, prange
```
For a more detailed usage, or to see how you can configure/customize each tool, see the documentation of each module.

## Documentation
You can go take a look at the [docs](docs) folder to see the documentation of each module.