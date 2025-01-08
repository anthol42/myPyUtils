# Documentation
This directory contains the documentation for each module of the package.

## Configuration
Most module are customizable, so you can configure them. For big projects, I recommend creating a setup.py file where 
the configuration code will be written, then importing it into your entry file. If you do not understand the following 
code, you can read the documentation of each packages, I hope it will make it clearer.
Example:
- setup.py
```python
# The following file doesn't execute any task, except configuring the tools.
from pyutils import Colors, RGBColor, TraceBackColor
import sys

# Configure the theme
Colors.set_theme(
    accent=RGBColor(143, 188, 187),  # Frost - Teal
    text=RGBColor(216, 222, 233),  # Snow Storm - Main text
    error=RGBColor(220, 70, 80),  # Flashy Error - Bright Crimson
    warning=RGBColor(255, 170, 50),  # Flashy Warning - Golden Orange
    success=RGBColor(100, 220, 120),  # Flashy Success - Emerald Green
    link=RGBColor(136, 192, 208),  # Frost - Light Blue
    white=RGBColor(236, 239, 244),  # Snow Storm - Bright text
    black=RGBColor(46, 52, 64),  # Polar Night - Dark background
    red=RGBColor(191, 97, 106),  # Aurora - Red
    blue=RGBColor(94, 129, 172),  # Frost - Dark Blue
    green=RGBColor(163, 190, 140),  # Aurora - Green
    yellow=RGBColor(235, 203, 139),  # Aurora - Yellow
    cyan=RGBColor(143, 188, 187),  # Frost - Teal
    magenta=RGBColor(180, 142, 173),  # Aurora - Purple
    brown=RGBColor(121, 85, 72),  # Invented Brown
    orange=RGBColor(208, 135, 112),  # Aurora - Orange
    purple=RGBColor(180, 142, 173),  # Aurora - Purple
    pink=RGBColor(216, 155, 176)  # Invented Pink
)
# Configure the traceback formatting tool
sys.excepthook = TraceBackColor()
```
- main.py
```python
# Importing the setup file will execute the configuration code
import setup
import ...
...
if __name__ == "__main__":
    ...
```

## packages
- [Color](Color.md)
- [ConfigFile](ConfigFile.md)
- [Logger](Logger.md)
- [Progress](Progress.md)

## Questions?
If you have any questions, or you find bugs, feel free to ask them in the issues section of the repository. I will be 
happy to help you.
