from typing import Any
from abstractions import AbstractMachine
from cnc_file import CNCFile
from collection import Session

class FidiaCNCFile(CNCFile):
    INVALID_SYMBOLS = "[=/:;]"

    def __init__(self, path: str = None, name: str = None):
        super().__init__(path=path)
        self.name = name

    def add_mpf_string(self):
        pass


class Fidia(AbstractMachine):
    CNC_FILE_TYPE = FidiaCNCFile
    SESSION = None

    @classmethod
    def create_session(cls, data):
        #cls.SESSION = Session(data, type_=cls.CNC_FILE_TYPE)
        cls.SESSION = ""

    @classmethod
    def get_session_status(cls):
        pass

    @classmethod
    def start(cls, data: list[dict[str, Any]]):
        cls.SESSION = cls.create_session(data)
