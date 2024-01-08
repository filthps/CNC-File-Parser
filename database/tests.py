""" Тесты рассчитаны под PostreSQL диалект! """
import time
import unittest
from typing import Type, Union
from sqlalchemy.engine import create_engine
from sqlalchemy.sql import select
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.exc import InternalError, IntegrityError, PendingRollbackError, NoResultFound
from database.procedures import init_all_triggers
from .models import db, Cnc, Machine, Comment, Insert, Uncomment, Rename, Condition, Replace, Numeration, Remove, \
    OperationDelegation, HeadVarible, HeadVarDelegation, TaskDelegation, ModelController, DATABASE_PATH_FOR_TESTS


TRANSACTION_ISOLATION_LEVEL = "SERIALIZABLE"  # https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#setting-transaction-isolation-levels-dbapi-autocommit


def is_database_empty(s_factory: sessionmaker, is_empty=True, test_database_name="testdb", tables_count=15,
                      procedures_count=52) -> bool:
    time.sleep(1)  # Параллелизм будет?! На всякий случай подожду, если СУБД не успеет
    session = s_factory()
    exists_tables_counter = session.execute('SELECT COUNT(table_name) '
                                            'FROM information_schema."tables" '
                                            'WHERE table_type=\'BASE TABLE\' AND table_schema=\'public\';').scalar()
    exists_procedures_counter = session.execute(f'SELECT COUNT(*) '
                                                f'FROM information_schema."triggers" '
                                                f'WHERE trigger_schema=\'public\' AND '
                                                f'trigger_catalog=\'{test_database_name}\' AND '
                                                f'event_object_catalog=\'{test_database_name}\';').scalar()
    print(f"Тбалицы {exists_tables_counter}", f"Хранимые процедуры {exists_procedures_counter}")
    if is_empty:
        if exists_tables_counter or exists_procedures_counter:
            return is_database_empty(s_factory)
    if not is_empty:
        if tables_count != exists_tables_counter or exists_procedures_counter != procedures_count:
            return is_database_empty(s_factory, is_empty=is_empty, tables_count=tables_count,
                                     test_database_name=test_database_name, procedures_count=procedures_count)
    return True


def truncate_all(f):
    def w(self: "TestCncModel"):
        db.drop_all()
        if is_database_empty(self.session_factory):
            db.create_all()
            init_all_triggers()
            if is_database_empty(self.session_factory, is_empty=False):
                return f(self)
    return w


class TestCncModel(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(DATABASE_PATH_FOR_TESTS, isolation_level=TRANSACTION_ISOLATION_LEVEL)
        self.session_factory = sessionmaker(bind=self.engine)

    @staticmethod
    def is_obj_in_session(session, model_instance: Type[Union[ModelController, db.Model]]):
        for obj in session:
            if obj == model_instance:
                return True
        return False

    def test_create_valid_orm_cnc_object(self):
        valid_orm_obj = Cnc(name="Fidia", comment_symbol=",")
        self.assertIsInstance(valid_orm_obj, ModelController)
        self.assertIsInstance(valid_orm_obj, db.Model)

    @truncate_all
    def test_save_valid_instance(self):
        session = self.session_factory()
        valid_orm_obj = Cnc(name="Fidia", comment_symbol=",")
        session.add(valid_orm_obj)
        self.assertTrue(self.is_obj_in_session(session, valid_orm_obj), msg="Объект не добавился в сессию")
        session.commit()

    def test_exists_new_instance(self):
        self.assertEqual(self.session_factory().execute("SELECT COUNT(*) "
                                                        "FROM cnc "
                                                        "WHERE name='Fidia'").scalar(), 1)

    def test_update_cnc_instance(self):
        session = self.session_factory()
        original_instance = session.scalars(select(Cnc).where(Cnc.name == "Fidia")).one()
        setattr(original_instance, "except_symbols", "/")
        setattr(original_instance, "name", "Testname")
        session.add()

    @truncate_all
    def test_save_invalid__case_empty_name(self):
        invalid_orm_obj = Cnc(name="", comment_symbol=",")
        session = self.session_factory()
        session.add(invalid_orm_obj)
        with self.assertRaises(IntegrityError):
            session.commit()

    @truncate_all
    def test_save_invalid__case_empty_comment_symbol(self):
        session = self.session_factory()
        invalid_orm_obj = Cnc(name="Ram", comment_symbol="")
        session.add(invalid_orm_obj)
        with self.assertRaises(IntegrityError):
            session.commit()

    @truncate_all
    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        session = self.session_factory()
        valid_orm_obj = Cnc(name="NC200", comment_symbol=",")
        session.add(valid_orm_obj)
        session.commit()
        other_valid_same_object = Cnc(name="NC200", comment_symbol=",")
        session.add(other_valid_same_object)
        with self.assertRaises(PendingRollbackError):
            try:
                session.commit()
            except InternalError:
                session.rollback()
                raise PendingRollbackError
        self.assertEqual(session.execute("SELECT COUNT(name) "
                                         "FROM cnc "
                                         "WHERE name='NC200'").scalar(), 1)
        self.assertEqual(session.scalars(select(Cnc).where(Cnc.name == "NC200")).all().__len__(), 1)


class TestModelMachine(unittest.TestCase):
    """
    Запускать тесты по одному
    """
    def setUp(self) -> None:
        self.engine = create_engine(DATABASE_PATH_FOR_TESTS, isolation_level=TRANSACTION_ISOLATION_LEVEL)
        self.session_factory = sessionmaker(bind=self.engine)

    @staticmethod
    def is_obj_in_session(session, model_instance: Type[Union[ModelController, db.Model]]):
        for obj in session:
            if obj == model_instance:
                return True
        return False

    @staticmethod
    def get_or_create_cnc(session, name="NC210"):
        instance = session.scalars(select(Cnc).where(Cnc.name == name)).all()
        if not instance:
            obj = Cnc(name="NC210", comment_symbol="/")
            session.add(obj)
            session.commit()
            instance = session.scalars(select(Cnc).where(Cnc.name == name)).one()
            return instance
        return instance[0]

    def test_create_valid_orm_machine_object(self):
        valid_orm_obj = Machine(machine_name="Heller",
                                input_catalog="C://Heller", output_catalog="D://Heller")
        self.assertIsInstance(valid_orm_obj, db.Model)
        self.assertIsInstance(valid_orm_obj, ModelController)

    @truncate_all
    def test_save_valid_instance(self):
        session = self.session_factory()
        cnc_instance = self.get_or_create_cnc(session)
        valid_orm_obj = Machine(cncid=cnc_instance.cncid, machine_name="Heller",
                                input_catalog="C://Heller", output_catalog="D://Heller")
        session.add(valid_orm_obj)
        self.assertTrue(self.is_obj_in_session(session, valid_orm_obj), msg="Объект не добавился в сессию")
        session.commit()

    def test_exists_new_instance(self):
        session = self.session_factory()
        result_obj = session.scalars(select(Machine).where(Machine.machine_name == "Heller"))
        try:
            result_obj.one()
        except NoResultFound:
            assert False
        self.assertEqual(len(session.scalars(select(Machine).where(Machine.machine_name == "Heller")).all()), 1)

    @truncate_all
    def test_update_machine_instance(self):
        session = self.session_factory()
        cnc_instance = self.get_or_create_cnc(session)
        valid_orm_obj = Machine(cncid=cnc_instance.cncid, machine_name="Heller",
                                x_over=4000,
                                input_catalog="C://Heller", output_catalog="D://Heller")
        session.add(valid_orm_obj)
        self.assertTrue(self.is_obj_in_session(session, valid_orm_obj), msg="Объект не добавился в сессию")
        session.commit()
        saved_instance = session.scalars(select(Machine).where(Machine.machine_name == "Heller")).all()
        if not saved_instance:
            assert "Запись не сохранилась"
        instance = saved_instance.pop()
        if saved_instance:
            assert "Больше одного уникального результата"
        setattr(instance, "x_over", 200)
        setattr(instance, "y_over", 200)
        setattr(instance, "machine_name", "Other")
        session.add(instance)
        self.assertTrue(self.is_obj_in_session(session, instance), msg="Объект не добавился в сессию")
        session.commit()
        updated_instance = session.scalars(select(Machine).where(Machine.machine_name == "Other")).all()
        self.assertEqual(len(updated_instance), 1)

    @truncate_all
    def test_bad_machine_mame(self):
        session = self.session_factory()
        invalid_obj = Machine(machine_name="Bad name with spaces", input_catalog="C://Heller",
                              output_catalog="D://Heller")
        session.add(invalid_obj)
        self.assertTrue(self.is_obj_in_session(session, invalid_obj))
        with self.assertRaises(PendingRollbackError):
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                raise PendingRollbackError
        self.assertFalse(session.scalars(select(Machine).where(Machine.machine_name == "Bad name with spaces")).all())

    def test_save_invalid_instance___case_empty_input_catalog_value(self):
        session = self.session_factory()
        cnc_instance = self.get_or_create_cnc(session)
        invalid_orm_obj = Machine(cncid=cnc_instance.cncid, machine_name="Heller",
                                  input_catalog="", output_catalog="D://Heller")
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((PendingRollbackError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance___case_empty_output_catalog_value(self):
        session = self.session_factory()
        cnc_instance = self.get_or_create_cnc(session)
        invalid_orm_obj = Machine(cncid=cnc_instance.cncid, machine_name="Heller",
                                  input_catalog="C://Heller", output_catalog="")
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((PendingRollbackError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__case_empty_machine_name_value(self):
        session = self.session_factory()
        cnc_instance = self.get_or_create_cnc(session)
        invalid_orm_obj = Machine(cncid=cnc_instance.cncid, machine_name="",
                                  input_catalog="C://Heller", output_catalog="D://Heller")
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((PendingRollbackError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        session = self.session_factory()
        cnc_instance = self.get_or_create_cnc(session)
        valid_orm_obj = Machine(cncid=cnc_instance.cncid, machine_name="Heller",
                                input_catalog="C://Heller", output_catalog="D://Heller")
        session.add(valid_orm_obj)
        session.commit()
        time.sleep(1)
        other_valid_same_object = Machine(cncid=cnc_instance.cncid, machine_name="Heller",
                                          input_catalog="C://Heller", output_catalog="D://Heller")
        session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()


class TestModelComment(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(DATABASE_PATH_FOR_TESTS, isolation_level=TRANSACTION_ISOLATION_LEVEL)
        self.session_factory = sessionmaker(bind=self.engine)

    def test_create_valid_orm_object(self):
        valid_orm_obj = Comment(findstr="r", iffullmatch=False, ifcontains=True)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Comment(findstr="r", iffullmatch=False, ifcontains=True)
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        session.commit()

    def test_save_invalid_instance___case_multi_value(self):
        invalid_orm_obj = Comment(findstr="r", iffullmatch=True, ifcontains=True)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__case_empty_value(self):
        invalid_orm_obj = Comment(findstr="r", iffullmatch=False, ifcontains=False)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__case_empty_findstr(self):
        invalid_orm_obj = Comment(findstr="", iffullmatch=True, ifcontains=False)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Comment(findstr="", iffullmatch=True, ifcontains=False)
        session.add(valid_orm_obj)
        session.commit()
        time.sleep(1)
        other_valid_same_object = Comment(findstr="", iffullmatch=True, ifcontains=False)
        session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()


class TestModelUncomment(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(DATABASE_PATH_FOR_TESTS, isolation_level=TRANSACTION_ISOLATION_LEVEL)
        self.session_factory = sessionmaker(bind=self.engine)

    def test_create_valid_orm_object(self):
        valid_orm_obj = Uncomment(findstr="r", iffullmatch=False, ifcontains=True)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Uncomment(findstr="r", iffullmatch=False, ifcontains=True)
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        session.commit()

    def test_save_invalid_instance___case_multi_value(self):
        invalid_orm_obj = Uncomment(findstr="r", iffullmatch=True, ifcontains=True)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__case_empty_value(self):
        invalid_orm_obj = Uncomment(findstr="r", iffullmatch=False, ifcontains=False)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__case_empty_findstr(self):
        invalid_orm_obj = Uncomment(findstr="", iffullmatch=True, ifcontains=False)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Uncomment(findstr="", iffullmatch=True, ifcontains=False)
        session.add(valid_orm_obj)
        session.commit()
        time.sleep(1)
        other_valid_same_object = Uncomment(findstr="", iffullmatch=True, ifcontains=False)
        session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()


class TestModelRename(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(DATABASE_PATH_FOR_TESTS, isolation_level=TRANSACTION_ISOLATION_LEVEL)
        self.session_factory = sessionmaker(bind=self.engine)

    def test_create_valid_orm_rename_object(self):
        valid_orm_obj = Rename(uppercase=True, lowercase=False,
                               prefix="", postfix="", nametext="", removeextension=False, setextension=None)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Rename(uppercase=True, lowercase=False,
                               prefix="valid", postfix=None, nametext=None, removeextension=False, setextension=None)
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        session.commit()

    def test_save_invalid_instance___case_multi_value(self):
        """
        uppercase=True, lowercase=True
        """
        invalid_orm_obj = Rename(uppercase=True, lowercase=True,
                                 prefix="invalid", postfix=None, nametext=None, removeextension=False, setextension=None)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__case_empty_value(self):
        invalid_orm_obj = Rename(uppercase=False, lowercase=False,
                                 prefix=None, postfix=None, nametext=None, removeextension=False,
                                 setextension=None)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Rename(uppercase=True, prefix="valid")
        session.add(valid_orm_obj)
        session.commit()
        time.sleep(1)
        other_valid_same_object = Rename(uppercase=True, prefix="valid")
        session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()


class TestModelCondition(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(DATABASE_PATH_FOR_TESTS, isolation_level=TRANSACTION_ISOLATION_LEVEL)
        self.session_factory = sessionmaker(bind=self.engine)

    def test_create_valid_orm_condition_object(self):
        valid_orm_obj = Condition(targetstr="xyz", isntfind=True)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Condition(targetstr="xyz", isntfind=True)
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Condition(targetstr="zyx", isntfind=True)
        session.add(valid_orm_obj)
        session.commit()
        time.sleep(1)
        other_valid_same_object = Condition(targetstr="zyx", isntfind=True)
        session.add(other_valid_same_object)
        with self.assertRaises((IntegrityError, InternalError,)):
            session.commit()

    def test_save_invalid_instance___case_multi_value(self):
        invalid_orm_obj = Condition(targetstr="f23", isntfind=True, findfull=True)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance___case_empty_options(self):
        invalid_orm_obj = Condition(targetstr="f23")
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance___case_empty_targetstr(self):
        invalid_orm_obj = Condition(isntfind=True, targetstr="")
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance___case_null_targetstr(self):
        invalid_orm_obj = Condition(isntfind=True, targetstr=None)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()


class TestModelInsert(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(DATABASE_PATH_FOR_TESTS, isolation_level=TRANSACTION_ISOLATION_LEVEL)
        self.session_factory = sessionmaker(bind=self.engine)

    def test_create_valid_orm_comment_object(self):
        valid_orm_obj = Insert(target="G0", item="G1", after=True)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Insert(target="G0", item="G1", after=True)
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        session.commit()

    def test_save_invalid_instance___case_multi_value(self):
        invalid_orm_obj = Insert(target="G0", item="G1", after=True, before=True)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__case_empty_value(self):
        invalid_orm_obj = Insert(target="G0", item="G1")
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__case_empty_target(self):
        invalid_orm_obj = Insert(target="", item="G1", after=True)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__case_empty_item(self):
        invalid_orm_obj = Insert(target="G0", item="", after=True)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__case_empty_all_options(self):
        invalid_orm_obj = Insert(target="", item="")
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Comment(findstr="", iffullmatch=True, ifcontains=False)
        session.add(valid_orm_obj)
        session.commit()
        time.sleep(1)
        other_valid_same_object = Comment(findstr="", iffullmatch=True, ifcontains=False)
        session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()


class TestModelReplace(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(DATABASE_PATH_FOR_TESTS, isolation_level=TRANSACTION_ISOLATION_LEVEL)
        self.session_factory = sessionmaker(bind=self.engine)

    def test_create_valid_orm_rename_object(self):
        valid_orm_obj = Replace(findstr="G0", item="G1", ifcontains=True)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Replace(findstr="G0", item="G1", ifcontains=True)
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        session.commit()

    def test_save_invalid_instance___case_multi_value(self):
        invalid_orm_obj = Replace(findstr="G0", item="G1", ifcontains=True, iffullmatch=True)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance___case_empty_value(self):
        invalid_orm_obj = Replace(findstr="G0", item="G1")
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Replace(findstr="G0", item="G1", ifcontains=True)
        session.add(valid_orm_obj)
        session.commit()
        time.sleep(1)
        other_valid_same_object = Replace(findstr="G0", item="G1", ifcontains=True)
        session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()


class TestModelNumeration(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(DATABASE_PATH_FOR_TESTS, isolation_level=TRANSACTION_ISOLATION_LEVEL)
        self.session_factory = sessionmaker(bind=self.engine)

    def test_create_valid_orm_object(self):
        valid_orm_obj = Numeration()
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Numeration()
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        session.commit()

    def test_save_invalid_instance___case_multi_value(self):
        """
        uppercase=True, lowercase=True
        """
        invalid_orm_obj = Numeration(startat=0, endat=0)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance___case_invalid_startat_and_endat_values(self):
        invalid_orm_obj = Numeration(startat=500, endat=100)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance___case_invalid_startat_values(self):
        invalid_orm_obj = Numeration(startat=-1, endat=100)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance___case_invalid_endat_values(self):
        invalid_orm_obj = Numeration(startat=500, endat=-19)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Numeration(startat=1, endat=9999)
        session.add(valid_orm_obj)
        session.commit()
        time.sleep(1)
        other_valid_same_object = Numeration(startat=1, endat=9999)
        session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()


class TestModelRemove(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(DATABASE_PATH_FOR_TESTS, isolation_level=TRANSACTION_ISOLATION_LEVEL)
        self.session_factory = sessionmaker(bind=self.engine)

    def test_create_valid_orm_object(self):
        valid_orm_obj = Remove(findstr="G0", ifcontains=True)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Remove(findstr="G0", ifcontains=True)
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        session.commit()

    def test_save_invalid_instance___case_multi_value(self):
        invalid_orm_obj = Remove(findstr="G0", ifcontains=True, iffullmatch=True)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance___case_empty_value(self):
        invalid_orm_obj = Remove(findstr="")
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Replace(findstr="G1", ifcontains=True)
        session.add(valid_orm_obj)
        session.commit()
        time.sleep(1)
        other_valid_same_object = Replace(findstr="G1", ifcontains=True)
        session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()


class TestModelOperation(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(DATABASE_PATH_FOR_TESTS, isolation_level=TRANSACTION_ISOLATION_LEVEL)
        self.session_factory = sessionmaker(bind=self.engine)

    def get_or_create_insert(self):
        instance = Insert.query.first()
        if instance is None:
            q = Insert(target="test", item="G4544", after=True)
            session.add(q)
            session.commit()
            instance = Insert.query.first()
        return instance

    def get_or_create_comment(self):
        instance = Comment.query.first()
        if instance is None:
            q = Comment(findstr="r", iffullmatch=False, ifcontains=True)
            session.add(q)
            session.commit()
            instance = Comment.query.first()
        return instance

    def get_or_create_uncomment(self):
        instance = Insert.query.first()
        if instance is None:
            q = Uncomment(findstr="r", iffullmatch=False, ifcontains=True)
            session.add(q)
            session.commit()
            instance = Uncomment.query.first()
        return instance

    def test_create_valid_orm_object(self):
        valid_orm_obj = OperationDelegation(insertid=self.get_or_create_insert().insid)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = OperationDelegation(insertid=self.get_or_create_insert().insid)
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        insert_id = self.get_or_create_insert().insid
        valid_orm_obj = OperationDelegation(insertid=insert_id)
        session.add(valid_orm_obj)
        session.commit()
        time.sleep(1)
        other_valid_same_object = OperationDelegation(insertid=insert_id)
        session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__multi_options(self):
        """
        Этот экзмеляр сущности уже создан
        """
        insert_id = self.get_or_create_insert().insid
        comment_id = self.get_or_create_comment().commentid
        valid_orm_obj = OperationDelegation(insertid=insert_id, commentid=comment_id)
        session.add(valid_orm_obj)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__empty_options(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = OperationDelegation()
        session.add(valid_orm_obj)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()


class TestModelHeadVarible(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(DATABASE_PATH_FOR_TESTS, isolation_level=TRANSACTION_ISOLATION_LEVEL)
        self.session_factory = sessionmaker(bind=self.engine)

    def test_create_valid_orm_object(self):
        valid_orm_obj = HeadVarible(name="tool", separator=":", select_all=True)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = HeadVarible(name="tool", separator=":", select_all=True)
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = HeadVarible(name="sk", separator=":")
        session.add(valid_orm_obj)
        session.commit()
        time.sleep(1)
        other_valid_same_object = HeadVarible(name="sk", separator=":")
        session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__case_invalid_select_option_multiple(self):
        valid_orm_obj = HeadVarible(name="tool", separator=":", select_all=True, select_string=True)
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__case_invalid_isnotexists_option_multiple(self):
        valid_orm_obj = HeadVarible(name="tool", separator=":", select_all=True, isnotexistsdonothing=True, isnotexistsbreak=True)
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__case_invalid_select_option_empty(self):
        valid_orm_obj = HeadVarible(name="somevar", separator=":", select_all=False, select_string=False,
                                    select_numbers=False, select_reg=None)
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__case_invalid_isnotexists_option_empty(self):
        valid_orm_obj = HeadVarible(name="somevar1", separator=":", select_all=True,
                                    isnotexistsdonothing=False, isnotexistsbreak=False, isnotexistsvalue=None)
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__case_invalid_separator(self):
        valid_orm_obj = HeadVarible(name="somevar1", separator="", select_all=True,
                                    isnotexistsdonothing=True)
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()


class TestModelHeadVarDelegation(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(DATABASE_PATH_FOR_TESTS, isolation_level=TRANSACTION_ISOLATION_LEVEL)
        self.session_factory = sessionmaker(bind=self.engine)

    def get_or_create_headvar(self):
        instance = HeadVarible.query.first()
        if instance is None:
            instance = HeadVarible(name="someheadvar", separator=":", select_all=True)
            session.add(instance)
            session.commit()
            instance = HeadVarible.query.first()
        return instance

    def get_or_create_insert(self):
        instance = Insert.query.first()
        if instance is None:
            q = Insert(target="test", item="G4544", after=True)
            session.add(q)
            session.commit()
            instance = Insert.query.first()
        return instance

    def get_or_create_rename(self):
        instance = Rename.query.first()
        if instance is None:
            q = Rename(uppercase=True, prefix="valid")
            session.add(q)
            session.commit()
            instance = Rename.query.first()
        return instance

    def test_create_valid_orm_object(self):
        rename_id = self.get_or_create_rename().renameid
        var_id = self.get_or_create_headvar().varid
        valid_orm_obj = HeadVarDelegation(varid=var_id, renameid=rename_id)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        rename_id = self.get_or_create_rename().renameid
        var_id = self.get_or_create_headvar().varid
        valid_orm_obj = HeadVarDelegation(varid=var_id, renameid=rename_id)
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        session.commit()

    def test_save_invalid_fk(self):
        invalid_orm_obj = HeadVarDelegation(varid=109, renameid=101)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises(IntegrityError):
            session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        rename_id = self.get_or_create_rename().renameid
        var_id = self.get_or_create_headvar().varid
        valid_orm_obj = HeadVarDelegation(varid=var_id, renameid=rename_id)
        session.add(valid_orm_obj)
        session.commit()
        time.sleep(1)
        other_valid_same_object = HeadVarDelegation(varid=var_id, renameid=rename_id)
        session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__multiple_fk(self):
        """
        Указаны оба FK - rename и insert, что недопустимо
        """
        rename_id = self.get_or_create_rename().renameid
        insert_id = self.get_or_create_insert().insid
        var_id = self.get_or_create_headvar().varid
        valid_orm_obj = HeadVarDelegation(varid=var_id, renameid=rename_id, insertid=insert_id)
        session.add(valid_orm_obj)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__empty_fk(self):
        """
        Указаны оба FK - rename и insert, что недопустимо
        """
        rename_id = self.get_or_create_rename().renameid
        insert_id = self.get_or_create_insert().insid
        var_id = self.get_or_create_headvar().varid
        valid_orm_obj = HeadVarDelegation(varid=var_id)
        session.add(valid_orm_obj)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()

    def test_save_invalid_instance__empty_varid(self):
        """
        Указаны оба FK - rename и insert, что недопустимо
        """
        rename_id = self.get_or_create_rename().renameid
        insert_id = self.get_or_create_insert().insid
        var_id = self.get_or_create_headvar().varid
        valid_orm_obj = HeadVarDelegation(insertid=insert_id)
        session.add(valid_orm_obj)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()


class TestModelTaskDelegation(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(DATABASE_PATH_FOR_TESTS, isolation_level=TRANSACTION_ISOLATION_LEVEL)
        self.session_factory = sessionmaker(bind=self.engine)

    def get_or_create_rename(self):
        instance = Rename.query.first()
        if instance is None:
            q = Rename(uppercase=True, prefix="valid134")
            session.add(q)
            session.commit()
            instance = Rename.query.first()
        return instance

    def get_or_create_operation(self):
        instance = OperationDelegation.query.first()
        if instance is None:
            instance = OperationDelegation(renameid=self.get_or_create_rename().renameid)
            session.add(instance)
            session.commit()
            instance = OperationDelegation.query.first()
        return instance

    def get_or_create_cnc(self):
        instance = Cnc.query.first()
        if instance is None:
            obj = Cnc(name="Fidia1", comment_symbol="/")
            session.add(obj)
            session.commit()
            instance = Cnc.query.first()
        return instance

    def get_or_create_machine(self):
        instance = Machine.query.first()
        if instance is None:
            instance = Machine(cncid=self.get_or_create_cnc(session).cncid, machine_name="65A80",
                                input_catalog="C://65A80", output_catalog="D://65A80")
            session.add(instance)
            session.commit()
            instance = Machine.query.first()
        return instance

    def test_create_valid_orm_object(self):
        operation_id = self.get_or_create_operation().opid
        machine_id = self.get_or_create_machine().machineid
        valid_orm_obj = TaskDelegation(machineid=machine_id, operationid=operation_id)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        operation_id = self.get_or_create_operation().opid
        machine_id = self.get_or_create_machine().machineid
        valid_orm_obj = TaskDelegation(machineid=machine_id, operationid=operation_id)
        session.add(valid_orm_obj)
        exists_status = False
        for instance in session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        session.commit()

    def test_save_invalid_fk(self):
        invalid_orm_obj = TaskDelegation(machineid=344, operationid=0)
        session.add(invalid_orm_obj)
        exists_status = False
        for instance in session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises(IntegrityError):
            session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        operation_id = self.get_or_create_operation().opid
        machine_id = self.get_or_create_machine().machineid
        valid_orm_obj = TaskDelegation(machineid=machine_id, operationid=operation_id)
        session.add(valid_orm_obj)
        session.commit()
        time.sleep(1)
        other_valid_same_object = TaskDelegation(machineid=machine_id, operationid=operation_id)
        session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            session.commit()
