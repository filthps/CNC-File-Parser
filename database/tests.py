import unittest
from sqlalchemy import select
from .models import db, Cnc, Machine, Comment, Insert, Uncomment


CNC_NAME = "Fidia"
MACHINE_NAME = "Heller"


class TestCncModel(unittest.TestCase):

    def setUp(self) -> None:
        self.name = CNC_NAME
        self.test_session = db.session

    def test_create_valid_orm_cnc_object(self):
        valid_orm_obj = Cnc(name=self.name, comment_symbol=",")
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_add_valid_orm_cnc_object_to_session(self):
        valid_orm_obj = Cnc(name=self.name, comment_symbol=",")
        self.test_session.add(valid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")

    def test_save_session(self):
        self.test_session.commit()

    def test_exists_orm_object(self):
        item = select(Cnc).where(Cnc.name == self.name)
        print(self.test_session.scalars(item).one())


class TestMachineModel(unittest.TestCase):
    def setUp(self) -> None:
        self.machine_name = MACHINE_NAME
        self.test_session = db.session

    def test_create_valid_orm_machine_object(self):
        valid_orm_obj = Machine(
            cncid=self.test_session.scalars(select(Cnc).where(Cnc.name == CNC_NAME)).one(),
            machine_name=self.machine_name, input_catalog="C://somevar/d", output_catalog="C://someval/g"
        )
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_add_valid_orm_machine_object_to_session(self):
        find_cnc_query = select(Cnc).where(Cnc.name == CNC_NAME)
        valid_orm_obj = Machine(
            cncid=self.test_session.scalars(find_cnc_query).one().cncid,
            machine_name=self.machine_name, input_catalog="C://somevar/d", output_catalog="C://someval/g"
        )
        self.test_session.add(valid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")

    def test_save_session(self):
        self.test_session.commit()

    def test_exists_orm_object(self):
        item = select(Machine).where(Machine.machine_name == self.machine_name)
        print(self.test_session.scalars(item).one())


class TestCommentModel(unittest.TestCase):
    def setUp(self) -> None:
        self.test_session = db.session

    def test_create_valid_orm_comment_object(self):
        valid_orm_obj = Comment(
            findstr="Z500", iffullmatch=True, ifcontains=False
        )
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_add_valid_orm_comment_object_to_session(self):
        valid_orm_obj = Comment(
            findstr="Z500", iffullmatch=True, ifcontains=False
        )
        self.test_session.add(valid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")

    def test_save_session(self):
        self.test_session.commit()

    def test_exists_orm_object(self):
        query = select(Comment).where(Comment.commentid == 1)
        print(self.test_session.scalars(query).one())


class TestUncommentModel(unittest.TestCase):
    def setUp(self) -> None:
        self.test_session = db.session

    def test_create_valid_orm_uncomment_object(self):
        valid_orm_obj = Uncomment(
            findstr="Z500", iffullmatch=True, ifcontains=False
        )
        self.assertTrue(isinstance(valid_orm_obj, db.Model))

    def test_add_valid_orm_uncomment_object_to_session(self):
        valid_orm_obj = Uncomment(
            findstr="Z500", iffullmatch=True, ifcontains=False
        )
        self.test_session.add(valid_orm_obj)
        exists_status = False
        for instance in self.test_session:
            if valid_orm_obj == instance:
                exists_status = True
                break
        self.assertTrue(exists_status, msg="Объект не добавился в сессию")

    def test_save_session(self):
        self.test_session.commit()

    def test_exists_orm_object(self):
        query = select(Uncomment).where(Uncomment.id == 1)
        print(self.test_session.scalars(query).one())


if __name__ == "__main__":
    TestCncModel.main()
    TestMachineModel.main()
