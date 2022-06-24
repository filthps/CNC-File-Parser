from PySide2.QtCore import QThread, Signal, Qt


class DatabaseThread(QThread):
    signal = Signal(str)

    def push(self):
        print("Отправил в поток")

    def __set_result(self, result):
        print("Получил", result)
        self.result = result

    def run(self) -> None:

        self.signal.emit("result")
