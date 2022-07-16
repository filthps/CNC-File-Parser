import re
from typing import Optional, Iterable
from PySide2.QtGui import QColor, QPalette
from PySide2.QtWidgets import QLineEdit, QWidget, QRadioButton
from gui.ui import Ui_main_window


class Validator:
    REQUIRED_RADIO_BUTTONS: dict[str, Iterable[str]] = {}  # Ключ - имя GroupBox, значение - кортеж из кнопок radio, только одна кнопка должна быть enabled
    INVALID_TEXT_FIELD_VALUES: dict[str, re] = {}  # Ключи определяют перечень участвующих в валидации полей c текстовым содержимым, значение - регулярка, отображающая "плохое" значение

    def __init__(self, ui: Ui_main_window):
        self.ui = ui
        self._is_valid = False

    @property
    def is_valid(self):
        return self._is_valid

    @staticmethod
    def set_not_complete_edit_attributes(name: str, widget: QWidget):
        widget.setStyleSheet(f"#{name} {{border: 1px solid rgba(194, 107, 107, 1);}}")
        widget.setToolTip("Закончите редактирование. Заполните обязательные поля.")

    @staticmethod
    def set_complete_edit_attributes(widget) -> None:
        widget.setStyleSheet("")
        widget.setToolTip(None)

    @staticmethod
    def set_invalid_text_field(field: QLineEdit):
        field.setStyleSheet("border: 1px solid rgba(194, 107, 107, 1);")

    @staticmethod
    def set_valid_text_field(field: QLineEdit):
        field.setStyleSheet("")

    def refresh(self) -> bool:
        valid = True
        if self.INVALID_TEXT_FIELD_VALUES:
            for field_name, reg in self.INVALID_TEXT_FIELD_VALUES.items():
                field = getattr(self.ui, field_name, None)
                if field is not None:
                    result = re.fullmatch(reg, field.text())
                    if result:
                        self.set_invalid_text_field(field)
                        valid = False
                    else:
                        self.set_valid_text_field(field)
        if self.REQUIRED_RADIO_BUTTONS:
            for group_box_name, buttons in self.REQUIRED_RADIO_BUTTONS.items():
                result = set()
                for button_name in buttons:
                    button: Optional[QRadioButton] = getattr(self.ui, button_name, None)
                    if button is not None:
                        button_is_enabled = button.isChecked()
                        result.add(int(button_is_enabled))
                box = getattr(self.ui, group_box_name, None)
                is_valid_box = bool(sum(result))
                if box is not None:
                    if is_valid_box:
                        self.set_complete_edit_attributes(box)
                    else:
                        self.set_not_complete_edit_attributes(group_box_name, box)
                if not is_valid_box:
                    valid = False
        self._is_valid = valid
        return valid
