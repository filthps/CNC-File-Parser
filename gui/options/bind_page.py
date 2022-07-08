from typing import Optional
from PySide2.QtCore import Slot
from database.models import Machine, Operation
from gui.tools import Constructor, Tools
from gui.ui import Ui_main_window


class OptionsPageBind(Constructor, Tools):
    def __init__(self, ui: Ui_main_window, app):
        super().__init__(app, ui)
        self.main_app = app
        self.ui = ui

        def connect_signals():
            self.ui.bind_choice_machine.activated.connect(
                lambda: self.change_machine(self.ui.bind_choice_machine.currentText())
            )
        connect_signals()
        self.initialization()

    def initialization(self):
        machines = Machine.query.all()
        field = self.ui.bind_choice_machine
        field.clear()
        [field.insertItem(0, m.__dict__['machine_name']) for m in machines]

    @Slot(str)
    def change_machine(self, machine_name):
        machine = self.get_machine(machine_name)
        if machine is not None:
            self.update_disabled_operations()
            self.update_enabled_operations()

    def update_disabled_operations(self):
        disabled_operations = Operation.query.all()
        print(disabled_operations)

    def update_enabled_operations(self):
        ...

    @staticmethod
    def get_machine(name) -> Optional[dict]:
        m = Machine.query.filter_by(machine_name=name).first()
        if m is not None:
            return m.__dict__
