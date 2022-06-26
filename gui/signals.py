from PySide2.QtWidgets import QListWidgetItem
from ui import Ui_MainWindow as Ui
from database import Database, SQLQuery
from tools import Constructor


class Navigation:
    def __init__(self, ui: Ui, db: Database):
        self.ui = ui
        self.db = db

        def set_initial_page():
            self.set_initial_page()

        def connect_ui_signals():
            ui.to_converter.clicked.connect(self.nav_converter_main_page)
            ui.to_options.clicked.connect(self.nav_options_page)
            ui.add_machine_list_0.itemClicked.connect(self.nav_list_add_machine_list_0)
        set_initial_page()
        connect_ui_signals()

    def set_initial_page(self):
        self.ui.main_widget.setCurrentIndex(0)

    def nav_home_page(self):
        self.ui.main_widget.setCurrentIndex(0)

    def nav_converter_main_page(self):
        self.ui.main_widget.setCurrentIndex(1)
        self.ui.root_tab_widget.setCurrentIndex(2)

    def nav_options_page(self):
        self.ui.main_widget.setCurrentIndex(1)
        self.ui.root_tab_widget.setCurrentIndex(1)

    def nav_list_add_machine_list_0(self, item: QListWidgetItem):
        ...


class Actions(Constructor):
    def __init__(self, instance, ui: Ui, db: Database):
        self.main_app = instance
        self.ui: Ui = ui
        self.db = db
        super().__init__(instance, ui)

        def connect_signals():
            ui.add_button_0.clicked.connect(self.add_machine)
            ui.remove_button_0.clicked.connect(self.remove_machine)
            ui.add_machine_list_0.currentItemChanged.connect(lambda current, prev: print(current.text()))
        connect_signals()

    def select_machine(self):
        ...

    def add_machine(self):
        item = self.get_dialog_create_machine()
        if item is not None:
            query = SQLQuery()
            machine_name = item.text()
            query.insert("Machine", (machine_name,))
            self.main_app.query_list.append(query)
            self.ui.add_machine_list_0.addItem(QListWidgetItem(machine_name))

    def remove_machine(self):
        def get_selected_item() -> QListWidgetItem:
            return self.ui.add_machine_list_0.currentRow()

        def ok():
            query = SQLQuery()
            query.delete("Machine", "machine_name", "=", get_selected_item().getText())
            self._unlock_ui()

        dialog = self.get_confirm_dialog("Удалить станок?", "Внимание! Информация о свойствах станка будетм утеряна",
                                         cancell_callback=self._unlock_ui, ok_callback=ok)
        self._lock_ui()
        dialog.show()
