import time
import unittest
from sqlalchemy.exc import InternalError, IntegrityError, PendingRollbackError
from .models import db, Cnc, Machine, Comment, Insert, Uncomment, Rename, Condition, Replace, Numeration, Remove, Operation


class TestCncModel(unittest.TestCase):

    def setUp(self) -> None:
        self.test_session = db.session

    def test_create_valid_orm_cnc_object(self):
        valid_orm_obj = Cnc(name="Fidia", comment_symbol=",")
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Cnc(name="Fidia", comment_symbol=",")
        self.test_session.add(valid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        self.test_session.commit()

    def test_save_invalid__case_empty_name(self):
        invalid_orm_obj = Cnc(name="", comment_symbol=",")
        self.test_session.add(invalid_orm_obj)
        with self.assertRaises((PendingRollbackError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid__case_empty_comment_symbol(self):
        invalid_orm_obj = Cnc(name="Ram", comment_symbol="")
        self.test_session.add(invalid_orm_obj)
        with self.assertRaises((PendingRollbackError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Cnc(name="NC200", comment_symbol=",")
        self.test_session.add(valid_orm_obj)
        self.test_session.commit()
        time.sleep(1)
        other_valid_same_object = Cnc(name="NC200", comment_symbol=",")
        self.test_session.add(other_valid_same_object)
        with self.assertRaises((IntegrityError, InternalError,)):
            self.test_session.commit()


class TestModelMachine(unittest.TestCase):
    """
    Запускать тесты по одному
    """
    def setUp(self) -> None:
        self.test_session = db.session
        self.cnc_name = "NC210"
        self.machine_name = "Heller"

    def get_or_create_cnc(self):
        instance = Cnc.query.filter_by(name=self.cnc_name).first()
        if instance is None:
            obj = Cnc(name=self.cnc_name, comment_symbol="/")
            self.test_session.add(obj)
            self.test_session.commit()
            instance = Cnc.query.filter_by(name=self.cnc_name).first()
        return instance

    def test_create_valid_orm_machine_object(self):
        cnc_instance = self.get_or_create_cnc()
        valid_orm_obj = Machine(cncid=cnc_instance.cncid, machine_name=self.machine_name,
                                input_catalog="C://Heller", output_catalog="D://Heller")
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        cnc_instance = self.get_or_create_cnc()
        valid_orm_obj = Machine(cncid=cnc_instance.cncid, machine_name=self.machine_name,
                                input_catalog="C://Heller", output_catalog="D://Heller")
        self.test_session.add(valid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        self.test_session.commit()

    def test_save_invalid_instance___case_empty_input_catalog_value(self):
        cnc_instance = self.get_or_create_cnc()
        invalid_orm_obj = Machine(cncid=cnc_instance.cncid, machine_name=self.machine_name,
                                input_catalog="", output_catalog="D://Heller")
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((PendingRollbackError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance___case_empty_output_catalog_value(self):
        cnc_instance = self.get_or_create_cnc()
        invalid_orm_obj = Machine(cncid=cnc_instance.cncid, machine_name=self.machine_name,
                                input_catalog="C://Heller", output_catalog="")
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((PendingRollbackError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__case_empty_machine_name_value(self):
        cnc_instance = self.get_or_create_cnc()
        invalid_orm_obj = Machine(cncid=cnc_instance.cncid, machine_name="",
                                  input_catalog="C://Heller", output_catalog="D://Heller")
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((PendingRollbackError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        cnc_instance = self.get_or_create_cnc()
        valid_orm_obj = Machine(cncid=cnc_instance.cncid, machine_name=self.machine_name,
                                input_catalog="C://Heller", output_catalog="D://Heller")
        self.test_session.add(valid_orm_obj)
        self.test_session.commit()
        time.sleep(1)
        other_valid_same_object = Machine(cncid=cnc_instance.cncid, machine_name=self.machine_name,
                                          input_catalog="C://Heller", output_catalog="D://Heller")
        self.test_session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()


class TestModelComment(unittest.TestCase):
    """
    Запускать тесты по одному
    """

    def setUp(self) -> None:
        self.test_session = db.session

    def test_create_valid_orm_object(self):
        valid_orm_obj = Comment(findstr="r", iffullmatch=False, ifcontains=True)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Comment(findstr="r", iffullmatch=False, ifcontains=True)
        self.test_session.add(valid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        self.test_session.commit()

    def test_save_invalid_instance___case_multi_value(self):
        invalid_orm_obj = Comment(findstr="r", iffullmatch=True, ifcontains=True)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__case_empty_value(self):
        invalid_orm_obj = Comment(findstr="r", iffullmatch=False, ifcontains=False)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__case_empty_findstr(self):
        invalid_orm_obj = Comment(findstr="", iffullmatch=True, ifcontains=False)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Comment(findstr="", iffullmatch=True, ifcontains=False)
        self.test_session.add(valid_orm_obj)
        self.test_session.commit()
        time.sleep(1)
        other_valid_same_object = Comment(findstr="", iffullmatch=True, ifcontains=False)
        self.test_session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()


class TestModelUncomment(unittest.TestCase):
    """
    Запускать тесты по одному
    """
    def setUp(self) -> None:
        self.test_session = db.session

    def test_create_valid_orm_object(self):
        valid_orm_obj = Uncomment(findstr="r", iffullmatch=False, ifcontains=True)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Uncomment(findstr="r", iffullmatch=False, ifcontains=True)
        self.test_session.add(valid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        self.test_session.commit()

    def test_save_invalid_instance___case_multi_value(self):
        invalid_orm_obj = Uncomment(findstr="r", iffullmatch=True, ifcontains=True)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__case_empty_value(self):
        invalid_orm_obj = Uncomment(findstr="r", iffullmatch=False, ifcontains=False)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__case_empty_findstr(self):
        invalid_orm_obj = Uncomment(findstr="", iffullmatch=True, ifcontains=False)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Uncomment(findstr="", iffullmatch=True, ifcontains=False)
        self.test_session.add(valid_orm_obj)
        self.test_session.commit()
        time.sleep(1)
        other_valid_same_object = Uncomment(findstr="", iffullmatch=True, ifcontains=False)
        self.test_session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()


class TestModelRename(unittest.TestCase):
    """
    Запускать тесты по одному
    """
    def setUp(self) -> None:
        self.test_session = db.session

    def test_create_valid_orm_rename_object(self):
        valid_orm_obj = Rename(uppercase=True, lowercase=False,
                               prefix="", postfix="", nametext="", removeextension=False, setextension=None)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Rename(uppercase=True, lowercase=False,
                               prefix="valid", postfix=None, nametext=None, removeextension=False, setextension=None)
        self.test_session.add(valid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        self.test_session.commit()

    def test_save_invalid_instance___case_multi_value(self):
        """
        uppercase=True, lowercase=True
        """
        invalid_orm_obj = Rename(uppercase=True, lowercase=True,
                                 prefix="invalid", postfix=None, nametext=None, removeextension=False, setextension=None)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__case_empty_value(self):
        invalid_orm_obj = Rename(uppercase=False, lowercase=False,
                                 prefix=None, postfix=None, nametext=None, removeextension=False,
                                 setextension=None)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Rename(uppercase=True, prefix="valid")
        self.test_session.add(valid_orm_obj)
        self.test_session.commit()
        time.sleep(1)
        other_valid_same_object = Rename(uppercase=True, prefix="valid")
        self.test_session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()


class TestModelCondition(unittest.TestCase):
    """
        Запускать тесты по одному
        """
    def setUp(self) -> None:
        self.test_session = db.session

    def test_create_valid_orm_condition_object(self):
        valid_orm_obj = Condition(targetstr="xyz", isntfind=True)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Condition(targetstr="xyz", isntfind=True)
        self.test_session.add(valid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        self.test_session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Condition(targetstr="zyx", isntfind=True)
        self.test_session.add(valid_orm_obj)
        self.test_session.commit()
        time.sleep(1)
        other_valid_same_object = Condition(targetstr="zyx", isntfind=True)
        self.test_session.add(other_valid_same_object)
        with self.assertRaises((IntegrityError, InternalError,)):
            self.test_session.commit()

    def test_save_invalid_instance___case_multi_value(self):
        invalid_orm_obj = Condition(targetstr="f23", isntfind=True, findfull=True)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance___case_empty_options(self):
        invalid_orm_obj = Condition(targetstr="f23")
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance___case_empty_targetstr(self):
        invalid_orm_obj = Condition(isntfind=True, targetstr="")
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance___case_null_targetstr(self):
        invalid_orm_obj = Condition(isntfind=True, targetstr=None)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()


class TestModelInsert(unittest.TestCase):
    """
    Запускать тесты по одному
    """

    def setUp(self) -> None:
        self.test_session = db.session

    def test_create_valid_orm_comment_object(self):
        valid_orm_obj = Insert(target="G0", item="G1", after=True)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Insert(target="G0", item="G1", after=True)
        self.test_session.add(valid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        self.test_session.commit()

    def test_save_invalid_instance___case_multi_value(self):
        invalid_orm_obj = Insert(target="G0", item="G1", after=True, before=True)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__case_empty_value(self):
        invalid_orm_obj = Insert(target="G0", item="G1")
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__case_empty_target(self):
        invalid_orm_obj = Insert(target="", item="G1", after=True)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__case_empty_item(self):
        invalid_orm_obj = Insert(target="G0", item="", after=True)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__case_empty_all_options(self):
        invalid_orm_obj = Insert(target="", item="")
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Comment(findstr="", iffullmatch=True, ifcontains=False)
        self.test_session.add(valid_orm_obj)
        self.test_session.commit()
        time.sleep(1)
        other_valid_same_object = Comment(findstr="", iffullmatch=True, ifcontains=False)
        self.test_session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()


class TestModelReplace(unittest.TestCase):
    """
    Запускать тесты по одному
    """
    def setUp(self) -> None:
        self.test_session = db.session

    def test_create_valid_orm_rename_object(self):
        valid_orm_obj = Replace(findstr="G0", item="G1", ifcontains=True)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Replace(findstr="G0", item="G1", ifcontains=True)
        self.test_session.add(valid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        self.test_session.commit()

    def test_save_invalid_instance___case_multi_value(self):
        invalid_orm_obj = Replace(findstr="G0", item="G1", ifcontains=True, iffullmatch=True)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance___case_empty_value(self):
        invalid_orm_obj = Replace(findstr="G0", item="G1")
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Replace(findstr="G0", item="G1", ifcontains=True)
        self.test_session.add(valid_orm_obj)
        self.test_session.commit()
        time.sleep(1)
        other_valid_same_object = Replace(findstr="G0", item="G1", ifcontains=True)
        self.test_session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()


class TestModelNumeration(unittest.TestCase):
    """
    Запускать тесты по одному
    """
    def setUp(self) -> None:
        self.test_session = db.session

    def test_create_valid_orm_object(self):
        valid_orm_obj = Numeration()
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Numeration()
        self.test_session.add(valid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        self.test_session.commit()

    def test_save_invalid_instance___case_multi_value(self):
        """
        uppercase=True, lowercase=True
        """
        invalid_orm_obj = Numeration(startat=0, endat=0)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance___case_invalid_startat_and_endat_values(self):
        invalid_orm_obj = Numeration(startat=500, endat=100)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance___case_invalid_startat_values(self):
        invalid_orm_obj = Numeration(startat=-1, endat=100)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance___case_invalid_endat_values(self):
        invalid_orm_obj = Numeration(startat=500, endat=-19)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Numeration(startat=1, endat=9999)
        self.test_session.add(valid_orm_obj)
        self.test_session.commit()
        time.sleep(1)
        other_valid_same_object = Numeration(startat=1, endat=9999)
        self.test_session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()


class TestModelRemove(unittest.TestCase):
    """
    Запускать тесты по одному
    """
    def setUp(self) -> None:
        self.test_session = db.session

    def test_create_valid_orm_object(self):
        valid_orm_obj = Remove(findstr="G0", ifcontains=True)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Remove(findstr="G0", ifcontains=True)
        self.test_session.add(valid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        self.test_session.commit()

    def test_save_invalid_instance___case_multi_value(self):
        invalid_orm_obj = Remove(findstr="G0", ifcontains=True, iffullmatch=True)
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance___case_empty_value(self):
        invalid_orm_obj = Remove(findstr="")
        self.test_session.add(invalid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if invalid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Replace(findstr="G1", ifcontains=True)
        self.test_session.add(valid_orm_obj)
        self.test_session.commit()
        time.sleep(1)
        other_valid_same_object = Replace(findstr="G1", ifcontains=True)
        self.test_session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()


class TestModelOperation(unittest.TestCase):
    """
        Запускать тесты по одному
        """

    def setUp(self) -> None:
        self.test_session = db.session

    def get_or_create_insert(self):
        instance = Insert.query.first()
        if instance is None:
            q = Insert(target="test", item="G4544", after=True)
            self.test_session.add(q)
            self.test_session.commit()
            instance = Insert.query.first()
        return instance

    def get_or_create_comment(self):
        instance = Comment.query.first()
        if instance is None:
            q = Comment(findstr="r", iffullmatch=False, ifcontains=True)
            self.test_session.add(q)
            self.test_session.commit()
            instance = Comment.query.first()
        return instance

    def get_or_create_uncomment(self):
        instance = Insert.query.first()
        if instance is None:
            q = Uncomment(findstr="r", iffullmatch=False, ifcontains=True)
            self.test_session.add(q)
            self.test_session.commit()
            instance = Uncomment.query.first()
        return instance

    def test_create_valid_orm_object(self):
        valid_orm_obj = Operation(insertid=self.get_or_create_insert().insid)
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_save_valid_instance(self):
        valid_orm_obj = Operation(insertid=self.get_or_create_insert().insid)
        self.test_session.add(valid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")
        self.test_session.commit()

    def test_save_invalid_instance__the_same(self):
        """
        Этот экзмеляр сущности уже создан
        """
        insert_id = self.get_or_create_insert().insid
        valid_orm_obj = Operation(insertid=insert_id)
        self.test_session.add(valid_orm_obj)
        self.test_session.commit()
        time.sleep(1)
        other_valid_same_object = Operation(insertid=insert_id)
        self.test_session.add(other_valid_same_object)
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__multi_options(self):
        """
        Этот экзмеляр сущности уже создан
        """
        insert_id = self.get_or_create_insert().insid
        comment_id = self.get_or_create_comment().commentid
        valid_orm_obj = Operation(insertid=insert_id, commentid=comment_id)
        self.test_session.add(valid_orm_obj)
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()

    def test_save_invalid_instance__empty_options(self):
        """
        Этот экзмеляр сущности уже создан
        """
        valid_orm_obj = Operation()
        self.test_session.add(valid_orm_obj)
        with self.assertRaises((InternalError, IntegrityError,)):
            self.test_session.commit()
