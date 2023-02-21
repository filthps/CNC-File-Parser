"""
Назначить каждому классу модели атрибут __db_queue_primary_field_name__, который необходим для класса tools.ORMHelper
"""
from uuid import uuid4
from sqlalchemy import String, Integer, Column, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy as FlaskSQLAlchemy
from flask import Flask


DATABASE_PATH = "postgresql://postgres:g8ln7ze5vm6a@localhost:5432/intex1"
RESERVED_WORDS = ("__insert", "__update", "__delete", "__ready", "__model", "__callback", "__node_name",)  # Используются в классе ORMHelper


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_PATH
db = FlaskSQLAlchemy(app)


class ModelController:
    __remove_pk__ = False

    def __new__(cls):
        def check_class_attributes():
            """ Предотвратить использование заерезервированных в классе ORMHelper слов """
            for special_word in RESERVED_WORDS:
                if hasattr(cls, f"_{cls.__name__}{special_word}"):
                    raise AttributeError(
                        f"Не удалось инциализировать класс-модель {cls.__name__}. "
                        f"Атрибут {special_word} использовать нельзя, тк он зарезервирован."
                    )

        def check_db_helper_queue_main_field():
            """
            Проверить наличие атрибута __db_queue_primary_field_name__,
            который нужем в модуле tools, также, чтобы имя поля, хранящееся в его значении,
            присутствовало в данной модели
            """
            if "__db_queue_primary_field_name__" not in dir(cls):
                raise AttributeError("Добавьте атрибут __db_queue_primary_field_name__, "
                                     "содержащий имя поля, которое наиболее удобно в качестве первичного ключа для"
                                     "элеметнов очереди ORMItem, смотри модуль tools")
            primary_field_name = getattr(cls, "__db_queue_primary_field_name__")
            primary_field = getattr(cls, primary_field_name)
            if str(primary_field.property.columns[0].type) == "INTEGER" and \
                    primary_field.property.columns[0].autoincrement:
                # В случае, когда поле первичного ключа в таблице имеет значение int и автоинкремент,
                # то это поле будет удалено из значения ноды:
                # pk - целочисленный автоинкремент, то нет смысла пытаться это отправлять в бд
                cls.__remove_pk__ = True
        check_class_attributes()
        check_db_helper_queue_main_field()
        return cls


def get_uuid():
    return str(uuid4())


OPERATION_TYPES = (
    ("a", "Добавить"),
    ("r", "Переименовать"),
    ("d", "Удалить"),
    ("c", "Закомментировать"),
    ("uc", "Раскомментировать"),
)


class CustomModel(db.Model, ModelController):
    """
    Кстомный класс модели SQLAlchemy для использования в классе ORMHelper модуля tools!
    """
    abstract_field = Column(Integer, primary_key=True)


class TaskDelegation(db.Model, ModelController):
    __tablename__ = "taskdelegate"
    __db_queue_primary_field_name__ = "id"
    id = Column(String, primary_key=True, default=get_uuid)
    machineid = Column(db.ForeignKey("machine.machineid"), nullable=False)
    operationid = Column(db.ForeignKey("operation.opid"), nullable=False)


class Machine(db.Model, ModelController):
    __tablename__ = "machine"
    __db_queue_primary_field_name__ = "machine_name"
    machineid = Column(Integer, primary_key=True, autoincrement=True)
    cncid = Column(Integer, db.ForeignKey("cnc", ondelete="SET NULL", onupdate="SET NULL"), nullable=True)
    machine_name = Column(String(100), unique=True, nullable=False)
    x_over = Column(Integer, nullable=True, default=None)
    y_over = Column(Integer, nullable=True, default=None)
    z_over = Column(Integer, nullable=True, default=None)
    x_fspeed = Column(Integer, nullable=True, default=None)
    y_fspeed = Column(Integer, nullable=True, default=None)
    z_fspeed = Column(Integer, nullable=True, default=None)
    spindele_speed = Column(Integer, nullable=True, default=None)
    input_catalog = Column(String, nullable=False)
    output_catalog = Column(String, nullable=False)
    operations = relationship("Operation", secondary=TaskDelegation.__table__)
    __table_args__ = (
        CheckConstraint("machine_name!=''", name="machine_name_empty"),
        CheckConstraint("input_catalog!=''", name="input_catalog_empty"),
        CheckConstraint("output_catalog!=''", name="output_catalog_empty"),
        CheckConstraint("x_over>=0", name="x_over_must_be_positive"),
        CheckConstraint("y_over>=0", name="y_over_must_be_positive"),
        CheckConstraint("z_over>=0", name="z_over_must_be_positive"),
        CheckConstraint("x_fspeed>=0", name="x_fspeed_must_be_positive"),
        CheckConstraint("y_fspeed>=0", name="y_fspeed_must_be_positive"),
        CheckConstraint("z_fspeed>=0", name="z_fspeed_must_be_positive"),
        CheckConstraint("spindele_speed>=0", name="spindele_speed_must_be_positive"),
    )


class Operation(db.Model, ModelController):
    __tablename__ = "operation"
    __db_queue_primary_field_name__ = "operation_description"
    opid = Column(String, primary_key=True, default=get_uuid)
    conditionid = Column(String, db.ForeignKey("cond.cnd"), nullable=True, default=None)
    insertid = Column(Integer, db.ForeignKey("insert.insid"), nullable=True, default=None)
    commentid = Column(Integer, db.ForeignKey("comment.commentid"), nullable=True, default=None)
    uncommentid = Column(Integer, db.ForeignKey("uncomment.id"), nullable=True, default=None)
    removeid = Column(Integer, db.ForeignKey("remove.removeid"), nullable=True, default=None)
    renameid = Column(Integer, db.ForeignKey("renam.renameid"), nullable=True, default=None)
    replaceid = Column(Integer, db.ForeignKey("repl.replaceid"), nullable=True, default=None)
    numerationid = Column(Integer, db.ForeignKey("num.numerationid"), nullable=True, default=None)
    is_active = Column(Boolean, default=True, nullable=False)
    operation_description = Column(String(300), default="", nullable=False)
    machines = relationship("Machine", secondary=TaskDelegation.__table__)


class Condition(db.Model, ModelController):
    __tablename__ = "cond"
    __db_queue_primary_field_name__ = "cnd"
    cnd = Column(String, primary_key=True, default=get_uuid)
    useheadvarible = Column(Boolean, nullable=False, default=False)
    conditionbooleanvalue = Column(Boolean, default=True, nullable=False)
    parent = Column(String, db.ForeignKey("cond.cnd"), nullable=True, default=None)
    conditionstring = Column(String(100), nullable=False, default="")
    conditionvalue = Column(String(100), nullable=False, default="")
    isntfindfull = Column(Boolean, default=False, nullable=False)
    isntfindpart = Column(Boolean, default=False, nullable=False)
    findfull = Column(Boolean, default=False, nullable=False)
    findpart = Column(Boolean, default=False, nullable=False)
    parentconditionbooleanvalue = Column(Boolean, default=True, nullable=False)
    equal = Column(Boolean, default=False, nullable=False)
    less = Column(Boolean, default=False, nullable=False)
    larger = Column(Boolean, default=False, nullable=False)
    __table_args__ = (
        CheckConstraint("conditionstring!=''", name="cond_targetstr_empty"),
        CheckConstraint("conditionstring!=conditionvalue", name="cond_equal_strings"),
        CheckConstraint("conditionvalue!=''", name="cond_value_empty"),
    )


class Cnc(db.Model, ModelController):
    __tablename__ = "cnc"
    __db_queue_primary_field_name__ = "name"
    cncid = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), unique=True, nullable=False)
    comment_symbol = Column(String(1), nullable=False)
    except_symbols = Column(String(50), nullable=True, default=None)
    __table_args__ = (
        CheckConstraint("comment_symbol!=''", name="comment_symbol_empty"),
        CheckConstraint("name!=''", name="name_empty"),
    )


class HeadVarible(db.Model, ModelController):
    __tablename__ = "headvar"
    __db_queue_primary_field_name__ = "name"
    varid = Column(String, default=get_uuid, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    separator = Column(String(7), nullable=False)
    select_all = Column(Boolean, default=True, nullable=False)
    select_numbers = Column(Boolean, default=False, nullable=False)
    select_string = Column(Boolean, default=False, nullable=False)
    select_reg = Column(String, nullable=True, default=None)
    isnotexistsdonothing = Column(Boolean, default=True, nullable=False)
    isnotexistsvalue = Column(String, nullable=True, default=None)
    isnotexistsbreak = Column(Boolean, default=False, nullable=False)
    __table_args__ = (
        CheckConstraint("name!=''", name="headvar_empty_name"),
        CheckConstraint("select_reg IS NULL OR select_reg LIKE('%<v>%')", name="headvar_reg_format"),
        CheckConstraint("isnotexistsvalue!=''", name="isnotexistsvalue_empty"),
    )


class Insert(db.Model, ModelController):
    __tablename__ = "insert"
    __db_queue_primary_field_name__ = "id"
    insid = Column(Integer, primary_key=True, autoincrement=True)
    after = Column(Boolean, default=False, nullable=False)
    before = Column(Boolean, default=False, nullable=False)
    target = Column(String, nullable=False)
    item = Column(String, nullable=False)
    __table_args__ = (
        CheckConstraint("after!=before", name="after_equal_before"),
        CheckConstraint("target!=''", name="empty_target"),
        CheckConstraint("item!=''", name="empty_item"),
        CheckConstraint("target!=item", name="target_equal_item"),
    )


class Comment(db.Model, ModelController):
    __tablename__ = "comment"
    __db_queue_primary_field_name__ = "id"
    commentid = Column(Integer, primary_key=True, autoincrement=True)
    findstr = Column(String(100), nullable=False)
    iffullmatch = Column(Boolean, default=False, nullable=False)
    ifcontains = Column(Boolean, default=False, nullable=False)


class Uncomment(db.Model, ModelController):
    __tablename__ = "uncomment"
    __db_queue_primary_field_name__ = "id"
    id = Column(Integer, primary_key=True, autoincrement=True)
    findstr = Column(String(100), nullable=False)
    iffullmatch = Column(Boolean, default=False, nullable=False)
    ifcontains = Column(Boolean, default=False, nullable=False)
    __table_args__ = (
        CheckConstraint("findstr!=''", name="empty_findstr"),
    )


class Remove(db.Model, ModelController):
    __tablename__ = "remove"
    __db_queue_primary_field_name__ = "id"
    removeid = Column(Integer, primary_key=True, autoincrement=True)
    iffullmatch = Column(Boolean, default=False, nullable=False)
    ifcontains = Column(Boolean, default=False, nullable=False)
    findstr = Column(String(100), nullable=False)
    __table_args__ = (
        CheckConstraint("findstr!=''", name="empty_findstr"),
        CheckConstraint("iffullmatch!=ifcontains", name="equal_iffullmatch_and_ifcontains"),
    )


class HeadVarDelegation(db.Model, ModelController):
    __tablename__ = "varsec"
    __db_queue_primary_field_name__ = "id"
    secid = Column(String, default=get_uuid, primary_key=True)
    varid = Column(String, db.ForeignKey("headvar.varid"), nullable=False)
    insertid = Column(Integer, db.ForeignKey("insert.insid"), nullable=True, default=None)
    renameid = Column(Integer, db.ForeignKey("renam.renameid"), nullable=True, default=None)
    conditionid = Column(String, db.ForeignKey("cond.cnd"), nullable=True, default=None)
    strindex = Column(Integer, default=0, nullable=False)


class Rename(db.Model, ModelController):
    __tablename__ = "renam"
    __db_queue_primary_field_name__ = "id"
    renameid = Column(Integer, primary_key=True, autoincrement=True)
    uppercase = Column(Boolean, default=False, nullable=False)
    lowercase = Column(Boolean, default=False, nullable=False)
    prefix = Column(String(10), nullable=True, default=None)
    postfix = Column(String(10), nullable=True, default=None)
    nametext = Column(String(20), nullable=True, default=None)
    removeextension = Column(Boolean, default=False, nullable=False)
    setextension = Column(String(10), nullable=True, default=None)
    #  varibles = relationship("HeadVarDelegation")


class Numeration(db.Model, ModelController):
    __tablename__ = "num"
    __db_queue_primary_field_name__ = "id"
    numerationid = Column(Integer, autoincrement=True, primary_key=True)
    startat = Column(Integer, nullable=False, default=1)
    endat = Column(Integer, nullable=True, default=None)
    __table_args__ = (
        CheckConstraint("startat!=endat", name="startat_equal_endat"),
        CheckConstraint("startat<=0", name="negatory_startat_value"),
        CheckConstraint("endat<=0", name="negatory_endat_value"),
        CheckConstraint("startat>endat", name="startat_more_then_endat"),
    )


class Replace(db.Model, ModelController):
    __tablename__ = "repl"
    __db_queue_primary_field_name__ = "id"
    replaceid = Column(Integer, primary_key=True, autoincrement=True)
    findstr = Column(String(100), nullable=False)
    ifcontains = Column(Boolean, default=False, nullable=False)
    iffullmatch = Column(Boolean, default=False, nullable=False)
    item = Column(String(100), nullable=False)
    __table_args__ = (
        CheckConstraint("ifcontains!=iffullmatch", name="ifcontains_equal_iffullmatch"),
        CheckConstraint("item!=''", name="empty_item"),
        CheckConstraint("findstr!=''", name="empty_findstr"),
        CheckConstraint("findstr!=item", name="findstr_equal_item"),
    )


if __name__ == "__main__":
    def check_bad_attribute_name():
        TaskDelegation()
        Machine()
        Operation()
        Condition()
        Cnc()
        HeadVarible()
        Insert()
        Comment()
        Uncomment()
        Remove()
        HeadVarDelegation()
        Rename()
        Numeration()
        Replace()
    #check_bad_attribute_name()
    #db.drop_all()
    #db.create_all()
    Machine()
