import datetime
from typing import Callable, Optional
from traceback import print_exc
from itertools import repeat
from abstractions import AbstractLog
from config import LOG_PATH


class Log(AbstractLog):
    PATH = LOG_PATH
    FILE = None
    STATE = False

    @classmethod
    def msg(cls, data: dict[str, str]) -> None:
        if not cls.open():
            return
        message = cls.format_message(data)
        cls.write(message)

    @classmethod
    def open(cls):
        try:
            cls.FILE = open(cls.PATH, "at")
        except OSError:
            print_exc()
        else:
            return True

    @classmethod
    def write(cls, message):
        file = cls.FILE
        for i in message:
            file.write(i)

    @classmethod
    def close(cls):
        cls.FILE.flush()

    @staticmethod
    def head() -> str:
        return f"{'-':>10}{datetime.datetime.now():%d-%m-%Y %H:%M:%S}{'-':<10}"

    @staticmethod
    def tail():
        return repeat('-', 50)

    @classmethod
    def format_message(cls, msg: dict[str, str]) -> str:
        log_string = ""
        for reason, inner in msg.items():
            head_or_tail: Optional[Callable] = getattr(reason, cls)
            if head_or_tail is not None:
                log_string += head_or_tail()
            else:
                log_string += f"{reason} - {inner}"
            log_string += "\n"
        return log_string
