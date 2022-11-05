import os
import threading
import traceback
from typing import Union, Iterator, Iterable, Optional, Sequence, Any
from itertools import count, cycle
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTabWidget, QStackedWidget, QPushButton, QInputDialog, QDialogButtonBox, \
    QListWidgetItem, QListWidget, QDialog, QLabel, QVBoxLayout, QHBoxLayout, QTreeWidgetItem, QTreeWidget, QLineEdit
from PySide2.QtGui import QIcon
from sqlalchemy.exc import DBAPIError
from database.models import db
from gui.ui import Ui_main_window as Ui
from datatype import LinkedList, LinkedListItem
from database.models import Machine


class Tools:

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
        # button.setFocus() todo
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
            value = input_.text()
            if value:
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

    @staticmethod
    def get_current__q_list_widget_item(widget: QListWidget) -> QListWidgetItem:
        return widget.currentItem()

    def _lock_ui(self):
        self.main_ui.root_tab_widget.setDisabled(True)

    def _unlock_ui(self):
        self.main_ui.root_tab_widget.setEnabled(True)


class ORMItem(LinkedListItem):
    """ Именованный атрибут model должен присутствовать при инициализации """
    def __init__(self, name, **kw):
        super().__init__()
        self.__model: db.Model = kw.pop("__model")
        self.__dml_operation_type = kw.pop("__type")
        if self.__model is None:
            raise AttributeError("Не удалось инициализировать экземпляр ORMItem. Среди именованных атрибутов ожидался атрибут model.")
        self.__is_valid_model_instance(self.__model)
        if name is None:
            raise ValueError
        self.name: Any = name  # Имя для удобного поиска со стороны UI. Это может быть название станка, стойки итп
        self.value = {}  # Содержимое - пары ключ-значение: поле таблицы бд: значение
        if len(kw):
            self.value.update(kw)
        self.ready = kw.pop("__ready", False)

    @property
    def type(self):
        return self.__dml_operation_type

    @property
    def ready(self):
        return self.__is_ready
    
    @ready.setter
    def ready(self, status: bool):
        if not self.value:
            return
        if not isinstance(status, bool):
            raise TypeError("Статус готовности - это тип данных boolean")
        self.__is_ready = status

    @property
    def model(self):
        return self.__model

    @staticmethod
    def __is_valid_model_instance(item: db.Model):
        if not type(item) is db.Model:
            raise TypeError("Значение атрибута model - неподходящего типа")

    def __eq__(self, other: "ORMItem"):
        try:
            self.__is_valid_model_instance(other)
        except TypeError:
            return False
        return self.value == other.value


class ORMItemContainer(LinkedList):
    """
    Очередь
    """
    append = None

    LinkedListItem = ORMItem

    def __init__(self, items: Optional[Iterable[dict[str, dict]]] = None):
        super().__init__()
        if items is not None:
            for item in items:
                for block_name, inner in item.items():
                    self.enqueue(block_name, **inner)

    def enqueue(self, item_name, **kwargs):
        """ Если нода с name - item_name найдена, то произойдёт update словарю value,
        А также нода переносится в конец очереди """
        item = self.__search_node_by_name(item_name)
        if item is not None and item.type == "update" == kwargs.get("update", ""):
            item.value.update(kwargs)
        else:
            item = self.LinkedListItem(item_name, **kwargs)
        if self:
            last_element = self._tail
            self._set_prev(last_element, item)
            self._set_next(item, last_element)
            self._tail = item
        else:
            self._head = self._tail = item

    def remove(self, key):
        item = self.__search_node_by_name(key)
        if item is None:
            return
        self.__delitem__(key)
        return item

    def get(self, key):
        node = self.__search_node_by_name(key)
        return node.value

    def __getitem__(self, item: str):
        node = self.__search_node_by_name(item)
        if node is None:
            raise KeyError
        return node.value

    def __delitem__(self, name):
        node = self.__search_node_by_name(name)
        if node is None:
            raise KeyError
        prev_node = node.prev
        next_node = node.next
        if prev_node is None:
            self._head = next_node
            node.next = None
            return
        if next_node is None:
            self._tail = prev_node
            node.prev = None
            return
        next_node.prev = prev_node
        prev_node.next = next_node

    def __str__(self):
        items = list()
        for node in self:
            items.append({node.name: node.value})
        return str(items)

    def __repr__(self):
        items = list()
        for node in self:
            items.append({node.name: node.value})
        return f"{self.__class__}({items})"

    def __search_node_by_name(self, name) -> Optional[ORMItem]:
        for node in self:
            if node.name == name:
                return node


class ORMHelper:
    """
    Класс-контейнер не имеющий своих экземпляров.
    Связанный список, хранящий ноды, в основе реализована следующая логика при добавлении записи:
        --CONTAINER--
        - Присутствует атрибут model, он присваивается всем создающимся элементам-ITEM
        ----
        --ITEM--
        - При добавлении элемента он имеет статус ready=False
        - При редактировании элемента он получает статус ready=False
        - При Добавлении происходит попытка найти в связанном списке элемент с таким же name
        ----
    """
    RELEASE_INTERVAL_SECONDS = 10
    _items: Optional[ORMItemContainer] = None
    _timer: Optional[threading.Timer] = None
    _session: Optional[db.session] = None
    _model_obj: db.Model = None  # Текущий класс модели, присваиваемый автоматически всем экземплярам при добавлении в очередь
    _previous_saved_obj: Optional[ORMItem] = None

    @classmethod
    def set_up(cls, session: db.session):
        cls._session = session
        cls._items = ORMItemContainer()

        def init_timer():
            timer = threading.Timer(cls.RELEASE_INTERVAL_SECONDS * 1000, cls.release)
            timer.start()
            return timer
        cls._timer = init_timer()
        return cls

    @classmethod
    def set_item(cls, key, value: dict, insert=False, update=False, delete=False, ready=False):
        """
         Если ключ найден в очереди, то данная пара: ключ-значение удаляется
          и помещается в конец очереди
        """
        if cls.model is None:
            raise AttributeError("Не установлена модель БД для сохранения записей.")
        if insert and update and delete or not insert and not update and not delete:
            raise ValueError("Не правильно задан тип DML-SQL операции!")
        if not isinstance(value, dict):
            raise TypeError("Задумано таким образом, что в качестве значений выступают словари")
        cls._items.append(key, __model=cls.model,
                          __ready=ready, __insert=insert, __update=update, __delete=delete, **value)

    @classmethod
    def release(cls) -> None:
        """
        Этот метод стремится высвободить очередь сохраняемых объектов,
        путём итерации по ним, и попыткой сохранить в базу данных.
        :return: None
        """
        for obj in cls._items:
            operation_type = obj.popitem()

    @property
    def model(self):
        return self._model_obj

    @model.setter
    def model(self, obj):
        self._model_obj = obj

    @classmethod
    def _insert_items(cls, callback=None):
        """ SQL INSERT """
        if cls.model is None:
            raise AttributeError("Не установлен класс модели")
        session = cls._session
        success = False
        for item_name, data in cls:
            if cls._is_unique_saved_object(data, cls._previous_saved_obj):
                session.add(cls._model_obj(**data))
                success = True
        if not success:
            return
        try:
            session.commit()
        except DBAPIError:
            print("Ошибка API базы данных")
        else:
            cls._previous_saved_obj = dict(cls.items()).popitem()
            cls.__values = {}
            if callback is not None:
                callback()

    @classmethod
    def _update_items(cls, query_body: dict, callback=None):
        """ SQL UPDATE """
        if cls.model is None:
            raise AttributeError("Не установлен класс модели")
        session = cls._session
        success = False
        for item_name, data in cls.items():
            if not cls._is_unique_saved_object(data, cls._previous_saved_obj):
                return
            query = cls._model_obj.query.filter_by(**query_body)
            if not query.count():
                return
            instance = query.first()
            [setattr(instance, k, v) for k, v in data.items()]
            session.add(instance)
            success = True
        if not success:
            return
        try:
            session.commit()
        except DBAPIError:
            traceback.print_exc()
            print("Ошибка API базы данных")
        else:
            cls._previous_saved_obj = dict(cls.items()).popitem()
            cls.__values = {}
            if callback is not None:
                callback()

    @classmethod
    def _delete_items(cls):
        """ SQL DELETE """
        pass

    @staticmethod
    def _is_unique_saved_object(obj1, obj2):
        return obj1 != obj2


if __name__ == "__main__":
    test = ORMHelper.set_up(db.session)
    test.model = Machine
    test.update("key", 4, insert=True)
