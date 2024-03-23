import datetime
import itertools
import hashlib
import sys
import copy
import threading
import warnings
from weakref import ref, ReferenceType
from typing import Union, Iterator, Iterable, Optional, Literal, Callable, Type
from collections import ChainMap
from pymemcache.client.base import Client
from pymemcache.exceptions import MemcacheError
from pymemcache_dill_serde import DillSerde
from pymemcache.test.utils import MockMemcacheClient
from psycopg2.errors import Error as PsycopgError
from sqlalchemy import create_engine, ColumnDefault, delete
from sqlalchemy.sql.dml import Insert, Update, Delete
from sqlalchemy.sql.expression import select
from sqlalchemy.orm import Query, sessionmaker as session_factory, Session
from sqlalchemy.exc import DisconnectionError, OperationalError, SQLAlchemyError
from gui.datatype import LinkedList, LinkedListItem
from database.models import CustomModel, ModelController, DATABASE_PATH, DATABASE_PATH_FOR_TESTS
from gui.orm.exceptions import *


DEBUG = False


class ORMAttributes:
    @classmethod
    def is_valid_node(cls, node: Union["ORMItem", "SpecialOrmItem"]):
        if type(node) is not ORMItem and type(node) is not SpecialOrmItem:
            raise TypeError
        cls.is_valid_model_instance(node.model)

    @staticmethod
    def is_valid_model_instance(item):
        if callable(item):
            item = item()  # __new__
            if not hasattr(item, "column_names"):
                raise InvalidModel
            keys = {"type", "nullable", "primary_key", "autoincrement", "unique", "default"}
            if any(map(lambda x: keys - set(x), item.column_names.values())):
                raise ModelsConfigurationError
            return
        raise InvalidModel

    @staticmethod
    def is_valid_container(container):
        if not isinstance(container, (ORMItemQueue, SpecialOrmContainer,)):
            raise TypeError


class ModelTools(ORMAttributes):
    """ Высокоуровневый инструментарий для валидации полей данных в локальной очереди, производства ключей, и другого,
     что требует 'живой' связи между очередью в локальном хранилище и/или базой данных"""
    @classmethod
    def _create_autoincrement_pk(cls, node: Union["ORMItem", "SpecialOrmItem"]):
        return len(list(cls._get_nodes_by_current_model(node.container, node.model.__name__))) + 1

    @classmethod
    def _select_primary_key_value_from_scalars(cls, node: "ORMItem", field_name: str):
        """ Выбрать значние из значений ноды,
        если primary_key=True установлено для строки или другого поля со скалярными значекниями"""
        try:
            value = node.value[field_name]
        except KeyError:
            raise NodePrimaryKeyError("Должно быть значение для поля первичного ключа")
        return value

    @staticmethod
    def _get_nodes_by_current_model(container: "ORMItemQueue", model_name: str) -> Iterator[int]:
        for node in container:
            if node.model.__name__ == model_name:
                yield node.get_primary_key_and_value(only_value=True)

    @staticmethod
    def _check_unique_values(node) -> bool:
        model_data = node.model().column_names
        for column_name, value in node.value.items():
            if model_data[column_name]["unique"]:
                for n in node.container:
                    if n.model.__name__ == node.model.__name__:
                        if column_name in n.value:
                            if n.value[column_name] == value:
                                return False
        return True

    @staticmethod
    def _check_not_null_fields_in_node_value(node: "ORMItem") -> bool:
        """ Проверить все поля на предмет nullable """
        model_attributes: dict[dict] = node.model().column_names
        for k, attributes in model_attributes.items():
            if not attributes["nullable"]:
                if k not in node.value:
                    return False
                if type(node.value[k]) is None:
                    return False
        return True

    @staticmethod
    def _is_valid_column_type_in_sql_type(node: "ORMItem") -> bool:
        """ Проверить соответствие данных в ноде на предмет типизации.
         Если тип данных отличается от табличного в БД, то возбудить исключение"""
        data = node.model().column_names
        for column_name in node.value:
            if column_name not in data:
                return False
            if not isinstance(node.value[column_name], data[column_name]["type"]):
                if node.value[column_name] is None and data[column_name]["nullable"]:
                    continue
                raise NodeColumnValueError(text=f"Столбец {column_name} должен быть производным от "
                                                f"{str(data[column_name]['type'])}, "
                                                f"по факту {type(node.value[column_name])}")
        return True


class ORMItem(LinkedListItem, ModelTools):
    """ Иммутабельный класс ноды для ORMItemQueue. """
    def __init__(self, _container=None, **kw):
        """
            :arg _model: Расширенный клас model SQLAlchemy
            :arg _insert: Опицонально bool
            :arg _update: Опицонально bool
            :arg _delete: Опицонально bool
            :arg _ready: Если __delete=True - Необязательный
            :arg _where: Опицонально dict
            Все остальные параметры являются парами 'поле-значение'
            """
        super().__init__()
        if _container is None:
            raise ValueError("Необходимо указать ссылку на экземпляр контейнера")
        self.is_valid_container(_container)
        self._container: ReferenceType[Union["ORMItemQueue", "SpecialOrmContainer"]] = ref(_container)
        self.__model: Union[Type[CustomModel], Type[ModelController]] = kw.pop("_model")
        self.is_valid_model_instance(self.__model)
        self.__insert = kw.pop("_insert", False)
        self.__update = kw.pop("_update", False)
        self.__delete = kw.pop("_delete", False)
        self.__is_ready = kw.pop("_ready", True if self.__delete else False)
        self.__where = kw.pop("_where", None)
        self._create_at = kw.pop("_create_at", datetime.datetime.now())
        self.__transaction_counter = kw.pop('_count_retries', 0)  # Инкрементируется при вызове self.make_query()
        # Подразумевая тем самым, что это попытка сделать транзакцию в базу
        if not kw:
            raise NodeEmptyData
        self._value = {}  # Содержимое - пары ключ-значение: поле таблицы бд: значение
        self._value.update(kw)
        self.__foreign_key_fields = self.__model().foreign_keys
        self.__relative_primary_key = False

        def is_valid_dml_type():
            """ Только одино свойство, обозначающее тип sql-dml операции, может быть True """
            if not isinstance(self.__insert, bool) or not isinstance(self.__update, bool) or \
                    not isinstance(self.__delete, bool):
                raise TypeError
            if sum((self.__insert, self.__update, self.__delete,)) != 1:
                raise NodeDMLTypeError
        is_valid_dml_type()
        self._field_names_validation()
        self.__primary_key = self.__create_primary_key()
        self._value.update(self.__primary_key)
        _ = self.ready

        def check_current_primary_key_is_relative():
            """ Является ли первичный ключ относительным.
            Под этим понимается то, что при последующих репликациях во время
            enqueue значение первичного ключа является автоинкрементом или неким вычисляемым значением по умолчанию,
            предугадать которое не представляется возможным,- такой первичный ключ мы будем называть относительным."""
            model_data = self.model().column_names[self.get_primary_key_and_value(only_key=True)]
            if model_data["autoincrement"] or model_data["default"]:
                self.__relative_primary_key = True
        check_current_primary_key_is_relative()

    @property
    def value(self):
        return self._value.copy()

    @property
    def is_relative_primary_key(self):
        return self.__relative_primary_key

    @property
    def container(self):
        if not hasattr(self, "_container"):
            return
        return self._container()

    @container.setter
    def container(self, cnt):
        if type(cnt) is not ORMItemQueue:
            raise TypeError
        self._container = ref(cnt)

    @property
    def model(self):
        return self.__model

    @property
    def retries(self):
        return self.__transaction_counter

    @property
    def foreign_key_fields(self) -> Iterator[dict[str, str]]:
        """ Название таблицы и название поля PK у той таблицы, на которую ссылается ЭТА нода """
        def parse_foreign_key_table_name_and_column_name():
            for obj_ in self.__foreign_key_fields:
                string: str = obj_.column.__str__()
                table, column = string.split(".")
                yield {"table_name": table, "column_name": column}
        return parse_foreign_key_table_name_and_column_name()
    
    def get(self, k, default_value=None):
        try:
            value = self.__getitem__(k)
        except KeyError:
            value = default_value
        return value

    def get_primary_key_and_value(self, as_tuple=False, only_key=False, only_value=False) -> Union[dict, tuple, int, str]:
        """
        :param as_tuple: ключ-значение в виде кортежа
        :param only_key: только название столбца - PK
        :param only_value: только значение столбца первичного ключа
        """
        if only_key:
            return tuple(self.__primary_key.keys())[0]
        if only_value:
            return tuple(self.__primary_key.values())[0]
        return tuple(self.__primary_key.items())[0] if as_tuple else self.__primary_key

    @property
    def created_at(self):
        return self._create_at

    @property
    def where(self) -> dict:
        return self.__where.copy() if self.__where else {}

    @property
    def ready(self) -> bool:
        self.__is_ready = self._is_valid_column_type_in_sql_type(self)
        self.__is_ready = self._check_unique_values(self) if self.__is_ready else False
        self.__is_ready = self._check_not_null_fields_in_node_value(self) if self.__is_ready else False
        return self.__is_ready

    @ready.setter
    def ready(self, status: bool):
        if not isinstance(status, bool):
            raise NodeAttributeError("Статус готовности - это тип данных boolean")
        self.__is_ready = status

    @property
    def type(self) -> str:
        return "_insert" if self.__insert else "_update" if self.__update else "_delete"

    def get_attributes(self, with_update: Optional[dict] = None) -> dict:
        if with_update is not None and type(with_update) is not dict:
            raise TypeError
        result = {}
        result.update(self.value)
        if self.__update or self.__delete:
            if self.__where:
                result.update({"_where": self.where})
        result.update({"_model": self.__model, "_insert": False,
                       "_update": False, "_ready": self.__is_ready,
                       "_delete": False, "_count_retries": self.retries, "_container": self.container})
        result.update({self.type: True})
        result.update(with_update) if with_update else None
        return result

    def make_query(self) -> Optional[Query]:
        if self.__transaction_counter % 2:
            self.__insert, self.__update = self.__update, self.__insert
        query = None
        value: dict = self.value
        primary_key = self.get_primary_key_and_value(only_key=True)
        where = self.__where
        if self.__should_remove_primary_key:
            del value[primary_key]
            where = value if not where else where
        else:
            where = where if where else self.get_primary_key_and_value()
        if self.__insert:
            query = self.model(**value)
        if self.__update or self.__delete:
            query = self.model.query.filter_by(**where).first()
            if query is not None:
                if self.__update:
                    [setattr(query, key, value) for key, value in value.items()]
                if self.__delete:
                    query = delete(self.model).where(
                        ", ".join(map(lambda x: f"{self.model.__tablename__}.{x[0]} == '{x[1]}'", value.items()))
                    )
        self.__transaction_counter += 1
        return query

    def __len__(self):
        if not hasattr(self, "_value"):
            return 0
        return len(self._value)

    def __eq__(self, other: "ORMItem"):
        if type(other) is not type(self):
            return False
        return self.__hash__() == hash(other)

    def __contains__(self, item: str):
        if not isinstance(item, str):
            raise TypeError
        if ":" not in item:
            raise KeyError("Требуется формат 'key:value'")
        key, value = item.split(":")
        if key not in self.value:
            return False
        val = self.value[key]
        return value == val

    def __bool__(self):
        return bool(len(self))

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.value)

    def __hash__(self):
        value = self.value
        if self.is_relative_primary_key:
            del value[self.get_primary_key_and_value(only_key=True)]
        str_ = "".join(map(lambda x: str(x), itertools.chain(*value.items())))
        return int.from_bytes(hashlib.md5(str_.encode("utf-8")).digest(), "big")

    def __getitem__(self, item: str):
        if type(item) is not str:
            raise TypeError
        if item not in self.value:
            raise KeyError
        return self.value[item]

    def _field_names_validation(self, from_polymorphizm=False) -> Optional[set[str]]:
        """ соотнести все столбцы ноды в словаре value со столбцами из класса Model """
        def clear_names():
            """ ORM могла добавить префиксы вида 'ModelClassName.column_name', очистить имена от них """
            value = {(k[k.index(".") + 1:] if "." in k else k): v for k, v in self.value.items()}
            return value
        field_names = self.model().column_names
        any_ = set(clear_names()) - set(field_names)
        if any_:
            if from_polymorphizm:
                return any_
            raise NodeColumnError

    @property
    def __should_remove_primary_key(self) -> bool:
        """ Нужно ли удалить первичный ключ со значением из значений во время коммита в базу """
        self.is_valid_model_instance(self.model)
        attributes = self.model().column_names
        for field_name, data in attributes.items():
            if not data["primary_key"]:
                continue
            if data["autoincrement"]:
                return True
            if data["default"]:
                return True
            return False
    
    def __create_primary_key(self) -> dict[str, Union[str, int]]:
        """Повторный вызов недопустим. Вызывать в первую очередь! до добаления ноды в связанный список"""
        attributes = self.model().column_names
        for field_name, data in attributes.items():
            if not data["primary_key"]:
                continue
            if field_name in self._value:
                # Если первичный ключ и значение были переданы в ноду при инициализации - считать это первичным ключом
                return {field_name: self._value[field_name]}
            default_: Optional[ColumnDefault] = data["default"]
            autoincrement, type_ = data["autoincrement"], data["type"]
            if default_:
                return {
                    field_name: default_.execute(bind=create_engine(DATABASE_PATH_FOR_TESTS if DEBUG else DATABASE_PATH))
                }
            if type_ is str:
                return {field_name: self._select_primary_key_value_from_scalars(self, field_name)}
            if type_ is int:
                if autoincrement:
                    return {field_name: self._create_autoincrement_pk(self)}
                return {field_name: self._select_primary_key_value_from_scalars(self, field_name)}


class EmptyOrmItem(LinkedListItem):
    """
    Пустой класс для возврата пустой "ноды". Заглушка
    """
    def __eq__(self, other):
        if type(other) is type(self):
            return True
        return False

    def __len__(self):
        return 0

    def __bool__(self):
        return False

    def __repr__(self):
        return f"{type(self).__name__}()"

    def __str__(self):
        return "None"

    def __hash__(self):
        return 0


class ORMItemQueue(LinkedList):
    """
    Очередь на основе связанного списка.
    Управляется через адаптер ORMHelper.
    Класс-контейнер умеет только ставить в очередь ((enqueue) зашита особая логика) и снимать с очереди (dequeue)
    см логику в методе _replication.
    """
    LinkedListItem = ORMItem

    def __init__(self, items: Optional[Iterable[dict]] = None):
        super().__init__()
        if items is not None:
            for inner in items:
                self.enqueue(**inner)

    def enqueue(self, **attrs):
        """ Установка ноды в конец очереди с хитрой логикой проверки на совпадение. """
        exists_item, new_item = self._replication(**attrs)

        def check_foreign_key_nodes() -> ORMItemQueue:  # O(n) * (O(k) + O(i) + O(i)) -> O(n) * O(j) -> O(n)
            """
            Найти ноды, которые зависят от ноды, которая в настоящий момент добавляется:
            Если такие ноды найдутся, то они будут удалены и добавлены в очередь снова
            (перемена мест)
            """
            nodes_to_move_in_end_queue = self.__class__()
            new_item_primary_key_name = new_item.get_primary_key_and_value(only_key=True)
            for left_node in self:  # O(n)
                if new_item_primary_key_name in left_node.foreign_key_fields:  # O(k)
                    nodes_to_move_in_end_queue.enqueue(**left_node.get_attributes())  # O(i)
            new_container = self
            if nodes_to_move_in_end_queue:
                new_container = self + nodes_to_move_in_end_queue  # O(i)
            return new_container
        self._remove_from_queue(exists_item) if exists_item else None
        super().append(**new_item.get_attributes())
        new_nodes = check_foreign_key_nodes()
        self._replace_inner(new_nodes.head, new_nodes.tail)

    def dequeue(self) -> Optional[ORMItem]:
        """ Извлечение ноды с начала очереди """
        left_node = self._head
        if left_node is None:
            return
        self._remove_from_queue(left_node)
        return left_node

    def remove(self, model, pk_field_name, pk_field_value):
        left_node = self.get_node(model, **{pk_field_name: pk_field_value})
        if left_node:
            self._remove_from_queue(left_node)
            return left_node

    def get_related_nodes(self, main_node: ORMItem) -> "ORMItemQueue":
        """ Получить все связанные (внешним ключом) с передаваемой нодой ноды.
        O(i) * O(1) + O(n) = O(n)"""
        def get_column_name(data: dict, value) -> Optional[str]:
            """ Обойти все поля, и, если значение поля совпадает с value, то вернём это название """
            for name, val in data.items():
                if val == value:
                    return name
        container = self.__class__()
        for related_node in self:  # O(n) * O(j) * O(m) * O(n) * O(1) = O(n)
            if not related_node == main_node:  # O(g) * O(j) = O (j)
                for fk_field_data in main_node.foreign_key_fields:  # O(i)
                    table_name, column_name = fk_field_data["table_name"], fk_field_data["column_name"]
                    if table_name == related_node.model.__tablename__:
                        pk_field, pk_value = related_node.get_primary_key_and_value(as_tuple=True)
                        if pk_field == column_name:
                            main_node_fk_column_name = get_column_name(main_node.value, pk_value)
                            if main_node_fk_column_name is not None:
                                if main_node.value[main_node_fk_column_name] == related_node.value[column_name]:
                                    container.append(**related_node.get_attributes())  # O(1)
        return container

    def search_nodes(self, model, negative_selection=False, **_filter) -> "ORMItemQueue":  # O(n)
        """
        Искать ноды по совпадениям любых полей
        :arg model: кастомный объект, смотри модуль database/models
        :arg _filter: словарь содержащий набор полей и их значений для поиска
        :arg negative_selection: режим отбора нод (найти нады КРОМЕ ... [filter])
        """
        ORMItem.is_valid_model_instance(model)
        items = self.__class__()
        nodes = iter(self)
        while nodes:
            try:
                left_node: ORMItem = next(nodes)
            except StopIteration:
                return items
            if left_node.model.__name__ == model.__name__:  # O(u * k)
                if not _filter and not negative_selection:
                    items.append(**left_node.get_attributes())
                for field_name, value in _filter.items():
                    if field_name in left_node.value:
                        if negative_selection:
                            if not left_node.value[field_name] == value:
                                items.append(**left_node.get_attributes())
                                break
                        else:
                            if left_node.value[field_name] == value:
                                items.append(**left_node.get_attributes())
                                break
        return items

    def get_node(self, model: CustomModel, **primary_key_data) -> Optional[ORMItem]:
        """
        Данный метод используется при инициализации - _replication
        :arg model: объект модели
        :arg primary_key_data: словарь вида - {имя_первичного_ключа: значение}
        """
        ORMItem.is_valid_model_instance(model)
        if len(primary_key_data) != 1:
            raise NodePrimaryKeyError
        nodes = iter(self)
        while nodes:
            try:
                left_node: Optional[ORMItem] = next(nodes)
            except StopIteration:
                break
            if left_node.model.__name__ == model.__name__:  # O(k) * O(x)
                if left_node.get_primary_key_and_value() == primary_key_data:  # O(k1) * O(x1) * # O(k2) * O(x2)
                    return left_node

    def __repr__(self):
        return f"{self.__class__.__name__}({tuple(repr(m) for m in self)})"

    def __str__(self):
        return str(tuple(str(m) for m in self))

    def __contains__(self, item: ORMItem) -> bool:
        if type(item) is not ORMItem:
            return False
        for node in self:
            if hash(node) == item.__hash__():
                return True
        return False

    def __add__(self, other: "ORMItemQueue"):
        if not type(other) is self.__class__:
            raise TypeError
        result_instance = self.__class__()
        [result_instance.append(**n.get_attributes(with_update={"_container": result_instance})) for n in self]  # O(n)
        [result_instance.enqueue(**n.get_attributes(with_update={"_container": result_instance})) for n in other]  # O(n**2) todo n**2!
        return result_instance

    def __iadd__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError
        result: ORMItemQueue = self + other
        self._head = result.head
        self._tail = result.tail
        return result

    def __sub__(self, other: "ORMItemQueue"):
        if not isinstance(other, self.__class__):
            raise TypeError
        result_instance = copy.deepcopy(self)
        [result_instance.remove(n.model, *n.get_primary_key_and_value(as_tuple=True)) for n in other]
        return result_instance

    def __and__(self, other: "ORMItemQueue"):
        if type(other) is not self.__class__:
            raise TypeError
        output = self.__class__()
        for right_node in other:
            left_node = self.get_node(right_node.model, **right_node.get_primary_key_and_value())
            if left_node is not None:
                output.enqueue(**left_node.get_attributes())
                output.enqueue(**right_node.get_attributes())
        return output

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if len(self) != len(other):
            return False
        return hash(self) == hash(other)

    def __hash__(self):
        return sum(map(lambda n: hash(n), self))

    def _replication(self, **new_node_complete_data: dict) -> tuple[Optional[ORMItem], ORMItem]:  # O(l * k) + O(n) + O(1) = O(n)
        """
        Создавать ноды для добавления можно только здесь! Логика для постаовки в очередь здесь.
        1) Инициализация ноды: первичного ключа (согласно атрибутам класса модели), данных в ней и др
        2) Попытка найти ноду от той же модели с таким же первичным ключом -->
        заменяем ноду в очерени новой, смешивая value, если найдена, return
        Иначе
        3) Получаем список столбцов модели с unique=True
        Если столбца нету заменяем ноду в очерени новой, смешивая value, если найдена, return
        4) В новой ноде из п1 ищем все значения по столбцам из п3
        Если нет ни одного значения -> заменяем ноду в очерени новой, смешивая value, если найдена, return
        5) Найти в очереди ноды с той же моделью, полями и значениями
        Если не найдено ни одной ноды -> заменяем ноду в очерени новой, смешивая value, если найдена, return
        6) Берём ноду из очереди у которой максимальное кол-во совпадений -> заменяем ноду в очерени новой,
        смешивая value, если найдена, return
        """
        potential_new_item = self.LinkedListItem(**new_node_complete_data)  # O(1)
        new_item = None

        def merge(old_node: ORMItem, new_node: ORMItem, dml_type: str) -> ORMItem:
            new_node_data = old_node.get_attributes()
            old_where, new_where = old_node.where, new_node.where
            old_where.update(new_where)
            new_node_data.update({"_where": old_where})
            old_value, new_value = old_node.value, new_node.value
            old_value.update(new_value)
            new_node_data.update(old_value)
            new_node_data.update({"_insert": False, "_update": False, "_delete": False})
            new_node_data.update({dml_type: True, "_ready": new_node.ready})
            return self.LinkedListItem(**new_node_data)

        def find_node_to_replace_by_unique_values() -> Optional[ORMItem]:
            def get_unique_column_names():
                return [name for name, data in potential_new_item.model().column_names.items() if data["unique"]]

            def collect_values(n: ORMItem, *fields):
                d = {}
                for field in fields:
                    if field in n.value:
                        d.update({field: n.value[field]})
                return d

            def count_(node: ORMItem) -> int:
                counter = 0
                for key, value in node.value.items():
                    if key in unique_values_in_new_node:
                        if value == unique_values_in_new_node[key]:
                            counter += 1
                return counter
            unique_fields = get_unique_column_names()
            unique_values_in_new_node = collect_values(potential_new_item, *unique_fields)
            if not unique_values_in_new_node:
                return
            nodes_with_unique_fields = self.search_nodes(potential_new_item.model, **unique_values_in_new_node)
            if not nodes_with_unique_fields:
                return
            items_counter = dict(enumerate(map(lambda node: count_(node), nodes_with_unique_fields)))  # index: counter
            items_counter = dict(zip(items_counter.values(), items_counter.keys()))
            return nodes_with_unique_fields[items_counter[max(items_counter)]]
        exists_item = self.get_node(potential_new_item.model, **potential_new_item.get_primary_key_and_value())  # O(n)
        if not exists_item:
            exists_item = find_node_to_replace_by_unique_values()
        if not exists_item:
            new_item = potential_new_item
            return None, new_item
        new_item_is_update = new_node_complete_data.get("_update", False)
        new_item_is_delete = new_node_complete_data.get("_delete", False)
        new_item_is_insert = new_node_complete_data.get("_insert", False)
        if new_item_is_update:
            if exists_item.type == "_insert" or exists_item.type == "_update":
                if exists_item.type == "_insert":
                    new_item = merge(exists_item, potential_new_item, "_insert")
                if exists_item.type == "_update":
                    new_item = merge(exists_item, potential_new_item, "_update")
            if exists_item.type == "_delete":
                new_item = potential_new_item
        if new_item_is_delete:
            new_item = potential_new_item
        if new_item_is_insert:
            if exists_item.type == "_insert" or exists_item.type == "_update":
                new_item = merge(exists_item, potential_new_item, "_insert")
            if exists_item.type == "_delete":
                new_item = potential_new_item
        return exists_item, new_item

    def _remove_from_queue(self, left_node: ORMItem) -> None:
        if type(left_node) is not self.LinkedListItem:
            raise TypeError
        del self[left_node.index]


class SQLAlchemyQueryManager:
    MAX_RETRIES: Union[int, Literal["no-limit"]] = "no-limit"

    def __init__(self, connection_path: str, nodes: "ORMItemQueue", testing=False):
        def valid_node_type():
            if type(nodes) is not ORMItemQueue:
                raise ValueError
        if not isinstance(nodes, ORMItemQueue):
            raise TypeError
        if type(connection_path) is not str:
            raise TypeError
        valid_node_type()
        self.path = connection_path
        self._node_items = nodes
        self.remaining_nodes = ORMItemQueue()  # Отложенные для следующей попытки
        self._sorted: list[ORMItemQueue] = []  # [[save_point_group {pk: val,}], [save_point_group]...]
        self._query_objects: dict[Union[Insert, Update, Delete]] = {}  # {node_index: obj}
        self._testing = testing

    def start(self):
        self._sort_nodes()  # Упорядочить, разбить по savepoint
        self._manage_queries()  # Обратиться к left_node.make_query, - собрать объекты sql-иньекций
        self._open_connection_and_push()

    def _manage_queries(self):
        if self._query_objects:
            return self._query_objects
        for node_grop in self._sort_nodes():
            for left_node in node_grop:
                self._query_objects.update({left_node.index: left_node.make_query()})
        return self._query_objects

    def _open_connection_and_push(self):
        sorted_data = self._sort_nodes()
        if not sorted_data:
            return
        if not self._query_objects:
            return
        engine = create_engine(self.path)
        engine.execution_options(isolation_level="AUTOCOMMIT")
        factory_instance = session_factory()
        factory_instance.close_all()
        factory_instance.configure(bind=engine)
        session = factory_instance()
        while sorted_data:
            node_group = sorted_data.pop(-1)
            if not node_group:
                break
            multiple_items_in_transaction = True if len(node_group) > 1 else False
            has_error = False
            point = None
            counter = 0
            if multiple_items_in_transaction:
                point = session.begin_nested()
            for node in node_group:
                dml = self._query_objects.get(node.index)
                if not node.type == "_delete":
                    try:
                        session.add(dml)
                        print(f"session.add {repr(node)}")
                    except SQLAlchemyError as error:
                        self.remaining_nodes += node_group  # todo: O(n**2)!
                        has_error = True
                        print(error)
                    except PsycopgError as error:
                        self.remaining_nodes += node_group  # todo: O(n**2)!
                        print(error)
                        has_error = True
                    if multiple_items_in_transaction and counter < len(node_group) - 1:
                        session.flush()
                else:
                    try:
                        session.delete(dml)
                    except SQLAlchemyError as err:
                        self.remaining_nodes += node_group  # todo: O(n**2)!
                        has_error = True
                        print(err)
                    except PsycopgError as error:
                        self.remaining_nodes += node_group  # todo: O(n**2)!
                        print(error)
                        has_error = True
                counter += 1
            if has_error:
                if point:
                    point.rollback()
                    print("rollback")
            else:
                if not multiple_items_in_transaction:
                    point = session
                try:
                    print("COMMIT")
                    point.commit()
                except SQLAlchemyError as error:
                    print(error)
                    self.remaining_nodes += node_group
                except PsycopgError as error:
                    self.remaining_nodes += node_group  # todo: O(n**2)!
                    print(error)
        self._sorted = []
        self._query_objects = {}

    def _sort_nodes(self) -> list[ORMItemQueue]:
        """ Сортировать ноды по признаку внешних ключей, определить точки сохранения для транзакций """
        def make_sort_container(n: ORMItem, linked_nodes: ORMItemQueue, has_related_nodes):
            """
            Рекурсивно искать ноды с внешними ключами
            O(m) * (O(n) + O(j)) = O(n) * O(m) = O(n)
            """
            related_nodes = self._node_items.get_related_nodes(n)  # O(n)
            linked_nodes.add_to_head(**n.get_attributes())
            if not related_nodes:
                if has_related_nodes:
                    return linked_nodes
                return
            else:
                has_related_nodes = True
            for node in related_nodes:
                return make_sort_container(node, linked_nodes, has_related_nodes)
        if self._sorted:
            return self._sorted
        node_ = self._node_items.dequeue()
        other_single_nodes = ORMItemQueue()
        while node_:
            if self.MAX_RETRIES == "no-limit" or node_.retries < self.MAX_RETRIES:
                if node_.ready:
                    recursion_result = make_sort_container(node_, ORMItemQueue(), False)
                    if recursion_result is not None:
                        self._sorted.append(recursion_result)
                    else:
                        if node_ not in itertools.chain(*self._sorted):
                            other_single_nodes.append(**node_.get_attributes())
                else:
                    self.remaining_nodes.append(**node_.get_attributes())
            node_ = self._node_items.dequeue()
        self._sorted.append(other_single_nodes) if other_single_nodes else None
        return self._sorted


class SpecialOrmItem(ORMItem):
    def get(self, name, default_val=None):
        try:
            result = self.__getitem__(name)
        except KeyError:
            return default_val
        return result

    @property
    def hash_by_pk(self):
        str_ = "".join(map(lambda i: str(i), self.get_primary_key_and_value(as_tuple=True)))
        return int.from_bytes(hashlib.md5(str_.encode("utf-8")).digest(), "big")

    def _field_names_validation(self):
        column_names = set(self.model().column_names)
        loss_fields = super()._field_names_validation(from_polymorphizm=True)
        while loss_fields and column_names:
            field = loss_fields.pop()
            if f"{self.model.__name__}.{field}" not in column_names:
                if field not in column_names:
                    loss_fields.add(field)
            column_names.remove(field)
        if loss_fields:
            raise NodeColumnError


class SpecialOrmContainer(ORMItemQueue):
    """ Данный контейнер для использования в JoinSelectResult (результат вызова ORMHelper.join_select) """
    LinkedListItem = SpecialOrmItem

    def get(self, model_name, default=None):
        try:
            val = self.__getitem__(model_name)
        except KeyError:
            return default
        else:
            return val

    def is_containing_the_same_nodes(self, other_items: "SpecialOrmContainer"):
        if not isinstance(other_items, type(self)):
            raise TypeError
        return sum([n.hash_by_pk for n in self]) == sum(map(lambda i: i.hash_by_pk, other_items))

    def __getitem__(self, model_name: str):
        if not isinstance(model_name, str):
            raise TypeError
        for node in self:
            if node.model.__name__ == model_name:
                return node
        raise DoesNotExists


class ORMHelper(ORMAttributes):
    """
    Адаптер для ORMItemQueue
    Имеет таймер для единовременного высвобождения очереди объектов,
    при добавлении элемента в очередь таймер обнуляется.
    свойство items - ссылка на экземпляр ORMItemQueue.
    1) Инициализация
        LinkToObj = ORMHelper
    2) Установка ссылки на класс модели Flask-SqlAlchemy
        LinkToObj.set_model(CustomModel)
    3) Использование
        LinkToObj.set_item(name, data, **kwargs) - Установка в очередь, обнуление таймера
        LinkToObj.get_item(name, **kwargs) - получение данных из бд и из ноды
        LinkToObj.get_items(model=None) - получение данных из бд и из ноды
        LinkToObj.release() - высвобождение очереди с попыткой сохранить объекты в базе данных
        в случае неудачи нода переносится в конец очереди
        LinkToObj.remove_items - принудительное изъятие ноды из очереди.
    """
    MEMCACHED_PATH = "127.0.0.1:11211"
    DATABASE_PATH = DATABASE_PATH
    DATABASE_MOCK_PATH = DATABASE_PATH_FOR_TESTS
    TESTING = DEBUG  # Блокировка откравки в бд, блокировка dequeue с пролонгированием кеша очереди нод
    RELEASE_INTERVAL_SECONDS = 5.0
    RELEASE_INTERVAL_SECONDS_DEBUG = 0.5
    CACHE_LIFETIME_HOURS = 6 * 60 * 60
    JOIN_SELECT_DIFF_CACHE_MINUTES = 60 * 60
    _memcache_connection: Optional[Union[Client, MockMemcacheClient]] = None
    _database_session = None
    _timer: Optional[threading.Timer] = None
    _model_obj: Optional[Type[CustomModel]] = None  # Текущий класс модели, присваиваемый автоматически всем экземплярам при добавлении в очередь
    _was_initialized = False

    @classmethod
    def set_model(cls, obj):
        """
        :param obj: Кастомный класс модели Flask-SQLAlchemy из модуля models
        """
        cls.is_valid_model_instance(obj)
        cls._model_obj = obj
        cls._is_valid_config()
        return cls

    @classmethod
    @property
    def cache(cls):
        if cls._memcache_connection is None:
            if cls.TESTING:
                try:
                    cls._memcache_connection = MockMemcacheClient(cls.MEMCACHED_PATH, serde=DillSerde)
                except MemcacheError:
                    print("Ошибка инициализации тестового mermcache сервера")
                    raise MemcacheError
                return cls._memcache_connection
            try:
                cls._memcache_connection = Client(cls.MEMCACHED_PATH, serde=DillSerde)
            except MemcacheError:
                print("Нет соединения с сервисом кеширования!")
                raise MemcacheError
            else:
                print("Подключение к серверу memcached")
        return cls._memcache_connection

    @classmethod
    def drop_cache(cls):
        cls.cache.flush_all()

    @classmethod
    @property
    def database(cls) -> Session:
        if cls._database_session is None:
            try:
                engine = create_engine(cls.DATABASE_PATH if not cls.TESTING else cls.DATABASE_MOCK_PATH)
                session_f = session_factory(bind=engine)
                cls._database_session = session_f()
            except DisconnectionError:
                print("Ошибка соединения с базой данных!")
                raise DisconnectionError
            else:
                print("Подключение к базе данных")
        return cls._database_session

    @classmethod
    @property
    def items(cls) -> ORMItemQueue:
        """ Вернуть локальные элементы """
        return cls.cache.get("ORMItems", ORMItemQueue())

    @classmethod
    def init_timer(cls):
        timer = threading.Timer(cls.RELEASE_INTERVAL_SECONDS if not cls.TESTING else cls.RELEASE_INTERVAL_SECONDS_DEBUG, cls.release)
        timer.daemon = True
        timer.setName("ORMHelper(database push queue)")
        timer.start()
        return timer

    @classmethod
    def set_item(cls, _insert=False, _update=False,
                 _delete=False, _ready=False, _where=None, _model=None, **value):
        model = _model or cls._model_obj
        cls.is_valid_model_instance(model)
        items = cls.items
        items.enqueue(_model=model, _ready=_ready,
                      _insert=_insert, _update=_update,
                      _delete=_delete, _where=_where, _create_at=datetime.datetime.now(), _container=items,
                      **value)
        cls.__set_cache(items)
        cls._timer.cancel() if cls._timer else None
        cls._timer = cls.init_timer()

    @classmethod
    def get_item(cls, _model: Optional[Type[CustomModel]] = None, _only_db=False, _only_queue=False, **filter_) -> dict:
        """
        1) Получаем запись из таблицы в виде словаря
        2) Получаем данные из очереди в виде словаря
        3) db_data.update(quque_data)
        Если primary_field со значением left_node.name найден в БД, то нода удаляется
        """
        model = _model or cls._model_obj
        cls.is_valid_model_instance(model)
        if not filter_:
            return {}
        left_node: Optional[ORMItem] = None
        if _only_queue:
            nodes = cls.items.search_nodes(model, **filter_)
            if len(nodes):
                left_node = nodes[0]
            if left_node is None:
                return {}
            return left_node.value
        try:
            query = cls.database.query(model).filter_by(**filter_).first()
        except OperationalError:
            print("Ошибка соединения с базой данных! Смотри константу 'DATABASE_PATH' в модуле models.py, "
                  "такая проблема обычно возникает из-за авторизации. Смотри пароль!!!")
            raise OperationalError
        data_db = {} if not query else query.__dict__
        if _only_db:
            return data_db
        nodes = cls.items.search_nodes(model, **filter_)
        if len(nodes):
            left_node = nodes[0]
        if left_node is None:
            return data_db
        if left_node.type == "_delete":
            return {}
        updated_node_data = data_db
        updated_node_data.update(left_node.value)
        return updated_node_data

    @classmethod
    def get_items(cls, _model: Optional[Type[CustomModel]] = None, _db_only=False, _queue_only=False, **attrs) -> Iterator[dict]:  # todo: придумать пагинатор
        """
        1) Получаем запись из таблицы в виде словаря (CustomModel.query.all())
        2) Получаем данные из кеша, все элементы, у которых данная модель
        3) db_data.update(quque_data)
        """
        model = _model or cls._model_obj
        cls.is_valid_model_instance(model)
        if not attrs:
            try:
                items_db = cls.database.query(model).all()
            except OperationalError:
                print("Ошибка соединения с базой данных! Смотри константу 'DATABASE_PATH' в модуле models.py, "
                      "такая проблема обычно возникает из-за авторизации. Смотри пароль!!!")
                raise OperationalError
        else:
            try:
                items_db = cls.database.query(model).filter_by(**attrs).all()
            except OperationalError:
                print("Ошибка соединения с базой данных! Смотри константу 'DATABASE_PATH' в модуле models.py, "
                      "такая проблема обычно возникает из-за авторизации. Смотри пароль!!!")
                raise OperationalError
        if _db_only or not cls.items:
            return map(lambda t: t.__dict__, items_db)
        if _queue_only or not items_db:
            return map(lambda t: t.value,
                       tuple(filter(lambda x: not x.type == "_delete", cls.items.search_nodes(model, **attrs)))
                       )
        db_items = []
        queue_items = {}  # index: node_value
        nodes_implements_db = ORMItemQueue()  # Ноды, которые пересекаются с бд
        attrs = getattr(model(), "column_names", None)
        if not attrs:
            raise ModelsConfigurationError
        try:
            pk_name = [field_name for field_name, value in attrs.items() if "primary_key" in value and value["primary_key"]][0]
        except IndexError:
            raise ModelsConfigurationError
        for db_item in items_db:  # O(n)
            db_data: dict = db_item.__dict__
            if pk_name not in db_data:
                raise ORMExternalDataError
            left_node: ORMItem = cls.items.get_node(model, **{pk_name: db_data[pk_name]})
            if left_node:
                left_node.container = nodes_implements_db
                nodes_implements_db.enqueue(**left_node.get_attributes())
                if not left_node.type == "_delete":
                    db_data.update(left_node.value)
                    queue_items.update({left_node.index: db_data})
            else:
                db_items.append(db_data)
        for left_node in cls.items:  # O(k)
            if left_node not in nodes_implements_db:  # O(l)
                if left_node.model.__name__ == model.__name__:
                    if not left_node.type == "_delete":
                        val = left_node.value
                        queue_items.update({left_node.index: val}) if val else None
        # queue_items - нужен для сортировки
        # теперь все элементы отправим в output в следующей последовательности:
        # 1) ноды которые пересеклись со значениями из базы (сортировка по index)
        # 2) остальные ноды из очереди (сортировка по index)
        # 3) значения из базы
        sorted_nodes = dict(sorted(queue_items.items(), reverse=True))
        output = []
        for item in sorted_nodes.values():
            output.append(item)
        for item in db_items:
            output.append(item)
        return iter(output)

    @classmethod
    def join_select(cls, *models: Iterable[CustomModel], on: Optional[dict] = None,
                    _where: Optional[dict] = None, _db_only=False, _queue_only=False) -> "JoinSelectResult":
        """
        join_select(model_a, model,b, on={model_b: 'model_a.column_name'})

        :param _where: modelName: {column_name: some_val}
        :param on: modelName.column1: modelName2.column2
        :param _db_only: извлечь только sql inner join
        :param _queue_only: извлечь только из queue
        :return: специльный итерируемый объект класса JoinSelectResult, который содержит смешанные данные из локального
        хранилища и БД
        """
        def valid_params():
            nonlocal _where, models
            models = list(models)
            _where = _where or {}
            [cls.is_valid_model_instance(m) for m in models]
            if not models:
                raise ValueError
            if on is None:
                raise ValueError("Необходим аргумент on={model_b.column_name: 'model_a.column_name'}")
            if type(on) is not dict:
                raise TypeError
            if _where:
                if type(_where) is not dict:
                    raise TypeError
                for v in _where.values():
                    if not isinstance(v, dict):
                        raise TypeError
                    for key, value in v.items():
                        if type(key) is not str:
                            raise TypeError("Наименование столбца может быть только строкой")
                        if not isinstance(value, (str, int,)):
                            raise TypeError
            if len(on.keys()) + len(on.values()) != len(models):
                raise ValueError(
                    "Правильный способ работы с данным методом: join_select(model_a, model,b, on={model_b.column_name: 'model_a.column_name'})"
                )
            for left_table_dot_field, right_table_dot_field in on.items():
                if not type(left_table_dot_field) is str or not isinstance(right_table_dot_field, str):
                    raise TypeError("...on={model_b.column_name: 'model_a.column_name'}")
                if not all(itertools.chain(*[[len(x) for x in i.split(".")] for t in on.items() for i in t])):
                    raise AttributeError("...on={model_b.column_name: 'model_a.column_name'}")
                left_model = left_table_dot_field.split(".")[0]
                right_model = right_table_dot_field.split(".")[0]
                if len(left_table_dot_field.split(".")) != 2 or len(right_table_dot_field.split(".")) != 2:
                    raise AttributeError("...on={model_b.column_name: 'model_a.column_name'}")
                if left_model not in {m.__name__: m for m in models}:
                    raise ValueError(f"Класс модели {left_model} не найден")
                if right_model not in {m.__name__: m for m in models}:
                    raise ValueError(f"Класс модели {right_model} не найден")
                left_model_field = left_table_dot_field.split(".")[1]
                right_model_field = right_table_dot_field.split(".")[1]
                if not getattr({m.__name__: m for m in models}[left_model], left_model_field, None):
                    raise AttributeError(f"Столбец {left_model_field} у таблицы {left_model} не найден")
                if not getattr({m.__name__: m for m in models}[right_model], right_model_field, None):
                    raise AttributeError(f"Столбец {right_model_field} у таблицы {right_model} не найден")
        valid_params()

        def collect_db_data(self):
            def create_request() -> str:  # O(n) * O(m)
                s = f"orm_helper.database.query({', '.join(map(lambda x: x.__name__, models))}).filter("  # O(l) * O(1)
                for left_table_dot_field, right_table_dot_field in on.items():  # O(n)
                    left_table, left_table_field = left_table_dot_field.split(".")  # O(m)
                    s += f"{left_table}.{left_table_field} == {right_table_dot_field})"
                if _where:
                    on_keys_counter = 0
                    s += f".filter("
                    for table_name, column_and_value in _where.items():
                        for left_table_and_column, right_table_and_column in column_and_value.items():  # O(t)
                            s += f"{table_name}.{left_table_and_column} == '{right_table_and_column}'"
                            if on_keys_counter < len(_where) - 1:  # O(1)
                                s += ", "
                            on_keys_counter += 1
                        s += ")" if on_keys_counter == _where.__len__() else ""
                return s

            def add_items_to_orm_queue() -> Iterator[SpecialOrmContainer]:  # O(i) * O(k) * O(m) * O(n) * O(j) * O(l)
                data = query.all()
                for data_row in data:  # O(i)
                    row = SpecialOrmContainer()  # todo: что будет, если в 2 таблицах есть одноимённые столбцы-primary_key?! testcase
                    for join_select_result in data_row:
                        all_column_names = getattr(type(join_select_result), "column_names")
                        r = {col_name: col_val for col_name, col_val in join_select_result.__dict__.items()
                             if col_name in all_column_names}  # O(n) * O(j)
                        row.append(_model=join_select_result.__class__, _insert=True, _container=row, **r)  # O(l)
                    yield row
            sql_text = create_request()
            query: Query = eval(sql_text, {"orm_helper": cls}, ChainMap(*list(map(lambda x: {x.__name__: x}, models)), {"select": select}))
            return add_items_to_orm_queue()

        def collect_local_data(self) -> Iterator[SpecialOrmContainer]:
            def collect_all():  # n**2!
                nonlocal heap
                for model in models:  # O(n)
                    heap += cls.items.search_nodes(model, **_where.get(model.__name__, {}))  # O(n * k)

            def collect_node_values(on_keys_or_values: Union[dict.keys, dict.values]):  # f(n) = O(n) * (O(k) * O(u) * (O(l) * O(m)) * O(y)); g(n) = O(n * k)
                for node in heap:  # O(n)
                    for table_and_column in on_keys_or_values:  # O(k)
                        table, table_column = table_and_column.split(".")  # O(u)
                        if table == node.model.__name__:  # O(l) * O(m)
                            if table_column in node.value:  # O(y)
                                yield {node.model.__name__: node}

            def compare_by_matched_fk() -> Iterator:  # g(n) = O(n * k)
                # f(n) = O(u) + O(2u) + O(n) * (O(j) * O(k) * (O(l) * O(1) * O(b) * (O(a) + O(a) + O(c * v) + O(c1 * v1) + O(m1 * m2) + O(1) + O(1))))
                # f(n) = O(u) + O(2u) + O(n) * (O(j) * O(k) * (O(l) * O(1) * O(b) * O(m * v)))
                # f(n) = O(u) + O(2u) + O(n) * (O(j) * O(k) * O(l * v))
                # f(n) = O(u) + O(2u) + O(n) * O(j * k)
                # f(n) = O(3u) + O(n) * O(j * k)
                # f(n) = O(3u) + O(n * k)
                # g(n) = O(n * k)
                model_left_primary_key_and_value = collect_node_values(on.keys())  # O(u)
                model_right_primary_key_and_value = tuple(collect_node_values(on.values()))  # O(2u)
                for left_data in model_left_primary_key_and_value:  # O(n)
                    left_model_name, left_node = itertools.chain.from_iterable(left_data.items())  # O(j)
                    for right_data in model_right_primary_key_and_value:  # O(k)
                        right_model_name, right_node = itertools.chain.from_iterable(right_data.items())  # O(l)
                        raw = SpecialOrmContainer()  # O(1)
                        for left_table_dot_field, right_table_dot_field in on.items():  # O(b)
                            left_table_name_in_on, left_table_field_in_on = left_table_dot_field.split(".")  # O(a)
                            right_table_name_in_on, right_table_field_in_on = right_table_dot_field.split(".")  # O(a)
                            if left_model_name == left_table_name_in_on and right_model_name == right_table_name_in_on:  # O(c * v) + O(c1 * v1)
                                if left_node.value.get(left_table_field_in_on, None) == \
                                        right_node.value.get(right_table_field_in_on, None):  # O(1) + O(m1) * O(1) + O(m2) = O(m1 * m2)
                                    raw.enqueue(**left_node.get_attributes())  # todo fixit O(n ** 2)
                                    raw.enqueue(**right_node.get_attributes())  # todo fixit O(n ** 2)
                        if raw:
                            yield raw
            heap = ORMItemQueue()
            collect_all()
            return compare_by_matched_fk()
        JoinSelectResult.get_nodes_from_database = collect_db_data
        JoinSelectResult.get_local_nodes = collect_local_data
        return JoinSelectResult(only_database=_db_only, only_local=_queue_only)

    @classmethod
    def get_node_dml_type(cls, node_pk_value: Union[str, int], model=None) -> Optional[str]:
        """ Получить тип операции с базой, например '_update', по названию ноды, если она найдена, иначе - None
        :arg node_pk_value: значение поля первичного ключа
        :arg model: кастомный объект, смотри модуль database/models
        """
        model = model or cls._model_obj
        cls.is_valid_model_instance(model)
        if not isinstance(node_pk_value, (str, int,)):
            raise TypeError
        primary_key_field_name = getattr(model, "__db_queue_primary_field_name__")
        left_node = cls.items.get_node(model, **{primary_key_field_name: node_pk_value})
        return left_node.type if left_node is not None else None

    @classmethod
    def remove_items(cls, node_or_nodes: Union[Union[int, str], Iterable[Union[str, int]]], model=None):
        """
        Удалить ноду из очереди на сохранение
        :arg node_or_nodes: значение для поля первичного ключа, одно или несколько
        :arg model: кастомный объект, смотри модуль database/models
        """
        model = model or cls._model_obj
        cls.is_valid_model_instance(model)
        if not isinstance(node_or_nodes, (tuple, list, set, frozenset, str, int,)):
            raise TypeError
        primary_key_field_name = getattr(model, "__db_queue_primary_field_name__")
        items = cls.items
        if isinstance(node_or_nodes, (str, int,)):
            items.remove(model, **{primary_key_field_name: node_or_nodes})
        if isinstance(node_or_nodes, (tuple, list, set, frozenset)):
            for pk_field_value in node_or_nodes:
                if not isinstance(pk_field_value, (int, str,)):
                    raise TypeError
                items.remove(model, **{primary_key_field_name: pk_field_value})
        cls.__set_cache(items)

    @classmethod
    def remove_field_from_node(cls, pk_field_value, field_or_fields: Union[Iterable[str], str], _model=None):
        """
        Удалить поле или поля из ноды, которая в очереди
        :param pk_field_value: значения поля первичного ключа (по нему ищется нода)
        :param field_or_fields: изымаемые поля
        :param _model: кастомная модель SQLAlchemy
        """
        model = _model or cls._model_obj
        cls.is_valid_model_instance(model)
        if not isinstance(field_or_fields, (tuple, list, set, frozenset, str,)):
            raise TypeError
        primary_key_field_name = [attr_val for attr_name, attr_val in model().column_names
                                  if attr_name == "primary_key"][0]
        old_node = cls.items.get_node(model, **{primary_key_field_name: pk_field_value})
        if not old_node:
            return
        node_data = old_node.get_attributes()
        if isinstance(field_or_fields, (list, tuple, set, frozenset)):
            if set.intersection(set(field_or_fields), set(RESERVED_WORDS)):
                raise NodeAttributeError
            if primary_key_field_name in field_or_fields:
                raise NodePrimaryKeyError("Нельзя удалить поле, которое является первичным ключом")
            for field in field_or_fields:
                if field in node_data:
                    del node_data[field]
        if type(field_or_fields) is str:
            if field_or_fields in RESERVED_WORDS:
                raise NodeAttributeError
            if primary_key_field_name == field_or_fields:
                raise NodePrimaryKeyError("Нельзя удалить поле, которое является первичным ключом")
            if field_or_fields in node_data:
                del node_data[field_or_fields]
        container = cls.items
        container.enqueue(**node_data)
        cls.__set_cache(container)

    @classmethod
    def is_node_from_cache(cls, model=None, **attrs) -> bool:
        model = model or cls._model_obj
        cls.is_valid_model_instance(model)
        items = cls.items.search_nodes(model, **attrs)
        if len(items) > 1:
            warnings.warn(f"В очреди больше одной ноды/нод, - {len(items)}: {items}")
        if len(items):
            return True
        return False

    @classmethod
    def release(cls) -> None:
        """
        Этот метод стремится высвободить очередь сохраняемых объектов,
        путём итерации по ним, и попыткой сохранить в базу данных.
        :return: None
        """
        database_adapter = SQLAlchemyQueryManager(DATABASE_PATH, cls.items, testing=cls.TESTING)
        database_adapter.start()
        cls.__set_cache(database_adapter.remaining_nodes or None)
        cls._timer = cls.init_timer() if database_adapter.remaining_nodes else None
        sys.exit()

    @classmethod
    def __getattribute__(cls, item):
        if not cls._was_initialized:
            if not item == "set_model":
                raise ORMInitializationError("Сначала нужно установить модель Flask-SQLAlchemy, используя метод set_model")
        super().__getattribute__(item)

    @classmethod
    def _is_valid_config(cls):
        if type(cls.TESTING) is not bool:
            raise TypeError
        if type(cls.CACHE_LIFETIME_HOURS) is not int and type(cls.CACHE_LIFETIME_HOURS) is not bool:
            raise TypeError
        if not isinstance(cls.RELEASE_INTERVAL_SECONDS, (int, float,)):
            raise TypeError
        if cls.CACHE_LIFETIME_HOURS <= cls.RELEASE_INTERVAL_SECONDS:
            raise ORMInitializationError("Срок жизни кеша, который хранит очередь сохраняемых объектов не может быть меньше, "
                                         "чем интервал отправки объектов в базу данных.")
        cls._was_initialized = True
        #  cls.drop_cache()

    @classmethod
    def __set_cache(cls, nodes):
        cls.cache.set("ORMItems", nodes, cls.CACHE_LIFETIME_HOURS)


class JoinSelectResult:
    """
    Экземпляр этого класса возвращается функцией ORMHelper.join_select()
    1 экземпляр этого класса 1 результат вызова ORMHelper.join_select()
    Использовать следующим образом:
        Делаем join_select
        Резулбтаты можем вывести в какой-нибудь Q...Widget, этот результат (строки) можно привязать к содержимому,
        чтобы вносить правки со сторы UI, ни о чём лишнем не думая
        JoinSelectResultInstance.pointer = ['Некое значение из виджета1', 'Некое значение из виджета2',...]
        Теперь нужный инстанс SpecialOrmContainer можно найти:
        JoinSelectResultInstance.pointer['Некое значение из виджета1'] -> SpecialOrmContainer(node_model_a, node_model_b, node_model_c)
        Если нода потеряла актуальность(удалена), то вместо неё будет заглушка - Экземпляр EmptyORMItem
        SpecialOrmContainer имеет свойство - is_actual на которое можно опираться
    """
    class Pointer:
        """ Экземпляр данного объекта - оболочка для содержимого, обеспечивающая доступ к данным.
        Объект этого класса создан для 'слежки' за изменениями с UI."""
        wrap_items: Optional[list[str]] = None

        def __init__(self, joined_item: "JoinSelectResult"):
            self._blocked = False  # Если длина wrap_items и итератора joined_item начали отличаться - бракуем этот экземпляр
            self._joined_item = joined_item
            self._previous_hash = self._joined_item.previous_hash
            self._joined_item_data = self._joined_item.__iter__()
            self._is_valid()
            self.wrap_items = copy.copy(self.wrap_items)  # Для защиты cls.wrap_items от дурака на стороне UI

        @property
        def items(self) -> dict[str, int]:
            return dict(zip(self.wrap_items, self._joined_item_data))

        def has_changes(self, name: str = None) -> bool:
            if self._blocked:
                return True
            hash_names_map = {
                name: self._previous_hash[index] for index, name in enumerate(self.wrap_items)
            }
            if type(name) is not str:
                raise TypeError
            hash_ = hash_names_map[name]
            status = self._joined_item.has_changes(hash_, strict_mode=False)
            return status

        def __getitem__(self, item: str):
            return self.items[item]

        def __str__(self):
            return "".join(map(lambda x: f"{x[0]}:{x[1]} /n", zip(self.wrap_items, copy.copy(self._joined_item))))

        def _is_valid(self):
            data = tuple(copy.copy(self._joined_item_data))
            """ Если длины 2 последовательностей (см init) отличаются, то вызвать исключение """
            if type(self._joined_item) is not JoinSelectResult:
                raise JoinedItemPointerError(
                    "Экземпляр класса JoinedItemResult не установлен в атрибут класса joined_item"
                )
            if type(self.wrap_items) is not list and type(self.wrap_items) is not tuple:
                raise TypeError
            if not all(map(lambda x: isinstance(x, str), self.wrap_items)):
                raise TypeError
            if not isinstance(data, (list, tuple,)):
                raise TypeError
            if len(self.wrap_items) != len(data):
                self._blocked = True
                raise warnings.warn("Появились новые записи")
            if data:
                if not all(map(lambda x: isinstance(x, (ORMItemQueue, SpecialOrmContainer,)), data)):
                    raise TypeError
    get_local_nodes: Optional[Callable] = None
    get_nodes_from_database: Optional[Callable] = None

    def __init__(self, only_local=False, only_database=False):
        if not callable(self.get_nodes_from_database) or not callable(self.get_local_nodes):
            raise TypeError
        if type(only_local) is not bool:
            raise TypeError
        if not isinstance(only_database, bool):
            raise TypeError
        if only_database and only_local:
            raise ValueError
        self._only_queue = only_local
        self._only_db = only_database
        self._pointer = None

    def has_changes(self, hash_=None, strict_mode=True) -> bool:
        current_hash = self.previous_hash
        self.__iter__()
        new_hash = self.previous_hash
        if hash_:
            if hash_ not in current_hash:
                if strict_mode:
                    raise ValueError
                return True
            if hash_ in new_hash:
                return False
            return True
        return not current_hash == new_hash

    @property
    def pointer(self) -> Pointer:
        return self._pointer(self)

    @pointer.setter
    def pointer(self, items: list):
        self._pointer = self.Pointer
        self._pointer.wrap_items = items

    @property
    def previous_hash(self) -> Optional[tuple[int]]:
        return ORMHelper.cache.get("join_select_hash")

    @property
    def items(self) -> list[ChainMap]:
        items = tuple(self)
        result = []
        if self.__get_merged_column_names(items):
            items = self.__set_prefix_to_column_name(items)
        for group in items:
            result.append(ChainMap(*[values for values in group]))
        return result

    def __iter__(self):
        return iter(self._merge())

    def __len__(self):
        return sum([1 for _ in self])

    def __getitem__(self, item: int) -> SpecialOrmContainer:
        if not isinstance(item, int):
            raise TypeError
        if item not in self:
            raise DoesNotExists
        for group in self:
            if hash(group) == item:
                return group

    def __contains__(self, item: int):
        if type(item) is not int:
            return False
        return item in map(lambda x: hash(x), self)

    def _merge(self) -> list[SpecialOrmContainer]:
        result = []
        db_items = list(self.get_nodes_from_database()) if not self._only_queue else []
        local_items = list(self.get_local_nodes()) if not self._only_db else []
        for db_group_index, db_nodes_group in enumerate(db_items):
            for local_nodes_group_index, local_nodes_group in enumerate(local_items):
                if db_nodes_group.is_containing_the_same_nodes(local_nodes_group):
                    db_nodes_group += local_nodes_group
                    result.append(db_nodes_group)
                    del db_items[db_group_index]
                    del local_items[local_nodes_group_index]
        if db_items:
            while db_items:
                result.append(db_items.pop(0))
        if local_items:
            while local_items:
                result.append(local_items.pop(0))
        self.__set_previous_hash(tuple([hash(group) for group in result]))
        return result

    @staticmethod
    def __set_previous_hash(values: tuple[int]):
        if type(values) is not tuple:
            raise TypeError
        if not all(map(lambda b: type(b) is int, values)):
            raise TypeError
        ORMHelper.cache.set("join_select_hash", values, ORMHelper.JOIN_SELECT_DIFF_CACHE_MINUTES)

    @staticmethod
    def __get_merged_column_names(result: tuple[SpecialOrmContainer]) -> set[str]:
        """ Наименования столбцов, которые присутствуют в более чем 1 таблице результата join_select """
        if not result:
            return set()
        return set.intersection(*[set(n.value) for group in result for n in group])

    def __set_prefix_to_column_name(self, items: tuple[SpecialOrmContainer]) -> Iterator[list[dict]]:
        """ Добавить префикс вида - ModelName.column_name ко всем столбцам,
        чьи имена дублируются в нодах от нескольких моделей """
        merged_columns = list(self.__get_merged_column_names(items))
        while merged_columns:
            column_name = merged_columns.pop()
            for container in items:
                list_ = []
                for node in container:
                    if column_name in node.value:
                        values: dict = node.value
                        pk_value = values[column_name]
                        del values[column_name]
                        values.update({f"{node.model.__name__}.{column_name}": pk_value})
                        list_.append(values)
                    else:
                        list_.append(node.value)
                yield list_


if __name__ == "__main__":
    from database.models import Machine, Cnc

    container = ORMItemQueue()
    container.enqueue(_model=Cnc, name="test", _delete=True, _container=container)
    container.enqueue(_model=Machine, machine_name="Heller", _insert=True, _container=container)
    container.enqueue(_model=Cnc, name="Testname", _container=container, _update=True)
    print(container)
