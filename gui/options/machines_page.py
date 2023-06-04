import re
from typing import Optional
from itertools import repeat
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QListWidgetItem, QLineEdit, QComboBox
from PySide2.QtWidgets import QFileDialog
from gui.validation import Validator
from database.models import Cnc, Machine
from gui import orm
from gui.ui import Ui_main_window as Ui
from gui.tools import Constructor, Tools
from gui.threading import QThreadInstanceDecorator


empty_string = repeat("")



class OptionsPageCreateMachine(Constructor, Tools):
    _UI__TO_SQL_COLUMN_LINK__LINE_EDIT = {"lineEdit_10": "input_catalog",
                                          "lineEdit_21": "output_catalog",
                                          "lineEdit_11": "x_over", "lineEdit_12": "y_over", "lineEdit_13": "z_over",
                                          "lineEdit_14": "x_fspeed", "lineEdit_15": "y_fspeed", "lineEdit_16": "z_fspeed",
                                          "lineEdit_17": "spindele_speed"}
    _UI__TO_SQL_COLUMN_LINK__COMBO_BOX = {"choice_cnc": "name"}
    _COMBO_BOX_DEFAULT_VALUES = {"choice_cnc": "Выберите стойку"}
    _LINE_EDIT_DEFAULT_VALUES = {"lineEdit_10": empty_string, "lineEdit_21": empty_string,
                                 "lineEdit_11": empty_string, "lineEdit_12": empty_string, "lineEdit_13": empty_string,
                                 "lineEdit_14": empty_string, "lineEdit_15": empty_string, "lineEdit_16": empty_string, "lineEdit_17": empty_string}
    _INTEGER_FIELDS = ("lineEdit_11", "lineEdit_12", "lineEdit_13", "lineEdit_14",
                       "lineEdit_15", "lineEdit_16", "lineEdit_17")  # Для замены пустых значений нулями при отправке в бд

    def __init__(self, main_app_instance, ui: Ui):
        self.validator = None
        self.db_items: orm.ORMHelper = main_app_instance.db_items_queue
        self.main_app = main_app_instance
        self.ui = ui
        self.cnc_names = {}  # Хранить словарь названий стоек, чтобы избежать лишних запросов в БД (cncid: name)
        super().__init__(main_app_instance, ui)

        def init_validator():
            self.validator = AddMachinePageValidation(self.ui)

        def set_db_manager_model():
            self.db_items.set_model(Machine)

        set_db_manager_model()
        init_validator()
        self.reload()
        self.connect_main_signals()

    def reload(self, create_thread=True):
        """ Очистить поля и обновить данные из базы данных """
        def callback(machines, cnc_items):
            self.ui.add_machine_list_0.clear()
            for data in machines:
                name = data.pop('machine_name')
                item = QListWidgetItem(name)
                self.ui.add_machine_list_0.addItem(item)
                if self.db_items.is_node_from_cache(machine_name=name):
                    self.validator.set_not_complete_edit_attributes(item)
            self.clear_property_fields()
            self.insert_all_cnc_from_db(cnc_items)
            self.select_machine_item()
            self.connect_fields_signals()

        @QThreadInstanceDecorator(result_callback=callback, in_new_qthread=create_thread)
        def load_items():
            machines = self.db_items.get_items()
            cnc_items = self.db_items.get_items(_model=Cnc, _db_only=True)
            return machines, cnc_items
        load_items()

    def select_machine_item(self, index=0) -> Optional[QListWidgetItem]:
        machine_item: QListWidgetItem = self.ui.add_machine_list_0.takeItem(index)
        if machine_item is None:
            return
        self.ui.add_machine_list_0.addItem(machine_item)
        self.ui.add_machine_list_0.setItemSelected(machine_item, True)
        self.ui.add_machine_list_0.setCurrentItem(machine_item)
        return machine_item

    def connect_main_signals(self):
        """
        Подключение главных сигналов, их отключение, в рамках работы этого класса, не планируется
        """
        self.ui.add_button_0.clicked.connect(self.add_machine)
        self.ui.remove_button_0.clicked.connect(self.remove_machine)

    def connect_fields_signals(self):
        """
        Поключение временных сигналов редактируемых полях
        """
        self.ui.add_machine_list_0.currentItemChanged.connect(lambda current, prev: self.select_machine(current))
        self.ui.choice_cnc.textActivated.connect(lambda str_: self.change_cnc(str_))
        self.ui.add_machine_input.clicked.connect(lambda: self.choice_folder("lineEdit_10"))
        self.ui.add_machine_output.clicked.connect(lambda: self.choice_folder("lineEdit_21"))
        self.ui.lineEdit_11.textChanged.connect(lambda: self.update_data("lineEdit_11"))
        self.ui.lineEdit_12.textChanged.connect(lambda: self.update_data("lineEdit_12"))
        self.ui.lineEdit_13.textChanged.connect(lambda: self.update_data("lineEdit_13"))
        self.ui.lineEdit_14.textChanged.connect(lambda: self.update_data("lineEdit_14"))
        self.ui.lineEdit_15.textChanged.connect(lambda: self.update_data("lineEdit_15"))
        self.ui.lineEdit_16.textChanged.connect(lambda: self.update_data("lineEdit_16"))
        self.ui.lineEdit_17.textChanged.connect(lambda: self.update_data("lineEdit_17"))

    def disconnect_fields_signals(self):
        """
        Отключение сигналов для редактируемых полей.
        Делается для того, чтобы поля, значение в которые добавилось программным путём (при выборе станка),
        не вызывали сигналы, которые,  в свою очередь, инициируют UPDATE в БД.
        """
        try:
            self.ui.add_machine_list_0.currentItemChanged.disconnect()
            self.ui.choice_cnc.textActivated.disconnect()
            self.ui.add_machine_input.clicked.disconnect()
            self.ui.add_machine_output.clicked.disconnect()
            self.ui.lineEdit_11.textChanged.disconnect()
            self.ui.lineEdit_12.textChanged.disconnect()
            self.ui.lineEdit_13.textChanged.disconnect()
            self.ui.lineEdit_14.textChanged.disconnect()
            self.ui.lineEdit_15.textChanged.disconnect()
            self.ui.lineEdit_16.textChanged.disconnect()
            self.ui.lineEdit_17.textChanged.disconnect()
        except RuntimeError:
            print("ИНФО. Отключаемые сигналы не были подключены")

    def insert_all_cnc_from_db(self, cnc_items) -> None:
        """
        Запрос из БД и установка возможных значений в combo box - 'стойки',
        наполнение словаря self.cnc_names
        """
        while cnc_items:
            try:
                data = next(cnc_items)
            except StopIteration:
                break
            cnc_name = data["name"]
            self.cnc_names.update({data["cncid"]: cnc_name})
            self.ui.choice_cnc.addItem(cnc_name)

    @Slot(str)
    def choice_folder(self, line_edit_widget: str):
        selected_directory_name = QFileDialog.getExistingDirectory()
        if selected_directory_name:
            field: QLineEdit = getattr(self.ui, line_edit_widget)
            field.setText(selected_directory_name)
            self.update_data(line_edit_widget)

    @Slot(object)
    def select_machine(self, machine_: QListWidgetItem):
        """ Обновить данные при select в QListWidget -
        обновить все поля свойств станка (поля - Характеристики)"""
        def insert_machine_info_in_ui(machine_instance, cnc_items):
            self.disconnect_fields_signals()
            if not machine_instance:
                self.reload()
                return
            self.clear_property_fields()
            self.insert_all_cnc_from_db(cnc_items)
            cm_box_values = {}
            cnc_name = self.cnc_names.get(machine_instance.pop("cncid", None))
            cm_box_values.update({"name": cnc_name}) if cnc_name else None
            self.update_fields(line_edit_values=machine_instance, combo_box_values=cm_box_values)
            self.validator.set_machine(machine_)
            self.connect_fields_signals()

        @QThreadInstanceDecorator(result_callback=insert_machine_info_in_ui)
        def load_selected_machine():
            machine = self.db_items.get_item(machine_name=machine_item_name)
            cncs = self.db_items.get_items(_model=Cnc, _db_only=True)
            return machine, cncs
        if machine_ is None:
            return
        machine_item_name = machine_.text()
        load_selected_machine()

    @Slot()
    def add_machine(self):
        def error(machine_name: str):
            def callback():
                dialog_.close()
                self.reload(create_thread=False)
            dialog_ = self.get_alert_dialog("Ошибка", f"Станок {machine_name} уже добавлен",
                                            callback=callback)
            dialog_.show()

        def add(machine_name):
            @QThreadInstanceDecorator(result_callback=lambda: self.reload(create_thread=False))
            def inner():
                if self.db_items.get_item(machine_name=machine_name):
                    error(machine_name)
                    return
                self.db_items.set_item(machine_name=machine_name, _insert=True)
            if not machine_name:
                return
            inner()
        dialog = self.get_prompt_dialog("Введите название станка", ok_callback=add)
        dialog.show()

    @Slot()
    def remove_machine(self):
        def ok():
            @QThreadInstanceDecorator(result_callback=lambda: self.reload(create_thread=False))
            def process(name):
                self.db_items.set_item(_delete=True, machine_name=name)
            item: QListWidgetItem = self.ui.add_machine_list_0.currentItem()
            dialog.close()
            if item is None:
                return
            process(item.text())
        dialog = self.get_confirm_dialog("Удалить станок?", "Внимание! Информация о свойствах станка будетм утеряна",
                                         ok_callback=ok)
        dialog.show()

    @Slot(str)
    def update_data(self, field_n):
        """ Обновление записей в базе """
        @QThreadInstanceDecorator()
        def save_data(field_name: str, field_value: str, machine_n: str):
            def check_machine_is_exists():
                m = self.db_items.get_item(_model=Machine, machine_name=machine_n)
                if not m:
                    self.reload(create_thread=False)
            check_machine_is_exists()
            exists_node_type = self.db_items.get_node_dml_type(machine_n)
            sql_column_name = self._UI__TO_SQL_COLUMN_LINK__LINE_EDIT[field_name]
            self.db_items.set_item(**{sql_column_name: self.check_output_values(field_name, value)},
                                   _ready=self.validator.refresh(), machine_name=machine_n,
                                   **{("_update" if exists_node_type == "_update" else "_insert"): True})
        active_machine = self.ui.add_machine_list_0.currentItem()
        if active_machine is None:
            return
        value = getattr(self.ui, field_n).text()
        machine_name = active_machine.text()
        save_data(field_n, value, machine_name)

    @Slot(str)
    def change_cnc(self, cnc_name):
        @QThreadInstanceDecorator()
        def check_exists_machine_and_cnc_and_update_data(current_machine_name: str, selected_cnc_name: str):
            machine = self.db_items.get_item(machine_name=current_machine_name)
            cnc = self.db_items.get_item(_model=Cnc, name=selected_cnc_name)
            if not cnc or not machine:
                self.reload(create_thread=False)
            if selected_cnc_name == self._COMBO_BOX_DEFAULT_VALUES:
                self.db_items.remove_field_from_node(selected_machine_name, "cncid")
                return
            self.db_items.set_item(cncid=cnc["cncid"],
                                   machine_name=current_machine_name,
                                   _update=True, _ready=self.validator.refresh())
        if not cnc_name:
            return
        selected_machine = self.ui.add_machine_list_0.currentItem()
        if not selected_machine:
            return
        selected_machine_name = selected_machine.text()
        check_exists_machine_and_cnc_and_update_data(selected_machine_name, cnc_name)

    def clear_property_fields(self) -> None:
        super().reset_fields_to_default()
        self.cnc_names = {}

    def set_fields_state(self, disabled=False):
        for field_name in self._UI__TO_SQL_COLUMN_LINK__COMBO_BOX:
            item: QComboBox = getattr(self.ui, field_name)
            item.setDisabled(disabled)
        for field_name in self._UI__TO_SQL_COLUMN_LINK__LINE_EDIT:
            item: QLineEdit = getattr(self.ui, field_name)
            item.setDisabled(disabled)
        self.ui.add_machine_input.setDisabled(disabled)
        self.ui.add_machine_output.setDisabled(disabled)


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
        self.ui: Ui = ui
        self.current_machine: Optional[QListWidgetItem] = None

    @property
    def is_valid(self) -> bool:
        return self.refresh()

    def set_machine(self, current):
        self.current_machine = current
        self.refresh()

    def select_cnc(self):
        if self.current_machine:
            self.refresh()

    def refresh(self) -> bool:
        def mark_machine_list_widget_item():
            """ Выделить красным фотном станок или снять выделение """
            if not valid:
                self.set_not_complete_edit_attributes(self.current_machine)
            else:
                self.set_complete_edit_attributes(self.current_machine)
        valid = super().refresh()
        if self.current_machine:
            mark_machine_list_widget_item()
        return valid
