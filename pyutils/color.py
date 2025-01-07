import sys
import traceback
import re
from typing import *

class BaseColor:
    """
    Abstract class
    """
    def __str__(self):
        return self.value

class Color(BaseColor):
    """
    Use this class to color text.  Just write the color id of your choice.  You can use the ColorPalette class to see
    available colors with their id (number).  Then, place the Color object initialized with its color id at the
    begining of the string needed to be colored, and add the ResetColor object initialized without parameters at the end
    to avoid coloring all the text.

    Example:
        >>>print(f"{Color(154)}I am colored :) {ResetColor()} And I am not colored :(")
    """
    def __init__(self, i):
        self.value = f"\033[38;5;{i}m"

class ColorTheme:
    def __init__(self,
                 accent: Optional[BaseColor] = Color(12),
                 text: Optional[BaseColor] = Color(250),
                 error: Optional[BaseColor] = Color(203),
                 warning: Optional[BaseColor] = Color(208),
                 success: Optional[BaseColor] = Color(40),
                 link: Optional[BaseColor] = Color(39),
                 white: Optional[BaseColor] = Color(15),
                 black: Optional[BaseColor] = Color(0),
                 red: Optional[BaseColor] = Color(196),
                 blue: Optional[BaseColor] = Color(33),
                 green: Optional[BaseColor] = Color(40),
                 yellow: Optional[BaseColor] = Color(220),
                 cyan: Optional[BaseColor] = Color(51),
                 magenta: Optional[BaseColor] = Color(201),
                 brown: Optional[BaseColor] = Color(130),
                 orange: Optional[BaseColor] = Color(202),
                 purple: Optional[BaseColor] = Color(129),
                 pink: Optional[BaseColor] = Color(13),
                 darken: Optional[BaseColor] = Color(240),
                ):
        self.accent = accent
        self.text = text
        self.error = error
        self.warning = warning
        self.success = success
        self.link = link
        self.white = white
        self.black = black
        self.red = red
        self.blue = blue
        self.green = green
        self.yellow = yellow
        self.cyan = cyan
        self.magenta = magenta
        self.brown = brown
        self.orange = orange
        self.purple = purple
        self.pink = pink
        self.darken = darken

    def set_theme(self, accent: Optional[BaseColor] = None,
                  text: Optional[BaseColor] = None,
                  error: Optional[BaseColor] = None,
                  warning: Optional[BaseColor] = None,
                  success: Optional[BaseColor] = None,
                  link: Optional[BaseColor] = None,
                  white: Optional[BaseColor] = None,
                  black: Optional[BaseColor] = None,
                  red: Optional[BaseColor] = None,
                  blue: Optional[BaseColor] = None,
                  green: Optional[BaseColor] = None,
                  yellow: Optional[BaseColor] = None,
                  cyan: Optional[BaseColor] = None,
                  magenta: Optional[BaseColor] = None,
                  brown: Optional[BaseColor] = None,
                  orange: Optional[BaseColor] = None,
                  purple: Optional[BaseColor] = None,
                  pink: Optional[BaseColor] = None,
                  darken: Optional[BaseColor] = None,
                  **kwargs):
        """
        Set the color theme
        """
        self.accent = accent or self.accent
        self.text = text or self.text
        self.error = error or self.error
        self.warning = warning or self.warning
        self.success = success or self.success
        self.link = link or self.link
        self.white = white or self.white
        self.black = black or self.black
        self.red = red or self.red
        self.blue = blue or self.blue
        self.green = green or self.green
        self.yellow = yellow or self.yellow
        self.cyan = cyan or self.cyan
        self.magenta = magenta or self.magenta
        self.brown = brown or self.brown
        self.orange = orange or self.orange
        self.purple = purple or self.purple
        self.pink = pink or self.pink
        self.darken = darken or self.darken

        for new_color in kwargs:
            self.register_color(new_color, kwargs[new_color])

    def register_color(self, name: str, color: BaseColor):
        """
        Register a new color
        """
        setattr(self, name, color)

    def __str__(self):
        s = ""
        for attr in dir(self):
            if not attr.startswith("__") and not callable(getattr(self, attr)):
                s += f"{attr}: {getattr(self, attr)}AaBbCc{ResetColor()}\n"
        return s


class ResetColor(BaseColor):

    def __init__(self):
        self.value = "\033[0m"


class RGBColor(BaseColor):
    """
    This class is a subclass of Color, but using rgb colors.  Just pass the red value, green value and blue value
    to the constructor.  Values must be between 0 and 255
    """
    def __init__(self, r, g, b):
        """
        :param r: Red [0-255]
        :param g: Green [0-255]
        :param b: Blue [0-255]
        """
        self.rgb = (r, g, b)

    @property
    def value(self):
        r, g, b = self.rgb
        return f"\033[38;2;{r};{g};{b}m"

    @classmethod
    def FromHex(cls, html_color: str):
        """
        Convert a hex color to RGB
        :param html_color: The hex color
        :return: The RGB color
        """
        return cls(*(int(html_color[i:i+2], 16) for i in (0, 2, 4)))

    @property
    def hex(self):
        """
        Get the hex value of the color
        :return: hex value
        """
        return f"#{''.join([hex(c)[2:].zfill(2).upper() for c in self.rgb])}"

    def lighten(self, ratio: float):
        """
        credit to: Mark Ransom from stackoverflow https://stackoverflow.com/questions/141855/programmatically-lighten-a-color
        :param ratio: The ratio to lighten the color. 1 = white and 0 = same color
        :return: The new color
        """
        if ratio < 0 or ratio > 1:
            raise ValueError("factor must be between 0 and 1")
        cls = self.__class__
        r, g, b = self.rgb
        threshold = 255.999
        max_val = 3 * threshold  # ~768
        current = r + g + b
        if current == 0:
            r, g, b = 1, 1, 1
            current = 3
        factor = (ratio * ((max_val / current) - 1)) + 1
        # print(factor)
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        m = max(r, g, b)
        if m <= threshold:
            return cls(int(r), int(g), int(b))
        total = r + g + b
        if total >= 3 * threshold:
            return cls(int(threshold), int(threshold), int(threshold))
        x = (3 * threshold - total) / (3 * m - total)
        gray = threshold - x * m
        return cls(int(gray + x * r), int(gray + x * g), int(gray + x * b))

    def darken(self, ratio: float):
        """
        credit to: Mark Ransom from stackoverflow https://stackoverflow.com/questions/141855/programmatically-lighten-a-color
        :param ratio: The ratio to darken the color. 1 = black and 0 = same color
        :return: The new color
        """
        if ratio < 0 or ratio > 1:
            raise ValueError("factor must be between 0 and 1")
        cls = self.__class__
        r, g, b = self.rgb
        threshold = 255.999
        factor = -ratio + 1
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        m = max(r, g, b)
        if m <= threshold:
            return cls(int(r), int(g), int(b))
        total = r + g + b
        if total >= 3 * threshold:
            return cls(int(threshold), int(threshold), int(threshold))
        x = (3 * threshold - total) / (3 * m - total)
        gray = threshold - x * m
        return cls(int(gray + x * r), int(gray + x * g), int(gray + x * b))

class BackgroundColor(RGBColor):
    """
    This class is a subclass of RGBColor.  Just pass the red value, green value and blue value
    to the constructor.  Values must be between 0 and 255. It will set the background color of the text.
    """

    @property
    def value(self):
        r, g, b = self.rgb
        return f"\033[48;2;{r};{g};{b}m"


Colors = ColorTheme()

class ColorPalette:
    """
    Show the color available with their id.  To use it, it is only needed to print the initialized object.

    Example:
        >>>print(f"{ColorPalette()}")
    """
    def __init__(self):
        self.colors = []
        for i in range(255):
            self.colors.append(Color(i))
    def __str__(self):
        values = []
        max_len = 0
        for i, color in enumerate(self.colors):
            name = f"{color}color_{i}"
            if len(name) > max_len:
                max_len = len(name)
            values.append(name)
        s = ""
        counter = 0
        while counter < len(values):
            for _ in range(min(len(values) - counter, 7)):
                s += f"{values[counter]}{' '*(max_len - len(values[counter]))}\t"
                counter += 1
            s += "\n"
        return s

class TraceBackColor:
    """
    Useful class to color traceback with desired colors.
    It is really easy to use, it is only needed to type this line at the top of you main file after importing the class:

    Examples:

        >>> sys.excepthook = TraceBackColor(tb_color=Color(196), path_color=Color(33), line_color=Color(251))

        or use default colors by just writing:

        >>> sys.excepthook = TraceBackColor()

    Note:
        Colors might look different on different systems.
    """
    def __init__(self, tb_color=None, path_color=None, line_color=None):
        self.tb_color = tb_color or Colors.error
        self.path_color = path_color or Colors.link
        self.line_color = line_color or Colors.text

    def __call__(self, t, value, tb):
        """
        Called by system's exception hook to color tracebacks
        :param t: type
        :param value: value
        :param tb: traceback object
        :return: None
        """
        tb = ''.join(traceback.format_exception(t, value, tb))
        tb = tb.split("\n")
        tb = [self._colorPathLine(line) for line in tb]
        tb = [self._colorLineNumber(line) + "\n" for line in tb]
        tb = "".join(tb)
        print(f"{self.tb_color}{tb}{ResetColor()}")
    def _colorPathLine(self, line: str) -> str:
        """
        Need to be applied to each line.  Will color in the desired color the path in the line
        :param line: the line
        :return: line
        """
        regexp = re.compile(r'File ".*",')
        if regexp.search(line):
            f_idx = line.index(" \"") + 2
            l_idx = line.index("\",")
            return line[:f_idx] + str(self.path_color) + line[f_idx:l_idx] + str(self.tb_color) + line[l_idx:]
        else:
            return line

    def _colorLineNumber(self, line: str) -> str:
        """
        Need to be applied to each line.  Will color in the desired color the line number in the line
        :param line: the line
        :return: line
        """
        regexp = re.compile(r'File ".*",')
        if regexp.search(line):
            f_idx = line.index(", line ") + 7
            l_idx = line.index(", in")
            return line[:f_idx] + str(self.line_color) + line[f_idx:l_idx] + str(self.tb_color) + line[l_idx:]
        else:
            return line



#### Delete this function, it is only used for development
def main_func():
    fn = lambda x: x / 0
    print(fn(10))

if __name__ == '__main__':
    # Theme inspired by Nord Theme, made by ChatGPT (Works for True color terminals)
    # Colors.set_theme(
    #     accent=RGBColor(143, 188, 187),  # Frost - Teal
    #     text=RGBColor(216, 222, 233),  # Snow Storm - Main text
    #     error=RGBColor(220, 70, 80),  # Flashy Error - Bright Crimson
    #     warning=RGBColor(255, 170, 50),  # Flashy Warning - Golden Orange
    #     success=RGBColor(100, 220, 120),  # Flashy Success - Emerald Green
    #     link=RGBColor(136, 192, 208),  # Frost - Light Blue
    #     white=RGBColor(236, 239, 244),  # Snow Storm - Bright text
    #     black=RGBColor(46, 52, 64),  # Polar Night - Dark background
    #     red=RGBColor(191, 97, 106),  # Aurora - Red
    #     blue=RGBColor(94, 129, 172),  # Frost - Dark Blue
    #     green=RGBColor(163, 190, 140),  # Aurora - Green
    #     yellow=RGBColor(235, 203, 139),  # Aurora - Yellow
    #     cyan=RGBColor(143, 188, 187),  # Frost - Teal
    #     magenta=RGBColor(180, 142, 173),  # Aurora - Purple
    #     brown=RGBColor(121, 85, 72),  # Invented Brown
    #     orange=RGBColor(208, 135, 112),  # Aurora - Orange
    #     purple=RGBColor(180, 142, 173),  # Aurora - Purple
    #     pink=RGBColor(216, 155, 176)  # Invented Pink
    # )
    print(Colors)
    print(ColorPalette())
    # print(f"{Color(154)}I am colored :) {ResetColor()} And I am not colored :(")
    # sys.excepthook = TraceBackColor(tb_color=Color(203))
    # main_func()
    # print(f"{RGBColor(106,206,92)}Hello world!!!{ResetColor()}")



