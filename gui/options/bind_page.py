from typing import Optional
from PySide2.QtCore import Slot
from database.models import Machine, Operation
from gui.tools import Constructor, Tools
from gui.ui import Ui_main_window


class OptionsPageBind(Constructor, Tools):
    def __init__(self, ui: Ui_main_window, app):
        self.main_app = app
        self.ui = ui

        def connect_signals():
            self.ui.bind_choice_machine.activated.connect(
                lambda: self.change_machine(self.ui.bind_choice_machine.currentText())
            )

        def initialization():
            machine = Machine.query.first()
            if machine is not None:
                self.change_machine(machine.__dict__['machine_name'])
        connect_signals()
        initialization()

    @Slot(str)
    def change_machine(self, machine_name):
        machine = self.get_machine(machine_name)
        if machine is not None:
            o = Operation.query.filter_by()

    def update_disabled_operations(self):
        ...

    def update_enabled_operations(self):
        ...

    @staticmethod
    def get_machine(name) -> Optional[dict]:
        m = Machine.query.filter_by(machine_name=name).first()
        if m is not None:
            return m.__dict__

