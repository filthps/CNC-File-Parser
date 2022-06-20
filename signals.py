from typing import Callable
from PySide2.QtWidgets import QWidget, QTabWidget, QStackedWidget
from ui import Ui_MainWindow as Ui


class MainPage:

    @staticmethod
    def set_initial_page(ui: Ui):
        ui.main_widget.setCurrentIndex(0)

    @staticmethod
    def converter_main_page(ui: Ui):
        ui.to_converter.clicked.connect(lambda: ui.main_widget.setCurrentIndex(1))
        ui.root_tab_widget.setCurrentIndex(1)

