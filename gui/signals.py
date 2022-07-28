from PySide2.QtCore import Slot
from ui import Ui_main_window as Ui
from options.machines_page import OptionsPageCreateMachine
from options.add_operation_page import AddOperationMainPage
from options.create_insert import CreateInsert


class Navigation:
    def __init__(self, app, ui: Ui):
        self.app = app
        self.ui = ui

        def connect_ui_signals():
            def logo_page():
                ui.to_converter.clicked.connect(self.nav_converter_main_page)
                ui.to_options.clicked.connect(self.nav_options_page)

            def tab_widgets():
                ui.root_tab_widget.currentChanged.connect(lambda i: self.root_tab_widget_navigator(i))
                ui.converter_options.currentChanged.connect(lambda i: self.converter_options_navigator(i))
                ui.tabWidget_2.currentChanged.connect(lambda i: self.nav_operation_widget(i))

            def content_refresh():
                """ На все виджеты, где есть навигация, повесить сигналы синхронизации с БД! """
                def update_db():
                    self.app.save()
                    self.app.actions.re_init()
                ui.to_converter.clicked.connect(update_db)
                ui.to_options.clicked.connect(update_db)
                ui.root_tab_widget.currentChanged.connect(update_db)
                ui.converter_options.currentChanged.connect(update_db)
                ui.tabWidget_2.currentChanged.connect(update_db)

            content_refresh()
            logo_page()
            tab_widgets()

        connect_ui_signals()
        self.nav_home_page()

    @Slot(int)
    def root_tab_widget_navigator(self, page_index):  # Главная|Настройки|Конвертация
        if page_index == 0:
            self.nav_home_page()
        elif page_index == 1:
            self.set_default_position_create_operation()

    @Slot(int)
    def converter_options_navigator(self, tab_index):  # Станки|Операции|Привязать
        if tab_index == 1:
            self.set_default_position_create_operation()

    @Slot(int)
    def nav_operation_widget(self, page_index):  # Все_операции|Добавить
        if page_index == 1:
            self.set_default_position_create_operation()

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
        self.set_default_position_create_operation()

    def set_default_position_create_operation(self):
        self.ui.stackedWidget_2.setCurrentIndex(0)  # Установить страницу "Выбор типа операции"
        self.ui.operations_select_2.setCurrentIndex(0)  # Установить Категория задачи: "Выбрать типа операции"


class Actions:
    def __init__(self, app, ui: Ui):
        self.app = app
        self.ui = ui
        self.options_pages = {
            "CreateMachinePage": OptionsPageCreateMachine(self.app, self.ui),  # Страница "станки"
            "CreateCNCPage": ...,
            "AddOperationMainPage": AddOperationMainPage(app, ui),  # Страница "Выбор типа операции"
            "CreateInsert": CreateInsert(app, ui),  # Страница вставить кадр
        }

    def re_init(self):
        """ Пройтись по всем экземплярам страниц и сделать следующее:
        1) Очистить формы
        2) Запросить из базы данных свежие данные
        3) Вставить данные в формы"""
        for instance in self.options_pages.values():
            method = getattr(instance, "initialization", None)
            if method is not None:
                method()
