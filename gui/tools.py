import os
import sys
import threading
from typing import Any, Union, Iterator, Iterable, Optional, Sequence, Callable, Mapping, Generator
from itertools import count, cycle
from pymemcache.client.base import Client
from pymemcache import serde
from flask_sqlalchemy.model import Model
from sqlalchemy.orm import Query, Session
from PySide2.QtCore import Qt, QPoint, QSize
from PySide2.QtGui import QPixmap, QPainter, QPalette, QFont
from PySide2.QtWidgets import QMainWindow, QTabWidget, QStackedWidget, QPushButton, QDialogButtonBox,\
    QDialog, QLabel, QVBoxLayout, QLineEdit, \
    QComboBox, QRadioButton, QSplashScreen
from PySide2.QtGui import QIcon
from gui.ui import Ui_main_window as Ui
from datatype import LinkedList, LinkedListItem


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
    def __init__(self, *a, callback=None, callback_kwargs=None, **k):
        super().__init__(*a, **k)
        self.kw = k
        self.callback = callback
        self.callback_kwargs = callback_kwargs

    def run(self) -> None:
        if self.callback:
            callback_thread = self.__class__(target=super().run(), args=self.kw["args"], kwargs=self.kw["kwargs"])
            callback_thread.start()
            callback_thread.join()
            kwargs = self.callback_kwargs if self.callback_kwargs else {}
            self.callback(**kwargs) if self.callback else None
            return
        super().run()


class UiLoaderThreadFactory:
    """ Класс, экземпляр которого содержит поток для работы с базой данных,
      Если время превышает константное значение, то UI блокируется и ставит progressbar.
      Используется как декоратор
      """
    LOCK_UI_SECONDS = 0.1
    _main_application: Optional[QMainWindow] = None
    _thread: Optional[threading.Thread] = None
    _timer: Optional[threading.Timer] = None

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
        self._lock_ui_level = lock_ui
        self._banner_text = banner_text

    @classmethod
    def set_application(cls, instance):
        if not isinstance(instance, (QMainWindow, QTabWidget,)):
            raise TypeError
        cls._main_application = instance

    def _start_timer(self, banner_item):
        self._timer = threading.Timer(float(self.LOCK_UI_SECONDS), self._show_banner, args=(banner_item,),
                                      kwargs={"text": self._banner_text})
        self._timer.start()

    @classmethod
    def _stop_timer_and_remove_banner(cls, banner: QSplashScreen = None, timer=None, dialog: QMainWindow = None):
        timer.cancel() if cls._timer else None
        banner.clearMessage()
        banner.close()
        banner.finish(dialog)
        dialog.update()

    @classmethod
    def _show_banner(cls, splash_item: QSplashScreen, text="Работа с базой данных"):
        splash_item.show()
        splash_item.showMessage(text) if text else None

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
            splash_item = init_splash_item()
            if self._lock_ui_level == "lock_on_timer":
                self._start_timer(splash_item)
            if self._lock_ui_level == "lock_immediately":
                self._show_banner(splash_item, text=self._banner_text)
            self._thread = CustomThread(target=func, args=args, kwargs=kwargs,
                                        callback_kwargs={"banner": splash_item, "timer": self._timer,
                                                         "dialog": self._main_application},
                                        callback=self._stop_timer_and_remove_banner)
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


class ORMAttributes:
    @staticmethod
    def _is_valid_model_instance(item: Model):
        if not isinstance(item, Model) or not hasattr(item, "__tablename__"):
            raise TypeError("Значение атрибута model - неподходящего типа")
        if


class ORMItem(LinkedListItem, ORMAttributes):
    """ Иммутабельный класс ноды для ORMItemContainer.
    """
    def __init__(self, **kw):
        super().__init__()
        self._is_valid_dml_type(kw)
        self.__model = kw.pop("__model", None)
        self._is_valid_model_instance(self.__model)
        self._callback: Optional[Callable] = kw.pop("__callback", None)
        self.__insert = kw.pop("__insert", False)
        self.__update = kw.pop("__update", False)
        self.__delete = kw.pop("__delete", False)
        if self.__delete or self.__update:
            if "__where" not in kw:
                raise KeyError("Если тип DML-SQL операции - delete или update, то будь добр установи "
                               "__where со значением для поиска записи в таблице.")
        self.__is_ready = kw.pop("__ready", False)
        self._where = kw.pop("__where", None)
        self._value = {}  # Содержимое - пары ключ-значение: поле таблицы бд: значение
        if not kw:
            raise ValueError("Нет полей, нода пуста")
        if
        self._value.update(kw)

    @property
    def value(self):
        return self._value.copy()

    @property
    def model(self):
        return self.__model

    @property
    def ready(self):
        return self.__is_ready

    @property
    def where(self):
        return self._where

    @property
    def callback(self):
        return self._callback

    @ready.setter
    def ready(self, status: bool):
        if not isinstance(status, bool):
            raise TypeError("Статус готовности - это тип данных boolean")
        self.__is_ready = status

    @property
    def type(self) -> str:
        return "__insert" if self.__insert else "__update" if self.__update else "__delete"

    def remove(self, key) -> bool:
        if key in self.value:
            del self._value[key]
            return True
        return False

    def __delitem__(self, key):
        return self.remove(key)

    def __len__(self):
        return len(self.value)

    def get_attributes(self) -> dict:
        result = {}
        result.update(self._value)
        if self.__update or self.__delete:
            result.update({"__where": self._where})
        result.update({"__model": self.__model, "__insert": self.__insert,
                       "__update": self.__update, "__ready": self.ready,
                       "__delete": self.__delete, "__callback": self._callback,
                       "__key_field": self.__key_field})
        return result

    def __repr__(self):
        return f"{self.__class__.__name__}({self.get_attributes()})"

    def __str__(self):
        return str(self.value)

    def make_query(self) -> Optional[Query]:
        query = None
        if self.__insert:
            query = self.model()
        if self.__update or self.__delete:
            query = self.model.query.filter_by(**self.where).first()
        if self.__update or self.__insert:
            [setattr(query, key, value) for key, value in self.value.items()]
        return query

    @staticmethod
    def _is_valid_dml_type(data: dict):
        """ Только одино свойство, обозначающее тип sql-dml операции, может быть True """
        is_insert = data.get("__insert", False)
        is_update = data.get("__update", False)
        is_delete = data.get("__delete", False)
        if not (isinstance(is_insert, bool) and isinstance(is_update, bool) and isinstance(is_delete, bool)):
            raise TypeError
        if sum((is_insert, is_update, is_delete,)) != 1:
            raise ValueError

class EmptyOrmItem:
    """
    Пустой класс для возврата пустой "ноды". Заглушка
    """
    def __init__(self):
        pass

    def remove(self):
        pass

    def __delitem__(self, key):
        pass

    def __eq__(self, other):
        return False

    def __len__(self):
        return 0

    def __bool__(self):
        return False

    def __str__(self):
        return "None"


class ORMItemContainer(LinkedList):
    """
    Очередь на основе связанного списка.
    Управляется через адаптер ORMHelper.
    Класс-контейнер умеет только ставить в очередь ((enqueue) зашита особая логика) и снимать с очереди (dequeue)
    см логику в методе enqueue.

    """
    __delitem__ = None
    LinkedListItem = ORMItem

    def __init__(self, items: Optional[Iterable[dict]] = None):
        super().__init__()
        self._model_name = None  # Внимание! Содержит модель от элемента, который добавлялся крайний раз!!!
        self._primary_field_name = None  # Внимание! Содержит модель от элемента, который добавлялся крайний раз!!!
        if items is not None:
            for inner in items:
                self.enqueue(**inner)

    def enqueue(self, **attrs):
        """ Установка ноды в конец очереди с хитрой логикой проверки на совпадение. """
        new_item = self._initialize_node(**attrs)
        if new_item:
            if self:
                last_element = self._tail
                self._set_prev(new_item, last_element)
                self._set_next(last_element, new_item)
                self._tail = new_item
            else:
                self._head = self._tail = new_item

    def replace_node(self, old_node_attrs: dict, new_node_attrs: dict, model_name: str = None):  # O(n) + O(n) = O(2n) = O(n)
        """
        Заменить ноду, сохранив её позицию в очереди.
        Если исходной ноды не найдено, вернуть None и ничего не делать,
        если найдена - заменить ноду и вернуть новую ноду
        """
        if not model_name:
            model_name = self._model_name
        self._is_valid_model_name(model_name)
        exists_node = self.search_node(model_name=model_name, **old_node_attrs)  # O(n)
        if not exists_node or not len(self):
            return
        new_item = self._initialize_node(__model=model_name, **new_node_attrs)  # O(n)
        if len(self) == 1:
            self._head = self._tail = new_item
            return
        next_node = exists_node.next
        previous_node = exists_node.prev
        if exists_node.index == len(self) - 1:
            self._tail = new_item
        if exists_node.index == 0:
            self._head = new_item
        previous_node.next = new_item
        next_node.prev = new_item
        return new_item

    def _initialize_node(self, **kwargs) -> Optional[ORMItem]:  # O(l * k) + O(n) + O(1) = O(n)
        """
        Создавать ноды для добавления можно только здесь!
        Затрагивает другие элементы в текущем экземпляре коллекции: удалит совпадающую по значению ноду!!
        """
        model = kwargs.get("__model", None)
        if model:
            model_name = model.__name__
            self._model_name = model_name
        else:
            model_name = self._model_name
        self._is_valid_model_name(model_name)
        if self._primary_field_name not in kwargs:
            raise ValueError("В добавляемой ноде обязательно должено присутствовать значение для поля, "
                             "которое задано в настройках")
        potential_new_item = self.LinkedListItem(**kwargs)  # O(1)
        new_item = None

        def create_merged_values_node(old_node: ORMItem, new_node: ORMItem, dml_type: str, where=None) -> Optional[ORMItem]:
            """
            Соединение значений старой и создаваемой ноды
            """
            if not new_node.value:
                return
            temp_value = old_node.value
            temp_value.update({"__callback": new_node.callback or old_node.callback})
            temp_value.update({"__ready": new_node.ready or old_node.ready})
            temp_value.update(new_node.value)
            temp_value.update({dml_type: True, "__model": potential_new_item.model})
            if where:
                temp_value.update({"__where": where})
            return self.LinkedListItem(**temp_value)
        exists_item = self.search_node(model_name=model_name, **kwargs)  # O(n)
        if not exists_item:
            new_item = potential_new_item
            return new_item
        new_item_is_update = kwargs.get("__update", False)
        new_item_is_delete = kwargs.get("__delete", False)
        new_item_is_insert = kwargs.get("__insert", False)
        if new_item_is_update:
            if exists_item.type == "__insert" or exists_item.type == "__update":
                where_clause = exists_item.where
                where_clause.update(potential_new_item.where)
                if exists_item.type == "__insert":
                    new_item = create_merged_values_node(exists_item, potential_new_item, "__insert",
                                                         where=where_clause)
                if exists_item.type == "__update":
                    new_item = create_merged_values_node(exists_item, potential_new_item, "__update",
                                                         where=where_clause)
            if exists_item.type == "__delete":
                new_item = potential_new_item
        if new_item_is_delete:
            new_item = potential_new_item
        if new_item_is_insert:
            if exists_item.type == "__insert" or exists_item.type == "__update":
                new_item = create_merged_values_node(exists_item, potential_new_item, "__insert")
            if exists_item.type == "__delete":
                new_item = potential_new_item
        self._remove_from_queue(exists_item)
        return new_item

    def dequeue(self) -> Optional[ORMItem]:
        """ Извлечение ноды с начала очереди """
        node = self._head
        if node is None:
            return
        self._remove_from_queue(node)
        return node

    def remove_from_queue(self, model_name: str = None, **node_params) -> None:
        """
        Экстренное изъятие ноды из очереди
        :param model_name: Имя модели, к которой сущность привязана
        Остальные именованные аргументы - это содержимое свойста value и where ноды
        """
        if model_name is None:
            model_name = self._model_name
        self._is_valid_model_name(model_name)
        node = self.search_node(model_name=model_name, **node_params)
        if node:
            self._remove_from_queue(node)

    def get_nodes_by_model_name(self, model_name: str) -> ["ORMItemContainer"]:
        self._is_valid_model_name(model_name)
        items = self.__class__()
        for node in self:  # O(n) * O(u * k) * O(i-->n) = От Ω(n) - θ(n * i) до O(n**2)
            if node.model.__name__ == model_name:  # O(u * k)
                items.enqueue(node.get_attributes())  # O(i) i-->n
        return items

    def search_node(self, pk_field_name, pk_field_value, model_name=None) -> Optional[ORMItem]:
        def check_node_inner(n: ORMItem):  # O(j * l) + O
            if not n.model.__name__ == model_name:  # O(j * l)
                return
            if pk_field_name not in n.value:
                raise ValueError
            if n.value[pk_field_name] == pk_field_value:
                return n
        if model_name is None:
            model_name = self._model_name
        self._is_valid_model_name(model_name)
        nodes = iter(self)
        node = None
        match_fields: dict[int, list[str]]  = {}  # Индекс ноды: список с назваиями совпавших полей
        while not node:  # O(n) * O(u)
            try:
                node = next(nodes)
            except StopIteration:
                break
            result_node_item = check_node_inner(node)
            if result_node_item:
                return result_node_item

    def __repr__(self):
        return f"{self.__class__}({tuple(str(i) for i in self)})"

    def __str__(self):
        return str(tuple(str(i) for i in self))

    def __getitem__(self, item: str) -> Union[ORMItem, EmptyOrmItem]:
        if not isinstance(item, dict):
            raise TypeError
        if not self._model_name:
            return EmptyOrmItem()
        node = self.search_node(model_name=self._model_name, **item)
        return node or EmptyOrmItem()

    def __contains__(self, item: ORMItem) -> bool:
        if type(item) is not ORMItem:
            return False
        node_attributes = item.get_attributes()
        node = self.search_node(model_name=node_attributes["__model"], **node_attributes)
        return bool(node)

    def _remove_from_queue(self, node: ORMItem) -> None:
        prev_node = node.prev
        next_node = node.next
        node.next = None
        node.prev = None
        if prev_node is None:
            self._head = next_node
        else:
            prev_node.next = next_node
        if next_node is None:
            self._tail = prev_node
        else:
            next_node.prev = prev_node

    @staticmethod
    def _is_valid_model_name(name):
        if not isinstance(name, str):
            raise TypeError


class ORMHelper(ORMAttributes):
    """
    Адаптер для ORMItemContainer
    Имеет таймер для единовременного высвобождения очереди объектов,
    при добавлении элемента в очередь таймер обнуляется.
    items - ссылка на экземпляр ORMItemContainer.
    1) Инициализация
        LinkToObj = ORMHelper.set_up(db.session)
    2) Установка ссылки на класс модели Flask-SqlAlchemy
        LinkToObj.set_model(Model)
    3) Использование
        name - Это всегда либо действующий PK или поле с ограничением UNIQUE=TRUE!
        LinkToObj.set_item(name, data, **kwargs) - Установка в очередь, обнуление таймера
        LinkToObj.get_item(name, **kwargs) - получение данных из бд и из ноды
        LinkToObj.get_items(model=None) - получение данных из бд и из ноды
        LinkToObj.release() - высвобождение очереди с попыткой сохранить объекты в базе данных
        в случае неудачи нода переносится в конец очереди
        LinkToObj.remove_items - принудительное изъятие ноды из очереди.
    """
    MEMCACHED_CONFIG = "127.0.0.1:11211"
    _store: Optional[Client] = None
    RELEASE_INTERVAL_SECONDS = 5.0
    CACHE_LIFETIME_HOURS = 6 * 60 * 60
    _timer: Optional[threading.Timer] = None
    _items: ORMItemContainer = ORMItemContainer()  # Temp
    _session = None
    _model_obj: Optional[Model] = None  # Текущий класс модели, присваиваемый автоматически всем экземплярам при добавлении в очередь
    key_field_name: Optional[str] = None

    @classmethod
    def set_up(cls, session):
        if cls.CACHE_LIFETIME_HOURS <= cls.RELEASE_INTERVAL_SECONDS:
            raise Exception("Срок жизни кеша, который хранит очередь сохраняемых объектов не может быть меньше, "
                            "чем интервал отправки объектов в базу данных.")

        def connect_to_storage():
            store = Client(cls.MEMCACHED_CONFIG, serde=serde.pickle_serde)
            return store

        def drop_cache():
            cls._store.flush_all()
        cls._is_valid_session(session)
        cls._session = session
        cls._store = connect_to_storage()
        return cls

    @classmethod
    def init_timer(cls):
        timer = threading.Timer(cls.RELEASE_INTERVAL_SECONDS, cls.release)
        timer.daemon = True
        timer.setName("ORMHelper(database push queue)")
        timer.start()
        return timer

    @classmethod
    def set_item(cls, insert=False, update=False,
                 delete=False, ready=False, callback=None, where=None, model=None, **value):
        if cls._model_obj is None:
            raise AttributeError("Не установлена модель БД для сохранения записей.")
        if not insert and not update and not delete:
            raise ValueError("Задайте тип DML операции: insert, update или delete")
        if update or delete:
            if where is None:
                raise ValueError("Если тип DML-SQL операции - delete или update, то будь добр установи ключ "
                                 "__where со значением для поиска записи в таблице.")
        if insert and update and delete:
            raise ValueError("Не правильно задан тип DML-SQL операции!")
        if not delete:
            if not isinstance(value, dict):
                raise TypeError("В качестве значений выступают словари")
        else:
            value = {}
        cls.items.enqueue(__model=model or cls._model_obj, __ready=ready,
                          __insert=insert, __update=update,
                          __delete=delete, __where=where, __callback=callback, **value)
        cls.__set_cache(cls.items)
        cls._timer.cancel() if cls._timer else None
        cls._timer = cls.init_timer()

    @classmethod
    def get_item(cls, model: Optional[Model] = None, only_db=False, only_queue=False, **attributes) -> dict:
        """
        1) Получаем запись из таблицы в виде словаря
        2) Получаем данные из очереди в виде словаря
        3) db_data.update(quque_data)
        Если primary_field со значением node.name найден в БД, то нода удаляется
        """
        if not model:
            model = cls._model_obj
        cls._is_valid_model_instance(model, cls.key_field_name)
        if only_queue:
            node = cls.items.search_node(model_name=model.__name__, **attributes)
            if node is None:
                return {}
            data_node = node.value
            return data_node
        query = model.query.filter_by(**attributes).first()
        data_db = {} if not query else query.__dict__
        if only_db:
            return data_db
        node = cls.items.search_node(model_name=model.__name__, **attributes)
        if node is None:
            return data_db
        if node.type == "__delete":
            return {}
        updated_node_data = data_db
        updated_node_data.update(node.value)
        if node.type == "__insert":
            if data_db:
                updated_node_data.update({"__model": model,
                                          "__where": {model.pk_field_name: data_db[model.pk_field_name]},
                                          "__update": True
                                          })
                cls.items.replace_node(attributes, updated_node_data, model_name=model.__name__)
        return updated_node_data

    @classmethod
    def get_items(cls, model: Optional[Model] = None, db_only=False, queue_only=False, **attrs) -> Iterator[dict]:  # todo: придумать пагинатор
        """
        1) Получаем запись из таблицы в виде словаря (Model.query.all())
        2) Получаем данные из кеша, все элементы, у которых данная модель
        3) db_data.update(quque_data)
        """
        import time
        time.sleep(1)  # todo: Тестируем зарержку
        if not model:
            if not cls._model_obj:
                raise AttributeError("Не установлено и не передано значение для объекта-модели")
            model = cls._model_obj
        cls._is_valid_model_instance(model, cls.key_field_name)
        if not attrs:
            items_db = model.query.all()
        else:
            items_db = model.query.filter_by(attrs).all()
        if db_only:
            return map(lambda t: t.__dict__, items_db)
        if queue_only:
            if not attrs:
                return map(lambda n: n.value, cls.items.get_nodes_by_model_name(model.__name__))
            return map(lambda x: x, cls.items.search_node(model_name=model.__name__, **attrs))
        db_items = []
        queue_items = {}  # index: node_value
        if items_db:
            nodes_implements_db = ORMItemContainer()  # Ноды, значения которых совпали с записями в БД
            for db_item in items_db:  # O(n)
                db_data: dict = db_item.__dict__
                node: ORMItem = cls.items.search_node(model_name=model.__name__, **attrs)  # O(k)
                if node:
                    old_node_attrs = node.get_attributes()
                    new_data = db_data
                    new_data.update(old_node_attrs)  # O(1)
                    nodes_implements_db.enqueue(**old_node_attrs)  # O(k)
                    if node.type == "__insert":

                        new_node_attrs.update({"__where": {model.pk_field_name: db_data[model.pk_field_name]}})
                        new_node_attrs.update({"__update": True})
                        cls.items.replace_node(node.value, new_node_attrs)
                    elif node.type == "__update":
                        db_data.update(node.value)
                    if not node.type == "__delete":
                        queue_items.update({node.index: node.value})
                else:
                    db_items.append(db_data)
            for node in cls.items:  # O(k)
                if node not in nodes_implements_db:  # O(l)
                    if node.model.__name__ == model.__name__:
                        val = node.value
                        queue_items.update({node.index: val}) if val else None
            # queue_items - нужен для сортировки
            # теперь все элементы отправим в output в следующей последовательности:
            # 1) ноды которые пересеклись со значениями из базы (сортировка по index)
            # 2) остальные ноды из очереди (сортировка по index)
            # 3) значения из базы
            sorted_nodes = dict(sorted(queue_items.items(), reverse=True))
            for item in sorted_nodes.values():
                yield item
            for item in db_items:
                yield item
            return
        return filter(lambda item: item.model.__name__ == model.__name__, cls.items)

    @classmethod
    def get_node_dml_type(cls, node_name: str, model=None) -> Optional[str]:
        """ Получить тип операции с базой, например 'update', по названию ноды, если она найдена, иначе - None """
        model_name = model.__name__ if model else None
        node = cls.items.search_node_by_name(node_name, model_name=model_name)
        if not node:
            return
        return node.type

    @classmethod
    def remove_items(cls, nodes: Iterable[dict], model=None):
        """
        Удалить ноду из очереди на сохранение
        """
        model = model or cls._model_obj
        if not model:
            raise AttributeError("Не установлено и не передано значение для объекта-модели")
        [cls.items.remove_from_queue(**attrs, model_name=model.__name__) for attrs in nodes]
        cls.__set_cache(cls.items)

    @classmethod
    def is_node_from_cache(cls, node_name):
        node = cls.items.search_node_by_name(node_name)
        return node

    @classmethod
    def release(cls) -> None:
        """
        Этот метод стремится высвободить очередь сохраняемых объектов,
        путём итерации по ним, и попыткой сохранить в базу данных.
        :return: None
        """
        def enqueue(node):
            new_node_attributes = cls._create_node_attrs_dict_from_node(node)
            enqueue_items.enqueue(node.name, **new_node_attributes)
        orm_element = True
        is_nodes_in_session = False
        enqueue_items = ORMItemContainer()
        cls._items = cls.items
        while orm_element:
            orm_element = cls._items.dequeue()
            if orm_element is None:
                break
            if orm_element.ready:
                query = orm_element.make_query()
                if query:
                    if orm_element.type == "__delete":
                        cls._session.delete(query)
                    else:
                        cls._session.add(query)
                    is_nodes_in_session = True
            else:
                enqueue(orm_element)
        cls.__set_cache(enqueue_items or None)
        if is_nodes_in_session:
            cls._session.commit()
        sys.exit()

    @property
    def items(self) -> ORMItemContainer:
        if self._items:
            return self._items
        items = self._store.get("ORMItems")
        if not items:
            items = ORMItemContainer()
        self._items = items
        return items

    @classmethod
    def set_model(cls, obj: Model, key_field_name: str):
        """
        :param obj: Класс модели Flask-SQLAlchemy
        :param key_field_name: Строка с названием поля, которое является первичным ключом
        или любым другим УНИКАЛЬНЫМ полем
        """
        if type(key_field_name) is not str:
            raise TypeError
        cls._is_valid_model_instance(obj, key_field_name)
        cls._model_obj = obj
        cls.key_field_name = key_field_name

    @staticmethod
    def _is_valid_session(obj):  # todo: Пока не знаю как проверить
        return

    @classmethod
    def __set_cache(cls, container: Optional[ORMItemContainer]):
        cls._store.set("ORMItems", container, cls.CACHE_LIFETIME_HOURS)
        cls._items = container

    @staticmethod
    def _create_node_attrs_dict_from_node(node: ORMItem) -> dict:
        new_node_attributes = {"__insert": False, "__update": False, "__delete": False, "__model": node.model,
                               "__where": node.where, "__callback": node.callback}
        new_node_attributes.update({node.type: True})
        new_node_attributes.update(**node.value)
        return new_node_attributes
