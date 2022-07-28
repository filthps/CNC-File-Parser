import re
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QListWidget, QListWidgetItem
from gui.tools import Constructor, Tools
from gui.ui import Ui_main_window
from gui.validation import Validator


class AddCNC(Constructor, Tools):
    def __init__(self, ui: Ui_main_window):
        self.ui = ui

        def connect_signals():
            self.ui.add_button_2.clicked.connect(self.add_cnc)
            self.ui.remove_button_2.clicked.connect(self.remove_cnc)

        connect_signals()

    @Slot()
    def add_cnc(self):
        def add(name):
            item: QListWidgetItem = QListWidgetItem()
            item.setText(name)
            self.ui.add_var_list.addItem(item)
            dialog.close()
        dialog = self.get_prompt_dialog("Добавление стойки", label_text="Название стойки, включая версию",
                                        ok_callback=add)
        dialog.show()

    @Slot()
    def remove_cnc(self):
        def ok():
            pass
        self.get_confirm_dialog("Удалить стойку?", "Все данные")


class AddCNCValidator(Validator):
    REQUIRED_TEXT_FIELD_VALUES = ("var_name_to_save")
    INVALID_TEXT_FIELD_VALUES = {"var_name_to_save": re.compile(""),}
