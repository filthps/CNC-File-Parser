import unittest
import time
from sqlalchemy import func, select
from database.models import Machine, Cnc, db as sqlalchemy_instance
from orm import *
from exceptions import *


def db_reinit(m):
    def wrap(*args, **kwargs):
        sqlalchemy_instance.drop_all()
        sqlalchemy_instance.create_all()
        return m(*args, **kwargs)
    return wrap


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
