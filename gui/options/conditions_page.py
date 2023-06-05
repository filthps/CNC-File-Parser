import uuid
from typing import Optional, Union
from PySide2.QtWidgets import QMainWindow, QListWidget, QListWidgetItem, QHBoxLayout, \
    QVBoxLayout, QGroupBox, QLineEdit, QRadioButton, QDialogButtonBox, QSpacerItem
from PySide2.QtCore import Slot, Qt
from gui.tools import Tools, Constructor, MyAbstractDialog
from database.models import Condition, HeadVarible, HeadVarDelegation
from gui import orm
from gui.ui import Ui_main_window as Ui
from gui.validation import Validator
from gui.threading_ import QThreadInstanceDecorator


class AddConditionDialog(MyAbstractDialog):
    """
    Диалоговое окно для добавления 'условия' с вариантами выбора: 1) Поиск по вводимой строке; 2) Поиск по значению
    переменной.
    """
    EMPTY_VARIBLES_TEXT = "<Переменные не найдены>"

    def __init__(self, db: orm.ORMHelper, app=None, callback=None):
        self.accept_button = QDialogButtonBox.Apply
        self.button_box = QDialogButtonBox(self.accept_button, orientation=Qt.Orientation.Horizontal)
        self.button_box.setDisabled(True)
        super().__init__(parent=app.app, close_callback=callback, buttons=(self.accept_button,))
        self.conditions_page: Optional["ConditionsPage"] = app
        self.head_varible_area: Optional[QListWidget] = None
        self.string_input: Optional[QLineEdit] = None
        self.set_string_button: Optional[QRadioButton] = None
        self.set_varible_button: Optional[QRadioButton] = None
        self.db = db
        self.create_dialog_ui()
        self.show()

    def create_dialog_ui(self):
        def init_ui():
            self.setWindowTitle("Добавить условие")
            main_horizontal_layout = QVBoxLayout()
            horizontal_box_layout = QHBoxLayout()
            box = QGroupBox()
            box.setTitle("Что следует проверять")
            radio_button_search_string = QRadioButton("Искать следующую строку:")
            condition_string_input = QLineEdit()
            condition_string_input.setDisabled(True)
            vertical_layout_search_string = QVBoxLayout()
            vertical_layout_search_string.addWidget(radio_button_search_string)
            vertical_layout_search_string.addWidget(condition_string_input)
            vertical_layout_search_string.addSpacerItem(QSpacerItem(0, 200))
            vertical_layout_set_head_varible = QVBoxLayout()
            radio_button_set_headvar = QRadioButton("Искать значение переменной:")
            head_varible_area = QListWidget()
            head_varible_area.setDisabled(True)
            vertical_layout_set_head_varible.addWidget(radio_button_set_headvar)
            vertical_layout_set_head_varible.addWidget(head_varible_area)
            horizontal_box_layout.addLayout(vertical_layout_search_string)
            horizontal_box_layout.addLayout(vertical_layout_set_head_varible)
            box.setLayout(horizontal_box_layout)
            main_horizontal_layout.addWidget(box)
            self.setLayout(main_horizontal_layout)
            self.head_varible_area = head_varible_area
            self.string_input = condition_string_input
            self.set_string_button = radio_button_search_string
            self.set_varible_button = radio_button_set_headvar
            buttons_layout = QHBoxLayout()
            buttons_layout.addSpacerItem(QSpacerItem(300, 0))
            buttons_layout.addWidget(self.button_box)
            buttons_layout.addSpacerItem(QSpacerItem(300, 0))
            main_horizontal_layout.addLayout(buttons_layout)
        init_ui()
        self.connect_signals()

    def connect_signals(self):
        def toggle_disable_state(current_enabled: Union[QLineEdit, QListWidget]):
            self.button_box.setDisabled(False)
            self.head_varible_area.setDisabled(True)
            self.string_input.setDisabled(True)
            current_enabled.setEnabled(True)
        self.set_varible_button.toggled.connect(self.clear_form)
        self.set_string_button.toggled.connect(self.clear_form)
        self.set_varible_button.toggled.connect(lambda: toggle_disable_state(self.head_varible_area))
        self.set_string_button.toggled.connect(lambda: toggle_disable_state(self.string_input))
        self.set_varible_button.toggled.connect(self.load_head_varibles)
        self.button_box.clicked.connect(self.add_new_condition_item)

    def load_head_varibles(self):
        def insert_head_varibles(items):
            items = tuple(items)
            if items:
                [self.head_varible_area.addItem(QListWidgetItem(item["name"])) for item in items]
                return
            self.head_varible_area.addItem(QListWidgetItem(self.EMPTY_VARIBLES_TEXT))
            self._unlock_dialog()

        @QThreadInstanceDecorator(result_callback=insert_head_varibles)
        def load_items():
            items = self.db.get_items(_model=HeadVarible)
            return items
        load_items()
        self._lock_dialog()

    def clear_form(self):
        self.string_input.clear()
        self.head_varible_area.clear()

    def add_new_condition_item(self):
        def success_add():
            self.close()
            self.conditions_page.reload()

        @QThreadInstanceDecorator(result_callback=success_add)
        def set_to_database__head_varible(headvar_name: str):
            """ Выбор 'переменной из шапки' в кач-ве условия. Создание записи в табице 'HeadVarDelegation'"""
            head_varible_instance = self.db.get_item(_model=HeadVarible, name=headvar_name)
            if not head_varible_instance:
                return
            h_var_delegation_d = {"secid": str(uuid.uuid4()), "varid": head_varible_instance["varid"]}
            condition_item_data = {"cnd": str(uuid.uuid4())}
            h_var_delegation_d.update({"conditionid": condition_item_data["cnd"]})
            self.db.set_item(_model=Condition, _insert=True, **condition_item_data)
            self.db.set_item(_insert=True, _model=HeadVarDelegation, **h_var_delegation_d)

        @QThreadInstanceDecorator(result_callback=success_add)
        def set_to_database__search_string(search_string: str):
            """Создание условия на основе поисковой строки. Без создание записи в таблице 'HeadVarDelegation'"""
            self.db.set_item(_model=Condition, _insert=True, **{"cnd": str(uuid.uuid4()), "conditionstring": search_string})
        if self.set_string_button.isChecked():
            condition_string = self.string_input.text()
            if not condition_string:
                self.close()
                return
            set_to_database__search_string(condition_string)
        if self.set_varible_button.isChecked():
            head_var_area_selected_item = self.head_varible_area.currentItem()
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


class ConditionsPage(Constructor, Tools):
    _UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON = {
        "radioButton_45": {"conditionbooleanvalue": True},
        "radioButton_46": {"conditionbooleanvalue": False},
        "radioButton_24": {"findfull": True, "isntfindfull": False, "findpart": False, "isntfindpart": False,
                           "larger": False, "less": False, "equal": False},
        "radioButton_25": {"isntfindfull": True, "findfullfull": False, "findpart": False, "isntfindpart": False,
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
    }
    _UI__TO_SQL_COLUMN_LINK__LINE_EDIT = {"lineEdit_28": "conditionvalue"}
    _UI__TO_SQL_COLUMN_LINK__COMBO_BOX = {"parent_condition_combobox": "parent"}
    _STRING_FIELDS = ("lineEdit_28",)
    _LINE_EDIT_DEFAULT_VALUES = {"lineEdit_28": ""}
    _COMBO_BOX_DEFAULT_VALUES = {"parent_condition_combobox": "Выберите промежуточное условие"}
    _RADIO_BUTTON_DEFAULT_VALUES = {"radioButton_26": True}

    def __init__(self, app_instance: QMainWindow, ui: Ui):
        super().__init__(app_instance, ui)
        self.app = app_instance
        self.ui = ui
        self.db_items: orm.ORMHelper = app_instance.db_items_queue
        self.validator: Optional[ConditionsPageValidator] = None
        self.condition_items_id = {}  # name: id
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
        def add_(condition_items):
            def auto_select_condition_item(index=0) -> Optional[QListWidgetItem]:
                m = self.ui.conditions_list.takeItem(index)
                self.ui.conditions_list.addItem(m)
                self.ui.conditions_list.setItemSelected(m, True)
                self.ui.conditions_list.setCurrentItem(m)
                return m
            self.disconnect_parent_condition_combo_box()
            self.disconnect_field_signals()
            self.reset_fields()
            for item in condition_items:
                self.add_or_replace_condition_item_to_list_widget(item)
            self.disconnect_field_signals()
            active_item = auto_select_condition_item()
            self.validator.current_condition = active_item
            self.connect_field_signals()
            self.connect_parent_condition_combo_box()
            if active_item is not None:
                self.validator.refresh()

        @QThreadInstanceDecorator(in_new_qthread=in_new_qthread, result_callback=add_)
        def load_():
            items = self.db_items.get_items(_model=Condition)
            return items
        load_()

    def add_or_replace_condition_item_to_list_widget(self, condition_data: dict, replace=False):
        """ 1) Найти выбранный QListWidgetItem (со старым именем)
            2) Сгененировать новое имя
            3) Вставить новый QListWidgetItem (с новым именем) в индекс или в default_index
            4) Сохранить связку {id: новый_name} в condition_items_id """
        def create_condition_name(data: dict) -> str:
            map_ = {"conditionbooleanvalue": lambda: "Истинно если" if data.get("conditionbooleanvalue", None) else
                    "..." if data.get("conditionbooleanvalue", None) is None else "Ложно если",
                    "conditionstring": lambda: f"строка >> {data['conditionstring']} <<" if "conditionstring" in data else "переменная",
                    "findfull": "совпадает c",
                    "findpart": "содержит", "isntfindfull": "не совпадает c", "isntfindpart": "не содержит",
                    "equal": "равно", "less": "меньше чем", "larger": "больше чем",
                    "conditionvalue": lambda: f"<< {data['conditionvalue']} >>." if "conditionvalue" in data else "...",
                    "parent": lambda: "Выбрано внешнее условие!" if "parent" in data else ""}
            return " ".join(
                map(lambda t: t[1]() if not isinstance(t[1], str) else map_[t[0]] if (t[0] in data and data[t[0]]) else "", map_.items())
            )

        name = create_condition_name(condition_data)
        self.condition_items_id.update({name: condition_data["cnd"]})
        self.disconnect_field_signals()
        if replace:
            list_item = self.ui.conditions_list.currentItem()
            list_item.setText(name)
            self.connect_field_signals()
            return
        self.ui.conditions_list.addItem(QListWidgetItem(name))
        self.connect_field_signals()

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
        self.ui.conditions_list.currentItemChanged.connect(lambda current, prev: self.select_condition_item(current))

    def connect_field_signals(self):
        if self.field_signals_status:
            return
        self.ui.radioButton_45.toggled.connect(lambda x: self.update_data("radioButton_45", radio_button=True))
        self.ui.radioButton_46.toggled.connect(lambda x: self.update_data("radioButton_46", radio_button=True))
        self.ui.radioButton_24.clicked.connect(lambda: self.update_data("radioButton_24", radio_button=True))
        self.ui.radioButton_25.clicked.connect(lambda: self.update_data("radioButton_25", radio_button=True))
        self.ui.radioButton_38.clicked.connect(lambda: self.update_data("radioButton_38", radio_button=True))
        self.ui.radioButton_47.clicked.connect(lambda: self.update_data("radioButton_47", radio_button=True))
        self.ui.radioButton_35.clicked.connect(lambda: self.update_data("radioButton_35", radio_button=True))
        self.ui.radioButton_36.clicked.connect(lambda: self.update_data("radioButton_36", radio_button=True))
        self.ui.radioButton_37.clicked.connect(lambda: self.update_data("radioButton_37", radio_button=True))
        self.ui.radioButton_26.clicked.connect(lambda: self.update_data("radioButton_26", radio_button=True))
        self.ui.radioButton_27.clicked.connect(lambda: self.update_data("radioButton_27", radio_button=True))
        self.ui.radioButton_29.clicked.connect(lambda: self.update_data("radioButton_29", radio_button=True))
        self.ui.radioButton_30.clicked.connect(lambda: self.update_data("radioButton_30", radio_button=True))
        self.ui.lineEdit_28.textChanged.connect(lambda x: self.update_data("lineEdit_28", line_edit=True))
        self.field_signals_status = True

    def disconnect_field_signals(self):
        if not self.field_signals_status:
            return
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
            @QThreadInstanceDecorator(result_callback=lambda: self.reload(in_new_qthread=False))  # todo
            def delete(item_name):
                self.db_items.set_item(_delete=True, cnd=self.condition_items_id[item_name], _ready=True)
            current_item: QListWidgetItem = self.ui.conditions_list.currentItem()
            if current_item is None:
                return
            name = current_item.text()
            delete(name)
        dialog = self.get_prompt_dialog("Удалить условие", ok_callback=remove)
        dialog.show()

    @Slot(str)
    def select_condition_item(self, condition_item):
        def update_fields(data: dict):
            if not data:
                self.reload()
            line_edit_data = {"conditionvalue": data.pop("conditionvalue", None)}
            combo_box_data = {"parent": data.pop("parent", None)}
            self.disconnect_field_signals()
            self.disconnect_parent_condition_combo_box()
            self.update_fields(line_edit_values=line_edit_data, combo_box_values=combo_box_data, radio_button_values=data)
            self.connect_parent_condition_combo_box()
            self.connect_field_signals()

        @QThreadInstanceDecorator(result_callback=update_fields)
        def load_inner(item: str):
            item_data = self.db_items.get_item(cnd=item, _model=Condition)
            if not item_data:
                self.reload(in_new_qthread=False)
            return item_data
        if condition_item is None:
            return
        self.validator.set_condition_item(condition_item)
        item_text = condition_item.text()
        load_inner(self.condition_items_id[item_text])

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
        id_ = self.condition_items_id[current_condition_name]
        if item == self._COMBO_BOX_DEFAULT_VALUES["parent_condition_combobox"]:
            set_changes(id_)
            self.validator.refresh()
            return
        selected_condition_id = self.condition_items_id[item]
        set_changes(id_, selected_condition_id)

    def update_data(self, field_name, **kwargs):
        @QThreadInstanceDecorator(result_callback=self.validator.refresh, in_new_qthread=False)
        def load_condition_instance_and_update_name(id_):
            data = self.db_items.get_item(cnd=id_)
            if not data:
                self.reload()
            self.add_or_replace_condition_item_to_list_widget(data, replace=True)

        @QThreadInstanceDecorator(result_callback=lambda: load_condition_instance_and_update_name(condition_id))
        def set_data(id_, **data):
            exists_node_type = self.db_items.get_node_dml_type(id_, Condition)
            data.update({("_update" if exists_node_type == "_update" else "_insert"): True})
            self.db_items.set_item(cnd=id_, **data)
        selected_condition = self.ui.conditions_list.currentItem()
        if not selected_condition:
            return
        condition_text = selected_condition.text()
        condition_id = self.condition_items_id[condition_text]
        ui_field = getattr(self.ui, field_name)
        field_value = ui_field.text()
        if kwargs.get("line_edit", None):
            sql_field_name = self._UI__TO_SQL_COLUMN_LINK__LINE_EDIT[field_name]
            set_data(condition_id, **{sql_field_name: self.check_output_values(sql_field_name, field_value)})
        elif kwargs.get("radio_button", None):
            radio_button_values: dict = self._UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON[field_name]
            set_data(condition_id, **radio_button_values)

    def reset_fields(self):
        self.condition_items_id = {}
        self.ui.conditions_list.clear()
        super().reset_fields_to_default()


class ConditionsPageValidator(Validator):
    REQUIRED_TEXT_FIELD_VALUES = ("lineEdit_28",)
    REQUIRED_RADIO_BUTTONS = {"groupBox_19": ("radioButton_24", "radioButton_25", "radioButton_38",
                                              "radioButton_35", "radioButton_36", "radioButton_37", "radioButton_47")}

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
