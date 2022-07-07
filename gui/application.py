import sys
import sqlite3
from PySide2.QtWidgets import QMainWindow, QApplication
from PySide2.QtCore import Qt, QRect
from PySide2.QtGui import QPixmap, QBrush
from sqlalchemy_utils import database_exists
from database.models import db
from gui.ui import Ui_main_window as Ui
from gui.signals import Navigation, Actions
from tools import Tools
from database.models import DATABASE_PATH


class Main(QMainWindow, Tools):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.db_session = None
        self.database = None
        self.navigation = None
        self.actions = None
        self.ui = None

        def init_database():
            if not database_exists(DATABASE_PATH):
                raise sqlite3.DatabaseError("База данных не найдена!")
            self.database = db
            self.db_session = self.database.session

        def init_ui():
            def init_buttons():
                self.set_icon_buttons(self.ui, "add_button", "static/img/plus.png")
                self.set_icon_buttons(self.ui, "remove_button", "static/img/minus.png")
                self.set_icon_buttons(self.ui, "move_right", "static/img/arrow-right.png")
                self.set_icon_buttons(self.ui, "move_left", "static/img/arrow-left.png")

            self.ui = Ui()
            self.ui.setupUi(self)
            init_buttons()

        def init_styles():
            self.screen = application.primaryScreen()
            self.background_image = QPixmap("static/img/background.jpg")
            self.setStyleSheet(self.load_stylesheet("static/style.css"))

            def set_window_geometry():
                screen_size = self.screen.size()
                start_point_x = (screen_size.width() - self.background_image.width()) / 2
                start_point_y = (screen_size.height() - self.background_image.height()) / 2
                self.setGeometry(QRect(
                    start_point_x / 2,
                    start_point_y / 2,
                    start_point_x + self.background_image.width(),
                    start_point_y + self.background_image.height()
                ))
            set_window_geometry()

        def init_navigation():
            self.navigation = Navigation(self, self.ui)

        def init_filter():
            self.ui.root_tab_widget.installEventFilter(self)

        def init_actions():
            self.actions = Actions(self, self.ui)

        init_database()
        init_ui()
        init_styles()
        init_navigation()
        init_filter()
        init_actions()

    def save(self):
        self.db_session.commit()

    def resizeEvent(self, event) -> None:
        pal = self.palette()
        if self.background_image.width() >= self.width() and self.background_image.height() >= self.height():
            pal.setBrush(self.ui.backgroundRole(),
                         QBrush(
                             self.background_image.scaled(self.background_image.size(), Qt.KeepAspectRatioByExpanding,
                                                          Qt.SmoothTransformation))
                         )
        else:
            pal.setBrush(self.backgroundRole(),
                         QBrush(
                             self.background_image.scaled(self.size(), Qt.KeepAspectRatioByExpanding,
                                                          Qt.SmoothTransformation))
                         )
        self.setPalette(pal)
        super().resizeEvent(event)


if __name__ == "__main__":
    application = QApplication(sys.argv)
    main_window = Main()
    main_window.show()
    sys.exit(application.exec_())
