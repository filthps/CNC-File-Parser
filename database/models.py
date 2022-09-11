from uuid import uuid4
from sqlalchemy import ForeignKey, String, Integer, Column, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy as FlaskSQLAlchemy
from flask import Flask


DATABASE_PATH = "postgresql://postgres:g8ln7ze5vm6a@localhost:5432/intex"


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_PATH
db = FlaskSQLAlchemy(app)


def get_uuid():
    return str(uuid4())


OPERATION_TYPES = (
    ("a", "Добавить"),
    ("r", "Переименовать"),
    ("d", "Удалить"),
    ("c", "Закомментировать"),
    ("uc", "Раскомментировать"),
)


class TaskDelegation(db.Model):
    id = Column(String, primary_key=True, default=get_uuid)
    machineid = Column(ForeignKey("machine.machineid"))
    operationid = Column(ForeignKey("operation.opid"))


class Machine(db.Model):
    __tablename__ = "machine"
    machineid = Column(Integer, primary_key=True, autoincrement=True)
    cncid = Column(Integer, db.ForeignKey("cnc"))
    machine_name = Column(String(100), unique=True)
    x_over = Column(Integer, nullable=True, default=None)
    y_over = Column(Integer, nullable=True, default=None)
    z_over = Column(Integer, nullable=True, default=None)
    x_fspeed = Column(Integer, nullable=True, default=None)
    y_fspeed = Column(Integer, nullable=True, default=None)
    z_fspeed = Column(Integer, nullable=True, default=None)
    spindele_speed = Column(Integer, nullable=True, default=None)
    input_catalog = Column(String)
    output_catalog = Column(String)
    operations = relationship("Operation", secondary=TaskDelegation.__table__)
    __table_args__ = (
        CheckConstraint("machine_name!=''", name="machine_name_empty"),
        CheckConstraint("input_catalog!=''", name="input_catalog_empty"),
        CheckConstraint("output_catalog!=''", name="output_catalog_empty"),
    )


class Operation(db.Model):
    __tablename__ = "operation"
    opid = Column(String, primary_key=True, default=get_uuid)
    conditionid = Column(String, ForeignKey("cond.cnd"), nullable=True, default=None)
    insertid = Column(Integer, db.ForeignKey("insert.insid"), nullable=True, default=None)
    commentid = Column(Integer, db.ForeignKey("comment.commentid"), nullable=True, default=None)
    uncommentid = Column(Integer, db.ForeignKey("uncomment.id"), nullable=True, default=None)
    removeid = Column(Integer, db.ForeignKey("remove.removeid"), nullable=True, default=None)
    renameid = Column(Integer, db.ForeignKey("renam.renameid"), nullable=True, default=None)
    replaceid = Column(Integer, db.ForeignKey("repl.replaceid"), nullable=True, default=None)
    numerationid = Column(Integer, db.ForeignKey("num.numerationid"), nullable=True, default=None)
    is_active = Column(Boolean, default=True)
    operation_description = Column(String(300), default="")
    #machines = relationship("Machine", secondary=TaskDelegation.__table__)


class Condition(db.Model):
    __tablename__ = "cond"
    cnd = Column(String, primary_key=True, default=get_uuid)
    parent = Column(String, ForeignKey("cond.cnd"), nullable=True, default=None)
    targetstr = Column(String(100), unique=True, nullable=False)
    isntfind = Column(Boolean, default=False)
    findfull = Column(Boolean, default=False)
    findpart = Column(Boolean, default=False)
    conditionbasevalue = Column(Boolean, default=True)
    __table_args__ = (
        CheckConstraint("targetstr!=''"),
    )


class Cnc(db.Model):
    __tablename__ = "cnc"
    cncid = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), unique=True)
    comment_symbol = Column(String(1))
    except_symbols = Column(String(50), nullable=True, default=None)
    __table_args__ = (
        CheckConstraint("comment_symbol!=''", name="comment_symbol_empty"),
        CheckConstraint("name!=''", name="name_empty"),
    )


class HeadVarible(db.Model):
    __tablename__ = "headvar"
    varid = Column(String, default=get_uuid, primary_key=True)
    name = Column(String, unique=True)
    separator = Column(String(7))
    select_all = Column(Boolean, default=False)
    select_numbers = Column(Boolean, default=False)
    select_string = Column(Boolean, default=False)
    select_reg = Column(Boolean, default=False)
    isnotexistsdonothing = Column(Boolean, default=False)
    isnotexistsvalue = Column(Boolean, default=False)
    isnotexistsbreak = Column(Boolean, default=False)


class Insert(db.Model):
    __tablename__ = "insert"
    insid = Column(Integer, primary_key=True, autoincrement=True)
    after = Column(Boolean, default=False)
    before = Column(Boolean, default=False)
    target = Column(String)
    item = Column(String)
    __table_args__ = (
        CheckConstraint("after!=before", name="after_equal_before"),
        CheckConstraint("target!=''", name="empty_target"),
        CheckConstraint("item!=''", name="empty_item"),
        CheckConstraint("target!=item", name="target_equal_item"),
    )


class Comment(db.Model):
    __tablename__ = "comment"
    commentid = Column(Integer, primary_key=True, autoincrement=True)
    findstr = Column(String(100))
    iffullmatch = Column(Boolean, default=False)
    ifcontains = Column(Boolean, default=False)


class Uncomment(db.Model):
    __tablename__ = "uncomment"
    id = Column(Integer, primary_key=True, autoincrement=True)
    findstr = Column(String(100))
    iffullmatch = Column(Boolean, default=False)
    ifcontains = Column(Boolean, default=False)
    __table_args__ = (
        CheckConstraint("findstr!=''", name="empty_findstr"),
    )


class Remove(db.Model):
    __tablename__ = "remove"
    removeid = Column(Integer, primary_key=True, autoincrement=True)
    iffullmatch = Column(Boolean, default=False)
    ifcontains = Column(Boolean, default=False)
    findstr = Column(String(100))
    __table_args__ = (
        CheckConstraint("findstr!=''", name="empty_findstr"),
        CheckConstraint("iffullmatch!=ifcontains", name="equal_iffullmatch_and_ifcontains"),
    )


class HeadVarDelegation(db.Model):
    __tablename__ = "varsec"
    secid = Column(String, default=get_uuid, primary_key=True)
    varid = Column(String, db.ForeignKey("headvar.varid"))
    insertid = Column(Integer, db.ForeignKey("insert.insid"), nullable=True, default=None)
    renameid = Column(Integer, db.ForeignKey("renam.renameid"), nullable=True, default=None)
    strindex = Column(Integer, default=0)


class Rename(db.Model):
    __tablename__ = "renam"
    renameid = Column(Integer, primary_key=True, autoincrement=True)
    uppercase = Column(Boolean, default=False)
    lowercase = Column(Boolean, default=False)
    prefix = Column(String(10), nullable=True, default=None)
    postfix = Column(String(10), nullable=True, default=None)
    nametext = Column(String(20), nullable=True, default=None)
    removeextension = Column(Boolean, default=False)
    setextension = Column(String(10), nullable=True, default=None)
    #varibles = relationship("HeadVarDelegation")


class Numeration(db.Model):
    __tablename__ = "num"
    numerationid = Column(Integer, autoincrement=True, primary_key=True)
    startat = Column(Integer, nullable=True, default=None)
    endat = Column(Integer, nullable=True, default=None)
    __table_args__ = (
        CheckConstraint("startat!=endat", name="startat_equal_endat"),
        CheckConstraint("startat<=0", name="negatory_startat_value"),
        CheckConstraint("endat<=0", name="negatory_endat_value"),
        CheckConstraint("startat>endat", name="startat_more_then_endat"),
    )


class Replace(db.Model):
    __tablename__ = "repl"
    replaceid = Column(Integer, primary_key=True, autoincrement=True)
    findstr = Column(String(100))
    ifcontains = Column(Boolean, default=False)
    iffullmatch = Column(Boolean, default=False)
    item = Column(String(100))
    __table_args__ = (
        CheckConstraint("ifcontains!=iffullmatch", name="ifcontains_equal_iffullmatch"),
        CheckConstraint("item!=''", name="empty_item"),
        CheckConstraint("findstr!=''", name="empty_findstr"),
        CheckConstraint("findstr!=item", name="findstr_equal_item"),
    )


if __name__ == "__main__":
    db.drop_all()
    db.create_all()
