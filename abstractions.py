from typing import Any
from abc import ABC, abstractmethod
from collections.abc import Sequence


class AbstractLog(ABC):
    """
    К лог-файлу будет конкурентный доступ - запись в него от разных потоков.
    При создании записи в лог:
        1) открыть файл на дозапись
        2) произвести запись
        3) закрыть файл
    """

    @classmethod
    @abstractmethod
    def msg(cls, data: dict[str, str]) -> None:
        pass

    @classmethod
    @abstractmethod
    def open(cls):
        pass

    @classmethod
    @abstractmethod
    def close(cls):
        pass

    @classmethod
    @abstractmethod
    def write(cls, message):
        pass

    @classmethod
    def format_message(cls, text):
        pass

    @staticmethod
    @abstractmethod
    def head():
        pass

    @staticmethod
    @abstractmethod
    def tail(self):
        pass


class AbstractMachine(ABC):

    @classmethod
    @abstractmethod
    def create_session(cls, data: list[dict[str, Any]]):
        pass

    @classmethod
    @abstractmethod
    def get_session_status(cls):
        pass

    @classmethod
    @abstractmethod
    def start(cls, data: list[dict[str, Any]]):
        pass


class AbstractCNCFile(Sequence):
    """
    Контейнер содержимого файла
    """

    @abstractmethod
    def __init__(self):
        ...

    @abstractmethod
    def get_status(self):
        pass

    def get_length(self):
        pass

    @abstractmethod
    def is_valid_last_modify_attr(self):
        pass

    @abstractmethod
    def remove_invalid_symbols(self):
        """
        Удалить отдельно взятые символы, невоспринимаемые стойкой
        """
        pass

    @abstractmethod
    def is_valid_numerate(self):
        pass

    @abstractmethod
    def re_numerate(self):
        pass

    @abstractmethod
    def open(self, m: str):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def re_connect(self, m: str):
        pass

    @abstractmethod
    def is_origin(self):
        """
        Из-за того, что при каждом вызове __iter__ приходится заново открывать файл,
        придётся проверять подлинность файла (на предмет подмены) с момента первого открытия до последующих N-раз.
        :return: bool
        """
        pass

    @abstractmethod
    def parse_head(self):
        pass

    @abstractmethod
    def find_head_template(self):
        pass


class AbstractSession(Sequence):
    """
    Композиция к CNCFile
    """

    @abstractmethod
    def __init__(self):
        pass

    @property
    @abstractmethod
    def status(self):
        pass

class AbstractTemp(ABC):

    @abstractmethod
    def __int__(self):
        pass

    @abstractmethod
    def write(self, line: str):
        """
        Построчная запись
        :param line: содержимое без указателя-переноса
        :return: None
        """
        pass

    @abstractmethod
    def clone(self):
        """
        Считать содержимое-итератор
        :return: строка-содержимое
        """
        pass

    @abstractmethod
    def close(self):
        pass
