import re
from PySide2.QtCore import Slot
from gui.tools import Constructor, Tools
from gui.ui import Ui_main_window
from gui.validation import Validator


class CreateInsert(Constructor, Tools):
    def __init__(self, app, ui: Ui_main_window):
        super().__init__(app, ui)
        self.main_app = app
        self.ui = ui

        def connect_signals():
            self.ui.radioButton.toggled.connect(lambda v: self.radio_button_value("radioButton", v))
            self.ui.radioButton_2.toggled.connect(lambda v: self.radio_button_value("radioButton_2", v))
        connect_signals()

        def init_validator():
            self.validator = CreateInsertValidator(ui)
        init_validator()

    def radio_button_value(self, widget_name, v):
        print(widget_name, v)


class CreateInsertValidator(Validator):
    REQUIRED_RADIO_BUTTONS = {
        "groupBox": ("radioButton", "radioButton_2",),
        "groupBox_2": ("radioButton_5", "radioButton_4",),
    }
    REQUIRED_TEXT_FIELD_VALUES = ("lineEdit_3", "lineEdit_4",)

    def __init__(self, ui):
        super().__init__(ui)

        def connect_signals():
            self.ui.radioButton.toggled.connect(self.refresh)
            self.ui.radioButton_2.toggled.connect(self.refresh)
            self.ui.radioButton_5.toggled.connect(self.refresh)
            self.ui.radioButton_4.toggled.connect(self.refresh)
            self.ui.lineEdit_3.textChanged.connect(self.refresh)
            self.ui.lineEdit_4.textChanged.connect(self.refresh)
        connect_signals()

    def refresh(self):
        super().refresh()
        if self.is_valid:
            self.ui.commandLinkButton_3.setEnabled(True)
        else:
            self.ui.commandLinkButton_3.setEnabled(False)


