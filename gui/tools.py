from typing import Union, Iterator, Optional, Sequence
from itertools import count, cycle
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTabWidget, QStackedWidget, QPushButton, QInputDialog, QDialogButtonBox, \
    QListWidgetItem, QListWidget, QDialog, QLabel, QVBoxLayout, QHBoxLayout
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


class AbstractDialog(QDialog):
    """
    Диалоговое окно с возможностью контроля слота нажатия клавиш клавиатуры.
    Навигация по кнопкам
    """
    def __init__(self, parent=None, buttons: Optional[Sequence[QPushButton]] = None):
        super().__init__(parent)
        if buttons is not None:
            button: QDialogButtonBox = buttons[0]
            self.__set_active(button)
        buttons = list(buttons)
        left_orientation = buttons
        left_orientation.reverse()
        self._left = cycle(left_orientation)
        self._right = cycle(buttons)

    def keyPressEvent(self, event):
        if event == Qt.Key_Left:
            button = self.__get_button(self._left)
            self.__set_active(button)
        if event == Qt.Key_Right:
            button = self.__get_button(self._right)
            self.__set_active(button)

    @staticmethod
    def __get_button(buttons: cycle):
        return next(buttons)

    @staticmethod
    def __set_active(button: QDialogButtonBox):
        # button.setFocus() todo
        ...


class Constructor:
    def __init__(self, instance, ui: Ui):
        self.instance = instance
        self.main_ui = ui

    def get_dialog_create_machine(self) -> Optional[QListWidgetItem]:
        machine_name, is_submit = QInputDialog.getText(self.instance, "Добавление станка", "Введите название станка")
        if is_submit:
            return QListWidgetItem(machine_name)

    def get_confirm_dialog(self, title_text, label_text, cancell_callback=None, ok_callback=None):
        """ Всплывающее окно с текстом и 2 кнопками"""
        def set_signals():
            def keyboard_navigation(event):
                if event.event() == Qt.Key_Left:
                    dialog.Ok.setFocus()
            dialog.accepted.connect(ok_callback)
            dialog.rejected.connect(cancell_callback)
            dialog.rejected.connect(lambda: window.close())
            window.finished.connect(cancell_callback)
            window.keyPressEvent(lambda x: keyboard_navigation(x))
        ok_button, cancell_button = QDialogButtonBox.Ok, QDialogButtonBox.Cancel
        window = AbstractDialog(self.instance, buttons=(ok_button, cancell_button,))
        h_layout = QVBoxLayout(window)
        window.setFocus()
        label = QLabel(window)
        h_layout.addWidget(label)
        label.setText(label_text)
        dialog = QDialogButtonBox(label)
        h_layout.addWidget(dialog)
        dialog.setStandardButtons(ok_button | cancell_button)
        window.setWindowTitle(title_text)
        set_signals()
        return window

    @staticmethod
    def get_current__q_list_widget_item(widget: QListWidget) -> QListWidgetItem:
        return widget.currentItem()

    def _lock_ui(self):
        self.main_ui.root_tab_widget.setDisabled(True)

    def _unlock_ui(self):
        self.main_ui.root_tab_widget.setEnabled(True)
