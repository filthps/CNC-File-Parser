import os
from typing import Union, Iterator, Optional, Sequence, Iterable
from itertools import count, cycle, repeat
from pathlib import Path
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTabWidget, QStackedWidget, QPushButton, QInputDialog, QDialogButtonBox, \
    QListWidgetItem, QListWidget, QDialog, QLabel, QVBoxLayout, QHBoxLayout, QTreeWidgetItem, QTreeWidget,\
    QLineEdit
from PySide2.QtGui import QIcon, QColor
from gui.ui import Ui_main_window as Ui
from database import SQLQuery
from gui.tools import Constructor, Tools


class OptionsPageActions(Constructor, Tools):

    def __init__(self, main_app_instance, ui: Ui, db):
        self.main_app = main_app_instance
        self.ui = ui
        self.FIELDS_RAW = (ui.lineEdit_10, ui.lineEdit_21)
        self.db = db
        super().__init__(main_app_instance, ui)

        def connect_siagnals():
            ui.add_button_0.clicked.connect(self.add_machine)
            ui.add_button_0.clicked.connect(lambda: self.__update_form(tuple(repeat("", 10))))
            ui.remove_button_0.clicked.connect(self.remove_machine)
            ui.add_machine_list_0.currentItemChanged.connect(lambda current, prev: self.select_machine(current))
            ui.add_machine_input.clicked.connect(lambda: self.choice_folder("lineEdit_10"))
            ui.add_machine_output.clicked.connect(lambda: self.choice_folder("lineEdit_21"))
            ui.lineEdit_10.clicked.connect(lambda: self.update_field("lineEdit_10"))
            ui.lineEdit_21.clicked.connect(lambda: self.update_field("lineEdit_21"))
            ui.lineEdit_11.clicked.connect(lambda: self.update_field("lineEdit_11"))
            ui.lineEdit_12.clicked.connect(lambda: self.update_field("lineEdit_12"))
            ui.lineEdit_13.clicked.connect(lambda: self.update_field("lineEdit_13"))
            ui.lineEdit_14.clicked.connect(lambda: self.update_field("lineEdit_14"))
            ui.lineEdit_15.clicked.connect(lambda: self.update_field("lineEdit_15"))
            ui.lineEdit_16.clicked.connect(lambda: self.update_field("lineEdit_16"))
        connect_siagnals()

    def __update_form(self, values: tuple):
        map_ = (self.ui.lineEdit_10, self.ui.lineEdit_21, self.ui.lineEdit_11, self.ui.lineEdit_12,
                self.ui.lineEdit_13, self.ui.lineEdit_14, self.ui.lineEdit_15, self.ui.lineEdit_16)
        [field.setText(value) for field, value in zip(map_, values)]

    def choice_folder(self, output_line_edit_widget: str):
        def update_field(value):
            field: QLineEdit = getattr(self.ui, output_line_edit_widget)
            field.setText(value)
        dialog = self.get_folder_choice_dialog(ok_callback=update_field)
        dialog.show()

    def select_machine(self, machine_item: QListWidgetItem):
        """ Обновить данные при select в QListWidget -
        обновить все поля свойств станка (поля - Характеристики)"""
        def update_machines_list(values):
            self.__update_form(tuple(list(values)[2:]))
        name = machine_item.text()

        def create_db_request():
            q = SQLQuery()
            q.select("Machine", "*")
            q.where("machine_name", "=", name)
            self.db.connect_(q, lambda val: update_machines_list(val))
        push_queque = self.main_app.query_commit_list.get("add_machine_list_0")
        query = None
        if push_queque is not None:
            query = push_queque.get(name)
            if query is not None:
                update_machines_list(tuple(query))
        if query is None:
            create_db_request()

    def add_machine(self):
        def add(machine_name):
            query = SQLQuery(commit=True, complete=False, not_null_indexes=(1, 8, 9))
            query.insert("Machine",
                         (None, machine_name, None, None, None, None, None, None))
            item = QListWidgetItem(machine_name)
            queries = self.main_app.query_commit_list.get("add_machine_list_0", None)
            if queries is None:
                self.main_app.query_commit_list.update({"add_machine_list_0": {machine_name: query}})
            else:
                queries.update({machine_name: query})
            input_path_text = self.ui.lineEdit_10.text()
            output_path_text = self.ui.lineEdit_21.text()
            x_size_text = self.ui.lineEdit_11.text()
            y_size_text = self.ui.lineEdit_12.text()
            z_size_text = self.ui.lineEdit_13.text()
            x_speed_text = self.ui.lineEdit_14.text()
            y_speed_text = self.ui.lineEdit_15.text()
            z_speed_text = self.ui.lineEdit_16.text()
            if x_size_text:
                query.insert_column_value(x_size_text, 2)
            if y_size_text:
                query.insert_column_value(y_size_text, 3)
            if z_size_text:
                query.insert_column_value(z_size_text, 4)
            if x_speed_text:
                query.insert_column_value(x_speed_text, 5)
            if y_speed_text:
                query.insert_column_value(y_speed_text, 6)
            if z_speed_text:
                query.insert_column_value(z_speed_text, 7)
            if input_path_text:
                query.insert_column_value(input_path_text, 8)
            if output_path_text:
                query.insert_column_value(output_path_text, 9)
            self.set_not_complete_edit_attributes(item)
            self.ui.add_machine_list_0.addItem(item)
            self.ui.add_machine_list_0.setCurrentItem(item)
            self._unlock_ui()
            dialog.close()
        dialog = self.get_prompt_dialog("Введите название станка", ok_callback=add)
        self._lock_ui()
        dialog.show()

    def remove_machine(self):
        def get_selected_item() -> QListWidgetItem:
            return self.ui.add_machine_list_0.currentItem()

        def ok():
            name = get_selected_item().text()
            query = SQLQuery()
            query.delete("Machine", "machine_name", "=", name)
            add_commit_list = self.main_app.query_commit_list.get("add_machine_list_0")
            if add_commit_list is not None:
                del add_commit_list[name]

        dialog = self.get_confirm_dialog("Удалить станок?", "Внимание! Информация о свойствах станка будетм утеряна",
                                         ok_callback=ok)
        dialog.show()

    def update_field(self, field_name):
        ...
