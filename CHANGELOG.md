## 0.2.0
### Bugs Fixed
- ```ConfigFile```: Fixed a debug print that was not removed
- ```Progress bar```: Now, the refresh rate is considered when using the `update` method.

### New Features
- ```logger```: Now fully integrated with python's logger module + have default colored formatters
- ```Progress bar```: Now use the Colors theme for the deep learning progress bar
- ```Colors```: Added the primary color and secondary color to the default theme
- ```ConfigFile```: Now support Literal type checking from the typing module
- ```ConfigFile```: Now support tagged parameters. You can tag parameters in the config format and then get all parameters with a specific tag.
- ```Spinner```: New undefined progress api 🎉

## 0.1.0
- ```Color```: Now themes have a `.reset` attribute by default
- ```ConfigFile```: Now have config options: Can get different variant of a config format
- ```ConfigFile```: Now support default values
- ```progress```: Fixed the progress that did not go all the way to the max when near 100%
## 0.0.3
- ```progress bar```: Fixed the auto-sizing (Now it should be accurate) + Remove trailing characters
## 0.0.2
- ```progress display parameter```: Progress api now has a display parameter that, if set to true, can make the bar hidden.
## 0.0.1
- ```ColorPalette``` is now available as top-level import
- ```Colors``` Theme now has the darken color field by default
- ```progress type=dl``` display format has been improved
## 0.0.0
- Initial release