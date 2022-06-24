import sqlite3
from typing import Union, Iterable, Callable
from threads import Thread


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


class Database:
    """
    Каждый экземпляр - подключаемая база данных,
    работающая через свой создаваемый паоток
    """
    def __init__(self, location: str):
        self.__path = location
        self.__thread = None
        self.__db = None

        def test():
            self.__open()
            self.__close()
        test()

    def commit(self, q: SQLQuery, callback: Callable):
        self.is_valid_query(q)
        cursor = self.__open()
        cursor.execute(str(q))
        self.db.commit()
        self.__close()

    def fetch(self, q: SQLQuery, callback: Callable):
        self.is_valid_query(q)
        cursor = self.__open()
        cursor.execute(str(q))
        val = cursor.fetchone()
        self.__close()
        return val

    @staticmethod
    def is_valid_query(val):
        if not isinstance(val, SQLQuery):
            raise sqlite3.DataError

    def __init_thread(self):
        self.__thread = Thread()
        self.__thread.signal.connect()

    def __open(self):
        self.__init_thread()
        self.db = sqlite3.connect(self.path)
        return self.db.cursor()

    def __close(self):
        self.db.close()


if __name__ == "__main__":
    db = Database("database.db")
    query = SQLQuery()
    query.select("Machine", "*")
    query.where("machine_id", "=", "1")
    print(db.fetch(query))
