# ConfigFile
The ConfigFile api enables you to easily parse and load configuration files. It supports YAML files. It can 
automatically verify if the given configuration file is valid by comparing it to a template. It will recursively verify 
each key, and each value datatype. You can specify how to handle the case where the config file is invalid: Raise, 
Error and quit or warn and continue. Verifying the configuration file at the beginning of the script can be helpful 
because it can prevent your long task from crashing after a few hours or even days because you have the wrong type or a
missing key in your config. In addition, this api provides statistique of usage for each key, so yu can see if some 
keys aren't used. This can help you to clean your configuration file, or identify bugs in your code, where you use a wrong key.

In addition, it supports different Profiles, so the same configuration file can be used on different machines or for
different, but analogous, tasks. For example, if you want to run your script locally for quicker development, but you
train on a HPC server, you do not want to make two configurations files that are almost identical. You can simply create
two profiles in the same configuration file with different paths or values, and use the appropriate profile depending on
the machine.

## Usage
### Basic
First, let's look at how to load a configuration file. The next code snippet shows the target configuration file:
```yaml
# config.yml
key1: value1
key2: 2
key3:
  keyA: valueA
  keyB: 42.42
key4: [
        "local/path",
        "remote/path"
]
```
Now, let's see how to load this configuration file:
```python
from pyutils import ConfigFile
config = ConfigFile("config.yml")
print(config)
print(config["key1"]) # Output: value1
```
It is as simple as that! The ConfigFile object is a dictionary-like object, so you can access the keys with the brackets.

### Verifications
However, if you want to fully use the config file tool, you can add a template format, and the class will automatically
verify the configuration file. Here is an example of a template and how to verify the configuration file with it:
```python
expected_format = {
    "key1": str,
    "key2": int,
    "key3": {
        "keyA": str,
        "keyB": float
    },
    "key4": list
}
config = ConfigFile("config.yml", config_format=expected_format)
```
Try to modify a key or a type, you will see that the class will print an error, and exit with the error code -1. You can
also specify how to handle errors with the ```error_notif``` parameter. You can choose between raise, error and quit, or
warn and continue. By default, the error and quit option is selected. You can select it from the enum ```RaiseType```.  
Example:
```python
...
from pyutils import RaiseType
...
config = ConfigFile("config.yml", config_format=expected_format, error_notif=RaiseType.WARN)
```
This will not exit the program if the configuration file is invalid, but it will print a warning and continue.

### Default values
Let's say you want a parameter in the config to be optional, you can specify a default value in the `config_format`. To
do so, import the Default class from `pyutils` and set the *type* of a key the Default object. Then, pass as the first
argument the expected type and as the second the default value. This way, this key becomes optional.

Example:
```python
from pyutils import Default
expected_format = {
    "key1": str,
    "key2": Default(int, 42),
    "key3": {
        "keyA": str,
        "keyB": float
    }
}
```

### Profiles
Finally, you can use Profiles by writing all the alternative of a key as an array, and specifying in the expected format
that this key is a profile. It is important to note that the order is important. Let's look at an example with the same 
configuration file as the previous example, but the list will be a profile:
```python
from pyutils import ConfigFile, Profile
expected_format = {
    "key1": str,
    "key2": int,
    "key3": {
        "keyA": str,
        "keyB": float
    },
    "key4": Profile(str)
}
config = ConfigFile("config.yml", config_format=expected_format, profiles=["local", "remote"])
print(config["key4"]) # Output: local/path
config.change_profile("remote")
print(config["key4"]) # Output: remote/path
```
The first print will print the configuration with the profile at index 0, because it is the default profile. However,
you can change the profile with the ```change_profile``` method. The second print will print the configuration with the
profile at index 1. You can add as many profiles as you like. The important is that the list in the configuration file
that corresponds to the profile key must have the same length as the profiles list. 

Personally, I automatically select the appropriate profile with the hostname of the machine, so once I have writen the 
few lines specifying the profiles, I never have to worry about it again. For example:
```python
import socket
def get_profile():
    hostname = socket.gethostname()
    if hostname == "local":
        return "local"
    elif hostname == "remote":
        return "remote"
    else:
        return "local" # Or any other profile name
...
config.change_profile(get_profile())
```

### Options
It is possible to make the configuration file more dynamic by having `config_format` branches. Let's say you have 
multiple program variant that each uses the same config base, but with some variant. Variant 1 might need the key ABC 
while Variant 2 might need keys ABDE. How to define the same `config_format` for both types of configurations? We can
use `Options`! Options will let you define a base `config_format` and allow multiple format for some keys. When loading 
the `config_format`, the program can choose which option to use to get the appropriate config. 

The different options must be named, and can contain any sub-config file (dict). To use options, we need to introduce
three new types: `ConfigFormat`, `Options`, `Option`. To use this functionality, you need to wrap your `config_format` 
dict by the `ConfigFormat` class. Next, you can specify the type `Options` for a key that should contain different 
options. Within this `Options` object, you can list different named options with the `Option` class. This class needs a 
single parameter - its name. Next, you can call the object with the sub_config_format associated with this option.

Finally, to use the appropriate config_format, you can call the `get` method of the `ConfigFormat` object and specify 
which option to use.

For example:
```python
from pyutils import ConfigFormat, Options, Option
config_format = ConfigFormat({
    "A": str,
    "B": int,
    "specific": Options(
        Option("Option1")({
            "C": int
        }),
        Option("Option2")({
            "D": int,
            "E": str
        })
    )
})

config_format1 = config_format.get(option="Option1")
config_format2 = config_format.get(option="Option2")
```
### Get statistics
As said before, this class comes with a statistics tool that counts the number of access to each key. It can help you 
see unused keys. To see this, you can simply print the statistics:
```python
...
print(config.stats())
```
If you have some keys that were not used, you will see a message like: ```WARNING: You have 4 unused variables in your 
config file. Consider removing them: <...>```. The keys listed will be the keys that were not accessed. If you want to 
automatically print this message if there are keys that were not accessed, and print nothing otherwise, you can easily
do it: 
```python
...
from pyutils import Colors, ResetColor
...
if config.have_warnings():
    print(f"{Colors.warning}{config.get_warnings()}{ResetColor()}")
```
This will print the message in the warning color only if there are warnings - keys that are unused.