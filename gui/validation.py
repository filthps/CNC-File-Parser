import re
from typing import Optional, Iterable
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QLineEdit, QWidget, QRadioButton, QComboBox
from gui.ui import Ui_main_window


class Validator:
    REQUIRED_COMBO_BOX: tuple = tuple()  # имя ComboBox, - не может быть пустым
    COMBO_BOX_DEFAULT_VALUES: dict[str, str] = {}  # Ключ - имя ComboBox, значение - текст в item по умолчанию
    REQUIRED_RADIO_BUTTONS: dict[str, Iterable[str]] = {}  # Ключ - имя GroupBox, значение - кортеж из кнопок radio, только одна кнопка должна быть enabled
    REQUIRED_TEXT_FIELD_VALUES: tuple = tuple()  # Кортеж имен инпутов, значения которых не могут быть пустыми
    INVALID_TEXT_FIELD_VALUES: dict[str, re.Pattern] = {}  # Ключи определяют перечень участвующих в валидации полей c текстовым содержимым, значение - регулярка, отображающая "плохое" значение
    INVALID_TEXT: dict[str, str] = {}  # Словарь - имя виджета: текст-подсказка к неправильному полю

    def __init__(self, ui: Ui_main_window):
        self.ui = ui
        self._is_valid = False

    @property
    def is_valid(self):
        return self._is_valid

    @staticmethod
    def set_not_complete_edit_attributes(name: str, widget: QWidget) -> None:
        widget.setBackground(QColor("#e86666"))
        widget.setToolTip("Закончите редактирование. Заполните обязательные поля.")

    @staticmethod
    def set_complete_edit_attributes(widget) -> None:
        widget.setBackground(QColor("#FFF"))
        widget.setToolTip(None)

    @staticmethod
    def set_invalid_text_field(field: QLineEdit) -> None:
        field.setStyleSheet("border: 1px solid rgb(194, 107, 107);")

    @staticmethod
    def set_valid_text_field(field: QLineEdit) -> None:
        field.setStyleSheet("")

    def refresh(self, input_name: Optional[str] = None) -> bool:
        valid = True
        if input_name is not None:
            #  Способ функционирования №1 - передаём имя проверямоего поля
            input_: QWidget = getattr(self.ui, input_name, None)
            if input_ is None:
                raise ValueError("Валидатор не нашёл в UI поле, которое ему передали на валидацию")
            input_text = input_.text()
            if input_name in self.REQUIRED_TEXT_FIELD_VALUES:
                if not input_text:
                    self.set_invalid_text_field(input_)
                    valid = False
                else:
                    self.set_valid_text_field(input_)
            if input_name in self.INVALID_TEXT_FIELD_VALUES:
                regex_obj: re.Pattern = self.INVALID_TEXT_FIELD_VALUES[input_name]
                match_obj: Optional[re.Match] = regex_obj.search(input_text)
                if match_obj is not None and match_obj.group():
                    self.set_invalid_text_field(input_)
                    valid = False
                else:
                    self.set_valid_text_field(input_)
            self._is_valid = valid
            return valid
        #  Способ функционирования №2 - Обход всех полей, если именованный аргумент не был передан
        if self.REQUIRED_TEXT_FIELD_VALUES:
            for input_name in self.REQUIRED_TEXT_FIELD_VALUES:
                input_: QWidget = getattr(self.ui, input_name)
                if not input_.text():
                    self.set_invalid_text_field(input_)
                    valid = False
                else:
                    self.set_valid_text_field(input_)
        if self.INVALID_TEXT_FIELD_VALUES:
            for field_name, reg in self.INVALID_TEXT_FIELD_VALUES.items():
                field: QWidget = getattr(self.ui, field_name, None)
                if field is not None:
                    result = reg.search(field.text())
                    if result is not None:
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
        if self.REQUIRED_COMBO_BOX:
            for field_name in self.REQUIRED_COMBO_BOX:
                field: QComboBox = getattr(self.ui, field_name, None)
                if field is not None:
                    if not field.currentText():
                        self.set_invalid_text_field(field)
                        valid = False
                    else:
                        self.set_valid_text_field(field)
        if self.COMBO_BOX_DEFAULT_VALUES:
            for field_name, base_value in self.COMBO_BOX_DEFAULT_VALUES.items():
                field: QComboBox = getattr(self.ui, field_name, None)
                if field is not None:
                    if field.currentText() == base_value:
                        self.set_invalid_text_field(field)
                        valid = False
                    else:
                        self.set_valid_text_field(field)
        self._is_valid = valid
        return valid
