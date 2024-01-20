from typing import Optional, Iterator
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QListWidgetItem, QLineEdit, QTextEdit
from database.models import Cnc
from gui.orm import orm
from gui.tools import Constructor, Tools
from gui.ui import Ui_main_window
from gui.validation import Validator
from gui.threading_ import QThreadInstanceDecorator


class AddCNC(Constructor, Tools):
    UI__TO_SQL_COLUMN_LINK__LINE_EDIT = {"textEdit_2": "except_symbols", "lineEdit_22": "comment_symbol"}
    LINE_EDIT_DEFAULT_VALUES = {"textEdit_2": "", "lineEdit_22": ""}

    def __init__(self, app, ui: Ui_main_window):
        super().__init__(app, ui)
        self.instance = app
        self.ui = ui
        self.db_items: orm.ORMHelper = app.db_items_queue
        self.validator: Optional[CncPageValidator] = None

        def set_db_manager_model():
            self.db_items.set_model(Cnc)

        def init_validator():
            self.validator = CncPageValidator(self.ui)

        set_db_manager_model()
        init_validator()
        self.reload()
        self.connect_main_signals()

    def reload(self, in_new_qthread: bool = True):
        def insert_cnc_items(cnc_items: Iterator):
            self.disconnect_text_field_signals()
            self.ui.cnc_list.clear()
            items = tuple(cnc_items)
            for item in items:
                list_item = QListWidgetItem(item["name"])
                self.ui.cnc_list.addItem(list_item)
                if self.db_items.is_node_from_cache(name=item["name"]):
                    self.validator.set_not_complete_edit_attributes(list_item)
            self.reset_fields_to_default()
            auto_select_cnc_item(items) if items else None
            self.connect_text_field_signals()

        def auto_select_cnc_item(items, index=0):
            selected_item = self.ui.cnc_list.takeItem(index)
            self.validator.set_cnc(selected_item)
            self.update_fields(line_edit_values=items[index])
            self.ui.cnc_list.addItem(selected_item)
            self.ui.cnc_list.setItemSelected(selected_item, True)
            self.ui.cnc_list.setCurrentItem(selected_item)
            self.validator.refresh()

        @QThreadInstanceDecorator(result_callback=insert_cnc_items, in_new_qthread=in_new_qthread)
        def load_all_cnc():
            items = self.db_items.get_items(_model=Cnc)
            return items
        load_all_cnc()

    def connect_main_signals(self):
        self.ui.add_button_1.clicked.connect(self.add_cnc)
        self.ui.remove_button_1.clicked.connect(self.remove_cnc)

    def connect_text_field_signals(self):
        self.ui.cnc_list.currentItemChanged.connect(lambda cur, prev: self.select_cnc(cur))
        self.ui.textEdit_2.textChanged.connect(lambda: self.update_data("textEdit_2"))
        self.ui.lineEdit_22.textChanged.connect(lambda: self.update_data("lineEdit_22"))

    def disconnect_text_field_signals(self):
        try:
            self.ui.cnc_list.currentItemChanged.disconnect()
            self.ui.textEdit_2.textChanged.disconnect()
            self.ui.lineEdit_22.textChanged.disconnect()
        except RuntimeError:
            print("ИНФО. Отключаемые сигналы не были подключены")

    def get_current_cnc_item(self):
        current_cnc = self.ui.cnc_list.currentItem()
        self.validator.current_cnc = current_cnc if self.validator is not None else None
        return current_cnc

    @Slot()
    def add_cnc(self):
        def add(name):
            @QThreadInstanceDecorator(result_callback=lambda: self.reload(in_new_qthread=False))
            def insert_cnc_item(name_: str):
                self.db_items.set_item(name=name_, _insert=True)
            insert_cnc_item(name)
            dialog.close()
        dialog = self.get_prompt_dialog("Добавление стойки", label_text="Название стойки, включая версию",
                                        ok_callback=add)
        dialog.show()

    @Slot()
    def remove_cnc(self):
        def ok():
            @QThreadInstanceDecorator(result_callback=lambda: self.reload(in_new_qthread=False))
            def delete_cnc(cnc_name_):
                self.db_items.set_item(_delete=True, name=cnc_name_, _ready=True)
            current_item = self.get_current_cnc_item()
            if not current_item:
                dialog.close()
                return
            cnc_name = current_item.text()
            delete_cnc(cnc_name)
            dialog.close()
        if not self.get_current_cnc_item():
            return
        dialog = self.get_confirm_dialog("Удалить стойку?", ok_callback=ok)
        dialog.show()

    def select_cnc(self, item: QListWidgetItem):
        def update_fields(data: Optional[dict]):
            if data is None:
                return
            self.disconnect_text_field_signals()
            self.reset_fields_to_default()
            self.update_fields(line_edit_values=data)
            self.validator.set_cnc(item)
            self.validator.refresh()
            self.connect_text_field_signals()

        @QThreadInstanceDecorator(result_callback=update_fields)
        def load_cnc(item_name):
            data = self.db_items.get_item(name=item_name)
            if not data:
                self.reload(in_new_qthread=False)
                return
            return data
        if not item:
            return
        name = item.text()
        load_cnc(name)

    def update_data(self, field_name):
        @QThreadInstanceDecorator()
        def set_data():
            self.db_items.set_item(name=cnc_name,
                                   **{self.UI__TO_SQL_COLUMN_LINK__LINE_EDIT[field_name]: value},
                                   _ready=self.validator.is_valid, _update=True)
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
        self.validator.refresh()
        set_data()


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
