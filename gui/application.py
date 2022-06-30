import sys
from PySide2.QtWidgets import QMainWindow, QApplication
from PySide2.QtCore import QEvent, QObject, Qt, QRect
from PySide2.QtGui import QPixmap, QBrush
from gui.ui import Ui_main_window as Ui
from database import Database, SQLQueryContainer
from gui.signals import Navigation, Actions, DataLoader
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
            self.background_image = QPixmap("static/img/background.jpg")
            self.setStyleSheet(self.load_stylesheet("static/style.css"))
            self.setGeometry(QRect(0, 0, self.background_image.width(), self.background_image.height()))

        def init_database():
            self.db = Database("../database.db")
            self.query_fetch_list = SQLQueryContainer()
            self.query_commit_list = SQLQueryContainer(commit_=True)

        def init_navigation():
            self.navigation = Navigation(self.ui, self.db)

        def init_filter():
            self.ui.root_tab_widget.installEventFilter(self)

        def init_actions():
            self.actions = Actions(self, self.ui, self.db)

        def init_form_loader():
            self.loader = DataLoader(self, self.ui, self.db)

        init_ui()
        init_styles()
        init_database()
        init_navigation()
        init_filter()
        init_actions()
        init_form_loader()

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
        def nav_to_home_page():
            if watched.objectName() == "root_tab_widget":
                if hasattr(watched, "currentIndex") and watched.currentIndex() == 0:
                    self.navigation.nav_home_page()
            if watched.objectName() == "converter_options":
                pass
            return QMainWindow.eventFilter(self, watched, event)

        return nav_to_home_page()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = Main()
    main_window.show()
    sys.exit(app.exec_())
