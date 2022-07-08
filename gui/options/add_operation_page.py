from PySide2.QtCore import Slot
from gui.tools import Constructor, Tools
from gui.ui import Ui_main_window


class AddOperationMainPage(Constructor, Tools):
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
        print(operation_type_index)
