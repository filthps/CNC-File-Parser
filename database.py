import os
import sqlite3
from typing import Union, Iterable, Callable, Optional
from PySide2.QtCore import QThread, Signal
from data_type import LinkedListItem, LinkedList


class SQLQuery(LinkedListItem):
    "Экземпляр запроса - один запрос"
    def __init__(self, body: str = ""):
        super().__init__(val=self)
        self.short_names = {}
        self._values = []
        self._inner = body
        self.__group = False
        self._closed = self._set_closed() if body else False
        self._container = False

    @property
    def is_group(self):
        return self.__group

    def set_has_group(self):
        self.__group = True

    def _check_closed(self):
        if self._closed:
            raise Exception("Экземпляр запроса уже заполнен")

    def _set_closed(self):
        self._closed = True

    def _set_values(self, val):
        self._values = list(val)

    def insert(self, table_name, values: Union[tuple, tuple[tuple]]):
        self._container = True
        self._check_closed()
        self._set_closed()
        self._set_values(values)
        self._inner = f"INSERT INTO {table_name} VALUES $>\n"
        return self._inner

    def select(self, table_name: str, values: Union[Iterable, str]):
        self._check_closed()
        self._set_closed()
        self._set_values(values)
        if type(values) is str:
            if not values == "*":
                raise ValueError
        self.short_names.update({table_name: table_name.upper()[:3]})
        self._inner = f"SELECT $ FROM {table_name} AS {self.short_names[table_name]}\n"
        return self._inner

    def append_column_values(self, values: Iterable):
        """
        Добавить значение N в конец (row_1, row_2..., N)
        """
        map(lambda v: self._values.append(v), values)

    def where(self, field_name: str, operator: str, value: str):
        if not self.is_group:
            value = value if not isinstance(value, str) else f"'{value}'"
            self._inner += f"WHERE {field_name} {operator} {value}\n"

    def having(self):
        ...

    def join(self, join_type: str, select: "SQLQuery", var1, var2):
        Database.is_valid_query(select)
        self._inner += f"{join_type.upper()} JOIN {select}\nON {var1} = {var2}\n"

    def delete(self, table_name: str, field_name: str, operator: str, value: str):
        self._check_closed()
        self._set_closed()
        self._inner = f"DELETE FROM {table_name}\n"
        self._inner += self.where(field_name, operator, value)

    def __str__(self):
        if self._values:
            print(str(tuple(self._values) if self._container else ", ".join(self._values)), self._container)
            return self._inner.replace(
                "$",
                str(tuple(self._values) if self._container else ", ".join(self._values))
            )
        return self._inner

    def __repr__(self):
        return f"{type(self)}({str(self)})"


class SQLQueryContainer(LinkedList):
    pass


class Database(QThread):
    signal_ = Signal(str)

    def __init__(self, location: str):
        super().__init__()
        self._db = None
        self._path = location
        self._query: Optional[SQLQuery] = None

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
        self.signal_.emit(str(val))

    def connect_(self, query: Union[SQLQueryContainer, SQLQuery], callback: Optional[Callable] = None):
        self.is_valid_query(query)
        self._query = query
        self.signal_.connect(callback)
        self.start()

    def _commit(self):
        cursor = self.__open()
        if isinstance(self._query, SQLQueryContainer) and len(self._query) > 1:
            val = cursor.executemany(self._query)
        else:
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
        self._db = None

    def is_open(self):
        return True if self._db is not None else False


if __name__ == "__main__":
    db = Database("database.db")
    q = SQLQuery()

    def callback(v):
        print(v, type(v))
    q.select("Machine", ("machine_id",))
    db.connect_(q, callback)
