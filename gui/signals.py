from typing import Optional, Callable
from PySide2.QtCore import Slot
from ui import Ui_main_window as Ui
from options.cnc_page import AddCNC
from options.machines_page import OptionsPageCreateMachine
from options.add_operation_page import AddOperationMainPage
from options.create_insert import CreateInsert


class Navigation:
    """
    Класс отвечает за корректную работу навигации, в основном по вкладкам QListWidget
    """
    ROOT_TAB_WIDGET = {  # QTabWidget с навигацией по настройкам: Главная|Настройки|Конвертация|Справка
        0: None, 1: None, 2: None, 3: None
    }
    CONVERTER_OPTIONS_TAB_WIDGET = {  # QTabWidget с навигацией по настройкам: Стойки|Станки|Операции|Привязать
        0: AddCNC, 1: OptionsPageCreateMachine, 2: ..., 3: ..., 4: AddOperationMainPage
    }
    TASK_OPTIONS_TAB_WIDGET = {  # Включение/выключение|Поменять последовательность|Добавить

    }

    def __init__(self, app, ui: Ui):
        self.app = app
        self.ui = ui
        self._location: Optional[str] = None

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
                def update_db(nav_place: dict, page_index: int) -> None:
                    self.app.save()
                    self.app.actions.re_init(nav_place[page_index])
                ui.to_converter.clicked.connect(update_db)
                ui.to_options.clicked.connect(update_db)
                ui.root_tab_widget.currentChanged.connect(lambda i: update_db(self.ROOT_TAB_WIDGET, i))
                ui.converter_options.currentChanged.connect(lambda i: update_db(self.CONVERTER_OPTIONS_TAB_WIDGET, i))
                ui.tabWidget_2.currentChanged.connect(lambda i: update_db(self.TASK_OPTIONS_TAB_WIDGET, i))

            content_refresh()
            logo_page()
            tab_widgets()
        connect_ui_signals()
        self.nav_home_page()

    @Slot(int)
    def root_tab_widget_navigator(self, page_index):  # Главная|Настройки|Конвертация|Справка
        if page_index == 0:  # Главная
            self.nav_home_page()
        elif page_index == 1:  # Настройки
            self.set_default_position_create_operation()

    @Slot(int)
    def converter_options_navigator(self, tab_index):  # Стойки|Станки|Условия|Переменные шапки|Задачи
        if tab_index == 1:
            self.set_default_position_create_operation()

    @Slot(int)
    def nav_operation_widget(self, page_index):  # Все_операции|Добавить
        if page_index == 1:  # Установить главную страницу выбора типа создаваемой операции, при нажатии на "задачи"
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
    """
    Класс отвечает за логику работы интерфейса, - форм,
    их инициализацию (постранично QTabWidgetItem), втч работа с базой данных
    """

    def __init__(self, app, ui: Ui):
        self.app = app
        self.ui = ui
        self.current_page_instance = None  # Ссылка на текущий экземпляр класса страницы с логикой интерфейса

    def re_init(self, page: Callable):
        """
        Инициализация экземпляра конкретной(текущей) страницы:
        1) Очистить формы
        2) Запросить из базы данных свежие данные
        3) Вставить данные в формы"""
        if getattr(page, "reload", None) is not None:
            self.current_page_instance = page(self.app, self.ui)
        else:
            raise AttributeError(f"Класс {page.__name__} не обладает методом reload")
