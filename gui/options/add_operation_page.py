from PySide2.QtCore import Slot
from gui.tools import Constructor, Tools
from gui.ui import Ui_main_window


class AddOperationMainPage(Constructor, Tools):
    MAP_ = {  # Перенаправление на нужную страницу создания задачи
        0: 0,  # "Выбор типа операции"
        1: 3,  # Перенумеровать программу
        2: 6,  # Заменить символы
        3: 4,  # Вставить
        4: 5,  # Удалить
        5: 1,  # Закомментировать кадр
        6: 2,  # Раскомментировать кадр
    }

    def __init__(self, app, ui: Ui_main_window):
        super().__init__(app, ui)
        self.main_app = app
        self.main_ui = ui

        def connect_signals():
            def go_to_create():  # Выбор типа создаваемой операции
                self.main_ui.operations_select_2.activated.connect(lambda index: self.move_to_create_page(index))
            go_to_create()
        connect_signals()

    @Slot(int)
    def move_to_create_page(self, operation_type_index):
        self.main_ui.stackedWidget_2.setCurrentIndex(self.MAP_[operation_type_index])
