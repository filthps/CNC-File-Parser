from typing import Any, ClassVar
from abstractions import AbstractSession
from data_type import LinkedList


class Session(LinkedList, AbstractSession):

    def __init__(self, data: list[dict[str, Any]], type_: ClassVar = None):
        if type_ is None:
            raise ValueError
        super().__init__(items=data, type_=type_)
        self.__status = None

    def is_valid_index(self, index):
        if not 0 <= index < self._length:
            raise IndexError
        return True

    @property
    def status(self):
        return self.__status

    def __repr__(self):
        return f"{type(self).__name__}({list(self)})"

    def __str__(self):
        return str(list(self))

    def __delitem__(self, key):
        item = super().__delitem__(key)
        item.close()
