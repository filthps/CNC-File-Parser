import os
import traceback
import sqlite3
from typing import Union, Iterable, Callable, Optional
from PySide2.QtCore import QThread, Signal
from data_type import LinkedListDictionary


class SQLQuery:
    """Экземпляр запроса - один запрос"""
    def __init__(self, body: str = "", commit=False, complete=True, not_null_indexes=tuple()):
        self.short_names = {}
        self._values = []
        self._table_name = None
        self._inner = body
        self.__group = False
        self._closed = self._set_closed() if body else False
        self.__commit = commit
        self.__ready = complete
        self._not_null_indexes = not_null_indexes

    def autocheck__complete(self):
        if not self._not_null_indexes:
            return
        status = True
        for index in self._not_null_indexes:
            if len(self._values) > index:
                if self._values[index] == 'null':
                    status = False
                    break
        if status:
            self.__ready = True

    def edit(self, *t: tuple):
        for v in t:
            self._values[v[0]] = v[1]

    def append(self, v):
        self._values.append(v)

    @property
    def is_group(self):
        return self.__group

    @property
    def is_complete(self):
        return self.__ready

    @is_complete.setter
    def is_complete(self, v):
        if not type(v) is bool:
            raise TypeError
        self.__ready = v

    @property
    def is_commit(self):
        return self.__commit

    @is_commit.setter
    def is_commit(self, v):
        if not type(v) is bool:
            raise TypeError
        self.__commit = v

    def set_has_group(self):
        self.__group = True

    def _check_closed(self):
        if self._closed:
            raise Exception("Экземпляр запроса уже заполнен")

    def _set_closed(self):
        self._closed = True

    def _set_values(self, val):
        self._check_closed()
        self._values = list(val)
        self._set_closed()

    def insert(self, table_name, values: Union[tuple, tuple[tuple]]):
        self.__commit = True
        self._table_name = table_name
        self._set_values(values)
        self.autocheck__complete()
        self._inner = f"INSERT INTO {table_name} VALUES $\n"
        return self._inner

    def insert_column_value(self, value, index=-1):
        self._values.insert(index, value)
        self.autocheck__complete()

    def select(self, table_name: str, values: Union[Iterable, str], special=False):
        self._table_name = table_name
        self._set_values(values)
        self.autocheck__complete()
        if type(values) is str:
            if not special:
                if not values == "*":
                    raise ValueError
        self.short_names.update({table_name: table_name.upper()[:3]})
        self._inner = f"SELECT $ FROM {table_name} AS {self.short_names[table_name]}\n"
        return self._inner

    def where(self, field_name: str, operator: str, value: str):
        if not self.is_group:
            value = value if not isinstance(value, str) else f"'{value}'"
            self._inner += f"WHERE {field_name} {operator} {value}\n"

    def join(self, join_type: str, select: "SQLQuery", var1, var2):
        Database.is_valid_query(select)
        self._inner += f"{join_type.upper()} JOIN {select}\nON {var1} = {var2}\n"

    def delete(self, table_name: str, field_name: str, operator: str, value: str):
        self._check_closed()
        self._set_closed()
        self._inner = f"DELETE FROM {table_name}\n"
        self.where(field_name, operator, value)

    @staticmethod
    def _parse_values(value: str) -> str:
        return value.replace('None', 'null')

    def __str__(self):
        s = self._inner.replace("$", str(tuple(self._values)) if self.is_commit else ", ".join(self._values))
        return self._parse_values(s)

    def __repr__(self):
        return f"{type(self)}({str(self)})"

    def __iter__(self):
        return iter(self._values)

    def __getitem__(self, item):
        return self._values[item]


class SQLQueryContainer(LinkedListDictionary):
    def __init__(self, *items, commit_=False):
        super().__init__(*items)
        self._type = commit_

    @property
    def is_commit(self):
        return self._type

    @is_commit.setter
    def is_commit(self, v):
        if not type(v) is bool:
            raise TypeError
        self._type = v

    def is_valid(self, value: SQLQuery):
        value = value[1]
        if not type(value) is SQLQuery and not isinstance(value, self.__class__):
            raise ValueError
        if not value.is_commit == self.is_commit:
            raise TypeError("Данный экземпляр контейнера не может принять этот запрос. "
                            "Потому как предназанчение их различно: один коммитит записи в БД, а другой получает.")

    def update(self, elem):
        self.is_valid(elem)
        super().update(elem)


class Database(QThread):
    signal_ = Signal(tuple)

    def __init__(self, location: str):
        super().__init__()
        self._db: Optional[sqlite3.connect] = None
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
        cursor = self.__open()
        try:
            val = self._commit(cursor)
        except sqlite3.OperationalError:
            traceback.print_exc()
            print(f"\n{'-'*10}\n", str(self._query))
        except sqlite3.IntegrityError:
            traceback.print_exc()
            print(f"\n{'-' * 10}\n", str(self._query))
        else:
            self.signal_.emit(tuple(val))
        finally:
            self.__close()

    def connect_(self, query: Union[SQLQueryContainer, SQLQuery], callback: Optional[Callable] = None):
        self.is_valid_query(query)
        self._query = query
        self.signal_.connect(callback)
        self.start()

    def _commit(self, cursor):
        if isinstance(self._query, SQLQueryContainer) and len(self._query) > 1:
            cursor.executemany(str(self._query))
            if self._query.is_commit:
                self._db.commit()
                return
            return cursor.fetchall()
        cursor.execute(str(self._query))
        if not self._query.is_commit:
            return cursor.fetchone()
        self._db.commit()

    @staticmethod
    def is_valid_query(val):
        if not isinstance(val, (SQLQuery, SQLQueryContainer,)):
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
    query = SQLQuery()
    container = SQLQueryContainer(commit_=True)
    container.update(
        ("gsdf", container.__class__(
            ("dfgdfg", query), commit_=True)
         )
    )
    print(container)
