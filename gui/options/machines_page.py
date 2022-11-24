import re
from typing import Optional
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QListWidgetItem, QLineEdit
from PySide2.QtWidgets import QFileDialog
from gui.validation import Validator
from database.models import Cnc, Machine
from gui.ui import Ui_main_window as Ui
from gui.tools import Constructor, Tools, ORMHelper


class OptionsPageCreateMachine(Constructor, Tools):
    __UI__TO_SQL_COLUMN_LINK__LINE_EDIT = {"lineEdit_10": "input_catalog",
                                           "lineEdit_21": "output_catalog",
                                           "lineEdit_11": "x_over", "lineEdit_12": "y_over", "lineEdit_13": "z_over",
                                           "lineEdit_14": "x_fspeed", "lineEdit_15": "y_fspeed", "lineEdit_16": "z_fspeed",
                                           "lineEdit_17": "spindele_speed"}
    __UI__TO_SQL_COLUMN_LINK__COMBO_BOX = {"choice_cnc": "name"}
    DEFAULT_COMBO_BOX_CNC_NAME = "Выберите стойку"
    INTEGER_FIELDS_LINE_EDIT = ("lineEdit_11", "lineEdit_12", "lineEdit_13", "lineEdit_14",
                                "lineEdit_15", "lineEdit_16", "lineEdit_17")  # Для замены пустых значений нулями при отправке в бд

    def __init__(self, main_app_instance, ui: Ui):
        self.validator = None
        self.db_items: ORMHelper = main_app_instance.db_items_queue
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

    def reload(self):
        """ Очистить поля и обновить данные из базы данных """
        self.disconnect_fields_signals()
        self.clear_property_fields()
        self.ui.add_machine_list_0.clear()
        self.insert_all_cnc_from_db()
        self.insert_machines_from_db()
        self.auto_select_machine_item()
        self.connect_fields_signals()

    def connect_main_signals(self):
        """
        Подключение главных сигналов, их отключение, в рамках работы этого класса, не планируется
        """
        self.ui.add_button_0.clicked.connect(self.add_machine)
        self.ui.remove_button_0.clicked.connect(self.remove_machine)
        self.ui.add_machine_list_0.currentItemChanged.connect(lambda current, prev: self.select_machine(current))

    def connect_fields_signals(self):
        """
        Поключение временных сигналов редактируемых полях
        """
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

    def auto_select_machine_item(self, index=0) -> None:
        """
        Выделить станок в списке автоматически, после инициализации
        :param index: Индекс QListWidgetItem в QListWidget
        """
        if len(self.db_items.get_items()):
            machine_item: QListWidgetItem = self.ui.add_machine_list_0.takeItem(index)
            self.ui.add_machine_list_0.addItem(machine_item)
            self.ui.add_machine_list_0.setItemSelected(machine_item, True)
            self.ui.add_machine_list_0.setCurrentItem(machine_item)
            self.select_machine(machine_item)

    def insert_machines_from_db(self):
        machines = self.db_items.get_items()
        for data in machines:
            name = data.pop('machine_name')
            item = QListWidgetItem(name)
            self.ui.add_machine_list_0.addItem(item)

    def insert_empty_cnc_item(self) -> None:
        self.ui.choice_cnc.addItem(self.DEFAULT_COMBO_BOX_CNC_NAME)

    def insert_all_cnc_from_db(self) -> None:
        """
        Запрос из БД и установка возможных значений в combo box - 'стойки',
        наполнение словаря self.cnc_names
        """
        cnc_items = self.db_items.get_items(model=Cnc)
        for data in cnc_items:
            cnc_name = data["name"]
            self.cnc_names.update({data["cncid"]: cnc_name})
            self.ui.choice_cnc.addItem(cnc_name)

    def get_selected_machine_item(self) -> Optional[QListWidgetItem]:
        return self.ui.add_machine_list_0.currentItem()

    def update_machine_property_fields(self, line_edit_values: Optional[dict] = None,
                                       combo_box_values: Optional[dict] = None) -> None:
        """ Обновление полей ХАРАКТЕРИСТИКИ в интерфейсе """
        for ui_field, orm_field in self.__UI__TO_SQL_COLUMN_LINK__LINE_EDIT.items():
            if line_edit_values:
                value = line_edit_values.get(orm_field)
                if value:
                    getattr(self.ui, ui_field).setText(str(value))
                else:
                    getattr(self.ui, ui_field).setText("")
            else:
                getattr(self.ui, ui_field).setText("")
        for ui_field, orm_field in self.__UI__TO_SQL_COLUMN_LINK__COMBO_BOX.items():
            if combo_box_values:
                value = combo_box_values.get(orm_field)
                if value:
                    getattr(self.ui, ui_field).setCurrentText(str(value))
                else:
                    getattr(self.ui, ui_field).setCurrentText(self.DEFAULT_COMBO_BOX_CNC_NAME)
            else:
                getattr(self.ui, ui_field).setCurrentText(self.DEFAULT_COMBO_BOX_CNC_NAME)

    @Slot(str)
    def choice_folder(self, line_edit_widget: str):
        def update_data(value):
            field: QLineEdit = getattr(self.ui, line_edit_widget)
            field.setText(value)
            self.update_data(line_edit_widget)
        dialog = QFileDialog.getExistingDirectory()
        if dialog:
            update_data(dialog)

    @Slot(object)
    def select_machine(self, machine_item: QListWidgetItem):
        """ Обновить данные при select в QListWidget -
        обновить все поля свойств станка (поля - Характеристики)"""
        if not machine_item:
            return
        name = machine_item.text()
        machine = self.db_items.get_item(name, where={"machine_name": name})
        if not machine:
            self.reload()
            return
        self.disconnect_fields_signals()
        self.clear_property_fields()
        self.insert_all_cnc_from_db()
        cm_box_values = {}
        cnc_name = self.cnc_names.get(machine.pop("cncid", None))
        cm_box_values.update({"name": cnc_name}) if cnc_name else None
        self.update_machine_property_fields(line_edit_values=machine,
                                            combo_box_values=cm_box_values)
        self.connect_fields_signals()
        self.validator.set_machine(machine_item)

    @Slot()
    def add_machine(self):
        def error(machine_name: str):
            def callback():
                dialog.close()
                self.reload()
            dialog_ = self.get_alert_dialog("Ошибка", f"Станок {machine_name} уже добавлен",
                                            callback=callback)
            dialog_.show()

        def add(machine_name):
            if self.db_items.get_item(machine_name, where={"machine_name": machine_name}, only_db=True):
                if not self.db_items.get_item(machine_name, where={"machine_name": machine_name}, only_queue=True):
                    error(machine_name)
                    dialog.close()
                    return
                self.reload()
                return
            self.db_items.set_item(machine_name, {"machine_name": machine_name}, insert=True)
            item = QListWidgetItem(machine_name)
            self.disconnect_fields_signals()
            self.ui.add_machine_list_0.addItem(item)
            self.ui.add_machine_list_0.setCurrentItem(item)
            self.clear_property_fields()
            self.insert_all_cnc_from_db()
            self.connect_fields_signals()
            dialog.close()
        dialog = self.get_prompt_dialog("Введите название станка", ok_callback=add)
        dialog.show()

    @Slot()
    def remove_machine(self):
        def ok():
            item: QListWidgetItem = self.get_selected_machine_item()
            item_name = item.text()
            self.db_items.set_item(item_name, delete=True, where={"machine_name": item_name}, ready=True)
            self.disconnect_fields_signals()
            self.clear_property_fields()
            dialog.close()
            self.ui.add_machine_list_0.takeItem(self.ui.add_machine_list_0.row(item))
            self.connect_fields_signals()
        dialog = self.get_confirm_dialog("Удалить станок?", "Внимание! Информация о свойствах станка будетм утеряна",
                                         ok_callback=ok)
        dialog.show()

    @Slot(str)
    def update_data(self, field_name):
        """ Обновление записей в базе, при изменении текстовых(LineEdit) полей-характеристик """
        def filter_value_for_integer_fields(field, val):
            if val == "":
                if field in self.INTEGER_FIELDS_LINE_EDIT:
                    return 0
            return val

        active_machine = self.get_selected_machine_item()
        if active_machine is None:
            return
        machine_name = active_machine.text()
        value = getattr(self.ui, field_name).text()
        machine_db = self.db_items.get_item(machine_name, where={"machine_name": machine_name}, only_db=True)
        self.validator.refresh()
        self.db_items.set_item(machine_name, {
            self.__UI__TO_SQL_COLUMN_LINK__LINE_EDIT[field_name]: filter_value_for_integer_fields(field_name, value)
        }, ready=self.validator.is_valid, where={"machine_name": machine_name},
                               **{("insert" if not machine_db else "update"): True})

    @Slot(str)
    def change_cnc(self, item):
        if not item:
            return
        selected_machine = self.get_selected_machine_item()
        if not selected_machine:
            return
        selected_machine_name = selected_machine.text()
        if item == self.DEFAULT_COMBO_BOX_CNC_NAME:
            del self.db_items.items[selected_machine_name]["cncid"]
            return
        cnc_db_instance = self.db_items.get_item(item, model=Cnc, where={"name": item})
        if not cnc_db_instance:
            self.reload()
            return
        machine_instance = self.db_items.get_item(selected_machine_name,
                                                  where={"machine_name": selected_machine_name})
        if not machine_instance:
            self.reload()
            return
        self.validator.select_cnc()
        self.db_items.set_item(selected_machine_name, {"cncid": cnc_db_instance["cncid"]},
                               where={"machine_name": selected_machine_name}, update=True, ready=self.validator.is_valid)

    def clear_property_fields(self) -> None:
        """
        Установить в стандартное значение все поля ХАРАКТЕРИСТИКИ
        """
        self.ui.choice_cnc.clear()
        self.insert_empty_cnc_item()
        self.ui.choice_cnc.setCurrentIndex(0)
        [getattr(self.ui, field_name).setText("") for field_name in self.__UI__TO_SQL_COLUMN_LINK__LINE_EDIT]
        self.cnc_names = {}


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

    def set_machine(self, current):
        self.current_machine = current
        self.refresh()

    def select_cnc(self):
        if self.current_machine:
            self.refresh()

    def refresh(self):
        valid = super().refresh()
        if self.current_machine:
            def mark_machine_list_widget_item():
                """ Выделить красным фотном станок или снять выделение """
                if not valid:
                    self.set_not_complete_edit_attributes(self.current_machine.text(), self.current_machine)
                else:
                    self.set_complete_edit_attributes(self.current_machine)
            mark_machine_list_widget_item()
