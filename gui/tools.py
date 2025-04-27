import os
from typing import Union, Iterator, Optional, Sequence
from itertools import count, cycle, repeat
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QPushButton, QDialogButtonBox,\
    QDialog, QLabel, QVBoxLayout, QLineEdit, \
    QComboBox, QRadioButton
from PySide2.QtGui import QIcon
from gui.ui import Ui_main_window as Ui
from two_m_root.orm import ResultORMItem, ResultORMCollection


class Tools:
    ui = None
    UI__TO_SQL_COLUMN_LINK__LINE_EDIT = {}
    UI__TO_SQL_COLUMN_LINK__COMBO_BOX = {}
    UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON: dict[str, dict[str, bool]] = {}
    COMBO_BOX_DEFAULT_VALUES = {}
    RADIO_BUTTON_DEFAULT_VALUES: dict = {}
    LINE_EDIT_DEFAULT_VALUES = {}
    INTEGER_FIELDS = tuple()
    STRING_FIELDS = tuple()
    FLOAT_FIELDS = tuple()
    NULLABLE_FIELDS = tuple()
    models = tuple()  # Указывать только для тех страниц, где join_select

    def update_fields(self, data: dict, set_all_radio_buttons=False) -> None:
        """ Обновление содержимого полей согласно данным, которые пришли из орм.
        Данный метод подразумевает использование на страничках, где используются одиночные запросы.
        :arg data: входящий объект с данными
        :arg set_all_radio_buttons: True - устанавливать вcе кнопки, а не только ту, что True
        """
        if type(data) is not dict:
            raise TypeError
        if not isinstance(set_all_radio_buttons, bool):
            raise TypeError
        reversed_line_edit_data = self.__reverse_ui_to_sql_dict(self.UI__TO_SQL_COLUMN_LINK__LINE_EDIT)
        reversed_radio_button_data = self.__reverse_ui_to_sql_dict(self.UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON)
        reversed_combo_box_data = self.__reverse_ui_to_sql_dict(self.UI__TO_SQL_COLUMN_LINK__COMBO_BOX)
        for sql_column, value in data.items():
            if not reversed_line_edit_data:
                continue
            if sql_column in reversed_line_edit_data:
                if value is None:
                    continue
                ui_item_name = reversed_line_edit_data[sql_column]
                line_edit: Optional[QLineEdit] = getattr(self.ui, ui_item_name)
                line_edit.setText(str(value))
            if not reversed_radio_button_data:
                continue
            if sql_column in reversed_radio_button_data:
                ui_name = None
                if not set_all_radio_buttons:
                    if value:
                        try:
                            ui_name = reversed_radio_button_data[(sql_column, True)]
                        except KeyError:
                            ui_name = None
                if set_all_radio_buttons:
                    try:
                        ui_name = reversed_radio_button_data[(sql_column, value)]
                    except KeyError:
                        ui_name = None
                if ui_name is not None:
                    radio_button: Optional[QRadioButton] = getattr(self.ui, ui_name)
                    radio_button.setChecked(value)
            if not reversed_combo_box_data:
                continue
            if sql_column in reversed_combo_box_data:
                combo_box_name = reversed_combo_box_data[sql_column]
                q_combo_box: Optional[QComboBox] = getattr(self.ui, combo_box_name)
                if value is None:
                    if self.COMBO_BOX_DEFAULT_VALUES:
                        q_combo_box.setCurrentText(self.COMBO_BOX_DEFAULT_VALUES[combo_box_name])
                    else:
                        q_combo_box.setCurrentText("")
                    continue
                q_combo_box.setCurrentText(str(value))

    def check_output_values(self, field_name, value):
        """ Форматировать типы выходных значений перед установкой в очередь отправки """
        if field_name in self.INTEGER_FIELDS:
            if not value:
                return 0
            if type(value) is int:
                return value
            return int(value) if str.isdigit(value) else value
        if field_name in self.FLOAT_FIELDS:
            if not value:
                return float()
            if isinstance(value, float):
                return value
            return float(value) if str.isdecimal(value) else value
        if field_name in self.STRING_FIELDS:
            if not value:
                return ""
            return str(value)
        if field_name in self.NULLABLE_FIELDS:
            if not value:
                return None
        return value

    def reset_fields_to_default(self):
        for radio_button_name, value in self.RADIO_BUTTON_DEFAULT_VALUES.items():
            field: QRadioButton = getattr(self.ui, radio_button_name, None)
            field.setChecked(value)
        for combo_box_name, default_text in self.COMBO_BOX_DEFAULT_VALUES.items():
            field: QComboBox = getattr(self.ui, combo_box_name)
            field.clear()
            field.addItem(default_text)
            field.setCurrentIndex(0)
        for line_edit_name, default_value in self.LINE_EDIT_DEFAULT_VALUES.items():
            field: QLineEdit = getattr(self.ui, line_edit_name)
            field.setText(next(default_value) if isinstance(default_value, repeat) else default_value)

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

    @staticmethod
    def __reverse_ui_to_sql_dict(d: dict) -> Optional[dict]:
        """ Обычно словари для связи между полями в ui и столбцами в бд имеют вид примерно такой:
         'ui_field_radio_button_name': {'sql_field': True} или 'ui_field_line_edit_name': 'sql_name'.
         Поменяем ключи и значения местами."""
        if type(d) is not dict:
            raise TypeError
        if not d:
            return
        if isinstance(tuple(d.values())[0], dict):
            return {(k, v): key for key, value in d.items() for k, v in value.items()}
        return dict(zip(d.values(), d.keys()))


class JoinedModelTools(Tools):
    def update_fields(self, line_edit_values: Union[ResultORMItem, ResultORMCollection] = None,
                      combo_box_values: Optional[dict] = None, radio_button_values: Optional[dict] = None):
        pass

    def get_radio_button_data(self, selected_button_name) -> dict[str, [str, dict]]:
        """ Получить значения для столбцов по нажатой QRadioButton """
        data = self.UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON[selected_button_name]
        result = {}
        for model_and_column_name, value in data.items():
            model_name, column_name = model_and_column_name.split(".")
            cur_model_values = result.get(model_name, {})
            if cur_model_values:
                cur_model_values.update({column_name: value})
            else:
                result.update({model_name: {column_name: value}})
        return result


class MyAbstractDialog(QDialog):
    """
    Диалоговое окно с возможностью контроля слота нажатия клавиш клавиатуры.
    Навигация по кнопкам
    """
    def __init__(self, parent=None, buttons: Optional[Sequence[QPushButton]] = None, init_callback=None, close_callback=None):
        super().__init__(parent)
        self._left = None
        self._right = None
        if buttons is not None:
            button: QDialogButtonBox = buttons[0]
            buttons = list(buttons)
            left_orientation = buttons
            left_orientation.reverse()
            self._left = cycle(left_orientation)
            self._right = cycle(buttons)
            self.__set_active(button)
        self._close_callback = close_callback
        self._open_callback = init_callback

    def set_close_callback(self, value):
        self._close_callback = value

    def set_open_callback(self, value):
        self._open_callback = value

    def keyPressEvent(self, event):
        if event == Qt.Key_Left:
            button = self.__get_button(self._left)
            if button:
                self.__set_active(button)
        if event == Qt.Key_Right:
            button = self.__get_button(self._right)
            if button:
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
        # button.setFocus()  # todo
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
        window = MyAbstractDialog(self.instance, buttons=(ok_button,),
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

    def get_prompt_dialog(self, title_text, label_text="", cancel_callback=None, ok_callback=None) -> MyAbstractDialog:
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
            return ok_callback(input_.text())

        def set_signals():
            dialog.accepted.connect(get_value if ok_callback is not None else None)
            dialog.accepted.connect(window.close)
            dialog.rejected.connect(cancel_callback)
            dialog.rejected.connect(window.close)
        input_ = QLineEdit()
        ok_button, cancel_button = QDialogButtonBox.Ok, QDialogButtonBox.Cancel
        window = MyAbstractDialog(self.instance, buttons=(ok_button, cancel_button))
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

    def get_confirm_dialog(self, title_text, label_text=None, cancel_callback=None, ok_callback=None) -> MyAbstractDialog:
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
        window = MyAbstractDialog(self.instance, buttons=(ok_button, cancel_button,),
                                  close_callback=self._unlock_ui, init_callback=self._lock_ui)

        h_layout = QVBoxLayout(window)
        window.setFocus()
        label = None
        if label_text is not None:
            label = QLabel(window)
            h_layout.addWidget(label)
            label.setText(label_text)
        dialog = QDialogButtonBox(label)
        h_layout.addWidget(dialog)
        dialog.setStandardButtons(ok_button | cancel_button)
        window.setWindowTitle(title_text)
        set_signals()
        return window

    def _lock_ui(self):
        self.main_ui.root_tab_widget.setDisabled(True)

    def _unlock_ui(self):
        self.main_ui.root_tab_widget.setEnabled(True)
