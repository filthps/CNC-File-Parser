import sys
from PySide2.QtWidgets import QMainWindow, QApplication
from PySide2.QtCore import QEvent, QObject
from gui.ui import Ui_MainWindow as Ui
from database import Database
from gui.signals import Navigation, Actions
from tools import Tools


class Main(QMainWindow, Tools):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        def init_ui():
            def init_buttons():
                self.set_icon_buttons(self.ui, "add_button", "static/img/plus.png")
                self.set_icon_buttons(self.ui, "remove_button", "static/img/minus.png")
                self.set_icon_buttons(self.ui, "move_right", "static/img/arrow-right.png")
                self.set_icon_buttons(self.ui, "move_left", "static/img/arrow-left.png")

            def init_stylesheets():
                self.setStyleSheet(self.load_stylesheet("static/css/style.css"))
            self.ui = Ui()
            self.ui.setupUi(self)
            init_buttons()
            init_stylesheets()

        def init_database():
            self.db = Database("database.db")

        def init_navigation():
            self.navigation = Navigation(self.ui, self.db)

        def init_actions():
            self.actions = Actions(self, self.ui, self.db)

        def init_filter():
            self.ui.root_tab_widget.installEventFilter(self)

        init_ui()
        init_database()
        init_navigation()
        init_filter()
        init_actions()

    def eventFilter(self, watched: QObject, event: QEvent):
        def nav_to_home_page():
            if watched.objectName() == "root_tab_widget" and watched.currentIndex() == 0:
                self.navigation.nav_home_page()
            return QMainWindow.eventFilter(self, watched, event)

        return nav_to_home_page()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = Main()
    main_window.show()
    sys.exit(app.exec_())
