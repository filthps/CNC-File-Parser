from typing import Optional, Callable
from PySide2.QtCore import Slot
from ui import Ui_main_window as Ui
from options.cnc_page import AddCNC
from options.machines_page import OptionsPageCreateMachine
from options.add_operation_page import AddOperationMainPage
from options.conditions_page import ConditionsPage
from options.create_insert import CreateInsert


class Navigation:
    """
    Класс отвечает за корректную работу навигации, в основном по вкладкам QListWidget
    """
    ROOT_TAB_WIDGET = {  # QTabWidget с навигацией по настройкам: Главная|Настройки|Конвертация|Справка
        0: None, 1: None, 2: None, 3: None
    }
    CONVERTER_OPTIONS_TAB_WIDGET = {  # QTabWidget с навигацией по настройкам: Стойки|Станки|Условия|Переменные шапки|задачи
        0: AddCNC, 1: OptionsPageCreateMachine, 2: ConditionsPage, 3: None, 4: AddOperationMainPage
    }
    TASK_OPTIONS_TAB_WIDGET = {  # Включение/выключение|Поменять последовательность|Добавить

    }
    app = None
    ui = None
    _location: Optional[str] = None
    
    @classmethod
    def set_up(cls, application, ui: Ui):
        cls.app = application
        cls.ui = ui
    
        def connect_ui_signals():
            def logo_page():
                ui.to_converter.clicked.connect(cls.nav_converter_main_page)
                ui.to_options.clicked.connect(cls.nav_options_page)

            def tab_widgets():
                ui.root_tab_widget.currentChanged.connect(lambda i: cls.root_tab_widget_navigator(i))
                ui.converter_options.currentChanged.connect(lambda i: cls.converter_options_navigator(i))
                ui.tabWidget_2.currentChanged.connect(lambda i: cls.nav_operation_widget(i))

            def content_refresh():
                """ На все виджеты, где есть навигация, повесить сигналы синхронизации с БД! """
                def update_db(nav_place: dict, page_index: int) -> None:
                    cls.app.actions.re_init(nav_place[page_index])
                ui.to_converter.clicked.connect(update_db)
                ui.to_options.clicked.connect(update_db)
                ui.root_tab_widget.currentChanged.connect(lambda i: update_db(cls.ROOT_TAB_WIDGET, i))
                ui.converter_options.currentChanged.connect(lambda i: update_db(cls.CONVERTER_OPTIONS_TAB_WIDGET, i))
                ui.tabWidget_2.currentChanged.connect(lambda i: update_db(cls.TASK_OPTIONS_TAB_WIDGET, i))

            content_refresh()
            logo_page()
            tab_widgets()
        connect_ui_signals()
        cls.nav_home_page()
        return cls

    @classmethod
    @Slot(int)
    def root_tab_widget_navigator(cls, page_index):  # Главная|Настройки|Конвертация|Справка
        if page_index == 0:  # Главная
            cls.nav_home_page()
        elif page_index == 1:  # Настройки
            cls.set_default_position_create_operation()

    @classmethod
    @Slot(int)
    def converter_options_navigator(cls, tab_index):  # Стойки|Станки|Условия|Переменные шапки|Задачи
        if tab_index == 1:
            cls.set_default_position_create_operation()

    @classmethod
    @Slot(int)
    def nav_operation_widget(cls, page_index):  # Все_операции|Добавить
        if page_index == 1:  # Установить главную страницу выбора типа создаваемой операции, при нажатии на "задачи"
            cls.set_default_position_create_operation()

    @classmethod
    def nav_home_page(cls):
        cls.ui.main_widget.setCurrentIndex(0)

    @classmethod
    @Slot()
    def nav_converter_main_page(cls):
        cls.ui.main_widget.setCurrentIndex(1)
        cls.ui.root_tab_widget.setCurrentIndex(2)

    @classmethod
    @Slot()
    def nav_options_page(cls):
        cls.ui.main_widget.setCurrentIndex(1)
        cls.ui.root_tab_widget.setCurrentIndex(1)
        cls.set_default_position_create_operation()

    @classmethod
    def set_default_position_create_operation(cls):
        cls.ui.stackedWidget_2.setCurrentIndex(0)  # Установить страницу "Выбор типа операции"
        cls.ui.operations_select_2.setCurrentIndex(0)  # Установить Категория задачи: "Выбрать типа операции"


class Actions:
    """
    Класс отвечает за логику работы интерфейса, - форм,
    их инициализацию (постранично QTabWidgetItem)
    """
    app = None
    ui = None
    current_page_instance = None  # Ссылка на текущий экземпляр класса страницы с логикой интерфейса

    @classmethod
    def set_up(cls, main_app, ui: Ui):
        cls.app = main_app
        cls.ui = ui
        return cls

    @classmethod
    def re_init(cls, page: Callable):
        """
        Инициализация экземпляра конкретной(текущей) страницы:
        1) Очистить формы
        2) Запросить из базы данных свежие данные
        3) Вставить данные в формы"""
        if getattr(page, "reload", None) is not None:
            cls.current_page_instance = page(cls.app, cls.ui)
        else:
            raise AttributeError(f"Класс {page.__name__} не обладает методом reload")
