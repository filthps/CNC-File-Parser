import re
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QLineEdit, QWidget, QRadioButton, QComboBox
from gui.ui import Ui_main_window


class Validator:
    REQUIRED_COMBO_BOX: tuple = tuple()  # имя ComboBox, - не может быть пустым
    REQUIRED_RADIO_BUTTONS: dict[str, tuple[str, str]] = {}  # Ключ - groupbox_name,  Во внутреннем коретеже одна из кнопок должна быть enabled
    COMBO_BOX_DEFAULT_VALUES: dict[str, str] = {}  # Ключ - имя ComboBox, значение - текст в item по умолчанию
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
    def set_not_complete_edit_attributes(widget: QWidget) -> None:
        widget.setBackground(QColor("#e86666"))
        widget.setToolTip("Закончите редактирование. Заполните обязательные поля.")

    @staticmethod
    def set_complete_edit_attributes(widget: QWidget) -> None:
        widget.setBackground(QColor("#FFF"))
        widget.setToolTip(None)

    @staticmethod
    def set_invalid_text_field(field: QLineEdit) -> None:
        field.setStyleSheet("border: 1px solid rgb(194, 107, 107);")

    @staticmethod
    def set_valid_text_field(field: QLineEdit) -> None:
        field.setStyleSheet("")

    @staticmethod
    def set_invalid_radio_button(filed: QRadioButton):
        filed.setStyleSheet("color: rgb(194, 107, 107);")

    @staticmethod
    def set_valid_radio_button(field: QRadioButton):
        field.setStyleSheet("")

    def refresh(self) -> bool:
        valid = True
        invalid_text_fields = []
        
        if self.REQUIRED_TEXT_FIELD_VALUES:
            for input_name in self.REQUIRED_TEXT_FIELD_VALUES:
                input_: QWidget = getattr(self.ui, input_name)
                if not input_.text():
                    self.set_invalid_text_field(input_)
                    valid = False
                    invalid_text_fields.append(input_name)
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
                        invalid_text_fields.append(field_name)
                    else:
                        self.set_valid_text_field(field) if field_name not in invalid_text_fields else None
        if self.REQUIRED_RADIO_BUTTONS:
            for group_box_name, buttons_group in self.REQUIRED_RADIO_BUTTONS.items():
                i = 0
                for button in buttons_group:
                    button: QRadioButton = getattr(self.ui, button)
                    if button.isChecked():
                        i += 1
                group_box = getattr(self.ui, group_box_name, None)
                if i != 1:
                    valid = False
                    if group_box:
                        self.set_invalid_text_field(group_box)
                    for button in buttons_group:
                        button: QRadioButton = getattr(self.ui, button)
                        self.set_invalid_radio_button(button)
                else:
                    if group_box:
                        self.set_valid_text_field(group_box)
                    for button in buttons_group:
                        button: QRadioButton = getattr(self.ui, button)
                        self.set_valid_radio_button(button)
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
