import os
import threading
from typing import Union, Iterator, Optional, Sequence, Callable
from itertools import count, cycle
from PySide2.QtCore import Qt, QPoint, QSize
from PySide2.QtGui import QPixmap, QPainter, QPalette, QFont
from PySide2.QtWidgets import QMainWindow, QTabWidget, QStackedWidget, QPushButton, QDialogButtonBox,\
    QDialog, QLabel, QVBoxLayout, QLineEdit, \
    QComboBox, QRadioButton, QSplashScreen
from PySide2.QtGui import QIcon
from gui.ui import Ui_main_window as Ui


class Tools:
    ui = None
    _UI__TO_SQL_COLUMN_LINK__LINE_EDIT = {}
    _UI__TO_SQL_COLUMN_LINK__COMBO_BOX = {}
    _UI__TO_SQL_COLUMN_LINK__RADIO_BUTTON: dict[dict[str, str]] = {}
    _COMBO_BOX_DEFAULT_VALUES = {}
    _RADIO_BUTTON_DEFAULT_VALUES = tuple()
    _LINE_EDIT_DEFAULT_VALUES = {}
    _INTEGER_FIELDS = tuple()
    _STRING_FIELDS = tuple()
    _FLOAT_FIELDS = tuple()
    _NULLABLE_FIELDS = tuple()

    def update_fields(self, line_edit_values: Optional[dict] = None,
                      combo_box_values: Optional[dict] = None, combo_box_default_values: Optional[dict] = None):
        """ Обновление содержимого полей """
        for line_edit_name, db_field_name in self._UI__TO_SQL_COLUMN_LINK__LINE_EDIT.items():
            val = line_edit_values.pop(db_field_name, None) if line_edit_values else None
            input_: QLineEdit = getattr(self.ui, line_edit_name)
            if val:
                input_.setText(str(val))
            else:
                input_.setText("")
        for ui_field, orm_field in self._UI__TO_SQL_COLUMN_LINK__COMBO_BOX.items():
            input_: QComboBox = getattr(self.ui, ui_field)
            value = combo_box_values.get(orm_field) if combo_box_values else None
            if value:
                input_.setCurrentText(str(value))
            else:
                default_value = self._COMBO_BOX_DEFAULT_VALUES.get(orm_field, None)
                if default_value:
                    input_.setCurrentText(default_value)
                else:
                    input_.setCurrentText("")

    def check_output_values(self, field_name, value):
        """ Форматировать типы выходных значений перед установкой в очередь отправки """
        if field_name in self._INTEGER_FIELDS:
            if not value:
                return 0
            if type(value) is int:
                return value
            return int(value) if str.isdigit(value) else value
        if field_name in self._FLOAT_FIELDS:
            if not value:
                return float()
            if isinstance(value, float):
                return value
            return float(value) if str.isdecimal(value) else value
        if field_name in self._STRING_FIELDS:
            if not value:
                return ""
            return str(value)
        if field_name in self._NULLABLE_FIELDS:
            if not value:
                return None
        return value

    def reset_fields_to_default(self):
        for radio_button_name in self._RADIO_BUTTON_DEFAULT_VALUES:
            field: QRadioButton = getattr(self.ui, radio_button_name)
            field.setChecked(True)
        for combo_box_name, default_text in self._COMBO_BOX_DEFAULT_VALUES.items():
            field: QComboBox = getattr(self.ui, combo_box_name)
            field.clear()
            field.addItem(default_text)
            field.setCurrentIndex(0)
        for line_edit_name, default_value in self._LINE_EDIT_DEFAULT_VALUES.items():
            field: QLineEdit = getattr(self.ui, line_edit_name)
            field.setText(default_value)

    @staticmethod
    def __get_widget_index_by_tab_name(widget_instance: Union[QTabWidget, QStackedWidget], tab_name: str) -> int:
        page = widget_instance.findChild(widget_instance.__class__, tab_name)
        return widget_instance.indexOf(page)

    @staticmethod
    def load_stylesheet(path: str) -> str:
        with open(path) as p:
            return p.read()

    @staticmethod
    def set_icon_buttons(ui: Ui, n: str, path: str) -> None:
        """
        Автоматизированный способ работы с идентичными кнопками;
        в имени кнопки заложен следущий смысл:
        [имя_кнопки]_[номер_кнопки]

        :param ui: Экземпляр Ui_MainWindow
        :param n: [имя_кнопки] без замыкающего нижнего подчёркивания
        :param path: строка-путь к иконке
        :return: None.
        """
        def gen() -> Iterator:
            counter = count()
            while True:
                b: QPushButton = getattr(ui, f"{n}_{next(counter)}", False)
                if not b:
                    return
                yield b

        icon = QIcon(path)
        [b.setIcon(icon) for b in gen()]


class CustomThread(threading.Thread):
    def __init__(self, target, *args, **kwargs):
        self.factory: UiLoaderThreadFactory = kwargs.pop("factory_instance")
        super().__init__(target=target, args=args, kwargs=kwargs)

    def run(self) -> None:
        if self.factory.lock_ui_level == "lock_on_timer":
            self.factory.start_timer()
        if self.factory.lock_ui_level == "lock_immediately":
            self.factory.show_banner()
        super().run()
        self.factory.stop_timer_and_remove_banner()


class UiLoaderThreadFactory:
    """ Класс, экземпляр которого содержит поток для работы с базой данных,
      Если время превышает константное значение, то UI блокируется и ставит progressbar.
      Используется как декоратор
      """
    LOCK_UI_SECONDS = 0.1
    _main_application: Optional[QMainWindow] = None
    _thread: Optional[threading.Thread] = None

    def __init__(self, lock_ui="no_lock", banner_text="Загрузка..."):
        """
        :param lock_ui: Степень блокировки интерфейса:
        no_lock - не показывать банер вообще (всё что происходит в потоке отдельном от ui, происходит незаметно на стороне ui)
        lock_on_timer - показ банера, блокирующего ui, если поток работает слишком долго, см константа LOCK_UI_SECONDS.
        lock_immediately - показ банера сразу
        :param banner_text: Текст баннера
        """
        if not isinstance(lock_ui, str):
            raise TypeError
        if lock_ui not in ("no_lock", "lock_on_timer", "lock_immediately",):
            raise ValueError
        if not type(banner_text) is str:
            raise TypeError
        self.lock_ui_level = lock_ui
        self._banner_text = banner_text
        self._timer: Optional[threading.Timer] = None
        self._banner_item: Optional[QSplashScreen] = None

    @classmethod
    def set_application(cls, instance):
        if not isinstance(instance, (QMainWindow, QTabWidget,)):
            raise TypeError
        cls._main_application = instance

    def start_timer(self):
        timer = threading.Timer(float(self.LOCK_UI_SECONDS), self.show_banner, args=(self._banner_item,),
                                kwargs={"text": self._banner_text})
        timer.start()
        self._timer = timer

    def stop_timer_and_remove_banner(self):
        self._timer.cancel() if self._timer else None
        if self._banner_item:
            self._banner_item.clearMessage()
            self._banner_item.close()
            self._banner_item.finish(self._main_application)
            self._main_application.update()

    def show_banner(self):
        self._banner_item.show()
        self._banner_item.showMessage(self._banner_text) if self._banner_text else None

    def __call__(self, func: Callable):
        def wrapper(*args, **kwargs):
            def init_splash_item():
                pixmap = QPixmap("static/img/gear.png")
                pixmap.scaled(QSize(20, 20), Qt.KeepAspectRatio)
                banner = QSplashScreen(pixmap)
                return banner
            if not self._main_application:
                raise AttributeError("Перед использованием необходимо использовать метод 'set_application', "
                                     "указав в нем экземпляр QMainWindow")
            self.banner_item = init_splash_item()
            self._thread = CustomThread(func, *args, factory_instance=self, **kwargs)
            self._thread.start()
        return wrapper


class MyAbstractDialog(QDialog):
    """
    Диалоговое окно с возможностью контроля слота нажатия клавиш клавиатуры.
    Навигация по кнопкам
    """
    def __init__(self, parent=None, buttons: Optional[Sequence[QPushButton]] = None, init_callback=None, close_callback=None):
        super().__init__(parent)
        self._left = None
        self._right = None
        if buttons is not None:
            button: QDialogButtonBox = buttons[0]
            buttons = list(buttons)
            left_orientation = buttons
            left_orientation.reverse()
            self._left = cycle(left_orientation)
            self._right = cycle(buttons)
            self.__set_active(button)
        self._close_callback = close_callback
        self._open_callback = init_callback

    def set_close_callback(self, value):
        self._close_callback = value

    def set_open_callback(self, value):
        self._open_callback = value

    def keyPressEvent(self, event):
        if event == Qt.Key_Left:
            button = self.__get_button(self._left)
            if button:
                self.__set_active(button)
        if event == Qt.Key_Right:
            button = self.__get_button(self._right)
            if button:
                self.__set_active(button)

    def closeEvent(self, event) -> None:
        self._close_callback() if self._close_callback else None

    def showEvent(self, event) -> None:
        self._open_callback() if self._open_callback else None

    @staticmethod
    def __get_button(buttons: cycle):
        return next(buttons)

    @staticmethod
    def __set_active(button: QDialogButtonBox):
        # button.setFocus()  # todo
        ...


class Constructor:
    DEFAULT_PATH = os.path.abspath(os.sep)

    def __init__(self, instance, ui: Ui):
        self.instance = instance
        self.main_ui = ui

    def get_alert_dialog(self, title_text, label_text="", callback=None):
        """ Всплывающее окно с текстом и  кнопкой
        ░░░░██████████████████████████░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░██████░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██░░░░░░░░░░░░░░░░░░░░░░██░░
        ░░░░██████████████████████████░░
        """
        def set_signals():
            dialog.accepted.connect(callback)
            dialog.rejected.connect(lambda: window.close())
        ok_button = QDialogButtonBox.Ok
        window = MyAbstractDialog(self.instance, buttons=(ok_button,),
                                  close_callback=self._unlock_ui, init_callback=self._lock_ui)
        h_layout = QVBoxLayout(window)
        window.setFocus()
        label = QLabel(window)
        h_layout.addWidget(label)
        label.setText(label_text)
        dialog = QDialogButtonBox(label)
        h_layout.addWidget(dialog)
        dialog.setStandardButtons(ok_button)
        window.setWindowTitle(title_text)
        set_signals()
        return window

    def get_prompt_dialog(self, title_text, label_text="", cancel_callback=None, ok_callback=None) -> MyAbstractDialog:
        """ Всплывающее окно с текстом, 2 кнопками и полем ввода
        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
        ░░░░░░░░████████████████████░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░████████████░░██░░░░
        ░░░░░░░░██░░██░░░░░░░░██░░██░░░░
        ░░░░░░░░██░░████████████░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░████░░░░████░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░████████████████████░░░░
        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
        """
        def get_value():
            return ok_callback(input_.text())

        def set_signals():
            dialog.accepted.connect(get_value if ok_callback is not None else None)
            dialog.rejected.connect(cancel_callback)
            dialog.rejected.connect(lambda: window.close())
        input_ = QLineEdit()
        ok_button, cancel_button = QDialogButtonBox.Ok, QDialogButtonBox.Cancel
        window = MyAbstractDialog(self.instance, buttons=(ok_button, cancel_button))
        window.set_open_callback(self._lock_ui)
        window.set_close_callback(self._unlock_ui)
        window.setWindowTitle(title_text)
        v_layout = QVBoxLayout(window)
        v_layout.addWidget(input_)
        if label_text:
            label = QLabel()
            label.setText(label_text)
            dialog = QDialogButtonBox(label)
        else:
            dialog = QDialogButtonBox(input_)
        v_layout.addWidget(dialog)
        dialog.setStandardButtons(ok_button | cancel_button)
        set_signals()
        return window

    def get_confirm_dialog(self, title_text, label_text=None, cancel_callback=None, ok_callback=None) -> MyAbstractDialog:
        """ Всплывающее окно с текстом и 2 кнопками
        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
        ░░░░░░░░████████████████████░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░██░░████░░░░████░░██░░░░
        ░░░░░░░░██░░░░░░░░░░░░░░░░██░░░░
        ░░░░░░░░████████████████████░░░░
        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
        """
        def set_signals():
            dialog.accepted.connect(ok_callback)
            dialog.rejected.connect(cancel_callback)
            dialog.rejected.connect(lambda: window.close())
            window.finished.connect(cancel_callback)
        ok_button, cancel_button = QDialogButtonBox.Ok, QDialogButtonBox.Cancel
        window = MyAbstractDialog(self.instance, buttons=(ok_button, cancel_button,),
                                  close_callback=self._unlock_ui, init_callback=self._lock_ui)

        h_layout = QVBoxLayout(window)
        window.setFocus()
        label = None
        if label_text is not None:
            label = QLabel(window)
            h_layout.addWidget(label)
            label.setText(label_text)
        dialog = QDialogButtonBox(label)
        h_layout.addWidget(dialog)
        dialog.setStandardButtons(ok_button | cancel_button)
        window.setWindowTitle(title_text)
        set_signals()
        return window

    def _lock_ui(self):
        self.main_ui.root_tab_widget.setDisabled(True)

    def _unlock_ui(self):
        self.main_ui.root_tab_widget.setEnabled(True)
