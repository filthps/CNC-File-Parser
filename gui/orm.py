import sys
import copy
import threading
import traceback
from typing import Union, Iterator, Iterable, Optional, Callable
from pymemcache.client.base import Client
from pymemcache.exceptions import MemcacheError
from pymemcache_dill_serde import DillSerde
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import update, insert, delete, create_engine, text
from sqlalchemy.sql.dml import Insert, Update, Delete
from sqlalchemy.orm import Query, sessionmaker as session_factory
from sqlalchemy.exc import IntegrityError, DisconnectionError
from gui.datatype import LinkedList, LinkedListItem
from database.models import CustomModel, DATABASE_PATH


class ORMAttributes:
    @staticmethod
    def is_valid_model_instance(item: CustomModel):
        if not hasattr(item, "__db_queue_primary_field_name__") or \
                not any([hasattr(i, "__remove_pk__") for i in item.mro()]):
            raise TypeError("Значение атрибута model - неподходящего типа."
                            "Используйте только кастомный класс - 'CustomModel', смотри models.")


class ORMItem(LinkedListItem, ORMAttributes):
    """ Иммутабельный класс ноды для ORMItemContainer. """
    def __init__(self, **kw):
        """
            :arg _model: Расширенный клас model SQLAlchemy
            :arg _insert: Опицонально bool
            :arg _update: Опицонально bool
            :arg _delete: Опицонально bool
            :arg _ready: Если __delete=True - Необязательный
            :arg _where: Опицонально dict
            :arg _callback: Опционально Callable
            Все остальные параметры являются парами 'поле-значение'
            """
        super().__init__()
        self._is_valid_dml_type(kw)
        self.__model = kw.pop("_model")
        self.is_valid_model_instance(self.__model)
        self.__callback: Optional[Callable] = kw.pop("_callback", None)
        self.__insert = kw.pop("_insert", False)
        self.__update = kw.pop("_update", False)
        self.__delete = kw.pop("_delete", False)
        self.__is_ready = kw.pop("_ready", True if self.__delete else False)
        self.__where = kw.pop("_where", None)
        self.__value = {}  # Содержимое - пары ключ-значение: поле таблицы бд: значение
        self.__transaction_counter = kw.pop('_count_retries', 0)  # Инкрементируется при вызове self.make_query()
        # Подразумевая тем самым, что это попытка сделать транзакцию в базу
        if not kw:
            raise ValueError("Нет полей, нода пуста")
        self.__value.update(kw)
        self._foreign_key_fields = tuple(self.__model.__table__.foreign_keys)
        _ = self.get_primary_key_and_value()  # test

    @property
    def value(self) -> dict:
        return self.__value.copy() if self.__value else {}

    @property
    def model(self):
        return self.__model

    @property
    def retries(self):
        return self.__transaction_counter

    @property
    def foreign_key_fields(self):
        return self._foreign_key_fields

    def get_primary_key_and_value(self, as_tuple=False, only_key=False, only_value=False) -> Union[dict, tuple, int, str]:
        key = getattr(self.__model(), "__db_queue_primary_field_name__")
        if only_key:
            return key
        try:
            value = self.__value[key]
        except KeyError:
            raise ValueError("Любая нода, будь то insert, update или delete,"
                  "должна иметь в значении поле первичного ключа со значением!")
        if only_value:
            return value
        return {key: value} if not as_tuple else (key, value,)

    @property
    def ready(self) -> bool:
        return self.__is_ready

    @property
    def where(self) -> dict:
        return self.__where.copy() if self.__where else {}

    @property
    def callback(self):
        return self.__callback

    @ready.setter
    def ready(self, status: bool):
        if not isinstance(status, bool):
            raise TypeError("Статус готовности - это тип данных boolean")
        self.__is_ready = status

    @property
    def type(self) -> str:
        return "_insert" if self.__insert else "_update" if self.__update else "_delete"

    def get_attributes(self) -> dict:
        result = {}
        result.update(self.value)
        if self.__update or self.__delete:
            if self.__where:
                result.update({"_where": self.where})
        result.update({"_model": self.__model, "_insert": False,
                       "_update": False, "_ready": self.__is_ready,
                       "_delete": False, "_callback": self.__callback, "_count_retries": self.retries})
        result.update({self.type: True})
        return result

    def make_query(self) -> Optional[Query]:
        if self.__transaction_counter % 2:
            self.__insert, self.__update = self.__update, self.__insert
        query = None
        value: dict = self.value
        primary_key = self.get_primary_key_and_value(only_key=True)
        if self.__insert:
            if self.__model().__remove_pk__:
                del value[primary_key]
            query = self.model(**value)
        if self.__update or self.__delete:
            where = self.__where
            if not where:
                where = self.get_primary_key_and_value()
            del value[primary_key]
            query = self.model.query.filter_by(**where).first()
            if query is None:
                if self.__delete:
                    return
                query = self.model(**self.value)
        if self.__update:
            if primary_key in value:
                del value[primary_key]
            [setattr(query, key, value) for key, value in value.items()]
        self.__transaction_counter += 1
        return query

    def __len__(self):
        return len(self.__value)

    def __eq__(self, other: "ORMItem"):
        if type(other) is not type(self):
            return False
        if not self.model.__name__ == other.model.__name__:
            return False
        if not self.get_primary_key_and_value() == other.get_primary_key_and_value():
            return False
        return True

    def __bool__(self):
        return bool(len(self))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.get_attributes()})"

    def __str__(self):
        return str(self.value)

    @staticmethod
    def _is_valid_dml_type(data: dict):
        """ Только одино свойство, обозначающее тип sql-dml операции, может быть True """
        is_insert = data.get("_insert", False)
        is_update = data.get("_update", False)
        is_delete = data.get("_delete", False)
        if not isinstance(is_insert, bool) or not isinstance(is_update, bool) or not isinstance(is_delete, bool):
            raise TypeError
        if sum((is_insert, is_update, is_delete,)) != 1:
            raise ValueError("Неверно установлен SQL-DML")


class EmptyOrmItem:
    """
    Пустой класс для возврата пустой "ноды". Заглушка
    """
    def __init__(self):
        pass

    def __eq__(self, other):
        return False

    def __len__(self):
        return 0

    def __bool__(self):
        return False

    def __repr__(self):
        return f"{type(self)}()"

    def __str__(self):
        return "None"


class ORMItemContainer(LinkedList):
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

        def check_foreign_key_nodes() -> ORMItemContainer:  # O(n) * (O(k) + O(i) + O(i)) -> O(n) * O(j) -> O(n)
            """
            Найти ноды, которые зависят от ноды, которая в настоящий момент добавляется:
            Если такие ноды найдутся, то они будут удалены и добавлены в очередь снова
            (перемена мест)
            """
            nodes_to_move_in_end_queue = self.__class__()
            new_item_primary_key_name = new_item.get_primary_key_and_value(only_key=True)
            for node in self:  # O(n)
                if new_item_primary_key_name in node.foreign_key_fields:  # O(k)
                    nodes_to_move_in_end_queue.enqueue(**node.get_attributes())  # O(i)
            new_container = self
            if nodes_to_move_in_end_queue:
                new_container = self + nodes_to_move_in_end_queue  # O(i)
            return new_container
        self.__remove_from_queue(exists_item) if exists_item else None
        super().append(**new_item.get_attributes())
        new_nodes = check_foreign_key_nodes()
        self._replace_inner(new_nodes._head, new_nodes._tail)

    def dequeue(self) -> Optional[ORMItem]:
        """ Извлечение ноды с начала очереди """
        node = self._head
        if node is None:
            return
        self.__remove_from_queue(node)
        return node

    def remove(self, model, pk_field_name, pk_field_value):
        node = self.get_node(model, **{pk_field_name: pk_field_value})
        if node:
            self.__remove_from_queue(node)
            return node

    def get_related_nodes(self, node: ORMItem) -> "ORMItemContainer":
        """ Получить все связанные (внешним ключом) с передаваемой нодой ноды.
        O(i) * O(1) + O(n) = O(n)"""
        container = self.__class__()
        foreign_key_values = []
        for fk_field in node.foreign_key_fields:  # O(i)
            foreign_key_values.append(node.value[fk_field]) if fk_field in node.value else None  # O(1)
        for node_item in self:  # O(n) * O(j) * O(m) * O(n) * O(1) = O(n)
            if not node_item == node:  # O(g) * O(j) = O (j)
                pk_field, pk_value = node_item.get_primary_key_and_value()
                if pk_field in foreign_key_values:  # O(l)
                    if pk_value == node.value[pk_field]:  # O(l) * O(m) * O(1) = O(l * m) = O(m)
                        container.append(**node_item.get_attributes())  # O(1)
        return container

    def search_nodes(self, model: CustomModel, negative_selection=False, **_filter) -> "ORMItemContainer":
        """
        Искать ноды по совпадениям любых полей
        :arg model: кастомный объект, смотри модуль database/models
        :arg _filter: словарь содержащий набор полей и их значений для поиска
        :arg negative_selection: режим отбора нод
        """
        ORMItem.is_valid_model_instance(model)
        items = self.__class__()
        nodes = iter(self)
        while nodes:  # O(n) * O(u * k) * O(i-->n) = От Ω(n) - θ(n * i) до O(n**2)
            try:
                node: ORMItem = next(nodes)
            except StopIteration:
                return items
            if node.model.__name__ == model.__name__:  # O(u * k)
                if not _filter and not negative_selection:
                    items.append(**node.get_attributes())
                for field_name, value in _filter.items():
                    if field_name in node.value:
                        if node.value[field_name] == value:
                            items.append(**node.get_attributes())
                        else:
                            items.remove(node.model, *node.get_primary_key_and_value(as_tuple=True))
        return items

    def get_node(self, model: CustomModel, **primary_key_data) -> Optional[ORMItem]:
        """
        Данный метод используется при инициализации - _replication
        :arg model: объект модели
        :arg primary_key_data: словарь вида - {имя_первичного_ключа: значение}
        """
        ORMItem.is_valid_model_instance(model)
        if len(primary_key_data) != 1:
            raise ValueError("Параметр primary_key_data содержит название поля, которое является первичным ключом модели"
                             "и значение для этого поля")
        nodes = iter(self)
        while nodes:  # O(n) * O(u)
            try:
                node: Optional[ORMItem] = next(nodes)
            except StopIteration:
                break
            if node.model.__name__ == model.__name__:
                if node.get_primary_key_and_value() == primary_key_data:
                    return node

    def __repr__(self):
        return f"{self.__class__}({tuple(str(i) for i in self)})"

    def __str__(self):
        return str(tuple(repr(i) for i in self))

    def __contains__(self, item: ORMItem) -> bool:
        if type(item) is not ORMItem:
            return False
        node = self.get_node(item.model, **item.get_primary_key_and_value())
        return bool(node)

    def __add__(self, other: "ORMItemContainer"):
        if not type(other) is self.__class__:
            raise TypeError
        result_instance = self.__class__()
        [result_instance.append(**n.get_attributes()) for n in self]  # O(n)
        [result_instance.enqueue(**n.get_attributes()) for n in other]  # O(n**2) todo n**2!
        return result_instance

    def __iadd__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError
        result = self + other
        return result

    def __sub__(self, other: "ORMItemContainer"):
        if not isinstance(other, self.__class__):
            raise TypeError
        result_instance = copy.copy(self)
        [result_instance.__remove_from_queue(n) for n in other]
        return result_instance

    def _replication(self, **new_node_complete_data: dict) -> tuple[Optional[ORMItem], ORMItem]:  # O(l * k) + O(n) + O(1) = O(n)
        """
        Создавать ноды для добавления можно только здесь! Логика для постаовки в очередь здесь.
        """
        potential_new_item = self.LinkedListItem(**new_node_complete_data)  # O(1)
        new_item = None

        def create_merged_values_node(old_node: ORMItem, new_node: ORMItem, dml_type: str) -> ORMItem:
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
        exists_item = self.get_node(potential_new_item.model, **potential_new_item.get_primary_key_and_value())  # O(n)
        if not exists_item:
            new_item = potential_new_item
            return None, new_item
        new_item_is_update = new_node_complete_data.get("_update", False)
        new_item_is_delete = new_node_complete_data.get("_delete", False)
        new_item_is_insert = new_node_complete_data.get("_insert", False)
        if new_item_is_update:
            if exists_item.type == "_insert" or exists_item.type == "_update":
                if exists_item.type == "_insert":
                    new_item = create_merged_values_node(exists_item, potential_new_item, "_insert")
                if exists_item.type == "_update":
                    new_item = create_merged_values_node(exists_item, potential_new_item, "_update")
            if exists_item.type == "_delete":
                new_item = potential_new_item
        if new_item_is_delete:
            new_item = potential_new_item
        if new_item_is_insert:
            if exists_item.type == "_insert" or exists_item.type == "_update":
                new_item = create_merged_values_node(exists_item, potential_new_item, "_insert")
            if exists_item.type == "_delete":
                new_item = potential_new_item
        return exists_item, new_item

    def __remove_from_queue(self, node: ORMItem) -> None:
        if type(node) is not self.LinkedListItem:
            raise TypeError
        del self[node.index]


class SQLAlchemyQueryManager:
    MAX_RETRIES = 4
    
    def __init__(self, connection_path: str, nodes: "ORMItemContainer"):
        if not isinstance(nodes, ORMItemContainer):
            raise TypeError
        if type(connection_path) is not str:
            raise TypeError
        self.path = connection_path
        self._node_items = nodes
        self.remaining_nodes = ORMItemContainer()  # Отложенные для следующей попытки
        self._sorted: list[ORMItemContainer] = []  # [[save_point_group {pk: val,}], [save_point_group]...]
        self._query_objects: dict[Union[Insert, Update, Delete]] = {}  # {node_index: obj}
        
    def start(self):
        self._sort_nodes()  # Упорядочить, разбить по savepoint
        self._manage_queries()  # Обратиться к node.make_query, - собрать объекты sql-иньекций
        self._open_connection_and_push()
        
    def _manage_queries(self):
        if self._query_objects:
            return self._query_objects
        for node_grop in self._sort_nodes():
            for node in node_grop:
                self._query_objects.update({node.index: node.make_query()})
        return self._query_objects

    def _open_connection_and_push(self):
        sorted_data = self._sort_nodes()
        if not sorted_data:
            return
        if not self._query_objects:
            return
        engine = create_engine(self.path)
        engine.execution_options(isolation_level="SERIALIZABLE")
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
            if multiple_items_in_transaction:
                point = session.begin_nested()
            for node in node_group:
                dml = self._query_objects.get(node.index)
                if not node.type == "_delete":
                    try:
                        session.add(dml)
                    except IntegrityError:
                        self.remaining_nodes += node_group  # todo: O(n**2)!
                        has_error = True
                else:
                    try:
                        session.delete(dml)
                    except IntegrityError:
                        self.remaining_nodes += node_group  # todo: O(n**2)!
                        has_error = True
            if has_error:
                if point:
                    point.rollback()
            else:
                if not multiple_items_in_transaction:
                    point = session
                try:
                    point.commit()
                except IntegrityError:
                    self.remaining_nodes += node_group
        self._sorted = []
        self._query_objects = {}

    def _sort_nodes(self) -> list[ORMItemContainer]:
        """ Сортировать ноды по признаку внешних ключей, определить точки сохранения для транзакций """
        def make_sort_container(node_: ORMItem, linked_nodes: ORMItemContainer):
            """
            Рекурсивно искать ноды с внешними ключами
            O(m) * (O(n) + O(j)) = O(n) * O(m) = O(n)
            """
            related_nodes = self._node_items.get_related_nodes(node_)  # O(n)
            if not related_nodes:
                linked_nodes.add_to_head(**node_.get_attributes())
                return linked_nodes
            return [make_sort_container(n, linked_nodes) for n in related_nodes]  # O(m)
        if self._sorted:
            return self._sorted
        node = self._node_items.dequeue()
        while node:  # todo: n**2
            if node.retries < self.MAX_RETRIES:
                if node.ready:
                    self._sorted.append(make_sort_container(node, ORMItemContainer()))  # O(n) + O(1) = O(n)
                else:
                    self.remaining_nodes.append(**node.get_attributes())
            node = self._node_items.dequeue()
        return self._sorted


class ORMHelper(ORMAttributes):
    """
    Адаптер для ORMItemContainer
    Имеет таймер для единовременного высвобождения очереди объектов,
    при добавлении элемента в очередь таймер обнуляется.
    items - ссылка на экземпляр ORMItemContainer.
    1) Инициализация
        LinkToObj = ORMHelper.set_up(db.session)
    2) Установка ссылки на класс модели Flask-SqlAlchemy
        LinkToObj.set_model(CustomModel)
    3) Использование
        name - Это всегда либо действующий PK или поле с ограничением UNIQUE=TRUE!
        LinkToObj.set_item(name, data, **kwargs) - Установка в очередь, обнуление таймера
        LinkToObj.get_item(name, **kwargs) - получение данных из бд и из ноды
        LinkToObj.get_items(model=None) - получение данных из бд и из ноды
        LinkToObj.release() - высвобождение очереди с попыткой сохранить объекты в базе данных
        в случае неудачи нода переносится в конец очереди
        LinkToObj.remove_items - принудительное изъятие ноды из очереди.
    """
    MEMCACHED_PATH = "127.0.0.1:11211"
    MEMCACHED_RETRY_CONNECTION_SECONDS = 4 * 1000
    DATABASE_RETRY_CONNECTION_SECONDS = 4 * 1000
    DATABASE_PATH = DATABASE_PATH
    _memcache_connection: Optional[Client] = None
    _database_connection = None
    RELEASE_INTERVAL_SECONDS = 5.0
    CACHE_LIFETIME_HOURS = 6 * 60 * 60
    _timer: Optional[threading.Timer] = None
    _items: ORMItemContainer = ORMItemContainer()  # Temp
    _model_obj: Optional[CustomModel] = None  # Текущий класс модели, присваиваемый автоматически всем экземплярам при добавлении в очередь
    _was_initialized = False

    @classmethod
    def initialization(cls):
        if cls.CACHE_LIFETIME_HOURS <= cls.RELEASE_INTERVAL_SECONDS:
            raise Exception("Срок жизни кеша, который хранит очередь сохраняемых объектов не может быть меньше, "
                            "чем интервал отправки объектов в базу данных.")
        cls._was_initialized = True
        #cls.drop_cache()
        return cls

    @classmethod
    def set_model(cls, obj):
        """
        :param obj: Кастомный класс модели Flask-SQLAlchemy из модуля models
        """
        cls.is_valid_model_instance(obj)
        cls._model_obj = obj

    @classmethod
    @property
    def cache(cls):
        if cls._memcache_connection is None:
            try:
                cls._memcache_connection = Client(cls.MEMCACHED_PATH, serde=DillSerde)
            except MemcacheError:
                print("Нет соединения с сервисом кеширования!")
                retry_connect = threading.Timer(cls.MEMCACHED_RETRY_CONNECTION_SECONDS, cls.cache)
                retry_connect.start()
                retry_connect.join()
            else:
                print("Подключение к серверу memcached")
        return cls._memcache_connection

    @classmethod
    def drop_cache(cls):
        cls.cache.flush_all()

    @classmethod
    @property
    def database(cls):
        if cls._database_connection is None:
            try:
                cls._database_connection = SQLAlchemy(cls.DATABASE_PATH)
            except DisconnectionError:
                print("Ошибка соединения с базой данных!")
                try_retry = threading.Timer(cls.DATABASE_RETRY_CONNECTION_SECONDS, cls.database)
                try_retry.start()
                try_retry.join()
            else:
                print("Подключение к базе данных")
        return cls._database_connection

    @classmethod
    @property
    def items(cls) -> ORMItemContainer:
        if cls._items:
            return cls._items
        items = cls.cache.get("ORMItems")
        if not items:
            items = ORMItemContainer()
        cls._items = items
        return items

    @classmethod
    def init_timer(cls):
        timer = threading.Timer(cls.RELEASE_INTERVAL_SECONDS, cls.release)
        timer.daemon = True
        timer.setName("ORMHelper(database push queue)")
        timer.start()
        return timer

    @classmethod
    def set_item(cls, _insert=False, _update=False,
                 _delete=False, _ready=False, _callback=None, _where=None, _model=None, **value):
        model = _model or cls._model_obj
        cls.is_valid_model_instance(model)
        cls.items.enqueue(_model=model, _ready=_ready,
                          _insert=_insert, _update=_update,
                          _delete=_delete, _where=_where, _callback=_callback, **value)
        cls.__set_cache(cls.items)
        cls._timer.cancel() if cls._timer else None
        cls._timer = cls.init_timer()

    @classmethod
    def get_item(cls, _model: Optional[CustomModel] = None, _only_db=False, _only_queue=False, **filter_) -> dict:
        """
        1) Получаем запись из таблицы в виде словаря
        2) Получаем данные из очереди в виде словаря
        3) db_data.update(quque_data)
        Если primary_field со значением node.name найден в БД, то нода удаляется
        """
        model = _model or cls._model_obj
        cls.is_valid_model_instance(model)
        if not filter_:
            return {}
        node: Optional[ORMItem] = None
        if _only_queue:
            nodes = cls.items.search_nodes(model, **filter_)
            if len(nodes):
                node = nodes[0]
            if node is None:
                return {}
            return node.value
        query = model.query.filter_by(**filter_).first()
        data_db = {} if not query else query.__dict__
        if _only_db:
            return data_db
        nodes = cls.items.search_nodes(model, **filter_)
        if len(nodes):
            node = nodes[0]
        if node is None:
            return data_db
        if node.type == "_delete":
            return {}
        updated_node_data = data_db
        updated_node_data.update(node.value)
        return updated_node_data

    @classmethod
    def get_items(cls, _model: Optional[CustomModel] = None, _db_only=False, _queue_only=False, **attrs) -> Iterator[dict]:  # todo: придумать пагинатор
        """
        1) Получаем запись из таблицы в виде словаря (CustomModel.query.all())
        2) Получаем данные из кеша, все элементы, у которых данная модель
        3) db_data.update(quque_data)
        """
        model = _model or cls._model_obj
        cls.is_valid_model_instance(model)
        if not attrs:
            items_db = model.query.all()
        else:
            items_db = model.query.filter_by(**attrs).all()
        if _db_only or not cls.items:
            return map(lambda t: t.__dict__, items_db)
        if _queue_only or not items_db:
            return map(lambda t: t.value,
                       filter(lambda x: not x.type == "_delete", cls.items.search_nodes(model, **attrs))
                       )
        db_items = []
        queue_items = {}  # index: node_value
        nodes_implements_db = ORMItemContainer()  # Ноды, которые пересекаются с бд
        pk_name = getattr(model(), "__db_queue_primary_field_name__")
        for db_item in items_db:  # O(n)
            db_data: dict = db_item.__dict__
            if pk_name not in db_data:
                raise Exception("Несогласованность данных в кэше и базе данных. ""Возможно, кэш сильно устарел.")
            node: ORMItem = cls.items.get_node(model, **{pk_name: db_data[pk_name]})
            if node:
                nodes_implements_db.enqueue(**node.get_attributes())
                if not node.type == "_delete":
                    db_data.update(node.value)
                    queue_items.update({node.index: db_data})
            else:
                db_items.append(db_data)
        for node in cls.items:  # O(k)
            if node not in nodes_implements_db:  # O(l)
                if node.model.__name__ == model.__name__:
                    if not node.type == "_delete":
                        val = node.value
                        queue_items.update({node.index: val}) if val else None
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
        return map(lambda x: x, output)

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
        node = cls.items.get_node(model, **{primary_key_field_name: node_pk_value})
        return node.type if node is not None else None

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
        if isinstance(node_or_nodes, (str, int,)):
            cls.items.remove(model, **{primary_key_field_name: node_or_nodes})
        if isinstance(node_or_nodes, (tuple, list, set, frozenset)):
            for pk_field_value in node_or_nodes:
                if not isinstance(pk_field_value, (int, str,)):
                    raise TypeError
                cls.items.remove(model, **{primary_key_field_name: pk_field_value})
        cls.__set_cache(cls.items)

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
        primary_key_field_name = getattr(model, "__db_queue_primary_field_name__")
        old_node = cls.items.get_node(model, **{primary_key_field_name: pk_field_value})
        if not old_node:
            return
        node_data = old_node.get_attributes()
        if not isinstance(field_or_fields, (tuple, list, set, frozenset, str,)):
            raise TypeError
        if isinstance(field_or_fields, (tuple, list, set, frozenset,)):
            if primary_key_field_name in field_or_fields:
                raise KeyError("Нельзя удалить поле, которое является первичным ключом")
            for field in field_or_fields:
                if field in node_data:
                    del node_data[field]
        if type(field_or_fields) is str:
            if primary_key_field_name == field_or_fields:
                raise KeyError("Нельзя удалить поле, которое является первичным ключом")
            if field_or_fields in node_data:
                del node_data[field_or_fields]
        cls.items.replace(old_node, ORMItemContainer.LinkedListItem(**node_data))
        cls.__set_cache(cls.items)

    @classmethod
    def is_node_from_cache(cls, model=None, **attrs) -> bool:
        model = model or cls._model_obj
        cls.is_valid_model_instance(model)
        items = cls.items.search_nodes(model, **attrs)
        if len(items) > 1:
            raise ValueError(f"В очреди больше одной ноды с данными параметрами: {attrs}")
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
        database_adapter = SQLAlchemyQueryManager(cls.DATABASE_PATH, cls.items)
        database_adapter.start()
        cls.__set_cache(database_adapter.remaining_nodes or None)
        cls._timer = cls.init_timer() if database_adapter.remaining_nodes else None
        print("remaining_nodes", database_adapter.remaining_nodes)
        sys.exit()

    @classmethod
    def __getattribute__(cls, item):
        if not cls._was_initialized and not item == "initialization":
            raise AttributeError("В первую очередь заупскается метод 'initialization'")
        if not item == "set_model":
            if cls._model_obj is None:
                raise AttributeError("Сначала нужно установить модель Flask-SQLAlchemy, используя метод set_model")
        super().__getattribute__(item)

    @classmethod
    def __set_cache(cls, container: Optional[ORMItemContainer]):
        cls._items = container
        cls.cache.set("ORMItems", container, cls.CACHE_LIFETIME_HOURS)


if __name__ == "__main__":
    from database.models import Machine

    i = ORMItemContainer()
    i.enqueue(name="test", _model=Machine, _insert=True, machine_name="1")
    i.enqueue(name="test_122", _model=Machine, _insert=True, machine_name="2")
    i.enqueue(name="test_123", _model=Machine, _insert=True, machine_name="3")
    print(len(i))
    i.dequeue()
    print(len(i))
    i.dequeue()
    print(len(i))
    i.dequeue()
    print(len(i))
    print(i)


