from PySide2.QtCore import Slot
from ui import Ui_main_window as Ui
from options import machines_page, bind_page


class Navigation:
    def __init__(self, app, ui: Ui):
        self.app = app
        self.ui = ui

        def connect_ui_signals():
            def logo_page():
                ui.to_converter.clicked.connect(self.nav_converter_main_page)
                ui.to_options.clicked.connect(self.nav_options_page)

            def tab_widgets():
                ui.root_tab_widget.currentChanged.connect(lambda i: self.tab_widgets_navigator("root_tab_widget", i))
                ui.converter_options.currentChanged.connect(lambda i: self.tab_widgets_navigator("converter_options", i))

            def content_refresh():
                """ На все виджеты, где есть навигация, повесить сигналы синхронизации с БД! """
                def update_db():
                    self.app.save()
                    self.app.actions.re_init()
                ui.to_converter.clicked.connect(update_db)
                ui.to_options.clicked.connect(update_db)
                ui.root_tab_widget.currentChanged.connect(update_db)
                ui.converter_options.currentChanged.connect(update_db)

            content_refresh()
            logo_page()
            tab_widgets()

        connect_ui_signals()
        self.nav_home_page()

    @Slot(str, int)
    def tab_widgets_navigator(self, widget_name, tab_index):
        if widget_name == "root_tab_widget" and tab_index == 0:
            self.nav_home_page()

    def nav_home_page(self):
        self.ui.main_widget.setCurrentIndex(0)

    @Slot()
    def nav_converter_main_page(self):
        self.ui.main_widget.setCurrentIndex(1)
        self.ui.root_tab_widget.setCurrentIndex(2)

    @Slot()
    def nav_options_page(self):
        self.ui.main_widget.setCurrentIndex(1)
        self.ui.root_tab_widget.setCurrentIndex(1)


class Actions:
    def __init__(self, app, ui: Ui):
        self.app = app
        self.ui = ui
        self.options_pages = {
            "CreateMachinePage": machines_page.OptionsPageCreateMachine(self.app, self.ui),
            "OptionsPageBind": bind_page.OptionsPageBind(self.ui, self.app),
        }

    def re_init(self):
        """ Пройтись по всем экземплярам страниц и сделать следующее:
        1) Очистить формы
        2) Запросить из базы данных свежие данные
        3) Вставить данные в формы"""
        for instance in self.options_pages.values():
            method = getattr(instance, "initialization")
            if method is not None:
                method()
