import sys
from PySide2.QtWidgets import QMainWindow, QApplication
from PySide2.QtCore import QEvent, QObject
from gui.ui import Ui_MainWindow as Ui
from threads.threads import DatabaseTread
from gui.signals import Navigation, Actions, DB
from database import Database, SQLQuery
from tools import Tools


class Main(QMainWindow, Tools):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        def init_database():
            self.db_signals = DB(self)
            self.db = Database("/database.db")

        def init_threads():
            self.db_thread = DatabaseTread()
            self.db_thread.db_signal.connect(lambda: self.db_signals.fetch_data)  # Получаем данные с потока

        def init_ui():
            def init_buttons():
                self.set_icon_buttons(self.ui, "add_button", "static/img/plus.png")
                self.set_icon_buttons(self.ui, "remove_button", "static/img/minus.png")
                self.set_icon_buttons(self.ui, "move_right", "static/img/arrow-right.png")
                self.set_icon_buttons(self.ui, "move_left", "static/img/arrow-left.png")
            self.ui = Ui()
            self.ui.setupUi(self)
            init_buttons()

        def init_stylesheets():
            self.setStyleSheet(self.load_stylesheet("static/css/style.css"))

        def init_navigation():
            self.navigation = Navigation(self.ui, self.db)

        def init_actions():
            self.actions = Actions(self, self.ui, self.db)

        def init_filter():
            self.ui.root_tab_widget.installEventFilter(self)

        init_database()
        init_threads()
        init_ui()
        init_stylesheets()
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
