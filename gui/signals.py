from PySide2.QtWidgets import QListWidget, QListWidgetItem, QLineEdit
from ui import Ui_main_window as Ui
from database import Database, SQLQuery
from tools import Constructor, Tools
from options import machines_page


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


class Actions(machines_page.OptionsPageActions):
    pass


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
