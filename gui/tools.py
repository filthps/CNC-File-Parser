from typing import Union, Iterator
from itertools import count
from PySide2.QtWidgets import QTabWidget, QStackedWidget, QPushButton, QInputDialog, QListWidgetItem
from PySide2.QtGui import QIcon
from gui.ui import Ui_MainWindow as Ui


class Tools:

    @staticmethod
    def __get_widget_index_by_tab_name(widget_instance: Union[QTabWidget, QStackedWidget], tab_name: str) -> int:
        page = widget_instance.findChild(widget_instance.__class__, tab_name)
        return widget_instance.indexOf(page)

    @staticmethod
    def load_stylesheet(path: str) -> str:
        with open(path) as p:
            return p.read()

    @staticmethod
    def set_icon_buttons(ui: Ui, n: str, path: str) -> None:
        """
        Автоматизированный способ работы с идентичными кнопками;
        в имени кнопки заложен следущий смысл:
        [имя_кнопки]_[номер_кнопки]

        :param ui: Экземпляр Ui_MainWindow
        :param n: [имя_кнопки] без замыкающего нижнего подчёркивания
        :param path: строка-путь к иконке
        :return: None.
        """
        def gen() -> Iterator:
            counter = count()
            while True:
                b: QPushButton = getattr(ui, f"{n}_{next(counter)}", False)
                if not b:
                    return
                yield b

        icon = QIcon(path)
        [b.setIcon(icon) for b in gen()]


class Constructor:

    @staticmethod
    def get_dialog_create_machine(instance, ui: Ui):
        machine_name, is_submit = QInputDialog.getText(instance, "Добавление станка", "Введите название станка")
        if is_submit:
            ui.add_machine_list_0.addItem(QListWidgetItem(machine_name))
