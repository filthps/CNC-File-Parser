from ui import Ui_MainWindow as Ui
from tools import Constructor


class Navigation:
    def __init__(self, ui: Ui):
        self.ui: Ui = ui

        def set_initial_page():
            self.set_initial_page()

        def connect_signals():
            ui.to_converter.clicked.connect(self.nav_converter_main_page)
            ui.to_options.clicked.connect(self.nav_options_page)
            ui.add_machine_list_0.itemClicked.connect(self.nav_list_add_machine_list_0)
        set_initial_page()
        connect_signals()

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

    def nav_list_add_machine_list_0(self):
        # todo: БД



class Actions(Constructor):
    def __init__(self, instance, ui: Ui):
        self.ui: Ui = ui
        super().__init__(instance)

        def connect_signals():
            ui.add_button_0.clicked.connect(self.add_machine)
            ui.remove_button_0.clicked.connect(self.remove_machine)
        connect_signals()

    def add_machine(self):
        # todo: БД
        item = self.get_dialog_create_machine()
        self.ui.add_machine_list_0.addItem(item if item is not None else False)

    def remove_machine(self):
        pass
