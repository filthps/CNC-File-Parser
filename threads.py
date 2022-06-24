from typing import Optional
from PySide2.QtCore import QThread, Signal, Qt
from gui.ui import Ui_MainWindow
from database import Database, SQLQuery
from gui.application import Main


class DBConnector(QThread):
    result = None

    def __init__(self):
        signal: Signal = Signal(str)

        def init_signals():
            self.signal.connect(self.__set_result, Qt.AutoConnection)
        init_signals()

    def __set_result(self, result):
        self.result = result

    def run(self) -> None:
        ...
