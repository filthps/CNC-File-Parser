import re
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QLineEdit, QWidget
from gui.ui import Ui_main_window


class Validator:
    INVALID_VALUES = {}  # Ключи определяют перечень участвующих в валидации полей

    def __init__(self, ui: Ui_main_window):
        self.ui = ui
        self._is_valid = False

    @property
    def is_valid(self):
        return self._is_valid

    @staticmethod
    def set_not_complete_edit_attributes(widget: QWidget):
        widget.setBackgroundColor(QColor(194, 107, 107))
        widget.setToolTip("Закончите редактирование. Заполните обязательные поля.")

    @staticmethod
    def set_complete_edit_attributes(widget) -> None:
        widget.setBackgroundColor(QColor(255, 255, 255))
        widget.setToolTip(None)

    @staticmethod
    def set_invalid_text_field(field: QLineEdit):
        field.setStyleSheet("border: 1px solid red;")

    @staticmethod
    def set_valid_text_field(field: QLineEdit):
        field.setStyleSheet("")

    def refresh(self) -> bool:
        if self.INVALID_VALUES:
            valid = True
            for field_name, reg in self.INVALID_VALUES.items():
                field = getattr(self.ui, field_name)
                if field is not None:
                    result = re.fullmatch(reg, field.text())
                    if result:
                        self.set_invalid_text_field(field)
                        valid = False
                    else:
                        self.set_valid_text_field(field)
            self._is_valid = valid
        return valid
        

class AddMachinePageValidation(Validator):
    INVALID_VALUES = {
        "lineEdit_10": re.compile(r"|\d"),
        "lineEdit_21": re.compile(r"|\d"),
        "lineEdit_11": re.compile(r"\D"),
        "lineEdit_12": re.compile(r"\D"),
        "lineEdit_13": re.compile(r"\D"),
        "lineEdit_14": re.compile(r"\D"),
        "lineEdit_15": re.compile(r"\D"),
        "lineEdit_16": re.compile(r"\D"),
    }

    def __init__(self, ui):
        super().__init__(ui)
        self._is_valid = False
        self.ui: Ui_main_window = ui
        self.current_machine = None

        def connect_signals():
            ui.add_machine_list_0.itemEntered.connect(lambda item: self.__select_machine(item, None))
            ui.add_machine_list_0.currentItemChanged.connect(lambda current, prev: self.__select_machine(prev, current))
            ui.lineEdit_10.textChanged.connect(self.refresh)
            ui.lineEdit_21.textChanged.connect(self.refresh)
            ui.lineEdit_11.textChanged.connect(self.refresh)
            ui.lineEdit_12.textChanged.connect(self.refresh)
            ui.lineEdit_13.textChanged.connect(self.refresh)
            ui.lineEdit_14.textChanged.connect(self.refresh)
            ui.lineEdit_15.textChanged.connect(self.refresh)
            ui.lineEdit_16.textChanged.connect(self.refresh)
        connect_signals()

    def __select_machine(self, prev, current):
        if prev is not None:
            self.set_complete_edit_attributes(prev)
        self.current_machine = current
        self.refresh()

    def refresh(self):
        valid = super().refresh()
        if self.current_machine is not None:
            if not valid:
                self.set_not_complete_edit_attributes(self.current_machine)
            else:
                self.set_complete_edit_attributes(self.current_machine)
