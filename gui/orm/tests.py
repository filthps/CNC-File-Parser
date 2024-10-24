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
        self.orm_manager.set_item(_model=Machine, machineid=2, cncid=2, machinename="Fidia", inputcatalog=r"D:\Heller",
                                  outputcatalog=r"C:\Test", _insert=True)
        self.orm_manager.set_item(_model=Machine, machinename="Tesm", _insert=True)
        self.orm_manager.set_item(_model=Machine, machinename="65A90", _insert=True)
        self.orm_manager.set_item(_model=Machine, machinename="Rambaudi", _insert=True)

    def update_exists_items(self):
        self.orm_manager.set_item(cncid=1, name="name", _model=Cnc, _update=True)
        self.orm_manager.set_item(_update=True, _model=Machine, machineid=2, inputcatalog=r"C:\F")
        self.orm_manager.set_item(numerationid=2, endat=4, _model=Numeration, _update=True)
        self.orm_manager.set_item(_model=Comment, commentid=2, findstr="test_str_new", _update=True)
        self.orm_manager.set_item(_model=Machine, machinename="testname", machineid=1, _insert=True)


class TestORMHelper(unittest.TestCase, SetUp):
    def setUp(self) -> None:
        ORMHelper.TESTING = True
        ORMHelper.CACHE_LIFETIME_HOURS = 60
        self.orm_manager = ORMHelper

    def test_cache_property(self):
        """ Что вернёт это свойство: Если эклемпляр Client, то OK """
        self.assertIsInstance(self.orm_manager.cache, MockMemcacheClient,
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

    def test_items_property(self):
        self.assertTrue(type(self.orm_manager.items) is ORMItemQueue)

    def test_init_timer(self):
        t = self.orm_manager.init_timer()
        self.assertIsInstance(t, threading.Timer)
        self.assertEqual(t.getName(), "ORMHelper(database push queue)")

    @drop_cache
    @db_reinit
    def test_items_property(self):
        self.set_data_into_queue()
        self.assertEqual(self.orm_manager.cache.get("ORMItems", ORMItemQueue()), self.orm_manager.items[0])
        self.orm_manager.set_item(_insert=True, _model=Cnc, name="Fid")
        self.assertEqual(self.orm_manager.cache.get("ORMItems"), self.orm_manager.items[0])
        self.orm_manager.drop_cache()
        self.assertEqual(self.orm_manager.cache.get("ORMItems", ORMItemQueue()), self.orm_manager.items[0])

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
        result = self.orm_manager.get_item(_model=Machine, machinename="Helller", _only_db=True)
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
        self.assertEqual("NC210", result.items[0]["name"])
        self.assertEqual("Heller", result.items[0]["machinename"])
        self.assertEqual("Ram", result.items[1]["name"])
        self.assertEqual("Fidia", result.items[1]["machinename"])
        self.assertNotEqual(result.items[0]["Cnc.cncid"], result.items[1]["Cnc.cncid"])
        self.assertEqual(result.items[0]["Cnc.cncid"], result.items[0]["Machine.cncid"])
        #
        # Numeration - Operationdelegation
        #
        result = self.orm_manager.join_select(OperationDelegation, Numeration,
                                              on={"OperationDelegation.numerationid": "Numeration.numerationid"})
        self.assertEqual("Нумерация. Добавил сразу в БД", result.items[0]["operationdescription"])
        self.assertNotEqual("Нумерация. Добавил сразу в БД", result.items[1]["operationdescription"])
        self.assertEqual("Нумерация кадров", result.items[1]["operationdescription"])
        self.assertEqual(result.items[0]["Numeration.numerationid"], 3)
        self.assertEqual(269, result.items[1]["endat"])
        #
        # Comment - OperationDelegation
        #
        result = self.orm_manager.join_select(Comment, OperationDelegation, on={"Comment.commentid": "OperationDelegation.commentid"})
        self.assertEqual("test_string_set_from_queue", result.items[1]["findstr"])
        self.assertNotEqual("test_string_set_from_queue", result.items[0]["findstr"])
        self.assertEqual("test_str", result.items[0]["findstr"])
        self.assertNotEqual("test_str", result.items[1]["findstr"])
        self.assertEqual(result.items[0]["iffullmatch"], True)
        self.assertNotIn("iffullmatch", result.items[1])
        self.assertEqual(True, result.items[1]["ifcontains"])
        self.assertFalse(result.items[0]["ifcontains"])
        #
        # Отбор только из локальных данных (очереди), но в базе данных их пока что быть не должно
        #
        # Machine - Cnc
        #
        local_data = self.orm_manager.join_select(Machine, Cnc, on={"Machine.cncid": "Cnc.cncid"}, _queue_only=True)
        database_data = self.orm_manager.join_select(Cnc, Machine, on={"Cnc.cncid": "Machine.cncid"}, _db_only=True)
        self.assertEqual(local_data.items[0]["Machine.cncid"], local_data.items[0]["Cnc.cncid"])
        self.assertEqual(database_data.items[0]["Cnc.cncid"], database_data.items[0]["Machine.cncid"])
        self.assertIn("machineid", local_data.items[0])
        self.assertIn("machineid", database_data.items[0])
        self.assertNotEqual(local_data.items[0]["machineid"], database_data.items[0]["machineid"])
        self.assertEqual("Fidia", local_data.items[0]["machinename"])
        self.assertEqual("Ram", local_data.items[0]["name"])
        self.assertNotEqual(local_data.items[0]["name"], database_data.items[0]["name"])
        #
        # Comment - OperationDelegation
        #
        local_data = self.orm_manager.join_select(Comment, OperationDelegation, on={"Comment.commentid": "OperationDelegation.commentid"}, _queue_only=True)
        database_data = self.orm_manager.join_select(Comment, OperationDelegation, on={"Comment.commentid": "OperationDelegation.commentid"}, _db_only=True)
        self.assertNotEqual(local_data.items[0]["Comment.commentid"], database_data.items[0]["Comment.commentid"])
        self.assertEqual(local_data.items[0]["Comment.commentid"], local_data.items[0]["OperationDelegation.commentid"])
        self.assertEqual(database_data.items[0]["Comment.commentid"], database_data.items[0]["OperationDelegation.commentid"])
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
    def test_join_select__has_changes(self):
        """ Метод has_changes класса JoinSelectResult принимает в качестве аргумента хеш-сумму от одного контейнера
        со связанными моделями. """
        self.set_data_into_queue()
        self.set_data_into_database()
        join_select_result = self.orm_manager.join_select(Machine, Cnc, on={"Machine.machineid": "Cnc.cncid"})
        self.assertFalse(join_select_result.has_changes())  # Для всей выборки результатов
        self.update_exists_items()
        self.assertTrue(join_select_result.has_changes())  # Для всей выборки результатов

    @drop_cache
    @db_reinit
    def test_pointer_instance(self):
        """ Тестирование Pointer
        Pointer нужен для связывания данных на стороне UI с готовыми инструментами для повторного запроса на эти данные,
        тем самым перекладывая часть рутинной работы с UI на ORM.
        """
        self.set_data_into_database()
        self.set_data_into_queue()
        result = self.orm_manager.join_select(Machine, Cnc, on={"Machine.cncid": "Cnc.cncid"})
        wrapper = ["Результат в списке 1", "Результат в списке 2"]
        result.pointer = wrapper
        #
        # Тест wrap_items
        #
        self.assertEqual(result.pointer.wrap_items, ["Результат в списке 1", "Результат в списке 2"])
        #
        #  Тестировать refresh
        #
        self.assertFalse(result.pointer.has_changes("Результат в списке 1"))
        self.assertFalse(result.pointer.has_changes("Результат в списке 2"))
        self.assertFalse(result.pointer.has_changes("Результат в списке 2"))
        self.assertFalse(result.pointer.has_changes("Результат в списке 1"))
        #
        # Добавить изменения и проверить повторно
        self.update_exists_items()
        #
        self.assertTrue(result.pointer.has_changes("Результат в списке 2"))
        self.assertTrue(result.pointer.has_changes("Результат в списке 1"))

    @db_reinit
    def test_someone(self):
        self.assertEqual(1, 1)


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


