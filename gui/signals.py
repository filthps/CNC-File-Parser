from PySide2.QtWidgets import QListWidgetItem
from ui import Ui_main_window as Ui
from options import machines_page


class Navigation:
    def __init__(self, ui: Ui):
        self.ui = ui

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
