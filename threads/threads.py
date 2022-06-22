from PySide2.QtCore import QThread
from database import Database, SQLQuery


class DatabaseTread(QThread):
    db_signal = QThread(str)

    def launch(self, q: SQLQuery):
        ...

    def receive_value(self, value: str):
        self.db_signal.emit(value)

    def run(self):
        ...
