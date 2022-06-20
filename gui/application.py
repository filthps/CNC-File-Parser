import sys
from PySide2.QtWidgets import QMainWindow, QApplication, QTabWidget, QStackedWidget
from ui import Ui_MainWindow as Ui
from signals import MainPage


class Tools:
    @staticmethod
    def __get_widget_index_by_tab_name(widget_instance: QTabWidget, tab_name: str) -> int:
        page = widget_instance.findChild(QStackedWidget, tab_name)
        return widget_instance.indexOf(page)


class Main(QMainWindow, Tools, MainPage):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        def init_ui():
            self.ui = Ui()
            self.ui.setupUi(self)
        init_ui()
        self.converter_main_page(self.ui)
        self.set_initial_page(self.ui)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = Main()
    main_window.show()
    sys.exit(app.exec_())
