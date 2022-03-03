import os
from typing import Any
from collection import Session
from cnc_file import CNCFile
from abstractions import AbstractMachine
from config import MACHINES_INPUT_PATH, MACHINES_OUTPUT_PATH, HELLER


class HellerCNCFile(CNCFile):
    INVALID_SYMBOLS = "[=/:;]"

    def __init__(self, **kwargs):
        self._target = None
        super().__init__(**kwargs)
        self.__path = os.path.join(self.get_output_path(self.get_clear_path(kwargs['path'])),
                                   self.get_filename(self.name, self.format_))
        self.__target = self.open(self.__path, mode="xt")

    @classmethod
    def get_output_path(cls, p: str = ""):
        path = os.path.join(MACHINES_OUTPUT_PATH[HELLER], p)
        if not os.path.exists(path):
            os.makedirs(path, mode=0o777)
        return path

    @classmethod
    def get_clear_path(cls, p: str):
        """
        Получить 'чистый' путь файла - без учёта пути служебных папок-констант
        :return:
        """
        p = os.path.normpath(p)
        p = p.replace(MACHINES_INPUT_PATH[HELLER] + os.path.sep, "")
        return p

    def add_mpf_string(self):
        pass

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
    def start(cls, data: list[dict[str, Any]]):
        session = cls.create_session(data)


if __name__ == "__main__":
    path = 'C:\/Users\/filps\PycharmProjects\/cnc_file_parser\/files\/heller\/9109_verh\/'
    name = 'R400'
    format_ = 'txt'
    #t = HellerCNCFile(path=path, name=name, frmt=format_)
    Heller.start([{
        'path': 'C:\/Users\/filps\PycharmProjects\/cnc_file_parser\/files\/heller\/9109_verh\/',
        'name': 'R400',
        'frmt': 'txt'
    }])
