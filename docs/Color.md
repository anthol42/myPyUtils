# Color
Every color class in the color API is derived fromt he BaseColor class, which is an abstract class. (You cannot create 
an instance of the BaseColor class). The general usage is simple, you just have to print the color object before the 
text you want to be colored, then print a ```ResetColor()``` object after the text. Here is an example:
```python
from pyutils.color import Color, ResetColor
print(f"{Color(118)}This text is green{ResetColor()}")
```
This represent the basic usage of the color API: wrap the text between two color objects, one that defines the color, 
and one that reset it. However, there are multiple color objects that have been implemented.

You might wonder how to know that the number 118 means green. The next section will explain in more details how to work
with the different color objects.

## Color
The ```Color``` class can color text in 256 different colors. It works with terminal that support at least 256 colors.
The number passed to the class, like in the previous example, is the color code. The color code can be a number between
0 and 255. To see all the colors, and their respective codes, you can print a ```ColorPalette``` object, like so:
```python
print(ColorPalette())
```

## TrueColor
The color API also implements classes for TrueColor supporting terminals. The ```TrueColor``` class takes three
parameters: the red, green and blue values. Each value can be between 0 and 255. This class is available into two
types, the first one color text: ```RGBColor```, and the second one color the background: ```BackgroundColor```.
They work in a similar way, so let's explore the ```RGBColor``` class:
```python
from pyutils.color import RGBColor, BackgroundColor, ResetColor
red = RGBColor(255, 0, 0)
print(f"{red}This text is red{ResetColor()}")

# We can also load it from hex
red = RGBColor.FromHex("FF0000")
print(f"{red}This text is also red{ResetColor()}")

# We can also get a lighter or darker version of the color
light_red = red.lighten(0.5) # 50% lighter
dark_red = red.darken(0.5) # 50% darker

# We could write yellow on black using this synthax:
print(f"{RGBColor(255, 255, 0)}{BackgroundColor(0, 0, 0)}This text is yellow on black{ResetColor()}")
```

## Theme
If you think it is tedious to always specify the number, or the hex value, of the color you want to use, you can setup
a theme, and simply use the predefined color names. Here is an example:
```python
from pyutils.color import Colors

print(f"{Colors.green}This text is green{Colors.reset}")
```

You can also setup the theme using the ```Colors.set_theme(...)``` synthax. Every color that you specify in the method
will override the default theme. Colors that aren't specified or are set to None will use the default theme. Here is an
example that will define a Nord-like theme (Note: your terminal needs to support TrueColor to use this theme since it 
used RGBColors):
```python
    # Theme inspired by Nord Theme, made by ChatGPT (Works only in True color terminals)
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
```
## TraceBackColor
The ```TraceBackColor``` class is useful class that uses the Colors theme. If setup, it will setup a hook that will color
the traceback using the theme's colors to make it easier reading the traceback. The following shows an example on how to
set it up
```python
from pyutils.color import TraceBackColor
import sys
sys.excepthook = TraceBackColor()
```