import os
import sys
import threading
from typing import Union, Iterator, Iterable, Optional, Sequence, Callable
from itertools import count, cycle
from pymemcache.client.base import Client
from pymemcache import serde
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTabWidget, QStackedWidget, QPushButton, QDialogButtonBox,\
    QDialog, QLabel, QVBoxLayout, QLineEdit, \
    QComboBox, QRadioButton
from PySide2.QtGui import QIcon
from sqlalchemy.orm import Query
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


class MyAbstractDialog(QDialog):
    """
    Диалоговое окно с возможностью контроля слота нажатия клавиш клавиатуры.
    Навигация по кнопкам
    """
    def __init__(self, parent=None, buttons: Optional[Sequence[QPushButton]] = None, init_callback=None, close_callback=None):
        super().__init__(parent)
        if buttons is not None:
            button: QDialogButtonBox = buttons[0]
            self.__set_active(button)
        buttons = list(buttons)
        left_orientation = buttons
        left_orientation.reverse()
        self._left = cycle(left_orientation)
        self._right = cycle(buttons)
        self._close_callback = close_callback
        self._open_callback = init_callback

    def set_close_callback(self, value):
        self._close_callback = value

    def set_open_callback(self, value):
        self._open_callback = value

    def keyPressEvent(self, event):
        if event == Qt.Key_Left:
            button = self.__get_button(self._left)
            self.__set_active(button)
        if event == Qt.Key_Right:
            button = self.__get_button(self._right)
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
    INTEGER_FIELDS_LINE_EDIT = ...  # Для замены пустых значений нулями при отправке в бд

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


class ORMItem(LinkedListItem):
    """ Иммутабельный класс ноды для ORMItemContainer.

    """
    def __init__(self, __node_name, **kw):
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
                raise KeyError("Если тип DML-SQL операции - delete или update, то будь добр установи ключ "
                               "__where со значением для поиска записи в таблице.")
        if not isinstance(__node_name, str):
            raise ValueError
        self._name = __node_name  # Имя для удобного поиска со стороны UI. Это может быть название станка, стойки итп
        self.__is_ready = kw.pop("__ready", False)
        self._where = kw.pop("__where", None)
        self._value = {}  # Содержимое - пары ключ-значение: поле таблицы бд: значение
        if not self.__delete:
            if len(kw):
                self._value.update(kw)

    @property
    def name(self):
        return self._name

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

    def __eq__(self, other: "ORMItem"):
        if not isinstance(other, self.__class__):
            return False
        try:
            self._is_valid_model_instance(other.__model)
        except TypeError:
            return False
        if self.name == other.name:
            return self.__model.__name__ == other.__model.__name__
        return False

    def __ne__(self, other: "ORMItem"):
        return not self.__eq__(other)

    def __format_kwargs(self):
        result = {}
        result.update(self._value)
        if self.__update or self.__delete:
            result.update({"__where": self._where})
        result.update({"__model": self.__model, "__insert": self.__insert,
                       "__update": self.__update, "__ready": self.ready,
                       "__delete": self.__delete, "__callback": self._callback})
        kwargs = ""
        for k, v in result.items():
            kwargs += f"{k}={v}, "
        return result

    def __repr__(self):
        return f"{self.__class__.__name__}({{'{self._name}': {self.__format_kwargs()}}})"

    def __str__(self):
        return str({self.name: self.__format_kwargs()})

    def make_query(self) -> Optional[Query]:
        query = None
        if self.__insert:
            query = self.model()
        if self.__update or self.__delete:
            query = self.model.query.filter_by(**self._where).first()
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

    @staticmethod
    def _is_valid_model_instance(item):
        if not hasattr(item, "__tablename__"):
            raise TypeError("Значение атрибута model - неподходящего типа")


class EmptyOrmItem:
    """
    Пустой класс для возврата пустой "ноды".
    """
    def __init__(self):
        pass

    def remove(self):
        pass

    def __delitem__(self, key):
        pass


class ORMItemContainer(LinkedList):
    """
    Очередь на основе связанного списка.
    Управляется через адаптер ORMHelper.
    Класс-контейнер умеет только ставить в очередь ((enqueue) зашита особая логика) и снимать с очереди (dequeue)
    см логику в методе enqueue.
    """
    append = None
    __delitem__ = None
    LinkedListItem = ORMItem

    def __init__(self, items: Optional[Iterable[dict[str, dict]]] = None):
        super().__init__()
        self._model_name = None  # Внимание! Содержит модель от элемента, который добавлялся крайний раз!!!
        if items is not None:
            for item in items:
                for block_name, inner in item.items():
                    self.enqueue(block_name, **inner)

    def enqueue(self, item_name, **kwargs):
        """ Установка ноды в конец очереди.
        Если нода с name - item_name найдена, то произойдёт update словарю value,
        А также нода переносится в конец очереди """
        model_name = None
        model = kwargs.get("__model", None)
        if model:
            model_name = model.__name__
            self._model_name = model_name
        exists_item = self.search_node_by_name(item_name, model_name=model_name)
        potential_new_item = self.LinkedListItem(item_name, **kwargs)
        new_item = None

        def create_merged_values_node(old_node: ORMItem, new_node: ORMItem, dml_type: str, where=None) -> ORMItem:
            """
            Соединение значений старой и создаваемой ноды
            """
            temp_value = old_node.value
            temp_value.update({"__callback": new_node.callback or old_node.callback})
            temp_value.update({"__ready": new_node.ready or old_node.ready})
            temp_value.update(new_node.value)
            temp_value.update({dml_type: True, "__model": potential_new_item.model})
            if where:
                temp_value.update({"__where": where})
            return self.LinkedListItem(item_name, **temp_value)
        if exists_item == potential_new_item:
            new_item_is_update = kwargs.get("__update", False)
            new_item_is_delete = kwargs.get("__delete", False)
            new_item_is_insert = kwargs.get("__insert", False)
            if new_item_is_update:
                if exists_item.type == "__update" or exists_item.type == "__insert":
                    new_item_dml_operation_type = "__insert" if exists_item.type == "__insert" else "__update"
                    where_clause = None
                    if new_item_dml_operation_type == "__update":
                        where_clause = kwargs.get("__where", None)
                    new_item = create_merged_values_node(exists_item, potential_new_item, new_item_dml_operation_type,
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
        else:
            new_item = potential_new_item
        if new_item:
            if self:
                last_element = self._tail
                self._set_prev(new_item, last_element)
                self._set_next(last_element, new_item)
                self._tail = new_item
            else:
                self._head = self._tail = new_item

    def dequeue(self) -> Optional[ORMItem]:
        """ Извлечение ноды с начала очереди """
        node = self._head
        if node is None:
            return
        self._remove_from_queue(node)
        return node

    def remove_from_queue(self, node_name: str, model_name: str = None) -> None:
        """
        Экстренное изъятие ноды из очереди
        :param node_name: Имя сущности, сохраняющейся в БД, - идентификатор ноды
        :param model_name: Имя модели, к которой сущность привязана
        """
        if model_name is None:
            model_name = self._model_name
        if type(node_name) is not str or type(model_name) is not str:
            raise TypeError
        node = self.search_node_by_name(node_name, model_name)
        if node:
            self._remove_from_queue(node)

    def __repr__(self):
        return f"{self.__class__}({tuple(str(i) for i in self)})"

    def __str__(self):
        return str(tuple(str(i) for i in self))

    def __getitem__(self, item: str) -> Union[ORMItem, EmptyOrmItem]:
        if not isinstance(item, str):
            raise KeyError
        node = self.search_node_by_name(item, model_name=self._model_name)
        return node if node else EmptyOrmItem()

    def search_node_by_name(self, name: str, model_name: Optional[str] = None) -> Optional[ORMItem]:
        if model_name is None:
            model_name = self._model_name
        else:
            if type(model_name) is not str:
                raise TypeError
        for node in self:
            if node.name == name:
                if model_name is not None:
                    if model_name == node.model.__name__:
                        return node
                else:
                    return node

    def search_node_by_model(self, model_name: str) -> Optional[ORMItem]:
        for node in self:
            if node.model.__name__ == model_name:
                return node

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


class ORMHelper:
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
    _model_obj = None  # Текущий класс модели, присваиваемый автоматически всем экземплярам при добавлении в очередь
    _primary_field = None

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
    def set_item(cls, key, value: Optional[dict] = None, insert=False, update=False,
                 delete=False, ready=False, callback=None, where=None, model=None):
        cls._is_valid_node_name(key)
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
        print("Установка ноды", key, value, ready)
        cls.items.enqueue(key, __model=model or cls._model_obj, __ready=ready,
                          __insert=insert, __update=update,
                          __delete=delete, __where=where, __callback=callback, **value)
        cls.__set_cache(cls.items)
        cls._timer.cancel() if cls._timer else None
        cls._timer = cls.init_timer()

    @classmethod
    def get_item(cls, item_name, primary_field=None, where=None, model=None, only_db=False, only_queue=False) -> dict:
        """
        1) Получаем запись из таблицы в виде словаря
        2) Получаем данные из очереди в виде словаря
        3) db_data.update(quque_data)
        Если primary_field со значением node.name найден в БД, то нода удаляется
        """
        def create_where_clause(wh, p_field):
            updated_where = {p_field: item_name}
            if where:
                if not isinstance(where, dict):
                    raise TypeError
                updated_where.update(where)
            return updated_where
        cls._is_valid_node_name(item_name)
        if model:
            if not primary_field:
                raise ValueError("Если указана отличная от стандартной модель - то нужно указать и поле, "
                                 "по которому будет происходить выборка")
        else:
            primary_field = primary_field or cls._primary_field
            model = cls._model_obj
        cls._is_valid_model_instance(model, primary_field)
        if only_queue:
            node = cls.items.search_node_by_name(item_name, model_name=model.__name__)
            if node is None:
                return {}
            data_node = node.value
            return data_node
        where = create_where_clause(where, primary_field)
        query = model.query.filter_by(**where).first()
        data_db = {} if not query else query.__dict__
        if only_db:
            return data_db
        node = cls.items.search_node_by_name(item_name, model_name=model.__name__)
        if node is None:
            return data_db
        if node.type == "__delete":
            return {}
        if node.type == "__insert":
            if data_db:
                cls.remove_items((item_name,))
                return data_db
        data_db.update(node.value)
        return data_db

    @classmethod
    def get_items(cls, model=None, primary_field=None, db_only=False) -> list[dict]:  # todo: придумать пагинатор
        """
        1) Получаем запись из таблицы в виде словаря
        2) Получаем данные из очереди в виде словаря
        3) db_data.update(quque_data)
        primary_field - поле, по которому происходит фильтрация
        Если primary_field со значением node.name найден в БД, то нода удаляется
        """
        if model:
            if not primary_field:
                raise ValueError("Если указана отличная от стандартной модель - то нужно указать и поле, "
                                 "по которому будет происходить выборка")
        else:
            primary_field = primary_field or cls._primary_field
            model = cls._model_obj
        cls._is_valid_model_instance(model, primary_field)
        items_db = model.query.all()
        if db_only:
            return [item.__dict__ for item in items_db]
        db_items = []
        queue_items = {}  # index: node_value
        output = []
        if items_db:
            nodes_implements_db = ORMItemContainer()  # Ноды, значения которых совпали с записями в БД
            node_names_to_remove = []
            for db_item in items_db:  # O(n)
                db_data: dict = db_item.__dict__
                if primary_field not in db_data:  # O(i)
                    raise KeyError("Несогласованность данных при получении из кеша и бд")
                primary_field_value = db_data.get(primary_field, None)  # O(1)
                node: ORMItem = cls.items.search_node_by_name(primary_field_value, model_name=model.__name__)  # O(k)
                if node:
                    new_node_attrs = cls._create_node_attrs_dict_from_other_node(node)  # O(1)
                    nodes_implements_db.enqueue(node.name, **new_node_attrs)  # O(k)
                    if node.type == "__insert":
                        node_names_to_remove.append(node.name)
                    elif node.type == "__update":
                        db_data.update(node.value)
                    if not node.type == "__delete":
                        queue_items.update({node.index: db_data})
                else:
                    db_items.append(db_data)
            if node_names_to_remove:
                cls.remove_items(node_names_to_remove, model=model)
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
            output.extend(sorted_nodes.values())
            output.extend(db_items)
            return output
        for node in cls.items:  # O(k)
            if node.model.__name__ == model.__name__:
                val = node.value
                output.append(val) if val else None
        return output

    @classmethod
    def get_node_dml_type(cls, node_name: str, model=None) -> Optional[str]:
        """ Получить тип операции с базой, например 'update', по названию ноды, если она найдена, иначе - None """
        model_name = model.__name__ if model else None
        node = cls.items.search_node_by_name(node_name, model_name=model_name)
        if not node:
            return
        return node.type

    @classmethod
    def remove_items(cls, node_names: Iterable[str], model=None):
        """
        Удалить ноду из очереди на сохранение
        """
        model = model or cls._model_obj
        [cls.items.remove_from_queue(name, model.__name__) for name in node_names]
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
            new_node_attributes = cls._create_node_attrs_dict_from_other_node(node)
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

    @classmethod
    @property
    def items(cls) -> ORMItemContainer:
        if cls._items:
            return cls._items
        items = cls._store.get("ORMItems")
        if not items:
            items = ORMItemContainer()
        cls._items = items
        return items

    @classmethod
    def set_model(cls, obj, primary_field):
        """

        :param obj: Класс модели Flask-SQLAlchemy
        :param primary_field: поле по которому обычно идёт выборка
        """
        cls._is_valid_model_instance(obj, primary_field)
        cls._model_obj = obj
        cls._primary_field = primary_field

    @classmethod
    def _is_valid_node_name(cls, name):
        if type(name) is not str:
            raise ValueError

    @staticmethod
    def _is_valid_model_instance(item, special_field):
        if item is None or not hasattr(item, "__tablename__"):
            raise TypeError("Значение атрибута model - неподходящего типа")
        if not hasattr(item, special_field):
            raise AttributeError

    @staticmethod
    def _is_valid_session(obj):  # todo: Пока не знаю как проверить
        return

    @classmethod
    def __set_cache(cls, container: Optional[ORMItemContainer]):
        cls._store.set("ORMItems", container, cls.CACHE_LIFETIME_HOURS)
        cls._items = container

    @staticmethod
    def _create_node_attrs_dict_from_other_node(node: ORMItem) -> dict:
        new_node_attributes = {"__insert": False, "__update": False, "__delete": False, "__model": node.model,
                               "__where": node.where, "__callback": node.callback}
        new_node_attributes.update({node.type: True})
        new_node_attributes.update(**node.value)
        return new_node_attributes
