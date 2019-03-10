# Use https://github.com/micropython/micropython-lib/tree/master/logging ??

from micropython import const

ENABLE_COLOR = True

COLOR_CODE = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "cyan": 36,
    "white": 37,
    "default": 39
}
BG_CODE_SHIFT = const(10)
BRIGHT_CODE_SHIFT = const(60)
COLOR_STR_FORMAT = "\x1B[{};{}m"
LOGGER_PREFIX = "{}: {} =>"


def reset():
    if ENABLE_COLOR:
        return "\x1B[0m"


def color(font="default", background="default", bright=False):
    if ENABLE_COLOR:
        fg = COLOR_CODE.get(font) + (BRIGHT_CODE_SHIFT if bright else 0)
        bg = COLOR_CODE.get(background) + BG_CODE_SHIFT + (BRIGHT_CODE_SHIFT if bright else 0)
        return COLOR_STR_FORMAT.format(fg, bg)
    else:
        return None


class Logger:
    def __init__(self, name):
        self._name = name

    def debug(self, *args):
        print(color('cyan'), LOGGER_PREFIX.format('DEBUG', self._name), *args)
        print(reset(), end='')

    def info(self, *args):
        print(color(), LOGGER_PREFIX.format('INFO', self._name), *args)
        print(reset(), end='')

    def success(self, *args):
        print(color('green'), LOGGER_PREFIX.format('SUCCESS', self._name), *args)
        print(reset(), end='')

    def warn(self, *args):
        print(color('yellow'), LOGGER_PREFIX.format('WARN', self._name), *args)
        print(reset(), end='')

    def error(self, *args):
        print(color('red'), LOGGER_PREFIX.format('ERROR', self._name), *args)
        print(reset(), end='')
