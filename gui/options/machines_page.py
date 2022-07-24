import re
from typing import Optional
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QListWidgetItem, QLineEdit
from PySide2.QtWidgets import QFileDialog
from gui.validation import Validator
from database.models import Machine
from gui.ui import Ui_main_window as Ui
from gui.tools import Constructor, Tools


class OptionsPageCreateMachine(Constructor, Tools):
    __UI__TO_SQL_COLUMN_LINK = {"lineEdit_10": "input_catalog", "lineEdit_21": "output_catalog",
                                "lineEdit_11": "x_over", "lineEdit_12": "y_over", "lineEdit_13": "z_over",
                                "lineEdit_14": "x_fspeed", "lineEdit_15": "y_fspeed", "lineEdit_16": "z_fspeed",
                                "lineEdit_17": "spindele_speed"}

    def __init__(self, main_app_instance, ui: Ui):
        self.validator = None
        self.items = {}  # Словарное представление для **распаковки в сессию базы данных
        self.main_app = main_app_instance
        self.ui = ui
        super().__init__(main_app_instance, ui)

        def connect_signals():
            ui.add_button_0.clicked.connect(self.add_machine)
            ui.remove_button_0.clicked.connect(self.remove_machine)
            ui.add_machine_list_0.currentItemChanged.connect(lambda current, prev: self.select_machine(current))
            ui.add_machine_input.clicked.connect(lambda: self.choice_folder("lineEdit_10"))
            ui.add_machine_output.clicked.connect(lambda: self.choice_folder("lineEdit_21"))
            ui.lineEdit_11.editingFinished.connect(lambda: self.update_field("lineEdit_11"))
            ui.lineEdit_12.editingFinished.connect(lambda: self.update_field("lineEdit_12"))
            ui.lineEdit_13.editingFinished.connect(lambda: self.update_field("lineEdit_13"))
            ui.lineEdit_14.editingFinished.connect(lambda: self.update_field("lineEdit_14"))
            ui.lineEdit_15.editingFinished.connect(lambda: self.update_field("lineEdit_15"))
            ui.lineEdit_16.editingFinished.connect(lambda: self.update_field("lineEdit_16"))
            ui.lineEdit_17.editingFinished.connect(lambda: self.update_field("lineEdit_17"))

        def init_validator():
            self.validator = AddMachinePageValidation(self.ui)

        init_validator()
        self.initialization()
        connect_signals()

    def initialization(self):
        """ Обновить данные из базы данных """
        def clear_all():
            item = self.ui.add_machine_list_0.takeItem(0)
            while item is not None:
                item = self.ui.add_machine_list_0.takeItem(0)
            self.__update_form()
        clear_all()
        item_ = None  # Выбрать последнюю активной, если есть хотя бы одна

        def load_from_db():
            nonlocal item_
            machines = Machine.query.all()
            for machine in machines:
                data = machine.__dict__
                self.__update_form(data)
                name = data.pop('machine_name')
                item = QListWidgetItem(name)
                item_ = item
                self.ui.add_machine_list_0.addItem(item)

        def load_from_updates_queque():
            nonlocal item_
            for machine_name, data in self.items.items():
                self.__update_form(data)
                item = QListWidgetItem(machine_name)
                item_ = item
                self.ui.add_machine_list_0.addItem(item)

        load_from_db()
        load_from_updates_queque()
        if item_ is not None:
            self.ui.add_machine_list_0.setCurrentItem(item_)

    def get_selected_item(self) -> QListWidgetItem:
        return self.ui.add_machine_list_0.currentItem()

    @staticmethod
    def get_machine_from_database(machine_name) -> dict:
        machine = Machine.query.filter_by(machine_name=machine_name).first()
        if machine is not None:
            return machine.__dict__

    def __update_form(self, values: Optional[dict] = None):
        """ Обновление полей в интерфейсе """
        for ui_field, orm_field in self.__UI__TO_SQL_COLUMN_LINK.items():
            if values is not None:
                value = values.get(orm_field)
                if value is not None:
                    getattr(self.ui, ui_field).setText(str(value))
            else:
                getattr(self.ui, ui_field).setText("")

    @Slot(str)
    def choice_folder(self, output_line_edit_widget: str):
        def update_field(value):
            field: QLineEdit = getattr(self.ui, output_line_edit_widget)
            field.setText(value)
            self.update_field(output_line_edit_widget)
        dialog = QFileDialog.getExistingDirectory()
        if dialog:
            update_field(dialog)

    @Slot(object)
    def select_machine(self, machine_item: QListWidgetItem):
        """ Обновить данные при select в QListWidget -
        обновить все поля свойств станка (поля - Характеристики)"""
        if machine_item is not None:
            name = machine_item.text()
            self.clear_fields()
            data = self.get_machine_from_database(name)
            if data is None:
                item_ = self.items.get(name)
                if item_ is not None:
                    self.__update_form(item_)
                    self.validator.refresh()
                else:
                    self.initialization()
                    return
            else:
                self.__update_form(data)
                self.validator.refresh()

    @Slot()
    def add_machine(self):
        def add(machine_name):
            if self.get_machine_from_database(machine_name) is not None:
                dialog.close()
                dialog_ = self.get_alert_dialog("Ошибка", f"Станок {machine_name} уже добавлен",
                                                callback=lambda: dialog_.close())
                dialog_.show()
                return
            machine_data = self.items.get(machine_name)
            if machine_data is None:
                self.items.update({machine_name: {'machine_name': machine_name}})
            else:
                self.__update_form(machine_data)
                return
            item = QListWidgetItem(machine_name)
            self.ui.add_machine_list_0.addItem(item)
            self.ui.add_machine_list_0.setCurrentItem(item)
            self.clear_fields()
            dialog.close()
        dialog = self.get_prompt_dialog("Введите название станка", ok_callback=add)
        dialog.show()

    @Slot()
    def remove_machine(self):
        def ok():
            item: QListWidgetItem = self.get_selected_item()
            item_name = item.text()
            if self.get_machine_from_database(item_name) is not None:
                print(True)
                Machine.query.filter_by(machine_name=item_name).delete()
            stored = self.items.get(item_name)
            if stored is not None:
                del stored
            self.clear_fields()
            dialog.close()
            self.ui.add_machine_list_0.takeItem(self.ui.add_machine_list_0.row(item))

        dialog = self.get_confirm_dialog("Удалить станок?", "Внимание! Информация о свойствах станка будетм утеряна",
                                         ok_callback=ok)
        dialog.show()

    @Slot(str)
    def update_field(self, field_name):
        """ Обновление записей в базе, при изменении полей-характеристик """
        update = False
        active_machine = self.get_selected_item()
        if active_machine is not None:
            machine_name = active_machine.text()
            machine = self.items.get(machine_name)
            if machine is None:
                if self.get_machine_from_database(machine_name) is not None:
                    update = True
                self.items.update({machine_name: {'machine_name': machine_name}})
            machine = self.items[machine_name]
            machine.update({self.__UI__TO_SQL_COLUMN_LINK[field_name]: getattr(self.ui, field_name).text()})
        if self.validator.is_valid:
            if not update:
                self.push_items()
            else:
                self.update_items()

    def clear_fields(self):
        """ Поставить пустые значения во все поля ХАРАКТЕРИСТИКИ """
        [getattr(self.ui, field_name).setText("") for field_name in self.__UI__TO_SQL_COLUMN_LINK]

    def push_items(self):
        """ SQL INSERT добавить сессию """
        session = self.main_app.db_session
        while self.items:
            machine_name, data = self.items.popitem()
            session.add(Machine(**data))
        session.commit()

    def update_items(self):
        """ SQL UPDATE """
        session = self.main_app.db_session
        while self.items:
            machine_name, data = self.items.popitem()
            del data['machine_name']
            query = Machine.query.filter_by(machine_name=machine_name).first()
            [setattr(query, k, v) for k, v in data.items()]
            session.add(query)
            session.commit()


class AddMachinePageValidation(Validator):
    REQUIRED_TEXT_FIELD_VALUES = ("lineEdit_10", "lineEdit_21",)
    INVALID_TEXT_FIELD_VALUES = {
        "lineEdit_10": re.compile(r"\d"),
        "lineEdit_21": re.compile(r"\d"),
        "lineEdit_11": re.compile(r"\D"),
        "lineEdit_12": re.compile(r"\D"),
        "lineEdit_13": re.compile(r"\D"),
        "lineEdit_14": re.compile(r"\D"),
        "lineEdit_15": re.compile(r"\D"),
        "lineEdit_16": re.compile(r"\D"),
    }

    def __init__(self, ui):
        super().__init__(ui)
        self._is_valid = False
        self.ui: Ui = ui
        self.current_machine: Optional[QListWidgetItem] = None

        def connect_signals():
            ui.add_machine_list_0.itemEntered.connect(lambda item: self.__select_machine(item, None))
            ui.add_machine_list_0.currentItemChanged.connect(lambda current, prev: self.__select_machine(prev, current))
            ui.lineEdit_10.textChanged.connect(self.refresh)
            ui.lineEdit_21.textChanged.connect(self.refresh)
            ui.lineEdit_11.textChanged.connect(self.refresh)
            ui.lineEdit_12.textChanged.connect(self.refresh)
            ui.lineEdit_13.textChanged.connect(self.refresh)
            ui.lineEdit_14.textChanged.connect(self.refresh)
            ui.lineEdit_15.textChanged.connect(self.refresh)
            ui.lineEdit_16.textChanged.connect(self.refresh)
        connect_signals()

    def __select_machine(self, prev, current):
        if prev is not None:
            self.set_complete_edit_attributes(prev)
        self.current_machine = current
        self.refresh()

    def refresh(self):
        valid = super().refresh()
        if self.current_machine is not None:
            if not valid:
                self.set_not_complete_edit_attributes(self.current_machine.text())
            else:
                self.set_complete_edit_attributes(self.current_machine)
