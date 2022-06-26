import os
import sqlite3
from typing import Union, Iterable, Callable, Optional
from PySide2.QtCore import QThread, Signal


class SQLQuery:
    def __init__(self, body: str = ""):
        self.short_names = {}
        self.inner = body
        self.__group = False

    @property
    def is_group(self):
        return self.__group

    def set_has_group(self):
        self.__group = True

    def insert(self, table_name, values: Union[tuple, tuple[tuple]]):
        self.inner += f"INSERT INTO {table_name} VALUES {str(values)}\n"
        return self.inner

    def select(self, table_name: str, values: Union[Iterable, str]):
        if type(values) is str:
            if not values == "*":
                raise ValueError
        self.short_names.update({table_name: table_name.upper()[:3]})
        self.inner += f"SELECT {', '.join(values)} FROM {table_name} AS {self.short_names[table_name]}\n"
        return self.inner

    def where(self, field_name: str, operator: str, value: str):
        if not self.is_group:
            value = value if not isinstance(value, str) else f"'{value}'"
            self.inner += f"WHERE {field_name} {operator} {value}\n"

    def having(self):
        ...

    def join(self, join_type: str, select: "SQLQuery", var1, var2):
        Database.is_valid_query(select)
        self.inner += f"{join_type.upper()} JOIN {select}\nON {var1} = {var2}\n"

    def __str__(self):
        return self.inner

    def __repr__(self):
        return f"{type(self)}({self.inner})"


class Database(QThread):
    signal_ = Signal(str, object)

    def __init__(self, location: str):
        super().__init__()
        self._db = None
        self._path = location
        self._query: Optional[SQLQuery] = None
        self._callback: Optional[Callable] = None

        def check_database_location():
            if not os.path.exists(location):
                raise ConnectionError

        def test():
            self.__open()
            self.__close()

        check_database_location()
        test()

    def run(self) -> None:
        val = self._commit()
        self.signal_.emit(val)

    def connect_(self, query: SQLQuery, callback: Optional[Callable] = None):
        self.is_valid_query(query)
        self._query = query
        self._callback = callback
        self.signal_.connect(self._callback)
        self.start()

    def _commit(self):
        cursor = self.__open()
        print(str(self._query))
        val = cursor.execute(str(self._query))
        self.__close()
        return val

    @staticmethod
    def is_valid_query(val):
        if not isinstance(val, SQLQuery):
            raise sqlite3.DataError

    def __open(self):
        self._db = sqlite3.connect(self._path)
        return self._db.cursor()

    def __close(self):
        self._db.close()


if __name__ == "__main__":
    db = Database("database.db")
