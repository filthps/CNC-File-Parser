from typing import Any
from abstractions import AbstractMachine
from config import HELLER
from heller import HellerCNCFile
from collection import Session


class Machine(AbstractMachine):
    CNC_FILE_TYPE = {HELLER: HellerCNCFile}

    @classmethod
    def create_session(cls, data, name):
        session = Session(data, type_=cls.CNC_FILE_TYPE[name])
        return session

    @classmethod
    def get_session_status(cls):
        pass

    @classmethod
    def start(cls, data: list[dict[str, Any]], filename: str = "", machine_name: str = ""):
        session: Session = cls.create_session(data, machine_name)
        for file in session:
            if file.is_valid_tail(file[-1]):
                head_inner = file.create_new_head()
