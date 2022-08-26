import sqlalchemy as s
from uuid import uuid4
from flask import Flask
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy


DATABASE_PATH = "postgresql://postgres:g8ln7ze5vm6a@localhost:5432/intex"


app = Flask(__name__)
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
    machineid = s.Column(s.Integer, primary_key=True, autoincrement=True)
    cncid = s.Column(s.Integer, db.ForeignKey("cnc"), unique=True, nullable=False)
    machine_name = s.Column(s.String(100), nullable=False, unique=True)
    x_over = s.Column(s.Integer, nullable=True)
    y_over = s.Column(s.Integer, nullable=True)
    z_over = s.Column(s.Integer, nullable=True)
    x_fspeed = s.Column(s.Integer, nullable=True)
    y_fspeed = s.Column(s.Integer, nullable=True)
    z_fspeed = s.Column(s.Integer, nullable=True)
    spindele_speed = s.Column(s.Integer, nullable=True)
    input_catalog = s.Column(s.String, nullable=False)
    output_catalog = s.Column(s.String, nullable=False)
    operations = relationship("Operation", secondary=AssociationTable)
    __table__args = (
        s.CheckConstraint("input_catalog!=''"),
        s.CheckConstraint("output_catalog!=''"),
    )


class Operation(db.Model):
    __tablename__ = "operation"
    opid = s.Column(s.String, primary_key=True, default=get_uuid)
    insertid = s.Column(s.Integer, db.ForeignKey("insert.insid"), nullable=True)
    commentid = s.Column(s.Integer, db.ForeignKey("comment"), nullable=True)
    uncommentid = s.Column(s.Integer, db.ForeignKey("uncomment.id"), nullable=True)
    removeid = s.Column(s.Integer, db.ForeignKey("remove"), nullable=True)
    renameid = s.Column(s.Integer, db.ForeignKey("renam"), nullable=True)
    replaceid = s.Column(s.Integer, db.ForeignKey("repl"), nullable=True)
    numerationid = s.Column(s.Integer, db.ForeignKey("num"), nullable=True)
    is_active = s.Column(s.Boolean, default=True, nullable=False)
    operation_description = s.Column(s.String(300), default="", nullable=False)
    machines = relationship("Machine", secondary=AssociationTable)
    __table__args = (
        s.CheckConstraint("COALESCE("
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
       "ins s.Integer, "
       "comment_id s.Integer, "
       "uncomm s.Integer, "
       "remid s.Integer, "
       "renid s.Integer, "
       "replid s.Integer, "
       "numerateid s.Integer)"
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
    cncid = s.Column(s.Integer, primary_key=True, autoincrement=True)
    name = s.Column(s.String(20), nullable=False, unique=True)
    comment_symbol = s.Column(s.String(1), nullable=False)
    except_symbols = s.Column(s.String(50), nullable=True, default=None)


class HeadVarible(db.Model):
    __tablename__ = "headvar"
    varid = s.Column(s.String, default=get_uuid, primary_key=True)
    name = s.Column(s.String, nullable=False, unique=True)
    separator = s.Column(s.String(1), nullable=False)
    select_all = s.Column(s.Boolean, nullable=False, default=False)
    select_numbers = s.Column(s.Boolean, nullable=False, default=False)
    select_string = s.Column(s.Boolean, nullable=False, default=False)
    selection_value = s.Column(s.Boolean, nullable=False, default=False)
    selection_key = s.Column(s.Boolean, nullable=False, default=False)
    isnotexistsdonothing = s.Column(s.Boolean, nullable=False, default=False)
    isnotexistsvalue = s.Column(s.Boolean, nullable=False, default=False)
    isnotexistsbreak = s.Column(s.Boolean, nullable=False, default=False)


class Insert(db.Model):
    __tablename__ = "insert"
    insid = s.Column(s.Integer, primary_key=True, autoincrement=True)
    varid = s.Column(s.String, db.ForeignKey("headvar"), nullable=True, default=None)
    after = s.Column(s.Boolean, default=False, nullable=False)
    before = s.Column(s.Boolean, default=False, nullable=False)
    target = s.Column(s.String, nullable=False)
    item = s.Column(s.String, nullable=False)


db.DDL("CREATE TRIGGER control_option_insert"
       "BEFORE UPDATE,INSERT"
       "ON insert"
       "BEGIN"
       "CREATE TEMP TABLE IF NOT EXISTS Vcount (pk s.Integer PRIMARY_KEY AUTOINCREMENT,"
       "optionone s.Boolean DEFAULT FALSE, optiontwo s.Boolean DEFAULT FALSE)"
       "IF NEW.after = 1 INSERT Vcount (optionone) VALUES (1)"
       "IF NEW.before = 1 INSERT Vcount (optiontwo) VALUES (1)"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) > 1 ROLLBACK TRANSACTION"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) = 0 ROLLBACK TRANSACTION"
       "DROP Vcount"
       "END")


class Comment(db.Model):
    __tablename__ = "comment"
    commentid = s.Column(s.Integer, primary_key=True, autoincrement=True)
    findstr = s.Column(s.String(100), nullable=False)
    iffullmatch = s.Column(s.Boolean, default=False, nullable=False)
    ifcontains = s.Column(s.Boolean, default=False, nullable=False)


db.DDL("CREATE TRIGGER control_option_comment"
       "BEFORE UPDATE,INSERT"
       "ON comment"
       "BEGIN"
       "CREATE TEMP TABLE IF NOT EXISTS Vcount (pk s.Integer PRIMARY_KEY AUTOINCREMENT,"
       "optionone s.Boolean DEFAULT FALSE, optiontwo s.Boolean DEFAULT FALSE)"
       "IF NEW.iffullmatch = 1 INSERT Vcount (optionone) VALUES (1)"
       "IF NEW.ifcontains = 1 INSERT Vcount (optiontwo) VALUES (1)"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) > 1 ROLLBACK TRANSACTION"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) = 0 ROLLBACK TRANSACTION"
       "DROP Vcount"
       "END")


class Uncomment(db.Model):
    __tablename__ = "uncomment"
    id = s.Column(s.Integer, primary_key=True, autoincrement=True)
    findstr = s.Column(s.String(100), nullable=False)
    iffullmatch = s.Column(s.Boolean, nullable=False, default=False)
    ifcontains = s.Column(s.Boolean, nullable=False, default=False)


db.DDL("CREATE TRIGGER control_option_uncomment"
       "BEFORE UPDATE,INSERT"
       "ON uncomment"
       "BEGIN"
       "CREATE TEMP TABLE IF NOT EXISTS Vcount (pk s.Integer PRIMARY_KEY AUTOINCREMENT,"
       "optionone s.Boolean DEFAULT FALSE, optiontwo s.Boolean DEFAULT FALSE)"
       "IF NEW.iffullmatch = 1 INSERT Vcount (optionone) VALUES (1)"
       "IF NEW.ifcontains = 1 INSERT Vcount (optiontwo) VALUES (1)"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) > 1 ROLLBACK TRANSACTION"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) = 0 ROLLBACK TRANSACTION"
       "DROP Vcount"
       "END")


class Remove(db.Model):
    __tablename__ = "remove"
    removeid = s.Column(s.Integer, primary_key=True, autoincrement=True)
    iffullmatch = s.Column(s.Boolean, nullable=False, default=False)
    ifcontains = s.Column(s.Boolean, nullable=False, default=False)
    findstr = s.Column(s.String(100), nullable=False)


db.DDL("CREATE TRIGGER control_option_remove"
       "BEFORE UPDATE,INSERT"
       "ON remove"
       "BEGIN"
       "CREATE TEMP TABLE IF NOT EXISTS Vcount (pk s.Integer PRIMARY_KEY AUTOINCREMENT,"
       "optionone s.Boolean DEFAULT FALSE, optiontwo s.Boolean DEFAULT FALSE)"
       "IF NEW.iffullmatch = 1 INSERT Vcount (optionone) VALUES (1)"
       "IF NEW.ifcontains = 1 INSERT Vcount (optiontwo) VALUES (1)"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) > 1 ROLLBACK TRANSACTION"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) = 0 ROLLBACK TRANSACTION"
       "DROP Vcount"
       "END")


class VarSequence(db.Model):
    __tablename__ = "varsec"
    decid = s.Column(s.String, default=get_uuid, primary_key=True)
    varid = s.Column(s.String, db.ForeignKey("headvar"), nullable=False)
    insertid = s.Column(s.Integer, db.ForeignKey("insert.insid"), nullable=True)
    renameid = s.Column(s.Integer, db.ForeignKey("renam"), nullable=True)
    strindex = s.Column(s.Integer, nullable=False)


class Rename(db.Model):
    __tablename__ = "renam"
    renameid = s.Column(s.Integer, primary_key=True, autoincrement=True)
    uppercase = s.Column(s.Boolean, nullable=False, default=False)
    lowercase = s.Column(s.Boolean, nullable=False, default=False)
    defaultcase = s.Column(s.Boolean, nullable=False, default=True)
    prefix = s.Column(s.String(10), nullable=True, default=None)
    postfix = s.Column(s.String(10), nullable=True, default=None)
    nametext = s.Column(s.String(20), nullable=True, default=None)
    removeextension = s.Column(s.Boolean, nullable=False, default=False)
    setextension = s.Column(s.Boolean, nullable=False, default=False)
    varibles = relationship("VarSequence")
    __table__args = (
        s.CheckConstraint("uppercase > 0 OR lowercase > 0 OR defaultcase > 0", name="any_value_case_rename")
    )


class Numeration(db.Model):
    __tablename__ = "num"
    numerationid = s.Column(s.Integer, nullable=False, autoincrement=True, primary_key=True)
    startat = s.Column(s.Integer, nullable=True, default=None)
    endat = s.Column(s.Integer, nullable=True, default=None)


class Replace(db.Model):
    __tablename__ = "repl"
    replaceid = s.Column(s.Integer, primary_key=True, autoincrement=True)
    findstr = s.Column(s.String(100), nullable=False)
    ifcontains = s.Column(s.Boolean, nullable=False, default=False)
    iffullmatch = s.Column(s.Boolean, nullable=False, default=False)
    item = s.Column(s.String(100), nullable=False)


db.DDL("CREATE TRIGGER control_option_replace"
       "BEFORE UPDATE,INSERT"
       "ON repl"
       "BEGIN"
       "CREATE TEMP TABLE IF NOT EXISTS Vcount (pk Integer PRIMARY_KEY AUTOINCREMENT,"
       "optionone s.Boolean DEFAULT FALSE, optiontwo s.Boolean DEFAULT FALSE)"
       "IF NEW.iffullmatch = 1 INSERT Vcount (optionone) VALUES (1)"
       "IF NEW.ifcontains = 1 INSERT Vcount (optiontwo) VALUES (1)"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) > 1 ROLLBACK TRANSACTION"
       "IF (SELECT SUM(optionone, optiontwo) FROM Vcount) = 0 ROLLBACK TRANSACTION"
       "DROP Vcount"
       "END")


test_table = db.Table("t_table",
                      db.Column("k", db.Integer, primary_key=True, autoincrement=True),
                      db.Column("test_n", db.Integer, default=0)
                      )

if __name__ == "__main__":
    db.drop_all()
    db.create_all()

    db.engine.execute(s.DDL("""
        CREATE OR REPLACE FUNCTION rename_filter_values() RETURNS trigger
        AS $fnc$
        DECLARE 
        counter integer := 0;
        BEGIN
            SELECT counter + NEW.uppercase INTO counter;
            SELECT counter + NEW.lowercase INTO counter;
            SELECT counter + NEW.defaultcase INTO counter;
            IF counter > 1 THEN ROLLBACK;
            END IF;
        END; $fnc$
        LANGUAGE PLPGSQL
        """))

    db.engine.execute(s.DDL("""
        CREATE TRIGGER rename_case_value
        BEFORE INSERT OR UPDATE
        ON renam FOR EACH ROW
        EXECUTE PROCEDURE rename_filter_values();
        """))
