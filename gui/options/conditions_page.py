from PySide2.QtWidgets import QMainWindow
from PySide2.QtCore import Slot
from gui.tools import Tools, Constructor, ORMHelper
from database.models import Condition
from gui.ui import Ui_main_window as Ui
from gui.validation import Validator


class ConditionsPage(Constructor, Tools):
    _UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON = {
        "radioButton_24": {"findfull": True, "isntfind": False, "findpart": False,
                           "larger": False, "less": False, "equal": False},
        "radioButton_25": {"isntfind": True, "findfull": False, "findpart": False,
                           "larger": False, "less": False, "equal": False},
        "radioButton_38": {"findpart": True, "isntfind": False, "findfull": False,
                           "larger": False, "less": False, "equal": False},
        "radioButton_35": {"findpart": False, "isntfind": False, "findfull": False,
                           "larger": False, "less": True, "equal": False},
        "radioButton_36": {"findpart": False, "isntfind": False, "findfull": False,
                           "larger": False, "less": False, "equal": True},
        "radioButton_37": {"findpart": False, "isntfind": False, "findfull": False,
                           "larger": True, "less": False, "equal": False},
        "radioButton_29": {"parentconditiontrue": True, "parentconditionfalse": False},
        "radioButton_30": {"parentconditiontrue": False, "parentconditionfalse": True},
    }
    _UI__TO_SQL_COLUMN_LINK__LINE_EDIT = {"lineEdit_28": "targetstr"}
    _UI__TO_SQL_COLUMN_LINK__COMBO_BOX = {"comboBox": "parent"}
    _STRING_FIELDS = ("lineEdit_28",)
    _COMBO_BOX_DEFAULT_VALUES = {"comboBox": "Выберите промежуточное условие"}

    def __init__(self, app_instance: QMainWindow, ui: Ui):
        super().__init__(app_instance, ui)
        self.app = app_instance
        self.ui = ui
        self.db_items: ORMHelper = app_instance.db_items_queue
        self.validator = None

        def set_db_manager_model():
            self.db_items.set_model(Condition, "targetstr")

        def init_validator():
            self.validator = ConditionsPageValidator(ui)
        set_db_manager_model()
        init_validator()

    def reload(self):
        pass

    def connect_main_signals(self):
        self.ui.add_button_3.clicked.connect(self.add_condition)
        self.ui.remove_button_3.clicked.connect(self.remove_condition)
        self.ui.listWidget.currentItemChanged.connect(lambda current, prev: self.change_condition(current))
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

    def add_condition(self):
        pass

    def remove_condition(self):
        pass

    def change_condition(self, condition_item):
        pass

    def update_data(self, field_name, **kwargs):
        selected_condition = self.ui.listWidget.currentItem()
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
        if kwargs.get("radio_button", None):
            radio_button_values: dict = self._UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON[field_name]
            self.db_items.set_item(condition_text, radio_button_values,
                                   **{("update" if exists_node_type == "update" else "insert"): True},
                                   where={"targetstr": condition_text})
        if kwargs.get("combo_box"):
            ...

    @Slot(str)
    def change_parent_condition(self, item):
        current_condition_item = self.ui.comboBox.currentItem()
        if not current_condition_item:
            return
        if item == self._COMBO_BOX_DEFAULT_VALUES["comboBox"]:
            self.validator.refresh()
            return


    def reset_fields(self):
        ...

    def save(self):
        if self.validator.refresh():
            ...

    def create_condition_name(self):
        """ Создать  """


class ConditionsPageValidator(Validator):
    REQUIRED_TEXT_FIELD_VALUES = ("lineEdit_28",)

    def __init__(self, ui):
        super().__init__(ui)
        self.current_condition = None

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
