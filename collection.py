from typing import Any, ClassVar
from abstractions import AbstractSession
from data_type import LinkedList


class Session(LinkedList, AbstractSession):

    def __init__(self, data: list[dict[str, Any]], type_: ClassVar = None):
        if type_ is None:
            raise ValueError
        self.__length = 0
        self.__length = len(self)
        self.__status = None
        super().__init__(items=data, type_=type_)

    def is_valid_index(self, index):
        if not 0 <= index < self.__length:
            raise IndexError
        return True

    @property
    def status(self):
        return self.__status

    def to_list(self):
        return [item for item in self]

    def __repr__(self):
        return f"{type(self).__name__}({self.to_list()})"

    def __str__(self):
        return str(self.to_list())

    def __del__(self):
        for file in self:
            file.close()
