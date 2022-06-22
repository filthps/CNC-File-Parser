import sqlite3
from typing import Union, Iterable


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

    def select(self, values: Iterable, table_name: str):
        self.short_names.update({table_name: table_name.upper()[:3]})
        self.inner += f"SELECT {', '.join(values)} FROM {table_name} AS {self.short_names[table_name]}\n"
        return self.inner

    def where(self, field_name: str, operator: str, value: str):
        if not self.is_group:
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
    def __init__(self, location: str):
        self.db = sqlite3.connect(location)
        self.db.cursor()

    def commit(self, query: SQLQuery):
        self.is_valid_query(query)

    @staticmethod
    def is_valid_query(val):
        if not isinstance(SQLQuery, val):
            raise sqlite3.DataError


if __name__ == "__main__":
    db = Database("database.db")
    query = SQLQuery()
    query.select(["machine_id"], "Machine")
    query.where("machine_id", "!=", "1")
    print(query)
