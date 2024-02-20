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
import time
from sqlalchemy import func, select
from database.models import Machine, Cnc, OperationDelegation, SearchString, db as sqlalchemy_instance, Condition, \
    Numeration, Comment
from database.procedures import init_all_triggers
from orm import *


DEBUG = True


def is_database_empty(session, empty=True, tables=15, procedures=52, test_db_name="testdb"):
    table_counter = session.execute('SELECT COUNT(table_name) '
                                    'FROM information_schema."tables" '
                                    'WHERE table_type=\'BASE TABLE\' AND table_schema=\'public\';').scalar()
    procedures_counter = session.execute(f'SELECT COUNT(*) '
                                         f'FROM information_schema."triggers" '
                                         f'WHERE trigger_schema=\'public\' AND '
                                         f'trigger_catalog=\'{test_db_name}\' AND '
                                         f'event_object_catalog=\'{test_db_name}\';').scalar()
    if empty:
        if table_counter or procedures_counter:
            time.sleep(1)
            return is_database_empty(session, empty=empty, tables=tables, procedures=procedures,
                                     test_db_name=test_db_name)
        return True
    if table_counter < tables or procedures_counter < procedures:
        time.sleep(1)
        return is_database_empty(session, empty=empty, tables=tables, procedures=procedures,
                                 test_db_name=test_db_name)
    return True


def db_reinit(m):
    def wrap(self: "TestORMHelper"):
        sqlalchemy_instance.drop_all()
        if is_database_empty(self.orm_manager.database):
            sqlalchemy_instance.create_all()
            init_all_triggers()
            if is_database_empty(self.orm_manager.database, empty=False):
                return m(self)
    return wrap


def drop_cache(callable_):
    def w(self: "TestORMHelper"):
        self.orm_manager.drop_cache()
        return callable_(self)
    return w


class TestORMHelper(unittest.TestCase):
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
            session.add(Machine(machinename="Test", input_catalog=r"C:\Test", output_catalog="C:\\TestPath"))
            session.commit()
        self.assertEqual(self.orm_manager.database.execute("SELECT COUNT(machineid) FROM machine").scalar(), 1)
        data = self.orm_manager.database.execute(select(Machine).filter_by(machinename="Test")).scalar().__dict__
        self.assertEqual(data["machinename"], "Test")
        self.assertEqual(data["input_catalog"], "C:\\Test")
        self.assertEqual(data["output_catalog"], "C:\\TestPath")

    @db_reinit
    def test_database_insert_and_select_two_joined_entries(self):
        with self.orm_manager.database as session:
            session.add(Cnc(name="testcnc", commentsymbol="*"))
            session.add(Machine(machinename="Test", input_catalog="C:\\Test", output_catalog="C:\\TestPath", cncid=1))
            session.commit()
        self.assertEqual(self.orm_manager.database.execute("SELECT COUNT(*) "
                                                           "FROM machine "
                                                           "INNER JOIN cnc "
                                                           "ON machine.cncid=cnc.cncid "
                                                           "WHERE machine.machinename='Test' AND cnc.name='testcnc'"
                                                           ).scalar(), 1)
        self.assertEqual(self.orm_manager.database.execute("SELECT COUNT(*) "
                                                           "FROM machine "
                                                           "WHERE machine.cncid=(SELECT cncid FROM cnc WHERE name = 'testcnc')"
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
        self.assertEqual(self.orm_manager.cache.get("ORMItems", ORMItemQueue()), self.orm_manager.items)
        self.orm_manager.set_item(_insert=True, _model=Cnc, name="Fid")
        self.assertEqual(self.orm_manager.cache.get("ORMItems"), self.orm_manager.items)
        self.orm_manager.drop_cache()
        self.assertEqual(self.orm_manager.cache.get("ORMItems", ORMItemQueue()), self.orm_manager.items)

    @drop_cache
    @db_reinit
    def test_set_item(self):
        # GOOD
        self.orm_manager.set_item(_insert=True, _model=Cnc, name="Fid")
        self.assertIsNotNone(self.orm_manager.cache.get("ORMItems"))
        self.assertIsInstance(self.orm_manager.cache.get("ORMItems"), ORMItemQueue)
        self.assertEqual(self.orm_manager.cache.get("ORMItems").__len__(), 1)
        self.assertTrue(self.orm_manager.items[0]["name"] == "Fid")
        self.orm_manager.set_item(_insert=True, _model=Machine, machinename="Helller")
        self.assertEqual(len(self.orm_manager.items), 2)
        self.assertEqual(len(self.orm_manager.items), len(self.orm_manager.cache.get("ORMItems")))
        self.assertTrue(self.orm_manager.items[1]["machinename"] == "Helller")
        self.assertEqual(self.orm_manager.items[1].model, Machine)
        self.assertEqual(self.orm_manager.items[0].model, Cnc)
        self.orm_manager.set_item(_model=OperationDelegation, _update=True, operation_description="text")
        self.assertEqual(self.orm_manager.items[2].value["operation_description"], "text")
        self.orm_manager.set_item(_insert=True, _model=Condition, findfull=True, parentconditionbooleanvalue=True)
        self.assertEqual(self.orm_manager.items.__len__(), 4)
        self.orm_manager.set_item(_delete=True, machinename="Some_name", _model=Machine)
        self.orm_manager.set_item(_delete=True, machinename="Some_name_2", _model=Machine)
        self.assertEqual(len(self.orm_manager.items), 6)
        # start Invalid ...
        # плохой path
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, _insert=True, _model=Machine, input_path="path")  # input_catalog
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, _insert=True, _model=Machine, output_path="path")  # output_catalog
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _insert=True, _model=Machine, input_catalog=4)
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _insert=True, _model=Machine, output_catalog=7)
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _insert=True, _model=Machine, output_catalog=None)
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
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _model=OperationDelegation, _update=True, operation_description=lambda x: x)
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _model=OperationDelegation, _update=True, operation_description=4)
        # не указан тип DML(_insert | _update | _delete) параметр не передан
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Machine, machinename="Helller")
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Machine, machinename="Fid")
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Machine, input_catalog="C:\\Path")
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Cnc, name="NC21")
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Cnc, name="NC211")
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Cnc, name="NC214")

    @drop_cache
    @db_reinit
    def test_get_item(self):
        # Invalid model
        self.assertRaises(InvalidModel, self.orm_manager.get_item, _model=1)
        self.assertRaises(InvalidModel, self.orm_manager.get_item, _model=object())
        self.assertRaises(InvalidModel, self.orm_manager.get_item, _model=0)
        self.assertRaises(InvalidModel, self.orm_manager.get_item, _model=sqlalchemy_instance.Model)
        self.assertRaises(InvalidModel, self.orm_manager.get_item, _model="123")
        self.assertRaises(InvalidModel, self.orm_manager.get_item)
        self.assertRaises(InvalidModel, self.orm_manager.get_item, _model=None)
        # GOOD
        self.orm_manager.set_item(_insert=True, _model=Cnc, name="Fid")
        self.orm_manager.set_item(_insert=True, _model=Machine, machinename="Rambaudi")
        self.assertEqual(len(self.orm_manager.get_item(_model=Cnc, name="Fid")), 1)
        self.assertEqual(self.orm_manager.get_item(_model=Cnc, name="Fid")["name"], "Fid")
        # test only_db & only_queue

    @drop_cache
    @db_reinit
    def test_get_items(self):
        self.orm_manager.set_item(_model=Machine, machinename="Heller", _delete=True)
        self.assertEqual(list(self.orm_manager.get_items(_model=Machine)).__len__(), 0)
        self.assertFalse(list(self.orm_manager.get_items(_model=Machine)))
        # Элементы с _delete=True игнорируются в выборке через метод get_items,- согласно замыслу
        # Тем не менее, в очереди они должны присутствовать: см свойство items
        self.orm_manager.set_item(_model=Machine, machinename="Fidia", input_catalog="C:\\path", _insert=True)
        self.assertEqual(list(self.orm_manager.get_items(_model=Machine)).__len__(), 1)
        self.orm_manager.set_item(_model=Condition, condinner="text", less=True, _insert=True)
        self.orm_manager.set_item(_model=Cnc, name="Fid", commentsymbol="$", _update=True)
        self.assertEqual(list(self.orm_manager.get_items(_model=Machine)).__len__(), 1)
        self.assertEqual(list(self.orm_manager.get_items(_model=Condition)).__len__(), 1)
        self.assertEqual(list(self.orm_manager.get_items(_model=Cnc)).__len__(), 1)

    @drop_cache
    @db_reinit
    def test_join_select(self):
        # Добавить в базу и кеш данные
        def set_data_into_database():
            self.orm_manager.database.add(Cnc(name="NC210", commentsymbol=","))
            self.orm_manager.database.add(Numeration())
            self.orm_manager.database.add(Comment(findstr="test_str", iffullmatch=True))
            self.orm_manager.database.commit()
            self.orm_manager.database.add(Machine(machinename="Heller",
                                                  cncid=self.orm_manager.database.scalar(select(Cnc).where(Cnc.name == "NC210")).cncid,
                                                  inputcatalog=r"C:\Windows",
                                                  outputcatalog=r"X:\path"))
            self.orm_manager.database.add(OperationDelegation(
                numerationid=self.orm_manager.database.scalar(select(Numeration)).numerationid)
            )
            self.orm_manager.database.add(OperationDelegation(commentid=self.orm_manager.database.scalar(select(Comment)).commentid))
            self.orm_manager.database.commit()

        def set_data_into_queue():
            items = ORMItemQueue()
            items.enqueue(_model=Numeration, numerationid=2, endat=269, _insert=True, _container=items)
            items.enqueue(_insert=True, _model=OperationDelegation, numerationid=2, _container=items)
            items.enqueue(_model=Comment, findstr="test_string", ifcontains=True, _insert=True, commentid=2,
                          _container=items)
            items.enqueue(_model=OperationDelegation, commentid=2, _container=items, _insert=True)
            items.enqueue(_model=Cnc, _insert=True, cncid=2, name="Ram", commentsymbol="#", _container=items)
            items.enqueue(_model=Machine, machineid=2, cncid=2, machinename="Fidia", inputcatalog=r"D:\Heller",
                          outputcatalog=r"C:\Test", _container=items, _insert=True)
            self.orm_manager.cache.set("ORMItems", items, ORMHelper.CACHE_LIFETIME_HOURS)
        set_data_into_queue()
        set_data_into_database()
        # Возвращает ли метод экземпляр класса JoinSelectResult?
        self.assertIsInstance(self.orm_manager.join_select(Machine, Cnc, on={"Cnc.cncid": "Machine.cncid"}), JoinSelectResult)
        # GOOD
        # Найдутся ли записи с pk равными значениям, которые мы добавили
        # Локальные данные
        result = self.orm_manager.join_select(Machine, Cnc, on={"Machine.cncid": "Cnc.cncid"})
        self.assertTrue("cncid" in result.items and result.items["cncid"] == 2)
        self.assertTrue("machineid" in result.items and result.items["machineid"] == 2)
        self.assertEqual("Ram", result.items["name"])
        result_case_numeration = self.orm_manager.join_select(OperationDelegation, Numeration,
                                              on={"OperationDelegation.numerationid": "Numeration.numerationid"})
        self.assertIn("endat", result_case_numeration.items)
        self.assertTrue(result_case_numeration.items["endat"] == 269)
        self.assertTrue(result_case_numeration.items["numerationid"] == 2)
        #
        result_case_comment = self.orm_manager.join_select(Comment, OperationDelegation, on={"Comment.commentid": "OperationDelegation.commentid"})
        self.assertFalse(result_case_numeration.items["opid"] == result_case_comment.items["opid"])
        #self.assertEqual()
        # Отбор только из локальных данных (очереди)
        ...  # todo
        # Отбор только из базы данных
        ...  # todo
        # Плохие аргументы ...
        # invalid model
        self.assertRaises(InvalidModel, self.orm_manager.join_select, "str", Machine, on={"Cnc.cncid": "Machine.cncid"})
        self.assertRaises(InvalidModel, self.orm_manager.join_select, Machine, 5, on={"Cnc.cncid": "Machine.cncid"})
        self.assertRaises(InvalidModel, self.orm_manager.join_select, Machine, "str", on={"Cnc.cncid": "Machine.cncid"})
        self.assertRaises(InvalidModel, self.orm_manager.join_select, "str", object())
        # invalid named on...
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc, on=6)
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on=object())
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc, on=[])
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc, on="[]")
        # Модели, переданные в аргументах (позиционных), не связаны с моделями и полями в именованном аргументе 'on'.
        # join_select(a_model, b_model on={"a_model.column_name": "b_model.column_name"})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={"InvalidModel.invalid_field": "SomeModel.other_field"})
        self.assertRaises((AttributeError, TypeError, ValueError,), self.orm_manager.join_select, Machine, Cnc,
                          on={"InvalidModel.invalid_field": "SomeModel.other_field"})
        # Именованный параметр on содержит недействительные данные
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
