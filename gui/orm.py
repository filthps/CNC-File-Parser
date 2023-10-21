import itertools
import sys
import copy
import threading
from typing import Union, Iterator, Iterable, Optional
from collections import ChainMap
from pymemcache.client.base import Client
from pymemcache.exceptions import MemcacheError
from pymemcache_dill_serde import DillSerde
from psycopg2.errors import Error as PsycopgError
from sqlalchemy import create_engine
from sqlalchemy.sql.dml import Insert, Update, Delete
from sqlalchemy.orm import Query, sessionmaker as session_factory, Session
from sqlalchemy.exc import DisconnectionError, OperationalError, SQLAlchemyError
from gui.datatype import LinkedList, LinkedListItem
from database.models import CustomModel, DATABASE_PATH


class ORMAttributes:
    @staticmethod
    def is_valid_model_instance(item: CustomModel):
        item = item()  # __new__
        if not hasattr(item, "__db_queue_primary_field_name__") or \
                not hasattr(item, "__remove_pk__") or not hasattr(item, "column_names"):
            raise TypeError("Значение атрибута model - неподходящего типа."
                            "Используйте только кастомный класс - 'CustomModel', смотри models.")


class ORMItem(LinkedListItem, ORMAttributes):
    """ Иммутабельный класс ноды для ORMItemQueue. """
    def __init__(self, **kw):
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
        self._is_valid_dml_type(kw)
        self.__model: Union[CustomModel, Iterable[CustomModel]] = kw.pop("_model")
        self.is_valid_model_instance(self.__model)
        self.__insert = kw.pop("_insert", False)
        self.__update = kw.pop("_update", False)
        self.__delete = kw.pop("_delete", False)
        self.__is_ready = kw.pop("_ready", True if self.__delete else False)
        self.__where = kw.pop("_where", None)
        self.__transaction_counter = kw.pop('_count_retries', 0)  # Инкрементируется при вызове self.make_query()
        # Подразумевая тем самым, что это попытка сделать транзакцию в базу
        if not kw:
            raise ValueError("Нет полей, нода пуста")
        self._value = {}  # Содержимое - пары ключ-значение: поле таблицы бд: значение
        self._value.update(kw)
        self.__foreign_key_fields = tuple(self.__model.__table__.foreign_keys)

        def check_queue_and_database_pk():
            """ Обязательное наличие в value primary_key для БД и наличие значения для __db_queue_primary_field_name__
             необходимо для корректной работы ORMHelper.join_select"""
            _ = self.get_primary_key_and_value()  # test attr __db_queue_primary_field_name__
            db_primary_key = getattr(self.model(), "__primary_key__")
            local_primary_key = getattr(self.model(), "__db_queue_primary_field_name__")
            if db_primary_key not in self.value and local_primary_key not in self.value:
                raise ValueError("Любая нода, будь то insert, update или delete,"
                                 "должна иметь в значении поле первичного ключа (для базы данных) со значением!")
        check_queue_and_database_pk()

    @property
    def value(self):
        return self._value.copy()

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

    def get_primary_key_and_value(self, from_database=False, as_tuple=False, only_key=False, only_value=False) -> Union[dict, tuple, int, str]:
        """
        :param from_database: True - выдаст пару ключ-значение от атрибута '__primary_key__', - который установлен в БД
        False - '__db_queue_primary_field_name__' - который определяет уникальность ноды в ORMQueue
        :param as_tuple: ключ-значение в виде кортежа
        :param only_key: только название столбца - PK
        :param only_value: только значение столбца первичного ключа
         """
        key = getattr(self.__model(), "__db_queue_primary_field_name__" if not from_database else "__primary_key__", None)
        if key is None:
            key = getattr(self.__model(), "__db_queue_primary_field_name__" if from_database else "__primary_key__")
        if only_key:
            return key
        try:
            value = self._value[key]
        except KeyError:
            raise ValueError("Любая нода, будь то insert, update или delete,"
                  "должна иметь в значении поле первичного ключа (для нод) со значением!")
        if only_value:
            return value
        return {key: value} if not as_tuple else (key, value,)

    @property
    def ready(self) -> bool:
        return self.__is_ready

    @property
    def where(self) -> dict:
        return self.__where.copy() if self.__where else {}

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
                       "_delete": False, "_count_retries": self.retries})
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
        return len(self._value)

    def __eq__(self, other: "ORMItem"):
        if type(other) is not type(self):
            return False
        return self.__hash__() == hash(other)

    def __contains__(self, item: str):
        if not isinstance(item, str):
            return False
        if item in self.value:
            return True

    def __bool__(self):
        return bool(len(self))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.get_attributes()})"

    def __str__(self):
        return str(self.value)

    def __hash__(self):
        str_ = "".join(map(lambda x: str(x), self.get_primary_key_and_value(as_tuple=True)))
        return int.from_bytes(bytes(str_, "utf-8"), "big")

    def __getitem__(self, item: str):
        if type(item) is not str:
            raise TypeError
        if item not in self.value:
            raise KeyError
        return self.value[item]

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
        self._replace_inner(new_nodes._head, new_nodes._tail)

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

    def search_nodes(self, model: CustomModel, negative_selection=False, **_filter) -> "ORMItemQueue":  # O(n)
        """
        Искать ноды по совпадениям любых полей
        :arg model: кастомный объект, смотри модуль database/models
        :arg _filter: словарь содержащий набор полей и их значений для поиска
        :arg negative_selection: режим отбора нод
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
            raise ValueError("Параметр primary_key_data содержит название поля, которое является первичным ключом модели"
                             "и значение для этого поля")
        nodes = iter(self)
        while nodes:  # O(n) * O(k)
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

    def __add__(self, other: Union["ORMItemQueue"]):
        if not type(other) is self.__class__:
            raise TypeError
        result_instance = self.__class__()
        [result_instance.append(**n.get_attributes()) for n in self]  # O(n)
        [result_instance.enqueue(**n.get_attributes()) for n in other]  # O(n**2) todo n**2!
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

    def _remove_from_queue(self, left_node: ORMItem) -> None:
        if type(left_node) is not self.LinkedListItem:
            raise TypeError
        del self[left_node.index]


class SQLAlchemyQueryManager:
    MAX_RETRIES = 4
    
    def __init__(self, connection_path: str, nodes: "ORMItemQueue"):
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
            if node_.retries < self.MAX_RETRIES:
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
    pass


class SpecialOrmContainer(ORMItemQueue):
    LinkedListItem = SpecialOrmItem

    def get(self, key, default=None):
        try:
            val = self.__getitem__(key)
        except KeyError:
            return default
        else:
            return val

    def __getitem__(self, item: str):  # get by model name
        if not isinstance(item, str):
            raise TypeError
        for node in self:
            if node.model.__name__ == item:
                return node
        raise KeyError


class ORMHelper(ORMAttributes):
    """
    Адаптер для ORMItemQueue
    Имеет таймер для единовременного высвобождения очереди объектов,
    при добавлении элемента в очередь таймер обнуляется.
    свойство items (инкапсулирован в _items) - ссылка на экземпляр ORMItemQueue.
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
    DATABASE_PATH = DATABASE_PATH
    _memcache_connection: Optional[Client] = None
    _database_session = None
    RELEASE_INTERVAL_SECONDS = 5.0
    CACHE_LIFETIME_HOURS = 6 * 60 * 60
    _timer: Optional[threading.Timer] = None
    _items: ORMItemQueue = ORMItemQueue()  # Temp
    _model_obj: Optional[CustomModel] = None  # Текущий класс модели, присваиваемый автоматически всем экземплярам при добавлении в очередь
    _was_initialized = False

    @classmethod
    def initialization(cls):
        if cls.CACHE_LIFETIME_HOURS <= cls.RELEASE_INTERVAL_SECONDS:
            raise Exception("Срок жизни кеша, который хранит очередь сохраняемых объектов не может быть меньше, "
                            "чем интервал отправки объектов в базу данных.")
        cls._was_initialized = True
        #  cls.drop_cache()
        JoinedORMItem.set_adapter(cls)
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
                engine = create_engine(DATABASE_PATH)
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
        if cls._items:
            return cls._items
        items = cls.cache.get("ORMItems")
        if not items:
            items = ORMItemQueue()
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
                 _delete=False, _ready=False, _where=None, _model=None, **value):
        model = _model or cls._model_obj
        cls.is_valid_model_instance(model)
        cls.items.enqueue(_model=model, _ready=_ready,
                          _insert=_insert, _update=_update,
                          _delete=_delete, _where=_where, **value)
        cls.__set_cache()
        cls._timer.cancel() if cls._timer else None
        cls._timer = cls.init_timer()

    @classmethod
    def get_item(cls, _model: Optional[CustomModel] = None, _only_db=False, _only_queue=False, **filter_) -> dict:
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
    def get_items(cls, _model: Optional[CustomModel] = None, _db_only=False, _queue_only=False, **attrs) -> Iterator[dict]:  # todo: придумать пагинатор
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
        pk_name = getattr(model(), "__db_queue_primary_field_name__")
        for db_item in items_db:  # O(n)
            db_data: dict = db_item.__dict__
            if pk_name not in db_data:
                raise Exception("Несогласованность данных в кэше и базе данных. ""Возможно, кэш сильно устарел.")
            left_node: ORMItem = cls.items.get_node(model, **{pk_name: db_data[pk_name]})
            if left_node:
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
                    _where: Optional[dict] = None) -> "JoinedORMItem":
        """
        join_select(model_a, model,b, on={model_b: 'model_a.column_name'})

        :param _where: modelName: {column_name: some_val}
        :param on: modelName.column1: modelName2.column2
        :return: специльный итерируемый объект класса JoinedORMItem, который содержит смешанные данные из локального
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
                raise ValueError
            if _where:
                if type(_where) is not dict:
                    raise ValueError
                for v in _where.values():
                    if not isinstance(v, dict):
                        raise TypeError
                    for key, value in v.items():
                        if type(key) is not str:
                            raise TypeError("Наиенование столбца может быть только строкой")
                        if not isinstance(value, (str, int,)):
                            raise TypeError
            if len(on) != len(models) - 1:
                raise ValueError(
                    "Правильный способ работы с данным методом: join_select(model_a, model,b, on={model_b.column_name: 'model_a.column_name'})"
                )
            for left_table_dot_field, right_table_dot_field in on.items():
                if not type(left_table_dot_field) is str or not isinstance(right_table_dot_field, str):
                    raise TypeError("...on={model_b.column_name: 'model_a.column_name'}")
                left_model = left_table_dot_field.split(".")[0]
                right_model = right_table_dot_field.split(".")[0]
                if len(left_table_dot_field.split(".")) != 2 or len(right_table_dot_field.split(".")) != 2:
                    raise AttributeError("...on={model_b.column_name: 'model_a.column_name'}")
                if left_model not in name_and_model_dict:
                    raise ImportError(f"Класс модели {left_model} не найден")
                if right_model not in name_and_model_dict:
                    raise ImportError(f"Класс модели {right_model} не найден")
                left_model_field = left_table_dot_field.split(".")[1]
                right_model_field = right_table_dot_field.split(".")[1]
                if not getattr(name_and_model_dict[left_model], left_model_field, None):
                    raise AttributeError(f"Столбец {left_model_field} у таблицы {left_model} не найден")
                if not getattr(name_and_model_dict[right_model], right_model_field, None):
                    raise AttributeError(f"Столбец {right_model_field} у таблицы {right_model} не найден")
        name_and_model_dict = {m.__name__: m for m in models}
        valid_params()

        def count_ref_table():
            """ Опорная модель, - к которой, условно, применяется конструкция FROM (она встретится в словаре on 2 раза) """
            def get_reference_table() -> str:
                max_match_counter_index = list(models_repeat_counter.values()).index(max_repeat_counter)
                table_name_with_max_retries = tuple(models_repeat_counter.keys())[max_match_counter_index]
                return table_name_with_max_retries
            left_tables = [str_.split(".")[0] for str_ in on.keys()]
            right_tables = [str_.split(".")[0] for str_ in on.values()]
            all_tables = list(itertools.chain(left_tables, right_tables))
            models_repeat_counter = {model_name: all_tables.count(model_name) for model_name in all_tables}
            max_repeat_counter = max(models_repeat_counter.values())
            return get_reference_table()
        reference_table_name = count_ref_table()

        def collect_db_data():
            def create_request() -> str:  # O(n) * O(m)
                s = f"dirty_data = db.database.query({tuple(name_and_model_dict.keys())[0]})"  # O(l) * O(1)
                for left_table_dot_field, right_table_dot_field in on.items():  # O(n)
                    left_table, left_table_field = left_table_dot_field.split(".")  # O(m)
                    s += f".join({left_table}, "
                    s += f"{left_table}.{left_table_field} == {right_table_dot_field})"
                if _where:
                    on_keys_counter = 0
                    s += f".filter("
                    for table_name, column_and_value in _where.items():
                        for left_table_and_column, right_table_and_column in column_and_value.items():  # O(t)
                            s += f"{table_name}.{left_table_and_column} == '{right_table_and_column}'"
                            if on_keys_counter < len(column_and_value) - 1:  # O(1)
                                s += ", "
                            on_keys_counter += 1
                        s += ")"
                return s

            def add_items_to_orm_queue() -> Iterator[SpecialOrmContainer]:  # O(i) * O(k) * O(m) * O(n) * O(j) * O(l)
                for mix_table_data in dirty_data:  # O(i)
                    row = SpecialOrmContainer()  # todo: что будет, если в 2 таблицах есть одноимённые столбцы?! testcase
                    for model in models:  # O(k)
                        all_column_names = getattr(model(), "column_names")
                        r = {col_name: col_val for col_name, col_val in mix_table_data.items()
                             if col_name in all_column_names}  # O(n) * O(j)
                        row.append(_model=model, _insert=True, **r)  # O(l)
                    yield row
            dirty_data = []
            sql_text = create_request()
            exec(sql_text, {"db": cls}, ChainMap(*list(map(lambda x: {x.__name__: x}, models))))
            return add_items_to_orm_queue()

        def collect_local_data() -> Iterator[SpecialOrmContainer]:
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
                                    raw.append(**left_node.get_attributes())  # O(1) todo: протестировать этот момент, возможна замена на enqueue
                                    raw.append(**right_node.get_attributes())  # O(1) todo: протестировать этот момент, возможна замена на enqueue
                        if raw:
                            yield raw
            heap = ORMItemQueue()
            collect_all()
            return compare_by_matched_fk()
        database_data = collect_db_data()
        local_data = collect_local_data()
        return JoinedORMItem(list(local_data), list(database_data), reference_table_name, models=models,
                             join_select_kwargs={"_where": _where, "on": on})

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
        if isinstance(node_or_nodes, (str, int,)):
            cls.items.remove(model, **{primary_key_field_name: node_or_nodes})
        if isinstance(node_or_nodes, (tuple, list, set, frozenset)):
            for pk_field_value in node_or_nodes:
                if not isinstance(pk_field_value, (int, str,)):
                    raise TypeError
                cls.items.remove(model, **{primary_key_field_name: pk_field_value})
        cls.__set_cache()

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
        cls.items.replace(old_node, ORMItemQueue.LinkedListItem(**node_data))
        cls.__set_cache()

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
        database_adapter = SQLAlchemyQueryManager(DATABASE_PATH, cls.items)
        database_adapter.start()
        cls._items = database_adapter.remaining_nodes or None
        cls.__set_cache()
        cls._timer = cls.init_timer() if database_adapter.remaining_nodes else None
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
    def __set_cache(cls):
        cls.cache.set("ORMItems", cls._items, cls.CACHE_LIFETIME_HOURS)
        
        
class JoinedORMItem(ORMAttributes):
    """ Экземпляр этого класса возвращается функцией ORMHelper.join_select()
     Внутри него инкапсулированы ноды. Иммутабельный контейнер с контейнером нод.
      1 экземпляр этого класса 1 результат вызова ORMHelper.join_select()
      JoinedORMItem().__getitem__(model_name).__getitem__(node_value_dict_key).
      """

    def __init__(self, local_nodes: list[SpecialOrmContainer],
                 nodes_from_database__join_select: list[SpecialOrmContainer], reference_table: str,
                 models=None, join_select_kwargs=None):
        self._models = models
        self._join_select_kwargs = join_select_kwargs
        self._main_table_name: str = reference_table
        self._local_nodes = local_nodes
        self._database_nodes = nodes_from_database__join_select
        self._merged_nodes: tuple = tuple()
        self._merge()

    @classmethod
    def set_adapter(cls, val: ORMHelper):
        if val is not ORMHelper:
            raise TypeError
        cls._adapter = val

    def __iter__(self):
        return iter(self._merged_nodes)

    def __bool__(self):
        return bool(len(self))

    def __len__(self):
        return sum([1 for _ in self])

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        self_hash_counter = sum(map(lambda x: hash(x), iter(self)))
        other_hash_counter = sum(map(lambda x: hash(x), iter(other)))
        return self_hash_counter == other_hash_counter

    def __getitem__(self, item: int):
        if not isinstance(item, int):
            raise TypeError
        for container in self:
            if hash(container) == item:
                return container
        raise KeyError

    def __str__(self):
        s = "Локальные: "
        s += ", ".join([str(nodes) for nodes in self._local_nodes])
        s += " из базы данных "
        s += ", ".join([str(nodes) for nodes in self._database_nodes])
        return s

    def __repr__(self):
        return f"{self.__class__.__name__}({[repr(orm_container) for orm_container in self._local_nodes]}, " \
               f"{[repr(node) for node in self._database_nodes]})"

    def _merge(self):
        def get_all_merged_entries():
            for nodes_group_from_db in self._database_nodes:
                node, ref_node = None, None
                for node in nodes_group_from_db:
                    if node.model.__name__ == self._main_table_name:
                        ref_node = node
                        break
                for nodes_group_from_local_queue in self._database_nodes:
                    local_node = nodes_group_from_local_queue.get_node(ref_node.model,
                                                                       **ref_node.get_primary_key_and_value())
                    if local_node:
                        merged_data.update({local_node.get_primary_key_and_value(as_tuple=True):
                                            nodes_group_from_db + nodes_group_from_local_queue})
                        models.update({local_node.get_primary_key_and_value(as_tuple=True): node.model.__name__})

        def get_all_local_entries() -> list[SpecialOrmContainer]:
            local_items = copy.deepcopy(self._local_nodes)
            for index, container in enumerate(self._local_nodes):
                for pk_tuple in merged_data.keys():
                    find_node = container.get_node(models[pk_tuple], **dict(zip(*(tuple(x) for x in pk_tuple))))
                    if find_node:
                        del local_items[index]
            return local_items
        merged_data = {}
        models = {}
        get_all_merged_entries()
        not_intersected_data = get_all_local_entries()
        all_items = list(merged_data.values())
        all_items.extend(not_intersected_data)  # todo: ordering  ???
        self._merged_nodes = all_items

    def is_actual_nodes(self, hash_: int) -> bool:
        def collect_where_clause():
            for node in items:
                where.update({node.model.__name__: node.get_primary_key_and_value()})

        def get_new_join_select_items():
            return self._adapter.join_select(*self._models, _where=where, on=self._join_select_kwargs["on"])

        items = self[hash_]
        where = {}
        collect_where_clause()
        new_items = get_new_join_select_items()
        try:
            new_items[hash_]
        except KeyError:
            return False
        return True

    def refresh_all_items(self) -> Iterator[dict]:
        new_items = self._adapter.join_select(self._models, on=self._join_select_kwargs["on"])
        self._merged_nodes = dict(iter(new_items))
        return iter(self)


if __name__ == "__main__":
    from database.models import Machine, Condition, SearchString

    def test_join_select():
        adapter = ORMHelper
        adapter.set_model(Machine)
        #adapter.join_select(Condition, SearchString, on={"SearchString.strid": "Condition.stringid"})
        print(list(adapter.get_items(Condition, _db_only=True)))
        print(list(adapter.get_items(SearchString, _db_only=True)))
    #  test_join_select()

    def hash_test():
        container = ORMItemQueue()
        container.enqueue(_model=Machine, testval="123", testval2=435, _insert=True, machine_name="Heller")

        container1 = ORMItemQueue()
        container1.enqueue(_model=Machine, testval="123", testval2=45, _insert=True, machine_name="Helle")
        print(hash(container[0]) == hash(container1[0]))
        print(container1 == container)
        print(container1.__hash__())
    #  hash_test()
