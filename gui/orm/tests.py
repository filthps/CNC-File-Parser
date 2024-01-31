import unittest
import time
from sqlalchemy import func, select
from database.models import Machine, Cnc, OperationDelegation, SearchString, db as sqlalchemy_instance
from database.procedures import init_all_triggers
from orm import *


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
            self.orm_manager.get_item(_model=Machine, machine_name="test_name")
        with self.assertRaises(InvalidModel):
            self.orm_manager.get_items(_model=Machine)
        with self.assertRaises(InvalidModel):
            self.orm_manager.set_item(_insert=True, _model=Machine, machine_name="Heller", _ready=True)

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
            session.add(Machine(machine_name="Test", input_catalog="C:\\Test", output_catalog="C:\\TestPath"))
            session.commit()
        self.assertEqual(self.orm_manager.database.execute("SELECT COUNT(machineid) FROM machine").scalar(), 1)
        data = self.orm_manager.database.execute(select(Machine).filter_by(machine_name="Test")).scalar().__dict__
        self.assertEqual(data["machine_name"], "Test")
        self.assertEqual(data["input_catalog"], "C:\\Test")
        self.assertEqual(data["output_catalog"], "C:\\TestPath")

    @db_reinit
    def test_database_insert_and_select_two_joined_entries(self):
        with self.orm_manager.database as session:
            session.add(Cnc(name="testcnc", comment_symbol="*"))
            session.add(Machine(machine_name="Test", input_catalog="C:\\Test", output_catalog="C:\\TestPath", cncid=1))
            session.commit()
        self.assertEqual(self.orm_manager.database.execute("SELECT COUNT(*) "
                                                           "FROM machine "
                                                           "INNER JOIN cnc "
                                                           "ON machine.cncid=cnc.cncid "
                                                           "WHERE machine.machine_name='Test' AND cnc.name='testcnc'"
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
        self.orm_manager.set_item(_insert=True, _model=Machine, machine_name="Helller")
        self.assertEqual(len(self.orm_manager.items), 2)
        self.assertEqual(len(self.orm_manager.items), len(self.orm_manager.cache.get("ORMItems")))
        self.assertTrue(self.orm_manager.items[1]["machine_name"] == "Helller")
        self.assertEqual(self.orm_manager.items[1].model, Machine)
        self.assertEqual(self.orm_manager.items[0].model, Cnc)
        self.orm_manager.set_item(_model=OperationDelegation, _update=True, operation_description="text")
        self.assertEqual(self.orm_manager.items[2].value["operation_description"], "text")
        # start Invalid ...
        # плохой path
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, _insert=True, _model=Machine, input_path="path")  # input_catalog
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, _insert=True, _model=Machine, output_path="path")  # output_catalog
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _insert=True, _model=Machine, input_catalog=4)
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _insert=True, _model=Machine, output_catalog=7)
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _insert=True, _model=Machine, output_catalog="")
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _insert=True, _model=Machine, output_catalog="teststr")
        # Invalid model
        self.assertRaises(InvalidModel, self.orm_manager.set_item, machine_name="Test", _update=True)  # model = None
        self.assertRaises(InvalidModel, self.orm_manager.set_item, machine_name="Test", _insert=True, _model=2)  # model: Type[int]
        self.assertRaises(InvalidModel, self.orm_manager.set_item, machine_name="Test", _update=True, _model="test")  # model: Type[str]
        self.assertRaises(InvalidModel, self.orm_manager.set_item, machine_name="Test", _insert=True, _model=self.__class__)
        self.assertRaises(InvalidModel, self.orm_manager.set_item, machine_name="Heller", _delete=True, _model=None)
        self.assertRaises(InvalidModel, self.orm_manager.set_item, machine_name="Heller", _delete=True, _model={1: True})
        self.assertRaises(InvalidModel, self.orm_manager.set_item, machine_name="Heller", _delete=True, _model=['some_str'])
        # invalid field
        # field name | такого поля нет в таблице
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, invalid_="testval", _model=Machine, _insert=True)
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, invalid_field="val", other_field=2,
                          other_field_5="name", _model=Cnc, _update=True)  # Поля нету в таблице
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, field="value", _model=OperationDelegation, _delete=True)  # Поля нету в таблице
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, inv="testl", _model=Machine, _insert=True)  # Поля нету в таблице
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, machine_name=object(), _model=SearchString, _insert=True)
        self.assertRaises(NodeColumnError, self.orm_manager.set_item, name="123", _model=SearchString, _insert=True)
        # field value | значение не подходит
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _model=Machine, _update=True, machine_name=Machine())
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _model=Machine, _update=True, machine_name=Cnc())
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _model=Machine, _update=True, machine_name=int)
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _model=OperationDelegation, _update=True, operation_description=lambda x: x)
        self.assertRaises(NodeColumnValueError, self.orm_manager.set_item, _model=OperationDelegation, _update=True, operation_description=4)
        # не указан тип DML(_insert | _update | _delete) параметр не передан
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Machine, machine_name="Helller")
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Machine, machine_name="Fid")
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Machine, input_catalog="C:\\Path")
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Cnc, name="NC21")
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Cnc, name="NC211")
        self.assertRaises(NodeDMLTypeError, self.orm_manager.set_item, _model=Cnc, name="NC214")

    @unittest.skip("pass")
    def test_get_item(self):
        pass
