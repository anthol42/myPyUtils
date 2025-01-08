# Progress
The progress module is a simple implementation of a progress bar. It is highly customizable and can be used in a variety 
of ways. It is also possible to create your own progress bar. The module implements three different types of progress 
bars out of the box: a tqdm-like, a deep-learning one (inspired by keras progress bar) and a pip-like progress bar.

There are two main ways to use the progress module: **for** loops and **while** loops. 

## For loops
In for loops, you can use the progress bar as a quasi drop-in replacement for the tqdm decorator. Example:
```python
from pyutils import progress

for element in progress(range(100)):
    time.sleep(0.1)
```
To simplify this expression, you can use the prange function, which is similar to the trange function from tqdm:
```python
from pyutils import prange

for element in prange(100):
    time.sleep(0.1)
```

You can see the element index, without using the enumerate function by calling the ```enum()``` method:
```python
...
for i, element in progress(range(100)).enum():
    ...
```

If you want to report values that will be displayed in the progress bar, you can use the ```repport()``` method and get
a handle using the ```ref()``` method. Example:
```python
for bar, element in progress(range(100)).ref():
    time.sleep(0.1)
    bar.repport(loss=...)
```

You can specify the type of progress bar you want to use by passing the ```type``` argument. The default is the tqdm-like
progress bar. The other options are ```dl``` for the deep-learning progress bar and ```pip``` for the pip-like progress bar.
You can also define any other progress bar type that yu have defined. See the customizing section for more information.
Any parameter written in the configuration is a default parameter that can be overwritten by the user using the various 
parameters of the progress bar. See the docstring comments for more information.

## While loops
You can also use the progress bar in while loops. Example:
```python
from pyutils import progress
import time

i = 0
pbar = progress(total=100)
while i < 100:
    time.sleep(0.1)
    pbar.update(i)
    i += 1
```

Any key-word arguments you will pass to the update method will be displayed in the progress bar.As if you were using the 
```repport()``` method in for loops.

## Customizing
To understand how to customize the bar, you need to understand a design choice concept. Everything except the bar itself
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

### More than one configuration
You can use as many configuration as you like, without overwriting the default configuration. To do so, you can specify
the type parameter of the `set_config` method. Then, to use the configuration you want, you can specify the type parameter
of the progress object. For example, if you have a configuration named `dl`, you can use it like this:

```python
for i in progress(range(100), type="dl"):
    ... # computations
```

For examples on how to define you own progress bar tailored to your needs, see the end of the progress.py file, where 
the `pip` and `dl` progress bars are defined.

Example of a configuration for the pip progress bar:
```python
from pyutils import progress, Color, ResetColor

... # Callback definition (widgets)
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
```

## Examples
**Default, tqdm-like**:
```
4%|██                                                 |  403/10000 [00:05<01:41, 94.59it/s] metricA: -1.5266  metricB: -1.9381
```
Usually, the ```dl``` and ```pip``` progress bar have colors, but you can't see color in a simple markdown. Here is an
example of a progress bar using the `dl` type:

**dl**:
```
14%[=====>-----------------------------------]  1450/10000 1m 44s 12.18 ms/step  |  metricA: 1.8836  metricB: -1.0085
```
**pip**:
```
━━╸━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  659/10000 it 89.92 it/s eta 01:44
```