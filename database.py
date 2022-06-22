import sqlite3
from typing import Union, Iterable


class SQLQuery:
    def __init__(self, body: str=None):
        self.short_names = {}
        self.inner = ""
        self.__group = False

    @property
    def is_group(self):
        return self.__group

    def set_has_group(self):
        self.__group = True

    def insert(self, table_name, values: Union[tuple, tuple[tuple]]):
        self.inner += f"INSERT INTO {table_name} VALUES {str(values)}\n"
        return self.inner

    def select(self, table_name: str, values: tuple):
        self.short_names.update({table_name: table_name.upper()[:3]})
        self.inner += f"SELECT {values} FROM {table_name} AS {self.short_names[-1]}\n"
        return self.inner

    def where(self, field_name: str, value: str, operator: str):
        self.inner += f"WHERE {field_name} {operator} {value}\n"

    def join(self, join_type: str, select_inner: "SQLQuery", var1, var2):
        self.inner += f"{join_type.upper()} JOIN {select_inner}\nON {var1} = {var2}"

    def __str__(self):
        return self.inner

    def __repr__(self):
        return f"{type(self)}({self.inner})"


class Database:
    def __init__(self):
        self.db = sqlite3.connect("database.db")
        self.db.cursor()

    def commit(self, query: SQLQuery):
        self.is_valid_query(query)

    @staticmethod
    def is_valid_query(val):
        if not isinstance(SQLQuery, val):
            raise sqlite3.DataError
