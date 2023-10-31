import itertools
import re
import uuid
from typing import Optional, Union, Iterator, Iterable
from types import SimpleNamespace
from PySide2.QtWidgets import QButtonGroup, QMainWindow, QListWidget, QListWidgetItem, QHBoxLayout, \
    QVBoxLayout, QGroupBox, QLineEdit, QRadioButton, QDialogButtonBox, QSpacerItem, QTextBrowser, QLabel, QFormLayout
from PySide2.QtCore import Slot, Qt
from PySide2.QtGui import QSyntaxHighlighter, QColor
from gui.tools import Tools, Constructor, MyAbstractDialog
from database.models import Condition, HeadVarible, HeadVarDelegation, SearchString
from gui import orm
from gui.ui import Ui_main_window as Ui
from gui.validation import Validator
from gui.threading_ import QThreadInstanceDecorator


class Highlighter(QSyntaxHighlighter):  # todo: или реализовать пояснения через это, вместо html+css
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def rehighlight(self) -> None:
        pass


class InputTools:
    @staticmethod
    @Slot()
    def to_upper_case(input_: QLineEdit, text: str):
        cursor_position: int = input_.cursorPosition()
        input_.setText(text.upper())
        input_.setCursorPosition(cursor_position)


class AddConditionDialog(MyAbstractDialog, InputTools):
    """
    Диалоговое окно для добавления 'условия' с вариантами выбора: 1) Поиск по вводимой строке; 2) Поиск по значению
    переменной.
    """
    EMPTY_VARIBLES_TEXT = "<Переменные не найдены>"

    def __init__(self, db: orm.ORMHelper, app: Optional["ConditionsPage"] = None, callback=None):
        self.ui = SimpleNamespace()
        self.ui.accept_button = QDialogButtonBox.Apply
        self.ui.button_box = QDialogButtonBox(self.ui.accept_button, orientation=Qt.Orientation.Horizontal)
        self.ui.button_box.setDisabled(True)
        self.ui.head_varible_area = None
        self.ui.string_input = None
        self.ui.set_string_button = None
        self.ui.set_varible_button = None
        self.ui.string_help_text = None
        self.ui.sep_input = None
        self.ui.ignore_input = None
        self.ui.ignore_box = None
        self.ui.sep_box = None
        self.ui.disable_separating_button = None
        self.ui.disable_ignore_substring_button = None
        self.ui.enable_separating_button = None
        self.ui.enable_ignore_substring_button = None
        self.ui.main_buttons_group = None
        super().__init__(parent=app.app, close_callback=callback, buttons=(self.ui.accept_button,))
        self.conditions_page: Optional["ConditionsPage"] = app
        self.db = db
        self.create_dialog_ui()
        self.connect_signals()
        self.show()

    def create_dialog_ui(self):
        self.setWindowTitle("Проверяемая строка")
        main_button_grop = QButtonGroup()
        self.ui.main_buttons_group = main_button_grop
        main_horizontal_layout = QVBoxLayout()
        horizontal_box_layout = QHBoxLayout()
        separator_form = QFormLayout()
        separator_input = QLineEdit()
        separator_input.setDisabled(True)
        separator_input.setMaximumWidth(20)
        separator_input.setMaxLength(1)
        separator_label = QLabel("Разделитель:")
        separator_form.addRow(separator_label, separator_input)
        sep_v_layout = QVBoxLayout()
        radio_button_search_string = QRadioButton("Выделить участок разделителем")
        sep_v_layout.addWidget(radio_button_search_string)
        sep_v_layout.addLayout(separator_form)
        box = QGroupBox()
        box.setTitle("Что следует проверять")
        substr_box = QGroupBox()
        substr_box.setDisabled(True)
        substr_box.setTitle("Что искать")
        remove_ignore_items = QRadioButton("Искать строку полностью")
        remove_ignore_items.setChecked(True)
        ignore_sep_vertical_layout = QVBoxLayout()
        set_ignore_items = QRadioButton("Указать игнорируемый участок")
        ignore_sep_vertical_layout.addWidget(set_ignore_items)
        ignore_place_form = QFormLayout()
        ignore_symbols_separator_input = QLineEdit()
        ignore_symbols_separator_input.setDisabled(True)
        ignore_symbols_separator_input.setMaximumWidth(20)
        ignore_symbols_separator_input.setMaxLength(1)
        ignore_sep_vertical_layout.addLayout(ignore_place_form)
        ignore_pace_label = QLabel("Разделитель:")
        ignore_place_form.addRow(ignore_pace_label, ignore_symbols_separator_input)
        ignore_place_box = QGroupBox()
        ignore_place_box.setDisabled(True)
        ignore_place_box.setTitle("Что игнорировать")
        ignore_place_h_layout = QHBoxLayout()
        ignore_place_h_layout.addWidget(remove_ignore_items)
        ignore_place_h_layout.addLayout(ignore_sep_vertical_layout)
        ignore_place_box.setLayout(ignore_place_h_layout)
        search_by_string = QRadioButton("По введённой строке")
        main_button_grop.addButton(search_by_string)
        choice_sep_layout = QHBoxLayout()
        radio_button_search_full_text = QRadioButton("Искать строку полностью")
        radio_button_search_full_text.setChecked(True)
        choice_sep_layout.addWidget(radio_button_search_full_text)
        choice_sep_layout.addLayout(sep_v_layout)
        choice_sep_layout.addLayout(separator_form)
        substr_box.setLayout(choice_sep_layout)
        substr_box.setLayout(sep_v_layout)
        condition_string_input = QLineEdit()
        condition_string_input.setDisabled(True)
        desc = QTextBrowser()
        desc.setHtml(f"<p>Введите строку полностью, а внутри неё, при помощи символов <p style = 'color: #D05932'><ins>*<p style = 'color: #333'>, <p style = 'color: #333'>цель проверки, - то что будет проверяться."
                     "<p>Например:"
                     f"<p style = 'color: #074E67'><dfn> G1 X100 Y100 F <p style ='color: #D05932'>*2500*<p style = 'color: #D05932'><br><ins>2500</p><p style = 'color: #333'> - можно с чём-нибудь сравнить, или сопоставить."
                     )
        desc.setStyleSheet("p {display: inline-block; font-family: Times, serif; color: #333; word-break: normal;}")  # todo: разобраться здесь
        desc.setDisabled(True)
        self.ui.string_help_text = desc
        vertical_layout_search_string = QVBoxLayout()
        vertical_layout_search_string.addWidget(search_by_string)
        vertical_layout_search_string.addWidget(substr_box)
        vertical_layout_search_string.addWidget(ignore_place_box)
        vertical_layout_search_string.addWidget(condition_string_input)
        vertical_layout_search_string.addWidget(desc)
        vertical_layout_search_string.addSpacerItem(QSpacerItem(0, 200))
        vertical_layout_set_head_varible = QVBoxLayout()
        radio_button_set_headvar = QRadioButton("Искать значение переменной:")
        main_button_grop.addButton(radio_button_set_headvar)
        head_varible_area = QListWidget()
        head_varible_area.setDisabled(True)
        vertical_layout_set_head_varible.addWidget(radio_button_set_headvar)
        vertical_layout_set_head_varible.addWidget(head_varible_area)
        horizontal_box_layout.addLayout(vertical_layout_search_string)
        horizontal_box_layout.addLayout(vertical_layout_set_head_varible)
        box.setLayout(horizontal_box_layout)
        main_horizontal_layout.addWidget(box)
        self.setLayout(main_horizontal_layout)
        self.ui.head_varible_area = head_varible_area
        self.ui.string_input = condition_string_input
        self.ui.set_string_button = search_by_string
        self.ui.set_varible_button = radio_button_set_headvar
        self.ui.sep_input = separator_input
        self.ui.ignore_box = ignore_place_box
        self.ui.sep_box = substr_box
        self.ui.ignore_input = ignore_symbols_separator_input
        self.ui.disable_separating_button = radio_button_search_full_text
        self.ui.disable_ignore_substring_button = remove_ignore_items
        self.ui.enable_separating_button = radio_button_search_string
        self.ui.enable_ignore_substring_button = set_ignore_items
        buttons_layout = QHBoxLayout()
        buttons_layout.addSpacerItem(QSpacerItem(300, 0))
        buttons_layout.addWidget(self.ui.button_box)
        buttons_layout.addSpacerItem(QSpacerItem(300, 0))
        main_horizontal_layout.addLayout(buttons_layout)

    def connect_signals(self):
        def toggle_disable_state_for_all(current_enabled: Iterable[Union[QLineEdit, QListWidget]]):
            self.ui.head_varible_area.setDisabled(True)
            self.ui.string_input.setDisabled(True)
            self.ui.sep_box.setDisabled(True)
            self.ui.string_help_text.setDisabled(True)
            self.ui.ignore_box.setDisabled(True)
            self.ui.sep_input.setDisabled(True)
            self.ui.ignore_input.setDisabled(True)
            self.ui.disable_separating_button.setChecked(True)
            self.ui.disable_ignore_substring_button.setChecked(True)
            [i.setDisabled(False) for i in current_enabled]
        self.ui.set_varible_button.toggled.connect(self.clear_form)
        self.ui.set_string_button.toggled.connect(self.clear_form)
        self.ui.set_varible_button.toggled.connect(lambda: toggle_disable_state_for_all([self.ui.head_varible_area]))
        self.ui.set_string_button.toggled.connect(lambda: toggle_disable_state_for_all([self.ui.sep_box, self.ui.ignore_box,
                                                                                        self.ui.string_input, self.ui.string_help_text,
                                                                                        self.ui.ignore_box, self.ui.sep_box]))
        self.ui.sep_input.textChanged.connect(lambda val: self._is_valid_separator_input(val, self.ui.ignore_input.text()))
        self.ui.ignore_input.textChanged.connect(lambda v: self._is_valid_separator_input(v, self.ui.sep_input.text()))
        self.ui.disable_separating_button.toggled.connect(self._disable_or_enable_substring_separator_input)
        self.ui.disable_ignore_substring_button.toggled.connect(self._disable_or_enable_ignore_substring_separator_input)
        self.ui.disable_separating_button.toggled.connect(self._string_input_validation_by_select_substring_field)
        self.ui.disable_ignore_substring_button.toggled.connect(self._string_input_validation_by_select_substring_field)
        self.ui.enable_separating_button.toggled.connect(
            lambda: self._disable_or_enable_substring_separator_input(hidden=False)
        )
        self.ui.enable_ignore_substring_button.toggled.connect(
            lambda: self._disable_or_enable_ignore_substring_separator_input(hidden=False)
        )
        self.ui.string_input.textChanged.connect(self._string_input_validation_by_select_substring_field)
        self.ui.head_varible_area.itemChanged.connect(lambda item: self._head_varible_validation(item))
        self.ui.set_varible_button.toggled.connect(self.load_head_varibles)
        self.ui.button_box.clicked.connect(self.add_new_condition_item)
        if self.conditions_page.ui.radioButton_28.isChecked():
            self.ui.string_input.textEdited.connect(lambda val: self.to_upper_case(self.ui.string_input, val))

    @Slot()
    def _string_input_validation_by_select_substring_field(self):
        def check_invalid_separators_ordering() -> bool:
            """ / - ignore_sep, * - sep  st*r/it45g*n/g """
            if not separator or not ignore_separator:
                return True
            string_by_target_separator = self._get_condition_substring(separator)
            string_by_ignore_separator = self._get_condition_substring(ignore_separator)
            if ignore_separator in string_by_target_separator:
                return False
            if separator in string_by_ignore_separator:
                return False
            return True
        inner_text = self.ui.string_input.text()
        separator = self.ui.sep_input.text()
        ignore_separator = self.ui.ignore_input.text()
        if not inner_text:
            self.ui.button_box.setDisabled(True)
            return
        if self.ui.enable_separating_button.isChecked():
            if sum(map(lambda s: 1 if s == separator else 0, inner_text)) != 2:
                self.ui.button_box.setDisabled(True)
                return
            if not self._is_valid_separator_input(separator, ignore_separator, from_signal=False):
                self.ui.button_box.setDisabled(True)
                return
        if self.ui.enable_ignore_substring_button.isChecked():
            if sum(map(lambda x: 1 if x == ignore_separator else 0, inner_text)) != 2:
                self.ui.button_box.setDisabled(True)
                return
            if not self._is_valid_separator_input(ignore_separator, separator, from_signal=False):
                self.ui.button_box.setDisabled(True)
                return
        if self.ui.enable_separating_button.isChecked() and self.ui.enable_ignore_substring_button.isChecked():
            if not check_invalid_separators_ordering():
                self.ui.button_box.setDisabled(True)
                return
        self.ui.button_box.setDisabled(False)

    @Slot()
    def _head_varible_validation(self, item: Optional[QListWidgetItem]):
        if not item:
            self.ui.button_box.setDisabled(True)
            return
        item_text = item.text()
        if not item_text:
            self.ui.button_box.setDisabled(True)
            return
        if item_text == self.EMPTY_VARIBLES_TEXT:
            self.ui.button_box.setDisabled(True)
            return
        self.ui.button_box.setDisabled(False)

    @Slot()
    def _is_valid_separator_input(self, value, other_sep_input_value, from_signal=True) -> bool:
        if from_signal and not value:
            return True
        if not value:
            self.ui.button_box.setDisabled(True)
            return False
        if len(value) != 1:
            self.ui.button_box.setDisabled(True)
            return False
        if not bool(re.match(r"^\W$", value, flags=re.S)):
            self.ui.button_box.setDisabled(True)
            self.ui.sep_input.clear()
            return False
        if other_sep_input_value and other_sep_input_value == value:
            self.ui.button_box.setDisabled(True)
            return False
        if from_signal:
            self._string_input_validation_by_select_substring_field()
        return True

    @Slot()
    def _disable_or_enable_substring_separator_input(self, hidden=True):
        self.ui.sep_input.setDisabled(hidden)
        self._remove_separator_from_main_field_if_toggle_off(self.ui.sep_input.text())
        self.ui.sep_input.clear()

    @Slot()
    def _disable_or_enable_ignore_substring_separator_input(self, hidden=True):
        self.ui.ignore_input.setDisabled(hidden)
        self._remove_separator_from_main_field_if_toggle_off(self.ui.ignore_input.text())
        self.ui.ignore_input.clear()

    @Slot()
    def load_head_varibles(self):
        def insert_head_varibles(items):
            items = tuple(items)
            if items:
                [self.ui.head_varible_area.addItem(QListWidgetItem(item["name"])) for item in items]
                return
            self.ui.head_varible_area.addItem(QListWidgetItem(self.EMPTY_VARIBLES_TEXT))
            self._unlock_dialog()

        @QThreadInstanceDecorator(result_callback=insert_head_varibles)
        def load_items():
            items = self.db.get_items(_model=HeadVarible)
            return items
        load_items()
        self._lock_dialog()

    def clear_form(self):
        self.ui.string_input.clear()
        self.ui.head_varible_area.clear()

    @Slot()
    def add_new_condition_item(self):
        def success_add():
            self.close()
            self.conditions_page.reload()

        def get_index_from_separator(main_string: str, separator: str) -> tuple:
            return main_string.index(separator), main_string.rindex(separator) - 1,

        @QThreadInstanceDecorator(result_callback=success_add)
        def set_to_database__head_varible(headvar_name: str):
            """ Выбор 'переменной из шапки' в кач-ве условия. Создание записи в табице 'HeadVarDelegation'"""
            pass

        @QThreadInstanceDecorator(result_callback=success_add)
        def set_to_database__search_string(left_index, right_index,
                                           left_ignore_index, right_ignore_index, inner):
            """Создание условия на основе поисковой строки. Без создание записи в таблице 'HeadVarDelegation'"""
            def add_initial_values_radio_buttons_condition_table() -> dict:
                d, condition_table_columns = {}, ("conditionbooleanvalue",)
                [d.update(self.conditions_page.UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON[k])
                 if k in self.conditions_page.UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON else None
                 for k in self.conditions_page.RADIO_BUTTON_DEFAULT_VALUES]
                return {column_name: value for column_name, value in d.items() if column_name in condition_table_columns}

            def add_initial_values_radio_buttons_search_string_table():
                d, search_string_table_columns = {}, ("ignorecase",)
                [d.update(self.conditions_page.UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON[button])
                 if button in self.conditions_page.UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON else None
                 for button in self.conditions_page.RADIO_BUTTON_DEFAULT_VALUES]
                return {col: val for col, val in d.items() if col in search_string_table_columns}
            search_str_id = str(uuid.uuid4())
            self.db.set_item(_model=SearchString, inner_=inner, lindex=left_index, rindex=right_index, strid=search_str_id,
                             lignoreindex=left_ignore_index, rignoreindex=right_ignore_index,
                             _insert=True, **add_initial_values_radio_buttons_search_string_table())
            self.db.set_item(_model=Condition, stringid=search_str_id, cnd=str(uuid.uuid4()), _insert=True,
                             **add_initial_values_radio_buttons_condition_table())

        if self.ui.set_string_button.isChecked():
            is_rotate = False
            sep = self.ui.sep_input.text()
            ignore_sep = self.ui.ignore_input.text()
            condition_string: str = self.ui.string_input.text()
            if sep and ignore_sep:
                if condition_string.index(sep) > condition_string.index(ignore_sep):  # Этот блок ради того, чтобы начать с разделителей, которые слева
                    sep, ignore_sep = ignore_sep, sep
                    is_rotate = True
            if not sep:
                if not is_rotate:
                    index_by_sep = (0, len(condition_string) - 1,)
                else:
                    index_by_sep = None
            else:
                index_by_sep = get_index_from_separator(condition_string, sep)
                condition_string = condition_string.replace(sep, "")
            if not ignore_sep:
                index_by_ignore_sep = (None, None,)
            else:
                index_by_ignore_sep = get_index_from_separator(condition_string, ignore_sep)
            if is_rotate:
                index_by_sep, index_by_ignore_sep = index_by_ignore_sep, index_by_sep
            set_to_database__search_string(*index_by_sep, *index_by_ignore_sep, self._get_cond_string([sep, ignore_sep]))
        if self.ui.set_varible_button.isChecked():
            head_var_area_selected_item = self.ui.head_varible_area.currentItem()
            if head_var_area_selected_item is None:
                self.close()
                return
            if head_var_area_selected_item == self.EMPTY_VARIBLES_TEXT:
                self.close()
                return
            selected_varible_name = head_var_area_selected_item.text()
            set_to_database__head_varible(selected_varible_name)

    def _lock_dialog(self):
        self.setDisabled(True)

    def _unlock_dialog(self):
        self.setEnabled(True)

    def _get_cond_string(self, sep_symbols: Iterable[str]) -> str:
        """ Убрать символы разделителя """
        inner: str = self.ui.string_input.text()
        for sep in sep_symbols:
            inner = inner.replace(sep, "")
        return inner

    def _get_condition_substring(self, sep_symbol) -> str:
        str_ = self.ui.string_input.text()
        left_sep_index = str_.index(sep_symbol)
        right_sep_index = str_.rindex(sep_symbol)
        return str_[left_sep_index + 1:right_sep_index]

    def _remove_separator_from_main_field_if_toggle_off(self, sep: str):
        self.ui.string_input.setText(self._get_cond_string([sep]))


class ConditionsPage(Constructor, Tools, InputTools):
    UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON = {
        "radioButton_45": {"conditionbooleanvalue": True},
        "radioButton_46": {"conditionbooleanvalue": False},
        "radioButton_24": {"findfull": True, "isntfindfull": False, "findpart": False, "isntfindpart": False,
                           "larger": False, "less": False, "equal": False},
        "radioButton_25": {"isntfindfull": True, "findfull": False, "findpart": False, "isntfindpart": False,
                           "larger": False, "less": False, "equal": False},
        "radioButton_38": {"findpart": True, "isntfindfull": False, "findfull": False, "isntfindpart": False,
                           "larger": False, "less": False, "equal": False},
        "radioButton_35": {"findpart": False, "isntfindfull": False, "findfull": False, "isntfindpart": False,
                           "larger": False, "less": True, "equal": False},
        "radioButton_36": {"findpart": False, "isntfindfull": False, "findfull": False, "isntfindpart": False,
                           "larger": False, "less": False, "equal": True},
        "radioButton_37": {"findpart": False, "isntfindfull": False, "findfull": False, "isntfindpart": False,
                           "larger": True, "less": False, "equal": False},
        "radioButton_47": {"isntfindpart": True, "findpart": False, "isntfindfull": False, "findfull": False,
                           "larger": False, "less": False, "equal": False},
        "radioButton_29": {"parentconditionbooleanvalue": True},
        "radioButton_30": {"parentconditionbooleanvalue": False},
        "radioButton_28": {"ignorecase": True},
        "radioButton_48": {"ignorecase": False}
    }
    UI__TO_SQL_COLUMN_LINK__LINE_EDIT = {"lineEdit_28": "condinner"}
    UI__TO_SQL_COLUMN_LINK__COMBO_BOX = {"parent_condition_combobox": "parent"}
    LINE_EDIT_DEFAULT_VALUES = {"lineEdit_28": ""}
    COMBO_BOX_DEFAULT_VALUES = {"parent_condition_combobox": "Выберите промежуточное условие"}
    RADIO_BUTTON_DEFAULT_VALUES = {"radioButton_26": True, "radioButton_45": True, "radioButton_28": True}
    SQL_FIELD_NAMES = {model().column_names: model for model in [Condition, SearchString, HeadVarDelegation]}

    def __init__(self, app_instance: QMainWindow, ui: Ui):
        super().__init__(app_instance, ui)
        self.app = app_instance
        self.ui = ui
        self.db_items: orm.ORMHelper = app_instance.db_items_queue
        self.validator: Optional[ConditionsPageValidator] = None
        self.join_select_result: Optional[orm.JoinedORMItem] = None
        self.current_item_hash = None
        self.condition_map = {}  # text: hash
        self.add_condition_dialog: Optional[AddConditionDialog] = None
        self.field_signals_status = False

        def set_db_manager_model():
            self.db_items.set_model(Condition)

        def init_validator():
            self.validator = ConditionsPageValidator(ui)

        set_db_manager_model()
        init_validator()
        self.reload()
        self.connect_main_signals()

    def reload(self, in_new_qthread: bool = True):
        def add_(select_result: orm.JoinedORMItem):
            def auto_select_condition_item(index=0) -> Optional[QListWidgetItem]:
                m = self.ui.conditions_list.takeItem(index)
                self.ui.conditions_list.addItem(m)
                self.ui.conditions_list.setItemSelected(m, True)
                self.ui.conditions_list.setCurrentItem(m)
                return m
            self.disconnect_parent_condition_combo_box()
            self.disconnect_field_signals()
            self.reset_fields()
            [self.add_or_replace_condition_item_to_list_widget(group) for group in select_result]
            result_items = iter(select_result)
            self.condition_map = {value.text(): hash(next(result_items))
                                  for value in
                                  map(lambda x: self.ui.conditions_list.item(x), range(self.ui.conditions_list.count()))
                                  }
            self.join_select_result = select_result
            self.connect_field_signals()
            self.connect_parent_condition_combo_box()
            active_item = auto_select_condition_item()
            self.validator.current_condition = active_item
            if active_item is not None:
                self.validator.refresh()

        @QThreadInstanceDecorator(in_new_qthread=in_new_qthread, result_callback=add_)
        def load_():
            items = self.db_items.join_select(SearchString, Condition, HeadVarible,
                                              on={"Condition.stringid": "SearchString.strid",
                                                  "Condition.hvarid": "HeadVarible.varid"})
            return items
        load_()

    def add_or_replace_condition_item_to_list_widget(self, data: orm.SpecialOrmContainer, replace=False):
        """ 1) Найти выбранный QListWidgetItem (со старым именем)
            2) Сгененировать новое имя
            3) Вставить новый QListWidgetItem (с новым именем) в индекс или в default_index """
        def create_condition_name() -> str:
            def string_gen():
                for key_, string_or_anonimous_function in map_.items():
                    if not string_or_anonimous_function:
                        continue
                    for node in data:
                        model_name = node.model.__name__
                        for column_name, value in node.value.items():
                            if key_ == f"{model_name}.{column_name}":
                                if isinstance(string_or_anonimous_function, str):
                                    yield string_or_anonimous_function
                                else:
                                    yield string_or_anonimous_function(value)
            search_string_table = data["SearchString"]
            condition_table = data["Condition"]
            l_index, r_index = search_string_table.get("lindex", ""), search_string_table.get("rindex", "")
            default_inner = search_string_table.get("inner_", "")
            search_str_inner = search_string_table.get("inner_", "")
            left_ignore_separator = search_string_table.get("lignoreindex")
            right_ignore_separator = search_string_table.get("rignoreindex")
            m_lindex, m_rindex = search_string_table["lindex"], search_string_table["rindex"]
            if left_ignore_separator is not None and right_ignore_separator is not None:
                ignore_block = f"<ИГНОРИРОВАТЬ>[{(right_ignore_separator - left_ignore_separator) - 1}]"
                search_str_inner = search_str_inner.replace(
                    search_str_inner[left_ignore_separator:right_ignore_separator],
                    ignore_block)
                if left_ignore_separator < l_index:
                    m_lindex += (len(ignore_block) - 1) - left_ignore_separator
                    m_rindex += (len(ignore_block) - 1) - left_ignore_separator
            separated_inner = f"{search_str_inner[:m_lindex]}>{default_inner[l_index:r_index]}<{search_str_inner[m_rindex + 1:]}"
            parent_cond_bool_value = search_string_table.get('parentconditionbooleanvalue', "")
            condition_bool_val = search_string_table.get("conditionbooleanvalue",
                                                         self.RADIO_BUTTON_DEFAULT_VALUES["radioButton_45"])
            condition_bool_val = "Истинно если" if condition_bool_val else "Ложно если"
            condition_empty_details = condition_table.get(
                "findfull",
                condition_table.get("findpart",
                                    condition_table.get("isntfindfull",
                                                        condition_table.get("isntfindpart",
                                                                            condition_table.get("equal",
                                                                                                condition_table.get("less",
                                                                                                                    condition_table.get("larger", None)
                                                                                                                    )
                                                                                                )
                                                                            )
                                                        )
                                    )
            )
            map_ = {"Condition.conditionbooleanvalue": condition_bool_val,
                    "Condition.parentconditionbooleanvalue": lambda t: f"родительское условие {'верно' if parent_cond_bool_value else 'ложно'}",
                    "Condition.parent": "и ",
                    "Condition.stringid": f"подстрока >>{default_inner[l_index:r_index]}<<",
                    "SearchString.inner_": f"в строке {separated_inner} {'...' if condition_empty_details is None else ''}",
                    "Condition.findfull": lambda y: "совпадает c" if y else None,
                    "Condition.findpart": lambda y: "содержит" if y else None,
                    "Condition.isntfindfull": lambda y: "не совпадает c" if y else None,
                    "Condition.isntfindpart": lambda x: "не содержит" if x else "",
                    "Condition.equal": lambda u: "равно" if u else "",
                    "Condition.less": lambda i: "меньше чем" if i else "",
                    "Condition.larger": lambda i: "больше чем" if i else "",
                    "Condition.condinner": None,
                    "SearchString.lindex": None,
                    "SearchString.rindex": None,
                    "Condition.cnd": None
                    }
            return " ".join([string for string in string_gen() if string is not None])
        name = create_condition_name()
        self.current_item_hash = hash(data)
        self.disconnect_field_signals()
        if replace:
            list_item = self.ui.conditions_list.currentItem()
            list_item.setText(name)
            self.connect_field_signals()
            return
        self.ui.conditions_list.addItem(QListWidgetItem(name))

    def connect_main_signals(self):
        def open_create_condition_window():
            def close_create_condition_window():
                self._unlock_ui()
                self.add_condition_dialog = None
            self._lock_ui()
            self.add_condition_dialog = AddConditionDialog(self.db_items, app=self,
                                                           callback=close_create_condition_window)
        self.ui.add_button_3.clicked.connect(open_create_condition_window)
        self.ui.remove_button_3.clicked.connect(self.remove_condition)

    def connect_field_signals(self):
        if self.field_signals_status:
            return
        self.ui.conditions_list.currentItemChanged.connect(lambda current, prev: self.select_condition_item(current))
        self.ui.radioButton_45.toggled.connect(lambda x: self.update_data("radioButton_45", radio_button=True) if x else None)
        self.ui.radioButton_46.toggled.connect(lambda x: self.update_data("radioButton_46", radio_button=True) if x else None)
        self.ui.radioButton_24.clicked.connect(lambda x: self.update_data("radioButton_24", radio_button=True) if x else None)
        self.ui.radioButton_25.clicked.connect(lambda x: self.update_data("radioButton_25", radio_button=True) if x else None)
        self.ui.radioButton_38.clicked.connect(lambda x: self.update_data("radioButton_38", radio_button=True) if x else None)
        self.ui.radioButton_47.clicked.connect(lambda x: self.update_data("radioButton_47", radio_button=True) if x else None)
        self.ui.radioButton_35.clicked.connect(lambda x: self.update_data("radioButton_35", radio_button=True) if x else None)
        self.ui.radioButton_36.clicked.connect(lambda x: self.update_data("radioButton_36", radio_button=True) if x else None)
        self.ui.radioButton_37.clicked.connect(lambda x: self.update_data("radioButton_37", radio_button=True) if x else None)
        self.ui.radioButton_26.clicked.connect(lambda x: self.update_data("radioButton_26", radio_button=True) if x else None)
        self.ui.radioButton_27.clicked.connect(lambda x: self.update_data("radioButton_27", radio_button=True) if x else None)
        self.ui.radioButton_29.clicked.connect(lambda x: self.update_data("radioButton_29", radio_button=True) if x else None)
        self.ui.radioButton_30.clicked.connect(lambda x: self.update_data("radioButton_30", radio_button=True) if x else None)
        self.ui.lineEdit_28.textChanged.connect(lambda x: self.update_data("lineEdit_28", line_edit=True) if x else None)
        self.field_signals_status = True

    def disconnect_field_signals(self):
        if not self.field_signals_status:
            return
        self.ui.conditions_list.currentItemChanged.disconnect()
        self.ui.radioButton_45.toggled.disconnect()
        self.ui.radioButton_46.toggled.disconnect()
        self.ui.radioButton_24.clicked.disconnect()
        self.ui.radioButton_25.clicked.disconnect()
        self.ui.radioButton_38.clicked.disconnect()
        self.ui.radioButton_47.clicked.disconnect()
        self.ui.radioButton_35.clicked.disconnect()
        self.ui.radioButton_36.clicked.disconnect()
        self.ui.radioButton_37.clicked.disconnect()
        self.ui.radioButton_26.clicked.disconnect()
        self.ui.radioButton_27.clicked.disconnect()
        self.ui.radioButton_29.clicked.disconnect()
        self.ui.radioButton_30.clicked.disconnect()
        self.ui.lineEdit_28.textChanged.disconnect()
        self.field_signals_status = False

    def connect_parent_condition_combo_box(self):
        self.ui.parent_condition_combobox.textActivated.connect(lambda inner: self.change_parent_condition(inner))

    def disconnect_parent_condition_combo_box(self):
        try:
            self.ui.parent_condition_combobox.textActivated.disconnect()
        except RuntimeError:
            print("ИНФО. Отключаемые сигналы не были подключены")

    @Slot()
    def remove_condition(self):
        def remove():
            @QThreadInstanceDecorator(result_callback=lambda: self.reload(in_new_qthread=False))
            def delete(item_name):
                self.db_items.set_item(_delete=True, cnd=self.join_select_result[item_name], _ready=True)
            current_item: QListWidgetItem = self.ui.conditions_list.currentItem()
            if current_item is None:
                return
            name = current_item.text()
            delete(name)
            dialog.close()
        dialog = self.get_confirm_dialog("Удалить условие", ok_callback=remove)
        dialog.show()

    @Slot(str)
    def select_condition_item(self, condition_item: Optional[QListWidgetItem]):
        def update_fields(item_hash: int, status: Optional[bool]):
            if not status:
                return

            def filter_radio_button_data():
                all_radio_buttons_sql_column_names = set(itertools.chain.from_iterable(val.keys() for val in self.UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON.values()))
                res = {key: value for key, value in all_data.items() if key in all_radio_buttons_sql_column_names}
                return res
            data = self.join_select_result[item_hash]
            all_data = {}
            [all_data.update(node.value) for node in data]
            line_edit_data = {"conditionvalue": all_data.pop("conditionvalue", None),
                              "condinner": all_data.pop("condinner", None)}
            combo_box_data = {"parent": all_data.pop("parent", None)}
            self.disconnect_field_signals()
            self.disconnect_parent_condition_combo_box()
            self.update_fields(line_edit_values=line_edit_data, combo_box_values=combo_box_data,
                               radio_button_values=filter_radio_button_data())
            self.validator.set_condition_item(condition_item)
            self.validator.refresh()
            self.connect_parent_condition_combo_box()
            self.connect_field_signals()
            self.current_item_hash = item_hash

        @QThreadInstanceDecorator(result_callback=lambda status: update_fields(selected_condition_hash, status))
        def check_inner(index: int):
            is_actual = self.join_select_result.is_actual_entry(index)
            if not is_actual:
                self.reload(in_new_qthread=False)
                return
            return True
        if not condition_item:
            return
        selected_condition_hash = self.condition_map[condition_item.text()]
        check_inner(selected_condition_hash)

    @Slot(str)
    def change_parent_condition(self, item):
        @QThreadInstanceDecorator(result_callback=self.validator.refresh)
        def set_changes(current_cond_id, val=None):
            def check_exists(selected_cnd_id, parent_cnd_id):
                if not self.db_items.get_item(cnd=selected_cnd_id):
                    self.reload(in_new_qthread=False)
                if val is not None:
                    if not self.db_items.get_item(cnd=parent_cnd_id):
                        self.reload(in_new_qthread=False)
            check_exists(current_cond_id, val)
            if val is None:
                self.db_items.remove_field_from_node(current_cond_id, "parent")
                return
            self.db_items.set_item(
                _ready=self.validator.is_valid,
                cnd=current_cond_id,
                parent=val,
                _update=True)
        current_condition_item = self.ui.conditions_list.currentItem()
        if not current_condition_item:
            return
        current_condition_name = current_condition_item.text()
        id_ = self.join_select_result[current_condition_name]
        if item == self.COMBO_BOX_DEFAULT_VALUES["parent_condition_combobox"]:
            set_changes(id_)
            self.validator.refresh()
            return
        selected_condition_id = self.join_select_result[item]
        set_changes(id_, selected_condition_id)

    def update_data(self, field_name, line_edit=False, radio_button=False):
        def get_value_from_ui() -> dict:  # sql_col_name: val
            def set_pk_to_values():
                """ Требует orm """
                nonlocal pk
                nodes = self.join_select_result[self.current_item_hash]
                node = nodes[model.__name__]
                pk = node.get_primary_key_and_value()
                val.update(pk)
            val = {}
            set_pk_to_values()
            if radio_button:
                val.update(self.UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON[field_name])
            if line_edit:
                input_: QLineEdit = getattr(self.ui, field_name)
                val.update({self.UI__TO_SQL_COLUMN_LINK__LINE_EDIT[field_name]: input_.text()})
            return val

        @QThreadInstanceDecorator(
            result_callback=lambda x:
            self.add_or_replace_condition_item_to_list_widget(x, replace=True) if x and x is not True else None
        )
        def check_exists_and_update(hash_, val):
            data = self.join_select_result.is_actual_entry(hash_)
            if not data:
                return False
            self.db_items.set_item(_update=True, _ready=is_valid, _model=model, **val)
            test = self.join_select_result.is_actual_entry(hash_)
            print(test)
            return test
        selected_condition = self.ui.conditions_list.currentItem()
        if not selected_condition:
            return
        condition_text = selected_condition.text()
        item_hash = self.condition_map[condition_text]
        sql_field_name = None
        if radio_button:
            sql_field_name = list(self.UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON[field_name].keys())[0]
        if line_edit:
            sql_field_name = self.UI__TO_SQL_COLUMN_LINK__LINE_EDIT[field_name]
        pk: Optional[dict] = None
        model = [model for fields, model in self.SQL_FIELD_NAMES.items() if sql_field_name in fields][0]
        values = get_value_from_ui()
        is_valid = self.validator.refresh()
        check_exists_and_update(item_hash, values)

    def reset_fields(self):
        self.join_select_result = {}
        self.ui.conditions_list.clear()
        super().reset_fields_to_default()


class ConditionsPageValidator(Validator):
    REQUIRED_TEXT_FIELD_VALUES = ("lineEdit_28",)
    REQUIRED_RADIO_BUTTONS = {"groupBox_19": ("radioButton_24", "radioButton_25", "radioButton_38",
                                              "radioButton_35", "radioButton_36", "radioButton_37", "radioButton_47"),
                              "boolvalbox": ("radioButton_45", "radioButton_46"),
                              "regsensitivebox": ("radioButton_28", "radioButton_48")}

    def __init__(self, ui):
        super().__init__(ui)
        self.current_condition: Optional[QListWidgetItem] = None

    def set_condition_item(self, item):
        self.current_condition = item

    def refresh(self) -> bool:
        def mark_invalid_condition():
            if valid:
                self.set_complete_edit_attributes(self.current_condition)
            else:
                self.set_not_complete_edit_attributes(self.current_condition)
        valid = super().refresh()
        if self.current_condition:
            mark_invalid_condition()
        return valid
