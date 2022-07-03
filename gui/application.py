import sys
from typing import Union
from PySide2.QtWidgets import QMainWindow, QApplication
from PySide2.QtCore import QEvent, QObject, Qt, QRect
from PySide2.QtGui import QPixmap, QBrush
from gui.ui import Ui_main_window as Ui
from database import Database, SQLQueryContainer, SQLQuery
from gui.signals import Navigation, Actions
from tools import Tools


class Main(QMainWindow, Tools):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.db = None
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
            self.db = Database("../database.db")
            self.query_fetch_list = {}
            self.query_commit_list = {}

        def init_navigation():
            self.navigation = Navigation(self.ui, self.db)

        def init_filter():
            self.ui.root_tab_widget.installEventFilter(self)

        def init_actions():
            self.actions = Actions(self, self.ui, self.db)

        init_ui()
        init_styles()
        init_database()
        init_navigation()
        init_filter()
        init_actions()

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

    def save(self):
        """ Освободить очередь, записать в базу данных"""

        def get_query(d: Union[dict, SQLQuery, SQLQueryContainer]):
            if isinstance(d, (SQLQuery, SQLQueryContainer,)):  # Базовый случай
                return d
            keys = tuple(d.keys())
            if keys:
                values = d.pop(keys[0])
                return get_query(values)
            return

        for value in self.query_commit_list.values():
            queries = get_query(value)
            print(queries)
            if queries.is_complete:
                self.db.connect_(queries)

    def eventFilter(self, watched: QObject, event: QEvent):
        if event.type() == QEvent.MouseButtonPress:
            def nav_to_home_page():
                if watched.objectName() == "root_tab_widget":
                    if hasattr(watched, "currentIndex") and watched.currentIndex() == 0:
                        self.navigation.nav_home_page()
                    self.save()
                if watched.objectName() == "converter_options":
                    pass
            nav_to_home_page()
            self.save()
        return QMainWindow.eventFilter(self, watched, event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = Main()
    main_window.show()
    sys.exit(app.exec_())
