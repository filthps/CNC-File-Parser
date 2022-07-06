import re
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QLineEdit, QTreeWidgetItem
from gui.ui import Ui_main_window


class AddMachinePageValidation:
    INVALID_VALUES = {
        "lineEdit_10": re.compile(r"|\d"),
        "lineEdit_21": re.compile(r"|\d"),
        "lineEdit_11": re.compile(r"\d"),
        "lineEdit_12": re.compile(r"\d"),
        "lineEdit_13": re.compile(r"\d"),
        "lineEdit_14": re.compile(r"\d"),
        "lineEdit_15": re.compile(r"\d"),
        "lineEdit_16": re.compile(r"\d")
    }

    def __init__(self, ui):
        self.__is_valid = False
        self.ui: Ui_main_window = ui
        self.current_machine = None

        def connect_signals():
            ui.add_machine_list_0.itemEntered.connect(lambda item: self.__select_machine(item))
            ui.add_machine_list_0.currentItemChanged.connect(lambda current, prev: self.__select_machine(current))
            ui.lineEdit_10.textChanged.connect(self.refresh)
            ui.lineEdit_21.textChanged.connect(self.refresh)
            ui.lineEdit_11.textChanged.connect(self.refresh)
            ui.lineEdit_12.textChanged.connect(self.refresh)
            ui.lineEdit_13.textChanged.connect(self.refresh)
            ui.lineEdit_14.textChanged.connect(self.refresh)
            ui.lineEdit_15.textChanged.connect(self.refresh)
            ui.lineEdit_16.textChanged.connect(self.refresh)
        connect_signals()

    @property
    def is_valid(self):
        return self.__is_valid

    @staticmethod
    def __set_not_complete_edit_attributes(widget: QTreeWidgetItem):
        widget.setBackgroundColor(QColor(204, 0, 0))
        widget.setToolTip("Закончите редактирование.")

    @staticmethod
    def __set_complete_edit_attributes(widget: QTreeWidgetItem) -> None:
        widget.setBackgroundColor(QColor(255, 255, 255))
        widget.setToolTip(None)

    @staticmethod
    def __set_invalid_text_field(field: QLineEdit):
        field.setStyleSheet("border: 1px solid red;")

    @staticmethod
    def __set_valid_text_field(field: QLineEdit):
        field.setStyleSheet("")

    def __select_machine(self, current):
        self.current_machine = current
        self.refresh()

    def refresh(self):
        valid = True
        for field_name, reg in self.INVALID_VALUES.items():
            field = getattr(self.ui, field_name)
            if field is not None:
                result = re.fullmatch(reg, field.text())
                if result:
                    self.__set_invalid_text_field(field)
                    valid = False
                else:
                    self.__set_valid_text_field(field)
        self.__is_valid = valid
        if self.current_machine is not None:
            if not valid:
                self.__set_not_complete_edit_attributes(self.current_machine)
            else:
                self.__set_complete_edit_attributes(self.current_machine)
