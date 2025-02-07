"""
Определение границ ответственности для тестов orm модуля.
Данные тесты проверяют:
    - Все методы и свойства
    - Возможность установить недействительные названия полей
    - Возможность установить недействительное значение полей (тип)
    - Возможность отсутствия nullable значений
    - unique
Данные тесты не могут проверить:
    - Триггеры, check constraint, и любые другие процедуры.
    База данных, её соответствие модели ACID, тестируется отдельными тестами!
"""
import unittest
import datetime
import time
from sqlalchemy import func, select, text
from database.models import Machine, Cnc, OperationDelegation, SearchString, db as sqlalchemy_instance, Condition, \
    Numeration, Comment, drop_db, create_db
from database.procedures import init_all_triggers
from gui.datatype import LinkedList
from orm import *


DEBUG = True


def is_database_empty(session, empty=True, tables=15, procedures=52, test_db_name="testdb"):
    table_counter = session.execute(text('SELECT COUNT(table_name) '
                                         'FROM information_schema."tables" '
                                         'WHERE table_type=\'BASE TABLE\' AND table_schema=\'public\';')).scalar()
    procedures_counter = session.execute(text(f'SELECT COUNT(*) '
                                              f'FROM information_schema."triggers" '
                                              f'WHERE trigger_schema=\'public\' AND '
                                              f'trigger_catalog=\'{test_db_name}\' AND '
                                              f'event_object_catalog=\'{test_db_name}\';')).scalar()
    print(f"procedures_counter {procedures_counter}")
    print(f"table_counter {table_counter}")
    if empty:
        if table_counter or procedures_counter:
            time.sleep(2)
            return is_database_empty(session, empty=empty, tables=tables, procedures=procedures,
                                     test_db_name=test_db_name)
        return True
    if table_counter < tables or procedures_counter < procedures:
        time.sleep(2)
        return is_database_empty(session, empty=empty, tables=tables, procedures=procedures,
                                 test_db_name=test_db_name)
    return True


def db_reinit(m):
    def wrap(self: "TestORMHelper"):
        drop_db()
        if is_database_empty(self.orm_manager.database):
            create_db()
            init_all_triggers()
            if is_database_empty(self.orm_manager.database, empty=False):
                return m(self)
    return wrap


def drop_cache(callable_):
    def w(self: "TestORMHelper"):
        self.orm_manager.drop_cache()
        return callable_(self)
    return w


class SetUp:
    orm_manager: Optional[ORMHelper] = None

    def set_data_into_database(self):
        self.orm_manager.database.add(Cnc(name="NC210", commentsymbol=","))
        self.orm_manager.database.add(Numeration(numerationid=3))
        self.orm_manager.database.add(Comment(findstr="test_str", iffullmatch=True))
        self.orm_manager.database.commit()
        self.orm_manager.database.add(Machine(machinename="Heller",
                                              cncid=self.orm_manager.database.scalar(select(Cnc).where(Cnc.name == "NC210")).cncid,
                                              inputcatalog=r"C:\Windows",
                                              outputcatalog=r"X:\path"))
        self.orm_manager.database.add(OperationDelegation(
            numerationid=self.orm_manager.database.scalar(select(Numeration)).numerationid,
            operationdescription="Нумерация. Добавил сразу в БД"
        ))
        self.orm_manager.database.add(OperationDelegation(commentid=self.orm_manager.database.scalar(select(Comment)).commentid))
        self.orm_manager.database.commit()
        time.sleep(1)

    def set_data_into_queue(self):
        self.orm_manager.set_item(_model=Numeration, numerationid=2, endat=269, _insert=True)
        self.orm_manager.set_item(_insert=True, _model=OperationDelegation, numerationid=2, operationdescription="Нумерация кадров")
        self.orm_manager.set_item(_model=Comment, findstr="test_string_set_from_queue", ifcontains=True, _insert=True, commentid=2)
        self.orm_manager.set_item(_model=OperationDelegation, commentid=2, _insert=True,
                                  operationdescription="Комментарий")
        self.orm_manager.set_item(_model=Cnc, _insert=True, cncid=2, name="Ram", commentsymbol="#")
        self.orm_manager.set_item(_model=Cnc, _insert=True, cncid=1, name="Newcnc", commentsymbol="!")
        self.orm_manager.set_item(_model=Machine, machineid=2, cncid=2, machinename="Fidia", inputcatalog=r"D:\Heller",
                                  outputcatalog=r"C:\Test", _insert=True)
        self.orm_manager.set_item(_model=Machine, machinename="Tesm", _insert=True, machineid=1, cncid=1)
        self.orm_manager.set_item(_model=Machine, machinename="65A90", _insert=True)
        self.orm_manager.set_item(_model=Machine, machinename="Rambaudi", _insert=True)

    def update_exists_items(self):
        self.orm_manager.set_item(cncid=1, name="nameeg", _model=Cnc, _update=True)
        self.orm_manager.set_item(_update=True, _model=Machine, machineid=2, inputcatalog=r"D:\other_path")
        self.orm_manager.set_item(numerationid=2, endat=4, _model=Numeration, _update=True)
        self.orm_manager.set_item(_model=Comment, commentid=2, findstr="test_str_new", _update=True)
        self.orm_manager.set_item(_model=Machine, machinename="testnameret", machineid=1, _update=True)


class TestLinkedList(unittest.TestCase):
    def test_init(self) -> None:
        LinkedList([{"node_val": 1}, {"nod2_val": 2}, {"node3_val": 3},
                    {"node3_val": 4}, {"node4_val": 5}])
        LinkedList()

    def test_getitem(self):
        linked_list = LinkedList([{"node_val": 1}, {"nod2_val": 2}, {"node3_val": 3},
                                  {"node3_val": 4}, {"node4_val": 5}])
        linked_list.__getitem__(4)
        linked_list[1]
        linked_list[-2]
        linked_list.__getitem__(-4)
        with self.assertRaises(IndexError):
            linked_list.__getitem__(8)
            linked_list[0]
            linked_list[-5]
        with self.assertRaises(TypeError):
            linked_list[{}]
            linked_list["w"]
            linked_list["34"]
            linked_list[None]
            linked_list[False]
            linked_list[True]

    def test_setitem(self):
        linked_list = LinkedList()
        self.assertEqual(linked_list.__len__(), 0)
        with self.assertRaises(IndexError):
            linked_list[1] = {"val": "val"}
            linked_list[1] = {"val": "val"}
            linked_list[5] = {"val": "val"}
            linked_list[-1] = {"val": "val"}
        with self.assertRaises(TypeError):
            linked_list[None] = {"val": "val"}
            linked_list["sdf"] = {"val": "val"}
            linked_list["0"] = {"val": "val"}
        linked_list.__setitem__(0, {"node_val": "test_val"})
        linked_list.__setitem__(0, {"node_val": "test_val"})
        with self.assertRaises(IndexError):
            linked_list[4] = "nodeval"

    def test_bool(self):
        linked_list = LinkedList()
        self.assertFalse(linked_list)
        self.assertFalse(linked_list)
        linked_list.__setitem__(0, {"val": "val"})
        self.assertTrue(linked_list)
        del linked_list[0]
        self.assertFalse(linked_list)
        linked_list[0] = {"val1": 1}
        self.assertTrue(linked_list)
        linked_list.__setitem__(0, {"val2": 4})
        self.assertTrue(linked_list)
        linked_list.__setitem__(0, {"val3": 3})
        self.assertTrue(linked_list)
        del linked_list[0]
        self.assertFalse(linked_list)

    def test_len(self):
        linked_list = LinkedList()
        self.assertEqual(linked_list.__len__(), 0)
        linked_list = LinkedList([{"node_val": 1}, {"nod2_val": 2}, {"node3_val": 3},
                                  {"node3_val": 4}, {"node4_val": 5}])
        self.assertEqual(len(linked_list), 5)
        del linked_list[-1]
        self.assertEqual(len(linked_list), 4)
        linked_list.append(**{"val": 1})
        self.assertEqual(len(linked_list), 5)

    def test_delitem(self):
        linked_list = LinkedList([{"node_val": 1}, {"nod2_val": 2}, {"node3_val": 3},
                                  {"node3_val": 4}, {"node4_val": 5}])
        linked_list.__delitem__(0)
        linked_list.__delitem__(0)
        linked_list.__delitem__(0)
        linked_list.__delitem__(0)
        self.assertEqual(len(linked_list), 1)
        linked_list.__delitem__(-1)
        self.assertEqual(linked_list.__len__(), 0)
        linked_list = LinkedList([{"node_val": 1}, {"nod2_val": 2}, {"node3_val": 3},
                                  {"node3_val": 4}, {"node4_val": 5}])
        del linked_list[-2]
        del linked_list[-1]
        del linked_list[1]
        del linked_list[0]
        self.assertEqual(linked_list[0].value, {"node3_val": 3})
        linked_list = LinkedList([{"node_val": 1}, {"nod2_val": 2}, {"node3_val": 3},
                                  {"node3_val": 4}, {"node4_val": 5}])
        linked_list.__delitem__(3)
        linked_list.__delitem__(3)

    def test_iter(self):
        linked_list = LinkedList([{"node_val": 1}, {"nod2_val": 2}, {"node3_val": 3},
                                  {"node3_val": 4}, {"node4_val": 5}])
        items = [{"node_val": 1}, {"nod2_val": 2}, {"node3_val": 3},
                                  {"node3_val": 4}, {"node4_val": 5}]
        self.assertTrue(hasattr(linked_list, "__iter__"))
        iterator = iter(linked_list)
        counter = 0
        while iterator:
            try:
                node = next(iterator)
                if counter == len(items):
                    assert False
                self.assertEqual(node.value, items[counter])
            except StopIteration:
                break
            else:
                counter += 1
        if not counter == len(linked_list):
            assert False

    def test_contains(self):
        linked_list = LinkedList([{"node_val": 1}, {"nod2_val": 2}, {"node3_val": 3},
                                  {"node3_val": 4}, {"node4_val": 5}])
        for node in linked_list:
            if node not in linked_list:
                assert False

        other_linked_list = LinkedList([{"other_node_val": 1}, {"other2_node_val": 2}, {"other3_node_val": 3},
                                        {"other4_node_val": 4}, {"other5_node_val": 5}])
        for node in other_linked_list:
            self.assertFalse(linked_list.__contains__(node))
        self.assertFalse(linked_list.__contains__(None))
        self.assertFalse(linked_list.__contains__("1"))
        self.assertFalse(linked_list.__contains__(1))
        self.assertFalse(linked_list.__contains__(1.6))
        self.assertFalse(linked_list.__contains__([1]))

    def test_append(self):
        linked_list = LinkedList([{"node_val": 1}, {"nod2_val": 2}, {"node3_val": 3},
                                  {"node3_val": 4}, {"node4_val": 5}])
        self.assertEqual(linked_list.__len__(), 5)
        self.assertEqual(linked_list[-1].value, {"node4_val": 5})
        self.assertEqual(linked_list[4].value, {"node4_val": 5})

        linked_list.append(new_value_after_append=100)

        self.assertEqual(linked_list.__len__(), 6)
        self.assertEqual(linked_list[-1].value, {"new_value_after_append": 100})
        self.assertEqual(linked_list[5].value, {"new_value_after_append": 100})

        linked_list = LinkedList()
        self.assertEqual(linked_list.__len__(), 0)
        with self.assertRaises(IndexError):
            linked_list[-1]
            linked_list[4]
        linked_list.append(new_value_after_append=100)
        linked_list.append(new_value1_after_append=100)
        self.assertEqual(linked_list.__len__(), 2)
        self.assertEqual(linked_list[0].value, {"new_value_after_append": 100})
        self.assertEqual(linked_list[-1].value, {"new_value1_after_append": 100})


class TestORMItemQueue(unittest.TestCase):
    def test_init(self):
        ORMItemQueue()
        queue = ORMItemQueue()
        data = [{"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                 "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                 "_primary_key_from_ui": False, "machinename": "Test"},
                {"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                 "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                 "_primary_key_from_ui": False, "machinename": "Name"},
                {"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                 "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                 "_primary_key_from_ui": False, "machinename": "NewTest"
                 }]
        new_queue = ORMItemQueue(data)

    def test_enqueue(self):
        queue = ORMItemQueue()
        data__len_3 = [{"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "Test"},
                       {"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "Test1"},
                       {"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "NewTest"
                        }]
        self.assertIsNone(queue.dequeue())
        self.assertEqual(queue.__len__(), 0)
        with self.assertRaises(IndexError):
            queue.__getitem__(0)
            queue[-1]
            queue[-4]
            queue[2]
            queue[1]
            queue[10]
        with self.assertRaises(StopIteration):
            next(iter(queue))
        queue.enqueue(**data__len_3[0])
        self.assertEqual(len(queue), 1)
        self.assertIsNotNone(queue[0])
        self.assertIsNotNone(queue[-1])
        queue.enqueue(**data__len_3[1])
        self.assertEqual(len(queue), 2)
        self.assertIsNotNone(queue[0])
        self.assertIsNotNone(queue[1])
        self.assertIsNotNone(queue[-1])
        self.assertIsNotNone(queue[-2])
        queue.append(**data__len_3[2])
        self.assertEqual(len(queue), 3)
        self.assertEqual(queue[-1].value["machinename"], "NewTest")
        self.assertEqual(queue[0].value["machinename"], "Test")
        self.assertEqual(queue[1].value["machinename"], "Test1")
        #
        # Столбец machinename с uniqie=True: произойдёт репликация без добавления новой ноды,
        # вместо этого будет замена старой ноды с дополнением её содержимого
        #
        queue = ORMItemQueue()
        data__len_1 = [{"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "Test", "xover": 10},
                       {"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "Test", "yover": 10},
                       {"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "Test", "zover": 10
                        }]
        [queue.enqueue(**data__len_1[i]) for i in range(len(data__len_1))]
        self.assertEqual(queue.__len__(), 1)
        #  Проверить, что новые данные, которые добавлялись за 3 итерации, вошли в результирующую ноду
        self.assertEqual(len(set(queue[0].value).intersection(set({"xover": 10, "yover": 10, "zover": 10}))), 3)
        #
        #  Ситуация, когда первичный ключ был передан явно
        #
        queue = ORMItemQueue()
        data_with_primary_key_from_ui = [{"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                                          "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                                          "_primary_key_from_ui":
                                              {"machineid": 1}, "machinename": "FirstTest", "xover": 10},
                                         {"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                                          "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                                          "_primary_key_from_ui":
                                              {"machineid": 1}, "machinename": "Test", "yover": 10},
                                         {"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                                          "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                                          "_primary_key_from_ui":
                                              {"machineid": 1}, "machinename": "LastName", "zover": 10, "xover": 0,
                                          }]
        [queue.enqueue(**data) for data in data_with_primary_key_from_ui]
        self.assertEqual(queue.__len__(), 1)
        for key, value in {"zover": 10, "xover": 0, "yover": 10, "machinename": "LastName"}.items():
            if key not in queue[0].value:
                assert False
            if not queue[0].value[key] == value:
                assert False

    def test_dequeue(self):
        queue = ORMItemQueue()
        data__len_3 = [{"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "Test"},
                       {"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "Test1"},
                       {"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "NewTest"
                        }]
        with self.assertRaises(IndexError):
            queue[0]
            queue[-1]
            queue[1]
            queue[2]
        [queue.enqueue(**data) for data in data__len_3]
        queue[1]
        queue[0]
        queue[2]
        queue[-1]
        queue[-2]
        self.assertEqual(len(data__len_3), len(queue))
        self.assertEqual(queue.dequeue().value["machinename"], "Test")
        self.assertEqual(2, queue.__len__())
        self.assertEqual(queue.dequeue().value["machinename"], "Test1")
        self.assertEqual(1, queue.__len__())
        self.assertEqual(queue.dequeue().value["machinename"], "NewTest")
        self.assertEqual(0, len(queue))
        with self.assertRaises(IndexError):
            queue[0]
            queue[-1]
            queue[1]
            queue[2]

    def test_remove_node_from_queue(self):
        queue = ORMItemQueue()
        data__len_3 = [{"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "Test"},
                       {"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "Test1"},
                       {"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "NewTest"
                        }]
        [queue.enqueue(**data) for data in data__len_3]
        self.assertEqual(3, len(queue))
        queue[0]
        queue[1]
        queue[2]
        queue[-1]
        queue[-2]
        with self.assertRaises(IndexError):
            queue[-3]
            queue[3]
        queue.remove(Machine, "machineid", 1)
        queue.remove(Machine, "machineid", 2)
        queue.remove(Machine, "machineid", 3)
        self.assertEqual(0, len(queue))


class TestResultORMCollection(unittest.TestCase):
    def setUp(self) -> None:
        queue = ORMItemQueue()
        data__len_3 = [{"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "Test"},
                       {"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "Test1"},
                       {"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "NewTest"
                        }]
        [queue.enqueue(**item) for item in data__len_3]
        self.result_collection = ResultORMCollection(queue)

    def test_result_orm_collection(self):
        self.assertEqual(self.result_collection.__len__(), 3)
        self.assertTrue(self.result_collection)
        hash_val = hash(self.result_collection)
        queue = SpecialOrmContainer()
        changed_data__len_3 = [{"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "Tdfgdfgerest"},
                       {"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "Test1"},
                       {"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "NewTgest"
                        }]
        [queue.enqueue(**item) for item in changed_data__len_3]
        result_queue = ResultORMCollection(queue)
        self.assertEqual(result_queue.__len__(), 3)
        self.assertTrue(result_queue)
        self.assertEqual(3, len(result_queue))
        self.assertNotEqual(hash_val, result_queue.__hash__())

    def test_add_model_prefix(self):
        self.result_collection.add_model_name_prefix()
        self.assertEqual(self.result_collection.prefix, "add")
        self.assertEqual([node for node in self.result_collection
                          for value in node.value if not value.startswith("Machine.")], [])
        self.assertTrue(all([[len(frozenset(filter(lambda x: 1 if x == "." else 0, val)))]
                            for node in self.result_collection
                            for val in node.value]))
        self.result_collection.remove_model_prefix()
        self.assertEqual(self.result_collection.prefix, "no-prefix")
        self.assertEqual([node for node in self.result_collection
                          for column in node.value if column.startswith("Machine.")], [])

    def test_remove_model_prefix(self):
        self.result_collection.add_model_name_prefix()
        self.result_collection.remove_model_prefix()
        self.assertFalse(all([val.startswith("Machine.") if True else False
                              for node in self.result_collection
                              for val in node.value]))

    def test_auto_mode_prefix(self):
        queue = SpecialOrmContainer()
        data__len_3 = [{"_model": Machine, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "machinename": "Test", "cncid": 1},
                       {"_model": Cnc, "_ready": False, "_insert": False, "_update": True,
                        "_delete": False, "_create_at": datetime.datetime.now(), "_container": queue,
                        "_primary_key_from_ui": False, "name": "Testcnc", "cncid": 1}
                       ]
        [queue.enqueue(**n) for n in data__len_3]
        self.result_collection = ResultORMCollection(queue)
        self.assertEqual("auto", self.result_collection.prefix)
        # Столбец cncid встречается в обеих нодах, должно произойти добавление префикса с названием таблицы
        # к одноимённым столбцам обеих нод
        self.assertIn("Machine.cncid", self.result_collection[0].value)



class TestORMHelper(unittest.TestCase, SetUp):
    def setUp(self) -> None:
        ORMHelper.TESTING = True
        ORMHelper.CACHE_LIFETIME_HOURS = 60
        self.orm_manager = ORMHelper

    def test_cache_property(self):
        """ Что вернёт это свойство: Если эклемпляр Client, то OK """
        self.assertIsInstance(self.orm_manager.cache, Client,
                              msg=f"Свойство должно было вернуть эклемпляр класса MockMemcacheClient, "
                                  f"а на деле {self.orm_manager.cache.__class__.__name__}")

    def test_cache(self):
        self.orm_manager.cache.set("1", 1)
        time.sleep(3)
        value = self.orm_manager.cache.get("1")
        self.assertEqual(value, 1, msg="Результирующее значение, полученное из кеша отличается от заданного в тесте")

    def test_not_configured_model(self):
        """ Предварительно не был вызван метод set_model. Неправильная конфигурация"""
        with self.assertRaises(InvalidModel):
            self.orm_manager.get_item(_model=Machine, machinename="test_name")
        with self.assertRaises(InvalidModel):
            self.orm_manager.get_items(_model=Machine)
        with self.assertRaises(InvalidModel):
            self.orm_manager.set_item(_insert=True, _model=Machine, machinename="Heller", _ready=True)

    def test_drop_cache(self):
        self.orm_manager.cache.set("1", "test")
        self.orm_manager.cache.set("3", "test")
        self.orm_manager.drop_cache()
        self.assertIsNone(self.orm_manager.cache.get("1"))
        self.assertIsNone(self.orm_manager.cache.get("3"))

    def test_database_property(self):
        self.assertIsInstance(self.orm_manager.database, Session)

    @db_reinit
    def test_database_insert_and_select_single_entry(self):
        with self.orm_manager.database as session:
            session.add(Machine(machinename="Test", inputcatalog=r"C:\Test", outputcatalog="C:\\TestPath"))
            session.commit()
        self.assertEqual(self.orm_manager.database.execute("SELECT COUNT(machineid) FROM machine").scalar(), 1)
        data = self.orm_manager.database.execute(select(Machine).filter_by(machinename="Test")).scalar().__dict__
        self.assertEqual(data["machinename"], "Test")
        self.assertEqual(data["inputcatalog"], "C:\\Test")
        self.assertEqual(data["outputcatalog"], "C:\\TestPath")

    @db_reinit
    def test_database_insert_and_select_two_joined_entries(self):
        with self.orm_manager.database as session:
            session.add(Cnc(name="testcnc", commentsymbol="*"))
            session.add(Machine(machinename="Test", inputcatalog="C:\\Test", outputcatalog="C:\\TestPath", cncid=1))
            session.commit()
        self.assertEqual(self.orm_manager.database.execute(text("SELECT COUNT(*) "
                                                                "FROM machine "
                                                                "INNER JOIN cnc "
                                                                "ON machine.cncid=cnc.cncid "
                                                                "WHERE machine.machinename='Test' AND cnc.name='testcnc'"
                                                                )
                                                           ).scalar(), 1)
        self.assertEqual(self.orm_manager.database.execute(text("SELECT COUNT(*) "
                                                                "FROM machine "
                                                                "WHERE machine.cncid=(SELECT cncid FROM cnc WHERE name = 'testcnc')"
                                                                )
                                                           ).scalar(), 1)

    @drop_cache
    @db_reinit
    def test_items_property(self):
        self.set_data_into_queue()
        self.assertEqual(self.orm_manager.cache.get("ORMItems"), self.orm_manager.items)
        self.orm_manager.set_item(_insert=True, _model=Cnc, name="Fid")
        self.assertEqual(len(self.orm_manager.items), 11)

    @drop_cache
    @db_reinit
    def test_set_item(self):
        # GOOD
        self.orm_manager.set_item(_insert=True, _model=Cnc, name="Fid", commentsymbol="$")
        self.assertIsNotNone(self.orm_manager.cache.get("ORMItems"))
        self.assertIsInstance(self.orm_manager.cache.get("ORMItems"), ORMItemQueue)
        self.assertEqual(self.orm_manager.cache.get("ORMItems").__len__(), 1)
        self.assertTrue(self.orm_manager.items[0]["name"] == "Fid")
        self.orm_manager.set_item(_insert=True, _model=Machine, machinename="Helller",
                                  inputcatalog=r"C:\\wdfg", outputcatalog=r"D:\\hfghfgh")
        self.assertEqual(len(self.orm_manager.items), 2)
        self.assertEqual(len(self.orm_manager.items), len(self.orm_manager.cache.get("ORMItems")))
        self.assertTrue(any(map(lambda x: x.value.get("machinename", None), self.orm_manager.items)))
        self.assertIs(self.orm_manager.items[1].model, Machine)
        self.assertIs(self.orm_manager.items[0].model, Cnc)
        self.orm_manager.set_item(_model=OperationDelegation, _update=True, operationdescription="text")
        self.assertEqual(self.orm_manager.items[2].value["operationdescription"], "text")
        self.orm_manager.set_item(_insert=True, _model=Condition, findfull=True, parentconditionbooleanvalue=True)
        self.assertEqual(self.orm_manager.items.__len__(), 4)
        self.orm_manager.set_item(_delete=True, machinename="Some_name", _model=Machine)
        self.orm_manager.set_item(_delete=True, machinename="Some_name_2", _model=Machine)
        time.sleep(3)
        result = self.orm_manager.get_items(_model=Machine, machinename="Helller", _db_only=True)
        self.assertTrue(result)
        # start Invalid ...
        # плохой path
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, _insert=True, _model=Machine, input_path="path")  # inputcatalog
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, _insert=True, _model=Machine, output_path="path")  # outputcatalog
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _insert=True, _model=Machine, inputcatalog=4)
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _insert=True, _model=Machine, outputcatalog=7)
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _insert=True, _model=Machine, outputcatalog=None)
        # Invalid model
        self.assertRaises(InvalidModel, self.orm_manager.set_item, machinename="Test", _update=True)  # model = None
        self.assertRaises(InvalidModel, self.orm_manager.set_item, machinename="Test", _insert=True, _model=2)  # model: Type[int]
        self.assertRaises(InvalidModel, self.orm_manager.set_item, machinename="Test", _update=True, _model="test")  # model: Type[str]
        self.assertRaises(InvalidModel, self.orm_manager.set_item, machinename="Test", _insert=True, _model=self.__class__)
        self.assertRaises(InvalidModel, self.orm_manager.set_item, machinename="Heller", _delete=True, _model=None)
        self.assertRaises(InvalidModel, self.orm_manager.set_item, machinename="Heller", _delete=True, _model={1: True})
        self.assertRaises(InvalidModel, self.orm_manager.set_item, machinename="Heller", _delete=True, _model=['some_str'])
        # invalid field
        # field name | такого поля нет в таблице
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, invalid_="testval", _model=Machine, _insert=True)
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, invalid_field="val", other_field=2,
                          other_field_5="name", _model=Cnc, _update=True)  # Поля нету в таблице
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, field="value", _model=OperationDelegation, _delete=True)  # Поля нету в таблице
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, inv="testl", _model=Machine, _insert=True)  # Поля нету в таблице
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, machinename=object(), _model=SearchString, _insert=True)
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, name="123", _model=SearchString, _insert=True)
        # field value | значение не подходит
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _model=Machine, _update=True, machinename=Machine())
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _model=Machine, _update=True, machinename=Cnc())
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _model=Machine, _update=True, machinename=int)
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _model=OperationDelegation, _update=True, operationdescription=lambda x: x)
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _model=OperationDelegation, _update=True, operationdescription=4)
        # не указан тип DML(_insert | _update | _delete) параметр не передан
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Machine, machinename="Helller")
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Machine, machinename="Fid")
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Machine, inputcatalog="C:\\Path")
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Cnc, name="NC21")
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Cnc, name="NC211")
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Cnc, name="NC214")

    @drop_cache
    @db_reinit
    def test_get_items(self):
        self.assertIsInstance(self.orm_manager.get_items(_model=Machine), Result)
        self.assertEqual(self.orm_manager.get_items(_model=Machine).__len__(), 0)
        # Элементы с _delete=True игнорируются в выборке через метод get_items,- согласно замыслу
        # Тем не менее, в очереди они должны присутствовать: см свойство items

        self.orm_manager.set_item(_model=Machine, machinename="Fidia", inputcatalog="C:\\path", _insert=True)
        self.assertEqual(self.orm_manager.get_items(_model=Machine).__len__(), 1)
        self.orm_manager.set_item(_model=Condition, condinner="text", less=True, _insert=True)
        self.orm_manager.set_item(_model=Cnc, name="Fid", cncid=3, commentsymbol="$", _update=True)
        self.assertEqual(self.orm_manager.get_items(_model=Machine).__len__(), 1)
        self.assertEqual(self.orm_manager.get_items(_model=Condition).__len__(), 1)
        self.assertEqual(self.orm_manager.get_items(_model=Cnc).__len__(), 1)
        self.orm_manager.set_item(_model=Machine, machinename="Fidia", inputcatalog="C:\\pathnew", _update=True)

    @drop_cache
    @db_reinit
    def test_join_select(self):
        # Добавить в базу и кеш данные
        self.set_data_into_database()
        self.set_data_into_queue()
        # Возвращает ли метод экземпляр класса JoinSelectResult?
        self.assertIsInstance(self.orm_manager.join_select(Machine, Cnc, on={"Cnc.cncid": "Machine.cncid"}), JoinSelectResult)
        # GOOD (хороший случай)
        # Найдутся ли записи с pk равными значениям, которые мы добавили
        # Machine - Cnc
        result = self.orm_manager.join_select(Machine, Cnc, on={"Machine.cncid": "Cnc.cncid"})
        self.assertEqual("Newcnc", result.items[0]["Cnc"]["name"])
        self.assertEqual("Tesm", result.items[0]["Machine"]["machinename"])
        self.assertEqual("Ram", result.items[1]["Cnc"]["name"])
        self.assertEqual("Fidia", result.items[1]["Machine"]["machinename"])
        self.assertNotEqual(result.items[0]["Cnc"]["cncid"], result.items[1]["Cnc"]["cncid"])
        self.assertEqual(result.items[0]["Cnc"]["cncid"], result.items[0]["Machine"]["cncid"])
        #
        # Numeration - Operationdelegation
        #
        result = self.orm_manager.join_select(OperationDelegation, Numeration,
                                              on={"OperationDelegation.numerationid": "Numeration.numerationid"})
        self.assertEqual("Нумерация. Добавил сразу в БД", result.items[0]["OperationDelegation"]["operationdescription"])
        self.assertNotEqual("Нумерация. Добавил сразу в БД", result.items[1]["OperationDelegation"]["operationdescription"])
        self.assertEqual("Нумерация кадров", result.items[1]["OperationDelegation"]["operationdescription"])
        self.assertEqual(result.items[0]["Numeration"]["numerationid"], 3)
        self.assertEqual(269, result.items[1]["Numeration"]["endat"])
        #
        # Comment - OperationDelegation
        #
        result = self.orm_manager.join_select(Comment, OperationDelegation, on={"Comment.commentid": "OperationDelegation.commentid"})
        self.assertEqual("test_string_set_from_queue", result.items[1]["Comment"]["findstr"])
        self.assertNotEqual("test_string_set_from_queue", result.items[0]["Comment"]["findstr"])
        self.assertEqual("test_str", result.items[0]["Comment"]["findstr"])
        self.assertNotEqual("test_str", result.items[1]["Comment"]["findstr"])
        self.assertEqual(result.items[0]["Comment"]["iffullmatch"], True)
        self.assertNotIn("iffullmatch", result.items[1]["Comment"])
        self.assertEqual(True, result.items[1]["Comment"]["ifcontains"])
        self.assertFalse(result.items[0]["Comment"]["ifcontains"])
        #
        # Отбор только из локальных данных (очереди), но в базе данных их пока что быть не должно
        #
        # Machine - Cnc
        #
        local_data = self.orm_manager.join_select(Machine, Cnc, on={"Machine.cncid": "Cnc.cncid"}, queue_only=True)
        database_data = self.orm_manager.join_select(Cnc, Machine, on={"Cnc.cncid": "Machine.cncid"}, db_only=True)
        self.assertEqual(local_data.items[0]["Machine"]["cncid"], local_data.items[0]["Cnc"]["cncid"])
        self.assertEqual(database_data.items[0]["Cnc"]["cncid"], database_data.items[0]["Machine"]["cncid"])
        self.assertIn("machineid", local_data.items[0]["Machine"])
        self.assertIn("machineid", database_data.items[0]["Machine"])
        self.assertNotEqual(local_data.items[0]["Machine"]["machineid"], database_data.items[0]["Machine"]["machineid"])
        self.assertEqual("Fidia", local_data.items[0]["Machine"]["machinename"])
        self.assertEqual("Ram", local_data.items[0]["Cnc"]["name"])
        self.assertNotEqual(local_data.items[0]["Cnc"]["name"], database_data.items[0]["Cnc"]["name"])
        #
        # Comment - OperationDelegation
        #
        local_data = self.orm_manager.join_select(Comment, OperationDelegation, on={"Comment.commentid": "OperationDelegation.commentid"}, queue_only=True)
        database_data = self.orm_manager.join_select(Comment, OperationDelegation, on={"Comment.commentid": "OperationDelegation.commentid"}, db_only=True)
        self.assertNotEqual(local_data.items[0]["Comment"]["commentid"], database_data.items[0]["Comment"]["commentid"])
        self.assertEqual(local_data.items[0]["Comment"]["commentid"], local_data.items[0]["OperationDelegation"]["commentid"])
        self.assertEqual(database_data.items[0]["Comment"]["commentid"], database_data.items[0]["OperationDelegation"]["commentid"])
        #
        # Плохие аргументы ...
        # invalid model
        #
        self.assertRaises(InvalidModel, self.orm_manager.join_select, "str", Machine, on={"Cnc.cncid": "Machine.cncid"})
        self.assertRaises(InvalidModel, self.orm_manager.join_select, Machine, 5, on={"Cnc.cncid": "Machine.cncid"})
        self.assertRaises(InvalidModel, self.orm_manager.join_select, Machine, "str", on={"Cnc.cncid": "Machine.cncid"})
        self.assertRaises(InvalidModel, self.orm_manager.join_select, "str", object())
        #
        # invalid named on...
        #
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc, on=6)
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on=object())
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc, on=[])
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc, on="[]")
        #
        # Модели, переданные в аргументах (позиционных), не связаны с моделями и полями в именованном аргументе 'on'.
        # join_select(a_model, b_model on={"a_model.column_name": "b_model.column_name"})
        #
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={"InvalidModel.invalid_field": "SomeModel.other_field"})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={"InvalidModel.invalid_field": "SomeModel.other_field"})
        #
        # Именованный параметр on содержит недействительные данные
        #
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={"invalid_field": "SomeModel.other_field"})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={"InvalidModel.invalid_field": "other_field"})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={"Machine.invalid_field": ".other_field"})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={".invalid_field": "SomeModel.other_field"})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={"InvalidModel.invalid_field": "SomeModel."})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={"InvalidModel.": "SomeModel.other_field"})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={"InvalidModel.": "SomeModel."})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={"InvalidModel.invalid_field": "."})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={".": "SomeModel.other_field"})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={"InvalidModel.invalid_field": " "})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={" ": "SomeModel.other_field"})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={"InvalidModel.invalid_field": "-"})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={"InvalidModel.invalid_field": 5})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={"InvalidModel.invalid_field": 2.3})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={2.9: 5})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={4: "Machine.machinename"})

    @drop_cache
    @db_reinit
    def test_single_select__has_changes(self):
        self.set_data_into_database()
        self.set_data_into_queue()
        select_result = self.orm_manager.get_items(Cnc)
        self.assertFalse(select_result.has_changes())
        pk_0_index = select_result.items[0].get_primary_key_and_value()
        pk_1_index = select_result.items[1].get_primary_key_and_value()
        hash_from_cncid1 = hash(select_result.items[0])
        hash_from_cncid2 = hash(select_result.items[1])
        self.orm_manager.set_item(_model=Cnc, **pk_0_index, name="newtestname", _update=True)
        self.assertFalse(select_result.has_changes(hash_from_cncid2))
        self.assertTrue(select_result.has_changes(hash_from_cncid1))
        self.assertFalse(select_result.has_changes(hash_from_cncid1))
        self.orm_manager.set_item(Cnc, name="testname", _update=True, **pk_1_index)
        self.assertTrue(select_result.has_changes())
        self.assertFalse(select_result.has_changes())

    @drop_cache
    @db_reinit
    def test_join_select__has_changes(self):
        """ Метод has_changes класса JoinSelectResult принимает в качестве аргумента хеш-сумму от одного контейнера
        со связанными моделями. """
        self.set_data_into_queue()
        self.set_data_into_database()
        join_select_result = self.orm_manager.join_select(Machine, Cnc, on={"Machine.machineid": "Cnc.cncid"})
        #  Первый запрос has_changes всегда вернёт None
        self.assertIsNone(join_select_result.has_changes(given_unknown_status=True))  # Для всей выборки результатов (не указан хеш)
        invalid_hash = 34535566543  # Совершенно постороннее значение, взятое с потолка
        self.assertIsNone(join_select_result.has_changes(invalid_hash, given_unknown_status=True))  # Для всей выборки результатов (не указан хеш)
        self.update_exists_items()
        self.assertTrue(join_select_result.has_changes())
        self.assertFalse(join_select_result.has_changes())
        self.assertFalse(join_select_result.has_changes())
        val_from_0 = join_select_result.items[0].__hash__()
        val_from_1 = hash(join_select_result.items[1])
        self.orm_manager.set_item(_model=Machine, _update=True, machinename="name", machineid=1)
        self.orm_manager.set_item(_model=Cnc, name="name_n", _update=True, cncid=1)
        self.orm_manager.set_item(_model=Cnc, name="naаке", _update=True, cncid=2)
        self.assertTrue(join_select_result.has_changes(val_from_0))
        self.assertTrue(join_select_result.has_changes(val_from_1))
        invalid_hash_1 = 345352340678  # Совершенно постороннее значение, взятое с потолка
        self.assertRaises(KeyError, join_select_result.has_changes, invalid_hash_1, given_unknown_status=False)  # Для всей выборки результатов (не указан хеш)

    @drop_cache
    @db_reinit
    def test_join_select_pointer_instance(self):
        """ Тестирование Pointer
        Pointer нужен для связывания данных на стороне UI с готовыми инструментами для повторного запроса на эти данные,
        тем самым перекладывая часть рутинной работы с UI на ORM.
        """
        self.set_data_into_database()
        self.set_data_into_queue()
        result = self.orm_manager.join_select(Machine, Cnc, on={"Machine.cncid": "Cnc.cncid"})
        result.pointer = ["Результат в списке 1", "Результат в списке 2"]
        #
        # Тест wrap_items
        #
        self.assertEqual(result.pointer.wrap_items, ["Результат в списке 1", "Результат в списке 2"])
        #
        #  Тестировать refresh
        #
        self.assertFalse(result.pointer.has_changes("Результат в списке 1"))
        self.assertFalse(result.pointer.has_changes("Результат в списке 1"))
        self.assertFalse(result.pointer.has_changes("Результат в списке 2"))
        self.assertFalse(result.pointer.has_changes("Результат в списке 2"))
        self.assertFalse(result.pointer.has_changes("Результат в списке 1"))
        #
        # Добавить изменения и проверить повторно
        self.orm_manager.set_item(cncid=1, name="nameeg", _model=Cnc, _update=True)
        self.orm_manager.set_item(_update=True, _model=Machine, machineid=2, xover=60)
        self.orm_manager.set_item(numerationid=2, endat=4, _model=Numeration, _update=True)
        self.orm_manager.set_item(_model=Comment, commentid=2, findstr="test_str_new", _update=True)
        self.orm_manager.set_item(_model=Machine, machinename="testnamesdfs", machineid=1, _update=True)
        #
        self.assertTrue(result.pointer.has_changes("Результат в списке 2"))
        self.assertIsNone(result.pointer.has_changes("Не установленный во wrapper элемент", given_unknown_status=True))
        self.assertRaises(KeyError, result.pointer.has_changes, "Во wrapper этого не было", given_unknown_status=False)
        self.assertTrue(result.pointer.has_changes("Результат в списке 1"))
        self.assertRaises(PointerException, result.pointer.has_changes, "Не установленный во wrapper элемент", given_unknown_status=False)
        self.assertIsNone(result.pointer.has_changes("Ещё Не установленный во wrapper элемент", given_unknown_status=True))
        self.assertTrue(result.pointer.has_changes("Результат в списке 2"))
        self.assertIsNone(PointerException, result.pointer.has_changes("Другой не установленный во wrapper элемент", given_unknown_status=True))


class TestQueueOrderBy(unittest.TestCase, SetUp):
    def setUp(self) -> None:
        ORMHelper.TESTING = True
        ORMHelper.CACHE_LIFETIME_HOURS = 60
        self.orm_manager = ORMHelper

    @db_reinit
    @drop_cache
    def test_order_by_field__alphabet(self):
        self.set_data_into_database()
        self.set_data_into_queue()
        result = self.orm_manager.get_items(Machine)
        # Передача правильных параметров
        result.order_by(by_create_time=True, alphabet=True)
        result.order_by(by_column_name="machinename", length=True)
        result.order_by(by_primary_key=True, alphabet=True)
        result.order_by(by_create_time=True, decr=True, alphabet=True)
        result.order_by(by_column_name="machinename", decr=True, length=True)
        result.order_by(by_primary_key=True, decr=True, length=True)
        result.order_by(by_create_time=True, decr=False, length=True)
        result.order_by(by_column_name="machinename", decr=False, alphabet=True)
        result.order_by(by_primary_key=True, decr=False, length=True)
        # Передача неправильных параметров
        self.assertRaises(ValueError, result.order_by)
        self.assertRaises(TypeError, result.order_by, by_create_time=4)
        self.assertRaises(TypeError, result.order_by, by_create_time="strf")
        self.assertRaises(ValueError, result.order_by, by_create_time=None)
        self.assertRaises(TypeError, result.order_by, by_create_time=8.9)
        self.assertRaises(TypeError, result.order_by, by_create_time=datetime.datetime.now())
        self.assertRaises(TypeError, result.order_by, by_create_time=b"0x43")
        self.assertRaises(TypeError, result.order_by, by_create_time=0)
        self.assertRaises(TypeError, result.order_by, by_primary_key=4)
        self.assertRaises(TypeError, result.order_by, by_primary_key="strf")
        self.assertRaises(ValueError, result.order_by, by_primary_key=None)
        self.assertRaises(TypeError, result.order_by, by_primary_key=8.9)
        self.assertRaises(TypeError, result.order_by, by_primary_key=datetime.datetime.now())
        self.assertRaises(TypeError, result.order_by, by_primary_key=b"0x43")
        self.assertRaises(TypeError, result.order_by, by_primary_key=0)
        self.assertRaises(TypeError, result.order_by, by_column_name=4)
        self.assertRaises(TypeError, result.order_by, by_column_name=True)
        self.assertRaises(TypeError, result.order_by, by_column_name=False)
        self.assertRaises(ValueError, result.order_by, by_column_name=None)
        self.assertRaises(TypeError, result.order_by, by_column_name=8.9)
        self.assertRaises(TypeError, result.order_by, by_column_name=datetime.datetime.now())
        self.assertRaises(TypeError, result.order_by, by_column_name=b"0x43")
        self.assertRaises(TypeError, result.order_by, by_column_name="machinename", decr=4)
        self.assertRaises(TypeError, result.order_by, by_create_time=True, decr=None)
        self.assertRaises(TypeError, result.order_by, by_primary_key=True, decr=6.8)
        self.assertRaises(TypeError, result.order_by, by_column_name="machinename", decr="teststr")
        self.assertRaises(ValueError, result.order_by, by_column_name="machinename", decr=True)
        self.assertRaises(ValueError, result.order_by, by_column_name="machinename", decr=True, length=True, alphabet=True)
        self.assertRaises((TypeError, ValueError), result.order_by, by_column_name="machinename", decr=True, length="123", alphabet=True)
        self.assertRaises((TypeError, ValueError), result.order_by, by_column_name="machinename", decr=True, length=True, alphabet=3)
        self.assertRaises((TypeError, ValueError), result.order_by, by_column_name="machinename", decr=True, length=True, alphabet=None)
        self.assertRaises((TypeError, ValueError), result.order_by, by_column_name="machinename", decr=True, length=True, alphabet=9.7)
        self.assertRaises((TypeError, ValueError), result.order_by, by_column_name="machinename", decr=True, length=True, alphabet=0)
        self.assertRaises((TypeError, ValueError), result.order_by, by_column_name="machinename", decr=True, length=0, alphabet=0)
        self.assertRaises((TypeError, ValueError), result.order_by, by_column_name="machinename", decr=True, alphabet="123", length=True)
        self.assertRaises((TypeError, ValueError), result.order_by, by_column_name="machinename", decr=True, alphabet=True, length=3)
        self.assertRaises((TypeError, ValueError), result.order_by, by_column_name="machinename", decr=True, alphabet=True, length=None)
        self.assertRaises((TypeError, ValueError), result.order_by, by_column_name="machinename", decr=True, alphabet=True, length=9.7)
        self.assertRaises((TypeError, ValueError), result.order_by, by_column_name="machinename", decr=True, alphabet=True, length=0)
        self.assertRaises((TypeError, ValueError), result.order_by, by_column_name="machinename", decr=True, alphabet=0, length=0)
        self.assertRaises(TypeError, result.order_by, by_column_name="machinename", decr=True, length="123")
        self.assertRaises(TypeError, result.order_by, by_column_name="machinename", decr=True, alphabet=0)
        self.assertRaises(TypeError, result.order_by, by_column_name="machinename", decr=True, alphabet=None)
        self.assertRaises(TypeError, result.order_by, by_column_name="machinename", decr=True, alphabet=6)
        self.assertRaises(TypeError, result.order_by, by_column_name="machinename", decr=True, alphabet=0.7)
        self.assertRaises(TypeError, result.order_by, by_column_name="machinename", decr=True, alphabet=b'')
        self.assertRaises(TypeError, result.order_by, by_column_name="machinename", decr=True, alphabet=b'0x3')
        self.assertRaises(TypeError, result.order_by, by_column_name="machinename", decr=True, alphabet=[])
        self.assertRaises(TypeError, result.order_by, by_column_name="machinename", decr=True, alphabet=tuple())
        self.assertRaises(TypeError, result.order_by, by_column_name="machinename", decr=True, alphabet=object())
        #
        # Проверка соответствия результатов
        #
        # Сортировка по алфавиту  todo
        ...

        # Сортировка по длине строки значения todo

    @drop_cache
    @db_reinit
    def test_order_by_time(self):
        self.set_data_into_database()
        self.set_data_into_queue()
        container = self.orm_manager.items
        container.order_by(Machine, by_create_time=True)
        print(container.search_nodes(Machine))


