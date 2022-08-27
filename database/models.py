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


class Comment(db.Model):
    __tablename__ = "comment"
    commentid = s.Column(s.Integer, primary_key=True, autoincrement=True)
    findstr = s.Column(s.String(100), nullable=False)
    iffullmatch = s.Column(s.Boolean, default=False, nullable=False)
    ifcontains = s.Column(s.Boolean, default=False, nullable=False)


class Uncomment(db.Model):
    __tablename__ = "uncomment"
    id = s.Column(s.Integer, primary_key=True, autoincrement=True)
    findstr = s.Column(s.String(100), nullable=False)
    iffullmatch = s.Column(s.Boolean, nullable=False, default=False)
    ifcontains = s.Column(s.Boolean, nullable=False, default=False)


class Remove(db.Model):
    __tablename__ = "remove"
    removeid = s.Column(s.Integer, primary_key=True, autoincrement=True)
    iffullmatch = s.Column(s.Boolean, nullable=False, default=False)
    ifcontains = s.Column(s.Boolean, nullable=False, default=False)
    findstr = s.Column(s.String(100), nullable=False)


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
        all_options_counter integer := 0;
        ext_counter integer := 0;
        case_counter integer := 0;
        BEGIN
            SELECT ext_counter + (CASE WHEN NEW.uppercase THEN 1 ELSE 0 END) INTO ext_counter;
            SELECT ext_counter + (CASE WHEN NEW.lowercase THEN 1 ELSE 0 END) INTO ext_counter;
            SELECT ext_counter + (CASE WHEN NEW.defaultcase THEN 1 ELSE 0 END) INTO ext_counter;
            IF ext_counter > 1 THEN RAISE EXCEPTION 'мультизначение и пустое для опций (uppercase, lowercase и defaultcase) - недопустимо!';
            END IF;
        
            SELECT case_counter + (CASE WHEN NEW.uppercase THEN 1 ELSE 0 END) INTO case_counter;
            SELECT case_counter + (CASE WHEN NEW.lowercase THEN 1 ELSE 0 END) INTO case_counter;
            SELECT case_counter + (CASE WHEN NEW.defaultcase THEN 1 ELSE 0 END) INTO case_counter;
            IF case_counter > 1 THEN RAISE EXCEPTION 'мультизначение и пустое для опций (uppercase, lowercase и defaultcase) - недопустимо!';
            END IF;
            
            RETURN NEW;
        END; $fnc$
        LANGUAGE PLPGSQL
        """))

    db.engine.execute(s.DDL("""
        CREATE TRIGGER rename_big_trigger
        BEFORE INSERT OR UPDATE
        ON renam FOR EACH ROW
        EXECUTE PROCEDURE rename_filter_values();
        """))
