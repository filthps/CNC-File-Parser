import uuid
from typing import Optional, Union
from PySide2.QtWidgets import QMainWindow, QListWidget, QListWidgetItem, QHBoxLayout, QVBoxLayout, QLabel, \
    QGroupBox, QLineEdit, QRadioButton, QDialogButtonBox, QSpacerItem
from PySide2.QtCore import Slot, Qt
from gui.tools import Tools, Constructor, ORMHelper, MyAbstractDialog, UiLoaderThreadFactory
from database.models import Condition, HeadVarible
from gui.ui import Ui_main_window as Ui
from gui.validation import Validator


class AddConditionDialog(MyAbstractDialog):
    """
    Диалоговое окно для добавления 'условия' с вариантами выбора: 1) Поиск по вводимой строке; 2) Поиск по значению
    переменной.
    """
    def __init__(self, db: ORMHelper, parent=None, callback=None):
        self.accept_button = QDialogButtonBox.Apply
        super().__init__(parent=parent, close_callback=callback, buttons=(self.accept_button,))
        self.head_varible_area: Optional[QListWidget] = None
        self.string_input: Optional[QLineEdit] = None
        self.set_string_button: Optional[QRadioButton] = None
        self.set_varible_button: Optional[QRadioButton] = None
        self.db = db
        self.get_add_condition_dialog()
        self.show()

    def get_add_condition_dialog(self):
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
            buttons_box = QDialogButtonBox(self.accept_button, orientation=Qt.Orientation.Horizontal)
            buttons_layout.addSpacerItem(QSpacerItem(300, 0))
            buttons_layout.addWidget(buttons_box)
            buttons_layout.addSpacerItem(QSpacerItem(300, 0))
            main_horizontal_layout.addLayout(buttons_layout)
        init_ui()
        self.connect_signals()

    def connect_signals(self):
        def toggle_diasable_state(current_enabled: Union[QLineEdit, QListWidget]):
            self.head_varible_area.setDisabled(True)
            self.string_input.setDisabled(True)
            current_enabled.setEnabled(True)
        self.set_varible_button.toggled.connect(self.clear_form)
        self.set_string_button.toggled.connect(self.clear_form)
        self.set_varible_button.toggled.connect(lambda: toggle_diasable_state(self.head_varible_area))
        self.set_string_button.toggled.connect(lambda: toggle_diasable_state(self.string_input))
        self.set_varible_button.toggled.connect(lambda: self.load_data() if self.set_varible_button.isChecked() else None)
        self.accept_button.clicked.connect(self.add_new_condition_item)

    def clear_form(self):
        self.string_input.clear()
        self.head_varible_area.clear()

    @UiLoaderThreadFactory()
    def load_data(self):
        self._lock_dialog()
        for data in self.db.get_items(HeadVarible, "name"):
            name = data["name"]
            self.head_varible_area.addItem(QListWidgetItem(name))
        self._unlock_dialog()

    def add_new_condition_item(self):
        if self.set_string_button.isChecked():
            condition_string = self.string_input.text()
            if not condition_string:
                return
            id_ = uuid.uuid4()
            self.db.set_item(id_, {"cnd": id_, "conditionstring": condition_string}, insert=True, ready=False)
        if self.set_varible_button.isChecked():
            selected_var = self.head_varible_area.currentItem().text()
            if not selected_var:
                return

        self.close()

    def _lock_dialog(self):
        self.setDisabled(True)

    def _unlock_dialog(self):
        self.setEnabled(True)


class ConditionsPage(Constructor, Tools):
    _UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON = {
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
                           "larger": True, "less": False, "equal": False},
        "radioButton_29": {"parentconditionbooleanvalue": True},
        "radioButton_30": {"parentconditionbooleanvalue": False},
    }
    _UI__TO_SQL_COLUMN_LINK__LINE_EDIT = {"lineEdit_28": "conditionvalue"}
    _UI__TO_SQL_COLUMN_LINK__COMBO_BOX = {"comboBox": "parent"}
    _STRING_FIELDS = ("lineEdit_28",)
    _LINE_EDIT_DEFAULT_VALUES = {"lineEdit_28": ""}
    _COMBO_BOX_DEFAULT_VALUES = {"comboBox": "Выберите промежуточное условие"}
    _RADIO_BUTTON_DEFAULT_VALUES = {"radioButton_26": True}

    def __init__(self, app_instance: QMainWindow, ui: Ui):
        super().__init__(app_instance, ui)
        self.app = app_instance
        self.ui = ui
        self.db_items: ORMHelper = app_instance.db_items_queue
        self.validator: Optional[ConditionsPageValidator] = None
        self.condition_items_id = {}
        self.add_condition_dialog: Optional[AddConditionDialog] = None

        def set_db_manager_model():
            self.db_items.set_model(Condition, "cnd")

        def init_validator():
            self.validator = ConditionsPageValidator(ui)
        set_db_manager_model()
        init_validator()
        self.connect_main_signals()

    def reload(self):
        def add_conditions():
            def create_condition_name(data: dict) -> str:
                map_ = {"conditiontrue": "Истинно если", "conditionfalse": "Ложно если", "findfull": "совпадает",
                        "findpart": "содержит", "isntfindfull": "не совпадает", "isntfindpart": "не совпадает",
                        "equal": "равно", "less": "меньше", "larger": "больше", "parent": "родитель " + data["parent"],
                        "conditionstring": data["conditionstring"], "conditionvalue": data["conditionvalue"]}
                return "".join(tuple(map(lambda n: str(map_[n]), data.keys())))
            items = self.db_items.get_items()
            for item in items:
                name = create_condition_name(item)
                self.condition_items_id.update({item["cnd"]: name})
                self.ui.conditions_list.addItem(QListWidgetItem(name))

        def auto_select_condition_item(index=0):
            item = self.ui.conditions_list.takeItem(index)
            self.ui.conditions_list.addItem(item)
            self.ui.conditions_list.setItemSelected(item, True)
            self.ui.conditions_list.setCurrentItem(item)
        self.disconnect_parent_condition_combo_box()
        self.disconnect_field_signals()
        self.reset_fields()
        add_conditions()
        auto_select_condition_item()
        self.connect_field_signals()

    def connect_main_signals(self):
        def open_create_condition_window():
            def close_create_condition_window():
                self._unlock_ui()
                self.add_condition_dialog = None
            self._lock_ui()
            self.add_condition_dialog = AddConditionDialog(self.db_items, parent=self.app,
                                                           callback=close_create_condition_window)
        self.ui.add_button_3.clicked.connect(open_create_condition_window)
        self.ui.remove_button_3.clicked.connect(self.remove_condition)
        self.ui.conditions_list.currentItemChanged.connect(lambda current, prev: self.change_condition(current))
        self.ui.commandLinkButton_9.clicked.connect(self.save)

    def connect_field_signals(self):
        self.ui.lineEdit_28.textChanged.connect(self.update_data("lineEdit_28", line_edit=True))
        self.ui.radioButton_24.clicked.connect(self.update_data("radioButton_24", radio_button=True))
        self.ui.radioButton_25.clicked.connect(self.update_data("radioButton_25", radio_button=True))
        self.ui.radioButton_26.clicked.connect(self.update_data("radioButton_26", radio_button=True))
        self.ui.radioButton_27.clicked.connect(self.update_data("radioButton_27", radio_button=True))
        self.ui.radioButton_29.clicked.connect(self.update_data("radioButton_29", radio_button=True))
        self.ui.radioButton_30.clicked.connect(self.update_data("radioButton_30", radio_button=True))

    def disconnect_field_signals(self):
        try:
            self.ui.lineEdit_28.textChanged.disconnect()
            self.ui.radioButton_24.clicked.disconnect()
            self.ui.radioButton_25.clicked.disconnect()
            self.ui.radioButton_26.clicked.disconnect()
            self.ui.radioButton_27.clicked.disconnect()
            self.ui.radioButton_29.clicked.disconnect()
            self.ui.radioButton_30.clicked.disconnect()
        except RuntimeError:
            print("ИНФО. Отключаемые сигналы не были подключены")

    def connect_parent_condition_combo_box(self):
        self.ui.comboBox.textActivated.connect(lambda inner: self.change_parent_condition(inner))

    def disconnect_parent_condition_combo_box(self):
        self.ui.comboBox.textActivated.disconnect()

    @Slot()
    def remove_condition(self):
        def remove():
            current_item: QListWidgetItem = self.ui.conditions_list.currentItem()
            name = current_item.text()
            id = self.n
        dialog = self.get_prompt_dialog("Удалить условие", ok_callback=remove())
        dialog.show()

    @Slot(str)
    def change_condition(self, condition_item):
        pass

    @Slot(str)
    def change_parent_condition(self, item):
        current_condition_item = self.ui.comboBox.currentItem()
        if not current_condition_item:
            return
        if item == self._COMBO_BOX_DEFAULT_VALUES["comboBox"]:
            self.validator.refresh()
            return

    def update_data(self, field_name, **kwargs):
        selected_condition = self.ui.conditions_list.currentItem()
        if not selected_condition:
            return
        condition_text = selected_condition.text()
        field = getattr(self.ui, field_name)
        sql_field_name = self._UI__TO_SQL_COLUMN_LINK__LINE_EDIT[field_name]
        exists_node_type = self.db_items.get_node_dml_type(condition_text, Condition)
        if kwargs.get("line_edit", None):
            self.db_items.set_item(condition_text, {sql_field_name: self.check_output_values(field_name, field.text())},
                                   **{("update" if exists_node_type == "update" else "insert"): True},
                                   where={"targetstr": condition_text})
        elif kwargs.get("radio_button", None):
            radio_button_values: dict = self._UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON[field_name]
            self.db_items.set_item(condition_text, radio_button_values,
                                   **{("update" if exists_node_type == "update" else "insert"): True},
                                   where={"targetstr": condition_text})

    def reset_fields(self):
        self.condition_items_id = {}
        super().reset_fields_to_default()

    def save(self):
        if self.validator.refresh():
            ...


class ConditionsPageValidator(Validator):
    REQUIRED_TEXT_FIELD_VALUES = ("lineEdit_28",)
    REQUIRED_RADIO_BUTTONS = {"groupBox_19": ("radioButton_24", "radioButton_25", "radioButton_38",
                                              "radioButton_35", "radioButton_36", "radioButton_37",)}

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
