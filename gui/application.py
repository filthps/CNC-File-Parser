import sys
from PySide2.QtWidgets import QMainWindow, QApplication, QTabWidget, QWidget


class Main(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.init_ui()

    def init_ui(self):
        converter_widget = QWidget()
        converter_widget.tex
        main_tab_widget = QTabWidget()
        main_tab_widget.addTab()
        main_tab_widget.move(15, 10)
        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = Main()
    main_window.show()
    sys.exit(app.exec_())
