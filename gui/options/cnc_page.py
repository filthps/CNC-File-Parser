from PySide2.QtCore import Slot
from PySide2.QtWidgets import QListWidgetItem, QLineEdit, QTextEdit
from database.models import Cnc
from gui.tools import Constructor, Tools, ORMHelper
from gui.ui import Ui_main_window
from gui.validation import Validator


class AddCNC(Constructor, Tools):
    __UI__TO_SQL_COLUMN_LINK__LINE_EDIT = {"textEdit_2": "except_symbols", "lineEdit_22": "comment_symbol"}

    def __init__(self, app, ui: Ui_main_window):
        super().__init__(app, ui)
        self.instance = app
        self.ui = ui
        self.db_items: ORMHelper = app.db_items_queue
        self.validator = None

        def set_db_manager_model():
            self.db_items.set_model(Cnc, "name")

        def init_validator():
            self.validator = CncPageValidator(self.ui)
        set_db_manager_model()
        init_validator()
        self.reload()
        self.connect_main_signals()

    def reload(self):
        def insert_all_cnc():
            cnc_items = self.db_items.get_items()
            for item in cnc_items:
                list_item = QListWidgetItem(item["name"])
                self.ui.cnc_list.addItem(list_item)
                if self.db_items.is_node_from_cache(item["name"]):
                    self.validator.set_not_complete_edit_attributes(list_item)
        self.disconnect_text_field_signals()
        self.ui.cnc_list.clear()
        self.clean_fields()
        insert_all_cnc()
        self.auto_select_cnc_item()
        self.connect_text_field_signals()

    def connect_main_signals(self):
        self.ui.add_button_1.clicked.connect(self.add_cnc)
        self.ui.remove_button_1.clicked.connect(self.remove_cnc)
        self.ui.cnc_list.currentItemChanged.connect(lambda cur, prev: self.select_cnc(cur))

    def connect_text_field_signals(self):
        print("Подключение сигналов cnc_page")
        self.ui.textEdit_2.textChanged.connect(lambda: self.update_data("textEdit_2"))
        self.ui.lineEdit_22.textChanged.connect(lambda: self.update_data("lineEdit_22"))

    def disconnect_text_field_signals(self):
        try:
            self.ui.textEdit_2.textChanged.disconnect()
            self.ui.lineEdit_22.textChanged.disconnect()
        except RuntimeError:
            print("ИНФО. Отключаемые сигналы не были подключены")

    def auto_select_cnc_item(self, index=0):
        selected_item = self.ui.cnc_list.takeItem(index)
        self.ui.cnc_list.addItem(selected_item)
        self.ui.cnc_list.setItemSelected(selected_item, True)
        self.ui.cnc_list.setCurrentItem(selected_item)
        self.select_cnc(selected_item)

    def get_current_cnc_item(self):
        return self.ui.cnc_list.currentItem()

    @Slot()
    def add_cnc(self):
        def add(name):
            self.disconnect_text_field_signals()
            item = QListWidgetItem()
            item.setText(name)
            self.ui.cnc_list.addItem(item)
            self.db_items.set_item(name, {'name': name}, insert=True)
            self.clean_fields()
            self.auto_select_cnc_item()
            self.connect_text_field_signals()
            dialog.close()
            self.reload()
        dialog = self.get_prompt_dialog("Добавление стойки", label_text="Название стойки, включая версию",
                                        ok_callback=add)
        dialog.show()

    @Slot()
    def remove_cnc(self):
        def ok():
            current_item = self.get_current_cnc_item()
            if not current_item:
                dialog.close()
                return
            cnc_name = current_item.text()
            self.db_items.set_item(cnc_name, delete=True, ready=True, where={"name": cnc_name})
            self.reload()
            dialog.close()
        if not self.get_current_cnc_item():
            return
        dialog = self.get_confirm_dialog("Удалить стойку?", ok_callback=ok)
        dialog.show()

    @Slot()
    def select_cnc(self, item: QListWidgetItem):
        if not item:
            return
        item_name = item.text()
        self.disconnect_text_field_signals()
        self.clean_fields()
        data = self.db_items.get_item(item_name, where={"name": item_name})
        if not data:
            self.reload()
            return
        self.update_fields(data)
        self.validator.set_cnc(item)
        self.validator.refresh()
        self.connect_text_field_signals()

    def update_data(self, field_name):
        current_cnc_item = self.get_current_cnc_item()
        if not current_cnc_item:
            return
        cnc_name = current_cnc_item.text()
        field = getattr(self.ui, field_name)
        value = None
        if isinstance(field, QTextEdit):
            value = field.toPlainText()
        if isinstance(field, QLineEdit):
            value = field.text()
        self.db_items.set_item(cnc_name,
                               {self.__UI__TO_SQL_COLUMN_LINK__LINE_EDIT[field_name]: value
                                }, ready=self.validator.refresh(), update=True, where={"name": cnc_name})

    def update_fields(self, orm_data: dict):
        for line_edit_name, db_field_name in self.__UI__TO_SQL_COLUMN_LINK__LINE_EDIT.items():
            val = orm_data.pop(db_field_name, None)
            input_: QLineEdit = getattr(self.ui, line_edit_name)
            if val:
                input_.setText(str(val))
            else:
                input_.setText("")

    def clean_fields(self):
        for field_name in self.__UI__TO_SQL_COLUMN_LINK__LINE_EDIT:
            field: QLineEdit = getattr(self.ui, field_name)
            field.setText("")


class CncPageValidator(Validator):
    REQUIRED_TEXT_FIELD_VALUES = ("lineEdit_22",)

    def __init__(self, ui):
        super().__init__(ui)
        self.current_cnc = None

    def set_cnc(self, item):
        self.current_cnc = item

    def refresh(self) -> bool:
        valid_status = super().refresh()

        def mark_list_widget_item():
            if valid_status:
                self.set_complete_edit_attributes(self.current_cnc)
            else:
                self.set_not_complete_edit_attributes(self.current_cnc)
        mark_list_widget_item()
        return valid_status
