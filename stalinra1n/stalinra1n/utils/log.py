import sys
from enum import Enum
from typing import Optional


class LogLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3
    FATAL = 4


_current_level = LogLevel.INFO
_gui_callback = None


def set_level(level: LogLevel):
    global _current_level
    _current_level = level


def set_gui_callback(callback):
    global _gui_callback
    _gui_callback = callback


def _log(level: LogLevel, message: str, prefix: str = None):
    if level.value < _current_level.value:
        return

    if prefix:
        formatted = f"[{prefix}] {message}"
    else:
        formatted = message

    if _gui_callback:
        _gui_callback(level, formatted)
    else:
        stream = sys.stderr if level.value >= LogLevel.WARN.value else sys.stdout
        print(formatted, file=stream)


def debug(message: str, prefix: str = "DBG"):
    _log(LogLevel.DEBUG, message, prefix)


def info(message: str, prefix: str = "*"):
    _log(LogLevel.INFO, message, prefix)


def warn(message: str, prefix: str = "!"):
    _log(LogLevel.WARN, message, prefix)


def error(message: str, prefix: str = "ERR"):
    _log(LogLevel.ERROR, message, prefix)


def fatal(message: str, prefix: str = "FTL"):
    _log(LogLevel.FATAL, message, prefix)
    sys.exit(1)


def step(message: str):
    info(f" {message}")
