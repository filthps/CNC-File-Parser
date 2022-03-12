import os
import re
from typing import Any, Optional
from collection import Session
from cnc_file import CNCFile
from abstractions import AbstractMachine
from config import MACHINES_INPUT_PATH, MACHINES_OUTPUT_PATH, HELLER


class HellerCNCFile(CNCFile):
    ORIGIN_ENUMERATION = ('G54', 'G55', 'G56', 'G57')
    DEFAULT_ORIGIN = 'G54'
    INVALID_SYMBOLS = "[=/:;]"

    def __init__(self, **kwargs):
        self.__origin: str = self.DEFAULT_ORIGIN
        self.__target: Optional[os.open] = None
        super().__init__(**kwargs)
        self.__path: str = os.path.join(self.get_output_path(
            self.get_clear_path(kwargs['path'])), self.get_filename(self.name, self.format_)
        )
        self.__target = self.open(self.__path, "xt")
        self.__head_inner: str = ""

    @property
    def origin(self):
        return self.__origin

    @origin.setter
    def origin(self, val):
        if val in self.ORIGIN_ENUMERATION:
            self.__origin = val

    def create_new_head(self):
        mpf_str = self.add_mpf_string()
        inner = "\n".join((mpf_str, self.__origin, "G64"))
        self.__head_inner = inner
        return inner

    @classmethod
    def get_output_path(cls, p: str = ""):
        path = os.path.join(MACHINES_OUTPUT_PATH[HELLER], p)
        if not os.path.exists(path):
            os.makedirs(path, mode=0o777)
        return path

    @classmethod
    def get_clear_path(cls, p: str) -> str:
        """
        Получить 'чистый' путь файла - без учёта пути служебных папок-констант
        :return:
        """
        p = os.path.normpath(p)
        p = p.replace(MACHINES_INPUT_PATH[HELLER] + os.path.sep, "")
        return p

    def add_mpf_string(self) -> str:
        clear_name_num = re.match(r"\D*(\d+)\D*", self.name, re.S).groups()[0]
        return f"%mpf{clear_name_num}"

    def large_10000(self):
        pass


class Heller(AbstractMachine):
    CNC_FILE_TYPE = HellerCNCFile

    @classmethod
    def create_session(cls, data):
        session = Session(data, type_=cls.CNC_FILE_TYPE)
        return session

    @classmethod
    def get_session_status(cls):
        pass

    @classmethod
    def start(cls, data: list[dict[str, Any]], origin: Optional[str]):
        session: Session = cls.create_session(data)
        for file_ in session:
            if origin:
                file_
            file_.create_new_head()
            ...
