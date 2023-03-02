import sys
import threading
import traceback
from typing import Union, Iterator, Iterable, Optional, Callable
from pymemcache.client.base import Client
from pymemcache_dill_serde import DillSerde
from sqlalchemy.orm import Query
from gui.datatype import LinkedList, LinkedListItem
from database.models import CustomModel


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
        self.__transaction_counter = 0  # Инкрементируется при вызове self.make_query()
        # Подразумевая тем самым, что это попытка сделать транзакцию в базу
        if not kw:
            raise ValueError("Нет полей, нода пуста")
        self.__value.update(kw)
        self.foreign_key_fields = tuple(self.__model.__table__.foreign_keys)
        _ = self.get_primary_key_and_value()  # test

    @property
    def value(self) -> dict:
        return self.__value.copy() if self.__value else {}

    @property
    def model(self):
        return self.__model

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
                       "_delete": False, "_callback": self.__callback})
        result.update({self.type: True})
        return result

    def make_query(self) -> Optional[Query]:
        if self.__transaction_counter > 1:
            return
        if self.__transaction_counter == 1:
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
    см логику в методе _initialize_node.
    """
    LinkedListItem = ORMItem

    def __init__(self, items: Optional[Iterable[dict]] = None):
        super().__init__()
        if items is not None:
            for inner in items:
                self.enqueue(**inner)

    def enqueue(self, **attrs):
        """ Установка ноды в конец очереди с хитрой логикой проверки на совпадение. """
        exists_item, new_item = self._initialize_node(**attrs)

        def check_foreign_key_nodes():  # O(n) * (O(k) + O(i) + O(i)) -> O(n) * O(j) -> O(n)
            """
            Найти ноды, которые зависят от ноды, которая в настоящий момент добавляется:
            если добавляемая ноды
            Если такие ноды найдутся, то они будут удалены и добавлены в очередь снова.
            """
            nodes_to_move_in_end_queue = self.__class__()
            new_item_primary_key_name = new_item.get_primary_key_and_value(only_key=True)
            for node in self:  # O(n)
                if new_item_primary_key_name in node.foreign_key_fields:  # O(k)
                    nodes_to_move_in_end_queue.enqueue(**node.get_attributes())  # O(i)
            if nodes_to_move_in_end_queue:
                self + nodes_to_move_in_end_queue  # O(i)
        self.__remove_from_queue(exists_item) if exists_item else None
        if self:
            last_element = self._tail
            self._set_prev(new_item, last_element)
            self._set_next(last_element, new_item)
            self._tail = new_item
        else:
            self._head = self._tail = new_item
        check_foreign_key_nodes()

    def dequeue(self) -> Optional[ORMItem]:
        """ Извлечение ноды с начала очереди """
        node = self._head
        if node is None:
            return
        self.__remove_from_queue(node)
        return node

    def replace(self, old_node: ORMItem, new_node: ORMItem) -> Optional[ORMItem]:  # O(n) + O(n) = O(2n) = O(n)
        """
        Заменить ноду, сохранив её позицию в очереди.
        Если исходной ноды не найдено, вернуть None и ничего не делать,
        если найдена - заменить ноду и вернуть новую ноду
        """
        if type(old_node) is not ORMItem or not isinstance(new_node, ORMItem):
            raise TypeError
        if not len(self):
            return
        if len(self) == 1:
            self._head = self._tail = new_node
            return
        next_node = old_node.next
        previous_node = old_node.prev()
        if old_node.index == len(self) - 1:
            self._tail = new_node
        if old_node.index == 0:
            self._head = new_node
        previous_node.next = new_node
        next_node.prev = new_node
        return new_node

    def remove(self, model, pk_field_name, pk_field_value):
        node = self.get_node(model, **{pk_field_name: pk_field_value})
        if node:
            self.__remove_from_queue(node)
            return node

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
                    items.enqueue(**node.get_attributes())
                for field_name, value in _filter.items():
                    if field_name in node.value:
                        if node.value[field_name] == value:
                            items.enqueue(**node.get_attributes())  # O(i) i->n
                        else:
                            items.remove(node.model, *node.get_primary_key_and_value(as_tuple=True))
        return items

    def get_node(self, model: CustomModel, **primary_key_data) -> Optional[ORMItem]:
        """
        Данный метод используется при инициализации - _initialize_node
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
        [self.enqueue(**n.get_attributes()) for n in other]
        return self

    def _initialize_node(self, **new_node_complete_data: dict) -> tuple[Optional[ORMItem], ORMItem]:  # O(l * k) + O(n) + O(1) = O(n)
        """
        Создавать ноды для добавления можно только здесь!
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
        if type(node) is not ORMItem:
            raise TypeError
        prev_node = node.prev
        prev_node = prev_node() if prev_node is not None else prev_node  # Вызываем потому что слабая ссылка
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
    MEMCACHED_CONFIG = "127.0.0.1:11211"
    _store: Optional[Client] = None
    RELEASE_INTERVAL_SECONDS = 5.0
    CACHE_LIFETIME_HOURS = 6 * 60 * 60
    _timer: Optional[threading.Timer] = None
    _items: ORMItemContainer = ORMItemContainer()  # Temp
    _session = None
    _model_obj: Optional[CustomModel] = None  # Текущий класс модели, присваиваемый автоматически всем экземплярам при добавлении в очередь

    @classmethod
    def set_up(cls, session):
        if cls.CACHE_LIFETIME_HOURS <= cls.RELEASE_INTERVAL_SECONDS:
            raise Exception("Срок жизни кеша, который хранит очередь сохраняемых объектов не может быть меньше, "
                            "чем интервал отправки объектов в базу данных.")

        def connect_to_storage():
            store = Client(cls.MEMCACHED_CONFIG, serde=DillSerde)
            return store

        def drop_cache():
            cls._store.flush_all()
        cls._is_valid_session(session)
        cls._session = session
        cls._store = connect_to_storage()
        #drop_cache()
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
    def items(cls) -> ORMItemContainer:
        if cls._items:
            return cls._items
        items = cls._store.get("ORMItems")
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
        #import time
        #time.sleep(1)  # todo: Тестируем зарержку
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
        for db_item in items_db:  # O(n)
            db_data: dict = db_item.__dict__
            nodes: ORMItemContainer = cls.items.search_nodes(model, **attrs)
            for node in nodes:
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
        def enqueue(node):
            enqueue_items.enqueue(**node.get_attributes())
        is_nodes_in_session = False
        enqueue_items = ORMItemContainer()
        cls._items = cls.items
        while True:
            orm_element = cls._items.dequeue()
            if orm_element is None:
                break
            if orm_element.ready:
                query = orm_element.make_query()
                if query:
                    if orm_element.type == "_delete":
                        cls._session.delete(query)
                    else:
                        cls._session.add(query)
                    is_nodes_in_session = True
            else:
                enqueue(orm_element)
        if is_nodes_in_session:
            cls._session.commit()
        cls.__set_cache(enqueue_items or None)
        if len(enqueue_items):
            cls.init_timer()
        sys.exit()

    @staticmethod
    def _is_valid_session(obj):  # todo: Пока не знаю как проверить
        return

    @classmethod
    def __set_cache(cls, container: Optional[ORMItemContainer]):
        cls._store.set("ORMItems", container, cls.CACHE_LIFETIME_HOURS)
        cls._items = container
