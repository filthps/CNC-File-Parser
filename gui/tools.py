import os
from typing import Union, Iterator, Optional, Sequence
from itertools import count, cycle
from pathlib import Path
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTabWidget, QStackedWidget, QPushButton, QInputDialog, QDialogButtonBox, \
    QListWidgetItem, QListWidget, QDialog, QLabel, QVBoxLayout, QHBoxLayout, QTreeWidgetItem, QTreeWidget
from PySide2.QtGui import QIcon, QColor
from gui.ui import Ui_main_window as Ui
from config import PROJECT_PATH


class Tools:

    @staticmethod
    def set_not_complete_edit_attributes(widget) -> None:
        widget.setBackgroundColor(QColor(204, 204, 204))
        widget.setToolTip("Закончите редактирование.")

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
    DEFAULT_PATH = os.path.abspath(os.sep)

    def __init__(self, instance, ui: Ui):
        self.instance = instance
        self.main_ui = ui

    def is_valid(self):
        ...

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

    def get_folder_choice_dialog(self, window_title="", cancell_callback=None, ok_callback=None):
        window = QDialog()
        v_box = QVBoxLayout(window)
        window.setFocus()
        window.setWindowTitle(window_title)
        tree = QTreeWidget(window)
        buttons = QDialogButtonBox(tree)
        ok_button, cancell_button = QDialogButtonBox.Ok, QDialogButtonBox.Cancel
        buttons.setStandardButtons(ok_button | cancell_button)
        v_box.addWidget(tree)
        v_box.addWidget(buttons)

        def create_items(path, level):
            dirs = os.listdir(path)
            for dir_ in dirs:
                item = QTreeWidgetItem()
                item.setText(level, os.path.join(self.DEFAULT_PATH, dir_))
                yield item

        def add_items(item: Union[QTreeWidgetItem, str], level=0):
            def get_full_path():
                path = []
                item_ = item
                while item_ is not None:
                    path.append(item_.text(level))
                    item_ = item_.parent()
                return os.path.join(*path)
            items = create_items(item if isinstance(item, str) else get_full_path(), level)
            tree.addTopLevelItems(tuple(items))

        def accept_folder():
            accepted_item = tree.currentItem()
            print(accepted_item)

        def reject():
            window.close()
            self._unlock_ui()

        def set_signals():
            buttons.accepted.connect(accept_folder)
            buttons.rejected.connect(lambda: reject)
            window.rejected.connect(lambda: reject)
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
