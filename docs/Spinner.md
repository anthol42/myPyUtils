# Spinner
While the progress module is useful to show progress, sometimes we encounter a long running function, but we don't 
know its progress. In this case, a spinner can be used to show that the program is still running. The spinner module 
implements a simple spinner that can be used in a variety of ways. Its api is simple:

```python
from pyutils import Spinner

with Spinner("Processing long running task..."):
    long_running_function()
```

Multiple themes are available out of the box, and you can create your own themes, by passing a list of characters.

```python
from pyutils import Spinner

# Moon theme with emojis
with Spinner("Processing long running task...", chars='moon'):
    long_running_function()

# Custom theme that counts up to 9, then restarts
with Spinner("Processing long running task...", chars=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):
    long_running_function()
```