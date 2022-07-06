import os
from typing import Union, Iterator, Optional, Sequence
from itertools import count, cycle
from pathlib import Path
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTabWidget, QStackedWidget, QPushButton, QInputDialog, QDialogButtonBox, \
    QListWidgetItem, QListWidget, QDialog, QLabel, QVBoxLayout, QHBoxLayout, QTreeWidgetItem, QTreeWidget, QLineEdit
from PySide2.QtGui import QIcon, QCloseEvent
from gui.ui import Ui_main_window as Ui
from config import PROJECT_PATH


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
    def __init__(self, parent=None, buttons: Optional[Sequence[QPushButton]] = None, init_callback=None, close_callback=None):
        super().__init__(parent)
        if buttons is not None:
            button: QDialogButtonBox = buttons[0]
            self.__set_active(button)
        buttons = list(buttons)
        left_orientation = buttons
        left_orientation.reverse()
        self._left = cycle(left_orientation)
        self._right = cycle(buttons)
        self._close_callback = close_callback
        self._open_callback = init_callback

    def set_close_callback(self, value):
        self._close_callback = value

    def set_open_callback(self, value):
        self._open_callback = value

    def keyPressEvent(self, event):
        if event == Qt.Key_Left:
            button = self.__get_button(self._left)
            self.__set_active(button)
        if event == Qt.Key_Right:
            button = self.__get_button(self._right)
            self.__set_active(button)

    def closeEvent(self, event) -> None:
        self._close_callback() if self._close_callback else None

    def showEvent(self, event) -> None:
        self._open_callback() if self._open_callback else None

    @staticmethod
    def __get_button(buttons: cycle):
        return next(buttons)

    @staticmethod
    def __set_active(button: QDialogButtonBox):
        # button.setFocus() todo
        ...


class Constructor:
    DEFAULT_PATH = os.path.abspath(os.sep)

    def __init__(self, instance, ui: Ui):
        self.instance = instance
        self.main_ui = ui

    def get_alert_dialog(self, title_text, label_text="", callback=None):
        """ Всплывающее окно с текстом и  кнопкой
        ░░░░██████████████████████████░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░██████░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██████████████████████████░░
        """
        def set_signals():
            dialog.accepted.connect(callback)
            dialog.rejected.connect(lambda: window.close())
        ok_button = QDialogButtonBox.Ok
        window = AbstractDialog(self.instance, buttons=(ok_button,),
                                close_callback=self._unlock_ui, init_callback=self._lock_ui)
        h_layout = QVBoxLayout(window)
        window.setFocus()
        label = QLabel(window)
        h_layout.addWidget(label)
        label.setText(label_text)
        dialog = QDialogButtonBox(label)
        h_layout.addWidget(dialog)
        dialog.setStandardButtons(ok_button)
        window.setWindowTitle(title_text)
        set_signals()
        return window

    def get_prompt_dialog(self, title_text, label_text="", cancel_callback=None, ok_callback=None) -> Optional[QListWidgetItem]:
        """ Всплывающее окно с текстом, 2 кнопками и полем ввода
        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
        ░░░░░░░░████████████████████░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░████████████░░██░░░░
        ░░░░░░░░██░░██░░░░░░░░██░░██░░░░
        ░░░░░░░░██░░████████████░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░████░░░░████░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░████████████████████░░░░
        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
        """
        def get_value():
            value = input_.text()
            if value:
                return ok_callback(input_.text())

        def set_signals():
            dialog.accepted.connect(get_value if ok_callback is not None else None)
            dialog.rejected.connect(cancel_callback)
            dialog.rejected.connect(lambda: window.close())
        input_ = QLineEdit()
        ok_button, cancel_button = QDialogButtonBox.Ok, QDialogButtonBox.Cancel
        window = AbstractDialog(self.instance, buttons=(ok_button, cancel_button))
        window.set_open_callback(self._lock_ui)
        window.set_close_callback(self._unlock_ui)
        window.setWindowTitle(title_text)
        v_layout = QVBoxLayout(window)
        v_layout.addWidget(input_)
        if label_text:
            label = QLabel()
            label.setText(label_text)
            dialog = QDialogButtonBox(label)
        else:
            dialog = QDialogButtonBox(input_)
        v_layout.addWidget(dialog)
        dialog.setStandardButtons(ok_button | cancel_button)
        set_signals()
        return window

    def get_confirm_dialog(self, title_text, label_text, cancel_callback=None, ok_callback=None):
        """ Всплывающее окно с текстом и 2 кнопками
        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
        ░░░░░░░░████████████████████░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░████░░░░████░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░████████████████████░░░░
        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
        """
        def set_signals():
            dialog.accepted.connect(ok_callback)
            dialog.rejected.connect(cancel_callback)
            dialog.rejected.connect(lambda: window.close())
            window.finished.connect(cancel_callback)
        ok_button, cancel_button = QDialogButtonBox.Ok, QDialogButtonBox.Cancel
        window = AbstractDialog(self.instance, buttons=(ok_button, cancel_button,),
                                close_callback=self._unlock_ui, init_callback=self._lock_ui)

        h_layout = QVBoxLayout(window)
        window.setFocus()
        label = QLabel(window)
        h_layout.addWidget(label)
        label.setText(label_text)
        dialog = QDialogButtonBox(label)
        h_layout.addWidget(dialog)
        dialog.setStandardButtons(ok_button | cancel_button)
        window.setWindowTitle(title_text)
        set_signals()
        return window

    def get_folder_choice_dialog(self, window_title="", cancel_callback=None, ok_callback=None):
        """ Вабор файла в дереве каталогов
        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
        ░░████████████████████████████░░
        ░░██░░░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░██░░░░░░░░░░████░░░░░░░░░░██░░
        ░░██░░████░░░░░░░░░░░░░░░░░░██░░
        ░░██░░░░░░░░░░████░░░░░░░░░░██░░
        ░░██░░░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░██░░████░░░░████░░░░░░░░░░██░░
        ░░██░░░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░██░░░░░░░░░░████░░░░░░░░░░██░░
        ░░██░░░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░██░░░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░██░░██████░░░░░░░░██████░░██░░
        ░░██░░░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░████████████████████████████░░
        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
        """
        current_column = 0
        ok_button, cancel_button = QDialogButtonBox.Ok, QDialogButtonBox.Cancel
        window = AbstractDialog(self.instance, buttons=(ok_button, cancel_button,),
                                close_callback=self._unlock_ui, init_callback=self._lock_ui)
        v_box = QVBoxLayout(window)
        window.setFocus()
        window.setWindowTitle(window_title)
        tree = QTreeWidget(window)
        buttons = QDialogButtonBox(tree)
        ok_button, cancel_button = QDialogButtonBox.Ok, QDialogButtonBox.Cancel
        buttons.setStandardButtons(ok_button | cancel_button)
        v_box.addWidget(tree)
        v_box.addWidget(buttons)

        def create_items(path, level):
            dirs = os.listdir(path)
            for dir_ in dirs:
                item = QTreeWidgetItem()
                yield item
                item.setText(level, os.path.join(self.DEFAULT_PATH, dir_))

        def add_items(item: Union[QTreeWidgetItem, str], level=current_column):
            def get_full_path():
                nonlocal current_column
                path = []
                item_ = item
                while item_ is not None:
                    path.append(item_.text(level))
                    item_ = item_.parent()
                current_column += 1
                return os.path.join(*path)
            items = create_items(item if isinstance(item, str) else get_full_path(), level)
            tree.addTopLevelItems(tuple(items))

        def accept_folder():
            accepted_item: QListWidgetItem = tree.currentItem()
            self._unlock_ui()
            window.close()
            return ok_callback(accepted_item.text(current_column))

        def set_signals():
            buttons.accepted.connect(accept_folder if ok_callback is not None else None)
            buttons.rejected.connect(cancel_callback)
            buttons.rejected.connect(lambda: window.close())
            tree.itemDoubleClicked.connect(lambda obj, level: add_items(obj, level))
        add_items(self.DEFAULT_PATH)
        set_signals()
        return window

    @staticmethod
    def get_current__q_list_widget_item(widget: QListWidget) -> QListWidgetItem:
        return widget.currentItem()

    def _lock_ui(self):
        self.main_ui.root_tab_widget.setDisabled(True)

    def _unlock_ui(self):
        self.main_ui.root_tab_widget.setEnabled(True)
