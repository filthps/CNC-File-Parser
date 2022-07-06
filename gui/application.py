import sys
from PySide2.QtWidgets import QMainWindow, QApplication
from PySide2.QtCore import QEvent, QObject, Qt, QRect
from PySide2.QtGui import QPixmap, QBrush
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session  # Будем считать, что это замена QThread
from sqlalchemy.orm import sessionmaker
from gui.ui import Ui_main_window as Ui
from gui.signals import Navigation, Actions
from tools import Tools


class Main(QMainWindow, Tools):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.session_factory = None
        self.db_session = None
        self.database = None
        self.navigation = None
        self.actions = None
        self.ui = None

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
            self.screen = app.primaryScreen()
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

        def init_database():
            self.database = create_engine("sqlite:///../database.db")
            self.session_factory = sessionmaker(bind=self.database, autoflush=False, autocommit=False, expire_on_commit=True)

        def init_navigation():
            self.navigation = Navigation(self.ui)

        def init_filter():
            self.ui.root_tab_widget.installEventFilter(self)

        def init_actions():
            self.actions = Actions(self, self.ui)

        init_ui()
        init_styles()
        init_database()
        init_navigation()
        init_filter()
        init_actions()

    def initialize_session(self):
        session = scoped_session(self.session_factory)
        self.db_session = session
        return session

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

    def eventFilter(self, watched: QObject, event: QEvent):
        if event.type() == QEvent.LayoutRequest:
            def nav_to_home_page():
                if watched.objectName() == "root_tab_widget":
                    if hasattr(watched, "currentIndex"):
                        if watched.currentIndex() == 0:
                            self.navigation.nav_home_page()
                if watched.objectName() == "converter_options":
                    ...
            nav_to_home_page()
        return QMainWindow.eventFilter(self, watched, event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = Main()
    main_window.show()
    sys.exit(app.exec_())
