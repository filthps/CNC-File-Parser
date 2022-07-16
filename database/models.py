from uuid import uuid4
from flask import Flask
from sqlalchemy import Integer, String, Column, CheckConstraint
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
DATABASE_PATH = 'sqlite:///' + '../database.db'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_PATH
db = SQLAlchemy(app)


AssociationTable = db.Table('association',
                            db.Column('machine_id', db.Integer, db.ForeignKey('machine.machine_id')),
                            db.Column('operation_id', db.String, db.ForeignKey('operation.opid')),
                            )


def get_uuid():
    return str(uuid4())


OPERATION_TYPES = (
    ("a", "Добавить"),
    ("r", "Переименовать"),
    ("d", "Удалить"),
    ("c", "Закомментировать"),
    ("uc", "Раскомментировать"),
)


class Machine(db.Model):
    __tablename__ = "machine"
    machine_id = Column(Integer, primary_key=True, autoincrement=True)
    machine_name = Column(String(100), nullable=False, unique=True)
    x_over = Column(Integer, nullable=True)
    y_over = Column(Integer, nullable=True)
    z_over = Column(Integer, nullable=True)
    x_fspeed = Column(Integer, nullable=True)
    y_fspeed = Column(Integer, nullable=True)
    z_fspeed = Column(Integer, nullable=True)
    spindele_speed = Column(Integer, nullable=True)
    input_catalog = Column(String, nullable=False)
    output_catalog = Column(String, nullable=False)
    operations = relationship('Operation', secondary=AssociationTable)
    __table__args = (
        CheckConstraint('input_catalog!=""'),
        CheckConstraint('output_catalog!=""'),
    )


class Operation(db.Model):
    __tablename__ = 'operation'
    opid = Column(String, primary_key=True, default=get_uuid)
    operation_type = Column(String, nullable=False)
    operation_name = Column(String, nullable=False)
    target = Column(String, nullable=False)
    after_or_before = Column(String, nullable=False)
    item = Column(String, nullable=False)
    __table__args = (
        CheckConstraint('operation_type IN("a", "r", "d", "c")', name='type_choice'),
        CheckConstraint('after_or_before IN("a", "b")', name='a_or_b'),
    )


class InsertOperation(db.Model):
    __tablename__ = "insert_operation"



if __name__ == "__main__":
    db.drop_all()
    db.create_all()

