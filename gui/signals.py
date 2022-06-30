from PySide2.QtWidgets import QListWidget, QListWidgetItem
from ui import Ui_main_window as Ui
from database import Database, SQLQuery
from tools import Constructor, Tools


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


class Actions(Constructor, Tools):
    def __init__(self, instance, ui: Ui, db: Database):
        self.main_app = instance
        self.ui: Ui = ui
        self.db = db
        super().__init__(instance, ui)

        def connect_signals():
            ui.add_button_0.clicked.connect(self.add_machine)
            ui.remove_button_0.clicked.connect(self.remove_machine)
            ui.add_machine_list_0.currentItemChanged.connect(lambda current, prev: self.select_machine(current))
            ui.add_machine_input.clicked.connect(self.choice_folder)
            #ui.add_machine_output.clicked.connect()
        connect_signals()

    def choice_folder(self):
        dialog = self.get_folder_choice_dialog()
        dialog.show()
        self._lock_ui()

    def select_machine(self, machine_item: QListWidgetItem):
        def update_machines_list(values):
            ...
        query = SQLQuery()
        query.select("Machine", "*")
        query.where("machine_name", "=", machine_item.text())
        self.db.connect_(query, lambda val: update_machines_list(val))

    def add_machine(self):
        item = self.get_dialog_create_machine()
        if item is not None:
            query = SQLQuery(commit=True, complete=False)
            machine_name = item.text()
            query.insert("Machine",
                         (None, machine_name, None, None, None, None, None, None))
            item = QListWidgetItem(machine_name)
            add_machines_queries = self.main_app.query_commit_list.get(
                "add_machine_list_0",
                self.main_app.query_commit_list.__class__(commit_=True)
            )
            add_machines_queries.update((item.text(), query))
            self.set_not_complete_edit_attributes(item)
            self.ui.add_machine_list_0.addItem(item)

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

    def add_machine_input_path(self):
        ...

    def add_machine_output_path(self):
        ...


class DataLoader:
    """ Начальное заполнение виджетов данными """
    def __init__(self, instance, ui, db):
        self.main_app_instance = instance
        self.ui = ui
        self.db = db

    @staticmethod
    def set_items_to_q_list_widget(widget: [QListWidget], items) -> None:
        """ Загрузить из базы и вставить данные в QListWidget, создав и вставив в него QListWidgetItem"""
        for i in items:
            list_item = QListWidgetItem(str(i))
            widget.addItem(list_item)
