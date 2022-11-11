import os
import threading
import traceback
from typing import Union, Iterator, Iterable, Optional, Sequence, Any, Callable
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
    def __init__(self, __node_name, **kw):
        super().__init__()
        self._is_valid_dml_type(kw)
        self.__model: db.Model = kw.pop("__model", None)
        self._is_valid_model_instance(self.__model)
        self._callback: Optional[Callable] = kw.pop("__callback", None)
        self.__insert = kw.pop("__insert")
        self.__update = kw.pop("__update")
        self.__delete = kw.pop("__delete")

        if __node_name is None:
            raise ValueError
        self.name: Any = __node_name  # Имя для удобного поиска со стороны UI. Это может быть название станка, стойки итп
        self.value = {}  # Содержимое - пары ключ-значение: поле таблицы бд: значение
        if len(kw):
            self.value.update(kw)
        self.ready = kw.pop("__ready", False)

    @property
    def type(self) -> str:
        return "__insert" if self.__insert else "__update" if self.__update else "__delete"

    @property
    def ready(self):
        return self.__is_ready

    @property
    def callback(self) -> Optional[callable]:
        return self._callback

    @ready.setter
    def ready(self, status: bool):
        if not self.value:
            return
        if not isinstance(status, bool):
            raise TypeError("Статус готовности - это тип данных boolean")
        self.__is_ready = status

    @property
    def model(self) -> db.Model:
        return self.__model

    def __eq__(self, other: "ORMItem"):
        if not isinstance(other, type(self)):
            return False
        try:
            self._is_valid_model_instance(other.model)
        except TypeError:
            return False
        return self.model.__name__ == other.model.__name__

    def __ne__(self, other: "ORMItem"):
        return not self.__eq__(other)

    def __repr__(self):
        return f"{type(self)}({self.__str__()})"

    def __str__(self):
        result = {}
        result.update(self.value)
        result.update({"__model": self.model, "__insert": False, "__update": False, "__delete": False, self.type: True})
        return f"{{'{self.name}': {result}}}"

    @staticmethod
    def _is_valid_dml_type(data: dict):
        """ Только одино свойство, обозначающее тип sql-dml операции, может быть True """
        is_insert = data.get("__insert", False)
        is_update = data.get("__update", False)
        is_delete = data.get("__delete", False)
        if not (isinstance(is_insert, bool) and isinstance(is_update, bool) and isinstance(is_delete, bool)):
            raise TypeError
        if sum((is_insert, is_update, is_delete)) != 1:
            raise ValueError

    @staticmethod
    def _is_valid_model_instance(item: db.Model):
        if not hasattr(item, "__tablename__"):
            raise TypeError("Значение атрибута model - неподходящего типа")


class ORMItemContainer(LinkedList):
    """
    Очередь
    Класс-контейнер умеет только ставить в очередь ((enqueue) зашита особая логика) и снимать с очереди (dequeue)
    """
    append = None
    __delitem__ = None
    LinkedListItem = ORMItem

    def __init__(self, items: Optional[Iterable[dict[str, dict]]] = None):
        super().__init__()
        if items is not None:
            for item in items:
                for block_name, inner in item.items():
                    self.enqueue(block_name, **inner)

    def enqueue(self, item_name, **kwargs):  # todo: Если будут ошмбки с БД - ищи их тут!
        """ Установка ноды в конец очереди.
        Если нода с name - item_name найдена, то произойдёт update словарю value,
        А также нода переносится в конец очереди """
        model_name = None
        model = kwargs.get("__model", None)
        if model is not None:
            model_name = model.__name__
        exists_item = self.__search_node_by_name(item_name, model_name=model_name)
        potential_new_item = self.LinkedListItem(item_name, **kwargs)
        new_item = None
        if exists_item == potential_new_item:
            new_item_is_update = kwargs.get("__update", False)
            new_item_is_delete = kwargs.get("__delete", False)
            new_item_is_insert = kwargs.get("__insert", False)
            if new_item_is_update == "__update":
                if exists_item.type == "__update" or exists_item.type == "__insert":
                    self._remove_from_queue(exists_item)
                    exists_item.value.update(kwargs)
                    new_item = exists_item
            if new_item_is_delete:
                self._remove_from_queue(exists_item)
                new_item = potential_new_item
            if new_item_is_insert:
                if exists_item.type == "__insert" or exists_item.type == "__update":
                    self._remove_from_queue(exists_item)
                    exists_item.value.update(kwargs)
                    new_item = exists_item
                if exists_item.type == "__delete":
                    self._remove_from_queue(exists_item)
                    new_item = potential_new_item
        else:
            new_item = potential_new_item
        if new_item is not None:
            if self._length:
                last_element = self._tail
                self._set_prev(new_item, last_element)
                self._set_next(last_element, new_item)
                self._tail = new_item
            else:
                self._head = self._tail = new_item

    def dequeue(self) -> Optional[ORMItem]:
        """ Узвлечение ноды с начала очереди """
        node = self._head
        if node is None:
            return
        self._remove_from_queue(node)
        return node

    def remove_from_queue(self, node_name: str, model_name: str) -> None:
        """

        :param node_name: Имя сущности, сохраняющейся в БД
        :param model_name: Имя модели, к которой сущность привязана,
        :return:
        """
        if type(node_name) is not str or type(model_name) is not str:
            raise TypeError
        node = self.__search_node_by_name(node_name, model_name)
        if node is not None:
            self._remove_from_queue(node)

    def _remove_from_queue(self, node) -> None:
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

    def __search_node_by_name(self, name: str, model_name: Optional[str] = None) -> Optional[ORMItem]:
        for node in self:
            if node.name == name:
                if model_name is not None:
                    if model_name == node.model.__name__:
                        return node
                else:
                    return node

    def __repr__(self):
        return f"{self.__class__}({tuple(str(i) for i in self)})"

    def __str__(self):
        return str(tuple(str(i) for i in self))


class ORMHelper:
    """
    Адаптер
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
    def set_item(cls, key, value: dict, insert=False, update=False, delete=False, ready=False, callback=None):
        """
         Если ключ найден в очереди, то данная пара: ключ-значение удаляется
          и помещается в конец очереди
        """
        if cls._model_obj is None:
            raise AttributeError("Не установлена модель БД для сохранения записей.")
        if not insert and not update and not delete:
            raise ValueError("Задайте тип DML операции: insert, update или delete")
        if insert and update and delete:
            raise ValueError("Не правильно задан тип DML-SQL операции!")
        if not isinstance(value, dict):
            raise TypeError("В качестве значений выступают словари")
        cls._items.enqueue(key, __model=cls._model_obj, __ready=ready,
                           __insert=insert, __update=update, __delete=delete, __callback=callback, **value)

    @classmethod
    def remove_item(cls, name: str):
        return cls._items.remove_from_queue(name, cls._model_obj)

    @classmethod
    def release(cls) -> None:
        """
        Этот метод стремится высвободить очередь сохраняемых объектов,
        путём итерации по ним, и попыткой сохранить в базу данных.
        :return: None
        """
        orm_element = cls._items.dequeue()
        while orm_element is not None:
            orm_element = cls._items.dequeue()
            if orm_element is None:
                return
            dml_method = getattr(cls, f"_{cls.__name__}{orm_element.type}", None)
            if dml_method is None:
                raise AttributeError
            try:
                dml_method(orm_element)
            except DBAPIError:
                print("Установка элементов в очередь")
                cls._items.enqueue(orm_element.name, **orm_element.value)
            finally:
                callback = orm_element.callback
                if callback is not None:
                    callback()

    @classmethod
    def set_model(cls, obj: db.Model):
        cls._is_valid_model_instance(obj)
        cls._model_obj = obj

    @classmethod
    def items(cls):
        return cls._items

    @classmethod
    def __insert(cls, orm_node):
        """ SQL INSERT """
        print(f"INSERT {orm_node}")

    @classmethod
    def __update(cls, orm_node):
        """ SQL UPDATE """
        print(f"UPDATE {orm_node}")

    @classmethod
    def __delete(cls, orm_node):
        """ SQL DELETE """
        print(f"DELETE {orm_node}")

    @staticmethod
    def _is_valid_model_instance(item: db.Model):
        if item is None or not hasattr(item, "__tablename__"):
            raise TypeError("Значение атрибута model - неподходящего типа")


if __name__ == "__main__":
    TestORMAdapter = ORMHelper.set_up(db.session)
    TestORMAdapter.set_model(Machine)
    TestORMAdapter.set_item("Heller", {"id": 3, "name": "Heller"}, insert=True, callback=lambda: print("Сработал callback"))
    TestORMAdapter.set_item("Fidia", {"id": 2, "name": "Rambaudi"}, update=True)
    TestORMAdapter.set_item("Fidia", {"id": 4, "name": "Rambaudi123"}, update=True)
    TestORMAdapter.set_item("Fidia", {"id": 4}, delete=True)
    print(TestORMAdapter.items())
    #TestORMAdapter.release()
    #print(TestORMAdapter.items())
    #print(len(TestORMAdapter.items()))

