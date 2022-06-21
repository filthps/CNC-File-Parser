from ui import Ui_MainWindow as Ui


class Navigation:
    def __init__(self, ui: Ui = None):
        self.ui: Ui = ui

        def set_initial_page():
            self.set_initial_page()

        def connect_signals():
            ui.to_converter.clicked.connect(self.nav_converter_main_page)
            ui.to_options.clicked.connect(self.nav_options_page)
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


class Actions:
    def __init__(self, ui: Ui = None):
        self.ui: Ui = ui

        def connect_signals():
            ui.add_button_0.clicked.connect(self.add_machine)
            ui.remove_button_0.clicked.connect(self.remove_machine)
        connect_signals()

    def add_machine(self):
        ...

    def remove_machine(self):
        pass
