import re
from typing import Optional
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QListWidgetItem, QLineEdit
from PySide2.QtWidgets import QFileDialog
from gui.validation import Validator
from database.models import Cnc, Machine
from gui.ui import Ui_main_window as Ui
from gui.tools import Constructor, Tools


class OptionsPageCreateMachine(Constructor, Tools):
    __UI__TO_SQL_COLUMN_LINK__LINE_EDIT = {"lineEdit_10": "input_catalog",
                                           "lineEdit_21": "output_catalog",
                                           "lineEdit_11": "x_over", "lineEdit_12": "y_over", "lineEdit_13": "z_over",
                                           "lineEdit_14": "x_fspeed", "lineEdit_15": "y_fspeed", "lineEdit_16": "z_fspeed",
                                           "lineEdit_17": "spindele_speed"}
    __UI__TO_SQL_COLUMN_LINK__COMBO_BOX = {"choice_cnc": "name"}
    DEFAULT_COMBO_BOX_CNC_NAME = "Выберите стойку"

    def __init__(self, main_app_instance, ui: Ui):
        self.validator = None
        self.items = {}  # Словарное представление для **распаковки в сессию базы данных
        self.main_app = main_app_instance
        self.ui = ui
        self.cnc_names = {}  # Хранить словарь названий стоек, чтобы избежать лишних запросов в БД (cncid: name)
        super().__init__(main_app_instance, ui)

        def connect_signals():
            ui.add_button_0.clicked.connect(self.add_machine)
            ui.remove_button_0.clicked.connect(self.remove_machine)
            ui.choice_cnc.textActivated.connect(lambda str_: self.change_cnc(str_))
            ui.add_machine_list_0.currentItemChanged.connect(lambda current, prev: self.select_machine(current, prev))
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
        self.reload()
        connect_signals()

    def reload(self):
        """ Очистить поля и обновить данные из базы данных """
        self.ui.add_machine_list_0.clear()
        self.clear_property_fields()
        self.insert_machines_from_db()
        self.insert_machines_from_updates_queque()
        self.insert_all_cnc_from_db()

    def insert_machines_from_db(self):
        machines = Machine.query.all()
        for machine in machines:
            data = machine.__dict__
            name = data.pop('machine_name')
            item = QListWidgetItem(name)
            self.ui.add_machine_list_0.addItem(item)

    def insert_machines_from_updates_queque(self):
        for machine_name, data in self.items.items():
            item = QListWidgetItem(machine_name)
            self.ui.add_machine_list_0.addItem(item)

    def insert_empty_cnc_item(self) -> None:
        self.ui.choice_cnc.addItem(self.DEFAULT_COMBO_BOX_CNC_NAME)

    def insert_all_cnc_from_db(self) -> None:
        cnc_items = Cnc.query.all()
        for instance in cnc_items:
            items = instance.__dict__
            cnc_name = items["name"]
            self.cnc_names.update({items["cncid"]: cnc_name})
            self.ui.choice_cnc.addItem(cnc_name)

    def get_selected_machine_item(self) -> QListWidgetItem:
        return self.ui.add_machine_list_0.currentItem()

    @staticmethod
    def get_cnc_name(cnc_id: int) -> Optional[str]:
        """
        Получить значение столбца name таблицы cnc из БД, найти запись по PK
        :param cnc_id: PK экземпляра 'стойка'
        """
        cnc = Cnc.query.filter_by(cncid=cnc_id).first()
        if cnc is not None:
            return cnc.name

    @staticmethod
    def load_machine_from_database(machine_name: str) -> Optional[Machine]:
        """
        Взять экземпляр таблицы 'станок' из БД
        :param machine_name: значение для поиска по столбцу machine_name
        """
        machine = Machine.query.filter_by(machine_name=machine_name).first()
        return machine

    def update_machine_property_fields(self, line_edit_values: Optional[dict] = None,
                                       combo_box_values: Optional[dict] = None) -> None:
        """ Обновление полей ХАРАКТЕРИСТИКИ в интерфейсе """
        for ui_field, orm_field in self.__UI__TO_SQL_COLUMN_LINK__LINE_EDIT.items():
            if line_edit_values is not None:
                value = line_edit_values.get(orm_field)
                if value is not None:
                    getattr(self.ui, ui_field).setText(str(value))
                else:
                    getattr(self.ui, ui_field).setText("")
            else:
                getattr(self.ui, ui_field).setText("")
        for ui_field, orm_field in self.__UI__TO_SQL_COLUMN_LINK__COMBO_BOX.items():
            if combo_box_values is not None:
                value = combo_box_values.get(orm_field)
                if value is not None:
                    getattr(self.ui, ui_field).setCurrentText(str(value))
                else:
                    getattr(self.ui, ui_field).setCurrentText(self.DEFAULT_COMBO_BOX_CNC_NAME)
            else:
                getattr(self.ui, ui_field).setCurrentText(self.DEFAULT_COMBO_BOX_CNC_NAME)

    @Slot(str)
    def choice_folder(self, line_edit_widget: str):
        def update_field(value):
            field: QLineEdit = getattr(self.ui, line_edit_widget)
            field.setText(value)
            self.update_field(line_edit_widget)
        dialog = QFileDialog.getExistingDirectory()
        if dialog:
            update_field(dialog)

    @Slot(object)
    def select_machine(self, machine_item: QListWidgetItem, previous_machine_item: QListWidgetItem):
        """ Обновить данные при select в QListWidget -
        обновить все поля свойств станка (поля - Характеристики)"""
        if previous_machine_item is None:
            return
        name = machine_item.text()
        self.clear_property_fields()
        machine_db = self.load_machine_from_database(name)
        self.insert_all_cnc_from_db()
        cm_box_values = None
        if machine_db is None:
            current_machine_item = self.items.get(name)
            if current_machine_item is not None:
                current_machine_item = current_machine_item.copy()
                cnc_id = current_machine_item.get("cncid", None)
                if cnc_id is not None:
                    cnc_name = self.cnc_names.get(cnc_id, None)
                    if cnc_name is not None:
                        cm_box_values = {"name": cnc_name}
                        del current_machine_item["cncid"]
            else:
                self.reload()
                return
        else:
            current_machine_item = machine_db.__dict__
            cnc_id = current_machine_item["cncid"]
            del current_machine_item["cncid"]
            cnc_name = self.cnc_names.get(cnc_id, None)
            if cnc_name is not None:
                cm_box_values = {"name": cnc_name}
        self.update_machine_property_fields(line_edit_values=current_machine_item,
                                            combo_box_values=cm_box_values)

    @Slot()
    def add_machine(self):
        def error(machine_name: str):
            dialog_ = self.get_alert_dialog("Ошибка", f"Станок {machine_name} уже добавлен",
                                            callback=lambda: dialog_.close())
            dialog_.show()

        def add(machine_name):
            if self.load_machine_from_database(machine_name) is not None:
                dialog.close()
                error(machine_name)
                return
            machine_data = self.items.get(machine_name)
            if machine_data is None:
                self.items.update({machine_name: {'machine_name': machine_name}})
            else:
                error(machine_name)
                return
            item = QListWidgetItem(machine_name)
            self.ui.add_machine_list_0.addItem(item)
            self.ui.add_machine_list_0.setCurrentItem(item)
            self.clear_property_fields()
            self.insert_all_cnc_from_db()
            dialog.close()
        dialog = self.get_prompt_dialog("Введите название станка", ok_callback=add)
        dialog.show()

    @Slot()
    def remove_machine(self):
        def ok():
            item: QListWidgetItem = self.get_selected_machine_item()
            item_name = item.text()
            if self.load_machine_from_database(item_name) is not None:
                Machine.query.filter_by(machine_name=item_name).delete()
            stored = self.items.get(item_name)
            if stored is not None:
                del stored
            self.clear_property_fields()
            dialog.close()
            self.ui.add_machine_list_0.takeItem(self.ui.add_machine_list_0.row(item))
        dialog = self.get_confirm_dialog("Удалить станок?", "Внимание! Информация о свойствах станка будетм утеряна",
                                         ok_callback=ok)
        dialog.show()

    @Slot(str)
    def update_field(self, field_name):
        """ Обновление записей в базе, при изменении текстовых(LineEdit) полей-характеристик """
        update = False
        active_machine = self.get_selected_machine_item()
        if active_machine is not None:
            machine_name = active_machine.text()
            machine = self.items.get(machine_name)
            if machine is None:
                if self.load_machine_from_database(machine_name) is not None:
                    update = True
                self.items.update({machine_name: {'machine_name': machine_name}})
            else:
                machine.update({self.__UI__TO_SQL_COLUMN_LINK__LINE_EDIT[field_name]: getattr(self.ui, field_name).text()})
        if self.validator.is_valid:
            if not update:
                self.push_items()
            else:
                self.update_items()

    @Slot(str)
    def change_cnc(self, item):
        if not item:
            return
        if item == self.DEFAULT_COMBO_BOX_CNC_NAME:
            selected_machine = self.get_selected_machine_item()
            if selected_machine is None:
                return
            machine_local_instance = self.items.get(selected_machine.text(), None)
            machine_local_instance.update({"cncid": None})
            return
        cnc_db_instance = Cnc.query.filter_by(name=item).first()
        if cnc_db_instance is None:
            self.reload()
        selected_machine = self.get_selected_machine_item()
        if selected_machine is not None:
            selected_machine_name = selected_machine.text()
            machine_local_instance = self.items.get(selected_machine_name, None)
            if machine_local_instance is None:
                machine_db_instance = self.load_machine_from_database(selected_machine_name)
                if machine_db_instance is None:
                    self.reload()
            machine_data = self.items.get(selected_machine_name, None)
            if machine_data is not None:
                #  Станок только что добавлен в ui, - его ещё нет в базе данных
                #  Он находится в словаре self.items
                machine_data.update({"cncid": cnc_db_instance.cncid})
            else:
                self.update_items()

    def clear_property_fields(self) -> None:
        """
        Установить в стандартное значение все поля ХАРАКТЕРИСТИКИ
        """
        self.ui.choice_cnc.clear()
        self.insert_empty_cnc_item()
        self.ui.choice_cnc.setCurrentIndex(0)
        [getattr(self.ui, field_name).setText("") for field_name in self.__UI__TO_SQL_COLUMN_LINK__LINE_EDIT]
        self.cnc_names = {}

    def push_items(self):
        """ SQL INSERT """
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
    REQUIRED_COMBO_BOX = ("choice_cnc",)
    COMBO_BOX_DEFAULT_VALUES = {"choice_cnc": "Выберите стойку"}

    def __init__(self, ui):
        super().__init__(ui)
        self._is_valid = False
        self.ui: Ui = ui
        self.current_machine: Optional[QListWidgetItem] = None

        def connect_signals():
            ui.add_machine_list_0.itemEntered.connect(lambda item: self.select_machine(item))
            ui.add_machine_list_0.currentItemChanged.connect(lambda current, prev: self.select_machine(current))
            ui.choice_cnc.currentTextChanged.connect(self.select_cnc)
            ui.lineEdit_10.textChanged.connect(self.refresh)
            ui.lineEdit_21.textChanged.connect(self.refresh)
            ui.lineEdit_11.textChanged.connect(self.refresh)
            ui.lineEdit_12.textChanged.connect(self.refresh)
            ui.lineEdit_13.textChanged.connect(self.refresh)
            ui.lineEdit_14.textChanged.connect(self.refresh)
            ui.lineEdit_15.textChanged.connect(self.refresh)
            ui.lineEdit_16.textChanged.connect(self.refresh)
        connect_signals()

    def select_machine(self, current):
        self.current_machine = current
        self.refresh()

    def select_cnc(self):
        if self.current_machine is not None:
            self.refresh()

    def refresh(self):
        valid = super().refresh()
        if self.current_machine is not None:
            def mark_machine_list_widget_item():
                """ Выделить красным фотном станок или снять выделение """
                if not valid:
                    self.set_not_complete_edit_attributes(self.current_machine.text(), self.current_machine)
                else:
                    self.set_complete_edit_attributes(self.current_machine)
            mark_machine_list_widget_item()
