from uuid import uuid4
from flask import Flask
from sqlalchemy import Integer, String, Boolean, Column, CheckConstraint
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
DATABASE_PATH = "sqlite:///" + "../database.db"
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_PATH
db = SQLAlchemy(app)


def get_uuid():
    return str(uuid4())


AssociationTable = db.Table("TaskDelegation",
                            db.Column("id", db.String, primary_key=True, default=get_uuid),
                            db.Column("machineid", db.Integer, db.ForeignKey("machine.machineid")),
                            db.Column("operationid", db.String, db.ForeignKey("operation.opid")),
                            )


OPERATION_TYPES = (
    ("a", "Добавить"),
    ("r", "Переименовать"),
    ("d", "Удалить"),
    ("c", "Закомментировать"),
    ("uc", "Раскомментировать"),
)


class Machine(db.Model):
    __tablename__ = "machine"
    machineid = Column(Integer, primary_key=True, autoincrement=True)
    cncid = Column(Integer, db.ForeignKey("cnc"), unique=True, nullable=False)
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
    operations = relationship("Operation", secondary=AssociationTable)
    __table__args = (
        CheckConstraint("input_catalog!=''"),
        CheckConstraint("output_catalog!=''"),
    )


class Operation(db.Model):
    __tablename__ = "operation"
    opid = Column(String, primary_key=True, default=get_uuid)
    insertid = Column(Integer, db.ForeignKey("insert.insid"), nullable=True)
    commentid = Column(Integer, db.ForeignKey("comment"), nullable=True)
    uncommentid = Column(Integer, db.ForeignKey("uncomment.id"), nullable=True)
    removeid = Column(Integer, db.ForeignKey("remove"), nullable=True)
    renameid = Column(Integer, db.ForeignKey("rename"), nullable=True)
    replaceid = Column(Integer, db.ForeignKey("repl"), nullable=True)
    numerationid = Column(Integer, db.ForeignKey("num"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    operation_description = Column(String(300), default="", nullable=False)
    machines = relationship("Machine", secondary=AssociationTable)
    __table__args = (
        CheckConstraint("COALESCE("
                        "insertid, "
                        "commentid, "
                        "uncommentid, "
                        "removeid, "
                        "renameid, "
                        "replaceid, "
                        "numerationid) IS NOT NULL", name="any_operation_is_not_null"),
    )


db.DDL("CREATE TRIGGER control_operation_type_count"
       "BEFORE INSERT, UPDATE"
       "ON operation"
       "BEGIN"
       "CREATE TEMP TABLE IF NOT EXISTS Vars (name TEXT PRIMARY KEY, "
       "ins INTEGER, "
       "comment_id INTEGER, "
       "uncomm INTEGER, "
       "remid INTEGER, "
       "renid INTEGER, "
       "replid INTEGER, "
       "numerateid INTEGER)"
       "INSERT Vars (name, ins, comment_id, uncomm, remid, renid, replid, numerateid) "
       "VALUES ('test', 0, 0, 0, 0, 0, 0, 0)"
       "IF NEW.insertid IS NOT NULL INSERT Vars (ins) VALUES (1)"
       "IF NEW.commentid IS NOT NULL INSERT Vars (comment_id) VALUES (1)"
       "IF NEW.uncommentid IS NOT NULL INSERT Vars (uncomm) VALUES (1)"
       "IF NEW.removeid IS NOT NULL INSERT Vars (remid) VALUES (1)"
       "IF NEW.renameid IS NOT NULL INSERT Vars (renid) VALUES (1)"
       "IF NEW.replaceid IS NOT NULL INSERT Vars (replid) VALUES (1)"
       "IF NEW.numerationid IS NOT NULL INSERT Vars (numerateid) VALUES (1)"
       "IF (SELECT SUM(ins, comment_id, uncomm, remid, renid, replid, numerateid)"
       "FROM Vars"
       "WHERE name='test') > 1 ROLLBACK TRANSACTION"
       "DROP Vars"
       "END;")


class Cnc(db.Model):
    __tablename__ = "cnc"
    cncid = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False, unique=True)
    comment_symbol = Column(String(1), nullable=False)
    except_symbols = Column(String(50), nullable=True, default=None)


class HeadVarible(db.Model):
    __tablename__ = "headvar"
    varid = Column(String, default=get_uuid, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    separator = Column(String(1), nullable=False)
    select_all = Column(Boolean, nullable=False, default=False)
    select_numbers = Column(Boolean, nullable=False, default=False)
    select_string = Column(Boolean, nullable=False, default=False)
    selection_value = Column(Boolean, nullable=False, default=False)
    selection_key = Column(Boolean, nullable=False, default=False)
    isnotexistsdonothing = Column(Boolean, nullable=False, default=False)
    isnotexistsvalue = Column(Boolean, nullable=False, default=False)
    isnotexistsbreak = Column(Boolean, nullable=False, default=False)


class Insert(db.Model):
    __tablename__ = "insert"
    insid = Column(Integer, primary_key=True, autoincrement=True)
    varid = Column(String, db.ForeignKey("headvar"), nullable=True, default=None)
    after = Column(Boolean, default=False, nullable=False)
    before = Column(Boolean, default=False, nullable=False)
    target = Column(String, nullable=False)
    item = Column(String, nullable=False)


db.DDL("CREATE TRIGGER control_option_insert"
       "BEFORE UPDATE,INSERT"
       "ON insert"
       "BEGIN"
       "CREATE TEMP TABLE IF NOT EXISTS Vcount (pk INTEGER PRIMARY_KEY AUTOINCREMENT,"
       "optionone BOOLEAN DEFAULT FALSE, optiontwo BOOLEAN DEFAULT FALSE)"
       "IF NEW.after = 1 INSERT Vcount (optionone) VALUES (1)"
       "IF NEW.before = 1 INSERT Vcount (optiontwo) VALUES (1)"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) > 1 ROLLBACK TRANSACTION"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) = 0 ROLLBACK TRANSACTION"
       "DROP Vcount"
       "END")


class Comment(db.Model):
    __tablename__ = "comment"
    commentid = Column(Integer, primary_key=True, autoincrement=True)
    findstr = Column(String(100), nullable=False)
    iffullmatch = Column(Boolean, default=False, nullable=False)
    ifcontains = Column(Boolean, default=False, nullable=False)


db.DDL("CREATE TRIGGER control_option_comment"
       "BEFORE UPDATE,INSERT"
       "ON comment"
       "BEGIN"
       "CREATE TEMP TABLE IF NOT EXISTS Vcount (pk INTEGER PRIMARY_KEY AUTOINCREMENT,"
       "optionone BOOLEAN DEFAULT FALSE, optiontwo BOOLEAN DEFAULT FALSE)"
       "IF NEW.iffullmatch = 1 INSERT Vcount (optionone) VALUES (1)"
       "IF NEW.ifcontains = 1 INSERT Vcount (optiontwo) VALUES (1)"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) > 1 ROLLBACK TRANSACTION"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) = 0 ROLLBACK TRANSACTION"
       "DROP Vcount"
       "END")


class Uncomment(db.Model):
    __tablename__ = "uncomment"
    id = Column(Integer, primary_key=True, autoincrement=True)
    findstr = Column(String(100), nullable=False)
    iffullmatch = Column(Boolean, nullable=False, default=False)
    ifcontains = Column(Boolean, nullable=False, default=False)


db.DDL("CREATE TRIGGER control_option_uncomment"
       "BEFORE UPDATE,INSERT"
       "ON uncomment"
       "BEGIN"
       "CREATE TEMP TABLE IF NOT EXISTS Vcount (pk INTEGER PRIMARY_KEY AUTOINCREMENT,"
       "optionone BOOLEAN DEFAULT FALSE, optiontwo BOOLEAN DEFAULT FALSE)"
       "IF NEW.iffullmatch = 1 INSERT Vcount (optionone) VALUES (1)"
       "IF NEW.ifcontains = 1 INSERT Vcount (optiontwo) VALUES (1)"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) > 1 ROLLBACK TRANSACTION"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) = 0 ROLLBACK TRANSACTION"
       "DROP Vcount"
       "END")


class Remove(db.Model):
    __tablename__ = "remove"
    removeid = Column(Integer, primary_key=True, autoincrement=True)
    iffullmatch = Column(Boolean, nullable=False, default=False)
    ifcontains = Column(Boolean, nullable=False, default=False)
    findstr = Column(String(100), nullable=False)


db.DDL("CREATE TRIGGER control_option_remove"
       "BEFORE UPDATE,INSERT"
       "ON remove"
       "BEGIN"
       "CREATE TEMP TABLE IF NOT EXISTS Vcount (pk INTEGER PRIMARY_KEY AUTOINCREMENT,"
       "optionone BOOLEAN DEFAULT FALSE, optiontwo BOOLEAN DEFAULT FALSE)"
       "IF NEW.iffullmatch = 1 INSERT Vcount (optionone) VALUES (1)"
       "IF NEW.ifcontains = 1 INSERT Vcount (optiontwo) VALUES (1)"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) > 1 ROLLBACK TRANSACTION"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) = 0 ROLLBACK TRANSACTION"
       "DROP Vcount"
       "END")


class VarSequence(db.Model):
    __tablename__ = "varsec"
    decid = Column(String, default=get_uuid, primary_key=True)
    varid = Column(String, db.ForeignKey("headvar"), nullable=False)
    insertid = Column(Integer, db.ForeignKey("insert.insid"), nullable=True)
    renameid = Column(Integer, db.ForeignKey("rename"), nullable=True)
    strindex = Column(Integer, nullable=False)


class Rename(db.Model):
    __tablename__ = "rename"
    renameid = Column(Integer, primary_key=True, autoincrement=True)
    uppercase = Column(Boolean, nullable=False, default=False)
    lowercase = Column(Boolean, nullable=False, default=False)
    defaultcase = Column(Boolean, nullable=False, default=True)
    prefix = Column(String(10), nullable=True, default=None)
    postfix = Column(String(10), nullable=True, default=None)
    nametext = Column(String(20), nullable=True, default=None)
    removeextension = Column(Boolean, nullable=False, default=False)
    setextension = Column(Boolean, nullable=False, default=False)
    varibles = relationship("VarSequence", back_populates="decid")


db.DDL("CREATE TRIGGER rename_case_value"
       "BEFORE INSERT, UPDATE"
       "ON rename"
       "BEGIN"
       "CREATE TEMP TABLE IF NOT EXISTS Tvar (k INTEGER PRIMARY_KEY AUTOINCREMENT, opt1 BOOLEAN DEFAULT FALSE,"
       "opt2 BOOLEAN DEFAULT FALSE, opt3 BOOLEAN DEFAULT FALSE)"
       "IF NEW.uppercase = 1 INSERT (opt1) VALUES (1)"
       "IF NEW.lowercase = 1 INSERT (opt2) VALUES (1)"
       "IF NEW.defaultcase INSERT (opt3) VALUES (1)"
       "IF (SELECT SUM(opt1, opt2, opt3) FROM rename) > 1 ROLLBACK TRANSACTION"
       "IF (SELECT SUM(opt1, opt2, opt3) FROM rename) = 0 ROLLBACK TRANSACTION"
       "END")


class Numeration(db.Model):
    __tablename__ = "num"
    numerationid = Column(Integer, nullable=False, autoincrement=True, primary_key=True)
    startat = Column(Integer, nullable=True, default=None)
    endat = Column(Integer, nullable=True, default=None)


class Replace(db.Model):
    __tablename__ = "repl"
    replaceid = Column(Integer, primary_key=True, autoincrement=True)
    findstr = Column(String(100), nullable=False)
    ifcontains = Column(Boolean, nullable=False, default=False)
    iffullmatch = Column(Boolean, nullable=False, default=False)
    item = Column(String(100), nullable=False)


db.DDL("CREATE TRIGGER control_option_replace"
       "BEFORE UPDATE,INSERT"
       "ON repl"
       "BEGIN"
       "CREATE TEMP TABLE IF NOT EXISTS Vcount (pk INTEGER PRIMARY_KEY AUTOINCREMENT,"
       "optionone BOOLEAN DEFAULT FALSE, optiontwo BOOLEAN DEFAULT FALSE)"
       "IF NEW.iffullmatch = 1 INSERT Vcount (optionone) VALUES (1)"
       "IF NEW.ifcontains = 1 INSERT Vcount (optiontwo) VALUES (1)"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) > 1 ROLLBACK TRANSACTION"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) = 0 ROLLBACK TRANSACTION"
       "DROP Vcount"
       "END")


if __name__ == "__main__":
    db.drop_all()
    db.create_all()
