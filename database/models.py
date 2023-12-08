"""
Назначить каждому классу модели атрибут __db_queue_primary_field_name__, который необходим для класса tools.ORMHelper
"""
import itertools
from uuid import uuid4
from sqlalchemy import String, Integer, Column, ForeignKey, Boolean, SmallInteger, Text, CheckConstraint
from sqlalchemy.orm import relationship, InstrumentedAttribute
from flask_sqlalchemy import SQLAlchemy as FlaskSQLAlchemy
from flask import Flask


DATABASE_PATH = "postgresql://postgres:g8ln7ze5vm6a@localhost:5432/intex1"
RESERVED_WORDS = ("__insert", "__update", "__delete", "__ready", "__model", "__primary_key__", "column_names")  # Используются в классе ORMHelper


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_PATH
db = FlaskSQLAlchemy(app)


class ModelController:
    def __new__(cls, **k):
        cls.__remove_pk__ = False
        cls.column_names = []

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
                                     "элеметнов очереди ORMItem.")
            primary_field_name = getattr(cls, "__db_queue_primary_field_name__")
            primary_field = getattr(cls, primary_field_name)
            if str(primary_field.property.columns[0].type) == "INTEGER" and \
                    primary_field.property.columns[0].autoincrement:
                # В случае, когда поле первичного ключа в таблице имеет значение int и автоинкремент,
                # то это поле будет удалено из значения ноды:
                # pk - целочисленный автоинкремент, то нет смысла пытаться это отправлять в бд
                cls.__remove_pk__ = True

        def set_primary_key_field_name_to_cls():
            """
            Найти столбец с первичным ключом, сохранить его имя в атрибут класса __primary_key__.
            Для orm.py
            """
            for attribute_name, val in cls.__dict__.items():
                if hasattr(val, "primary_key") and type(val) is InstrumentedAttribute:
                    setattr(cls, "__primary_key__", attribute_name)
                    break

        def collect_all_column_names():
            """ Собрать в атрибут класса column_names все имена стоблцов таблицы """
            for attr_name, value in cls.__dict__.items():
                if type(value) is InstrumentedAttribute:
                    cls.column_names.append(attr_name)
            cls.column_names = tuple(cls.column_names)
        check_class_attributes()
        check_db_helper_queue_main_field()
        set_primary_key_field_name_to_cls()
        collect_all_column_names()
        return super().__new__(cls)


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
    Абстрактный класс для аннотации типов.
    класс модели SQLAlchemy для использования в классе ORMHelper модуля tools!
    """
    __init__ = None
    __call__ = None


class TaskDelegation(db.Model, ModelController):
    __tablename__ = "taskdelegate"
    __db_queue_primary_field_name__ = "id"
    id = Column(String, primary_key=True, default=get_uuid)
    machineid = Column(ForeignKey("machine.machineid"), nullable=False)
    operationid = Column(ForeignKey("operationdelegation.opid"), nullable=False)


class Machine(db.Model, ModelController):
    __tablename__ = "machine"
    __db_queue_primary_field_name__ = "machine_name"
    machineid = Column(Integer, primary_key=True, autoincrement=True)
    cncid = Column(Integer, ForeignKey("cnc", ondelete="SET NULL", onupdate="SET NULL"), nullable=True)
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
    operations = relationship("OperationDelegation", secondary=TaskDelegation.__table__)
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


class OperationDelegation(db.Model, ModelController):
    __tablename__ = "operationdelegation"
    __db_queue_primary_field_name__ = "operation_description"
    opid = Column(String, primary_key=True, default=get_uuid)
    conditionid = Column(String, ForeignKey("cond.cnd"), nullable=True, default=None)
    insertid = Column(Integer, ForeignKey("insert.insid"), nullable=True, default=None)
    commentid = Column(Integer, ForeignKey("comment.commentid"), nullable=True, default=None)
    uncommentid = Column(Integer, ForeignKey("uncomment.uid"), nullable=True, default=None)
    removeid = Column(Integer, ForeignKey("remove.removeid"), nullable=True, default=None)
    renameid = Column(Integer, ForeignKey("renam.renameid"), nullable=True, default=None)
    replaceid = Column(Integer, ForeignKey("repl.replaceid"), nullable=True, default=None)
    numerationid = Column(Integer, ForeignKey("num.numerationid"), nullable=True, default=None)
    is_active = Column(Boolean, default=True, nullable=False)
    operation_description = Column(String(300), default="", nullable=False)
    machines = relationship("Machine", secondary=TaskDelegation.__table__)


class Condition(db.Model, ModelController):
    __tablename__ = "cond"
    __db_queue_primary_field_name__ = "cnd"
    cnd = Column(String, primary_key=True, default=get_uuid)
    parent = Column(String, ForeignKey("cond.cnd", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, default=None)
    hvarid = Column(ForeignKey("headvar.varid", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, default=None)
    stringid = Column(ForeignKey("sstring.strid", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, default=None)
    condinner = Column(String(50), nullable=False, default="")
    conditionbooleanvalue = Column(Boolean, default=True, nullable=False)
    isntfindfull = Column(Boolean, default=False, nullable=False)
    isntfindpart = Column(Boolean, default=False, nullable=False)
    findfull = Column(Boolean, default=False, nullable=False)
    findpart = Column(Boolean, default=False, nullable=False)
    parentconditionbooleanvalue = Column(Boolean, default=True, nullable=False)
    equal = Column(Boolean, default=False, nullable=False)
    less = Column(Boolean, default=False, nullable=False)
    larger = Column(Boolean, default=False, nullable=False)
    __table_args__ = (
        CheckConstraint("condinner!=''", name="condinner_empty"),
        CheckConstraint("hvarid IS NOT NULL OR stringid IS NOT NULL", name="check_cnd_target"),
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
    cncid = Column(ForeignKey("cnc.cncid", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    strid = Column(ForeignKey("sstring.strid", ondelete="CASCADE", onupdate="CASCADE"), unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    __table_args__ = (
        CheckConstraint("name!=''", name="headvar_empty_name"),
    )


class Insert(db.Model, ModelController):
    __tablename__ = "insert"
    __db_queue_primary_field_name__ = "insid"
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
    __db_queue_primary_field_name__ = "commentid"
    commentid = Column(Integer, primary_key=True, autoincrement=True)
    findstr = Column(String(100), nullable=False)
    iffullmatch = Column(Boolean, default=False, nullable=False)
    ifcontains = Column(Boolean, default=False, nullable=False)


class Uncomment(db.Model, ModelController):
    __tablename__ = "uncomment"
    __db_queue_primary_field_name__ = "uid"
    uid = Column(Integer, primary_key=True, autoincrement=True)
    findstr = Column(String(100), nullable=False)
    iffullmatch = Column(Boolean, default=False, nullable=False)
    ifcontains = Column(Boolean, default=False, nullable=False)
    __table_args__ = (
        CheckConstraint("findstr!=''", name="empty_findstr"),
    )


class Remove(db.Model, ModelController):
    __tablename__ = "remove"
    __db_queue_primary_field_name__ = "removeid"
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
    __db_queue_primary_field_name__ = "secid"
    secid = Column(String, default=get_uuid, primary_key=True)
    varid = Column(String, ForeignKey("headvar.varid"), nullable=False)
    insertid = Column(Integer, ForeignKey("insert.insid"), nullable=True, default=None)
    renameid = Column(Integer, ForeignKey("renam.renameid"), nullable=True, default=None)
    __table_args__ = (
        CheckConstraint("(insertid IS NULL OR renameid IS NULL)=TRUE AND (insertid IS NULL AND renameid IS NULL)=FALSE", name="check_one_item_delegation"),
    )


class Rename(db.Model, ModelController):
    __tablename__ = "renam"
    __db_queue_primary_field_name__ = "renameid"
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
    __db_queue_primary_field_name__ = "numerationid"
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
    __db_queue_primary_field_name__ = "replaceid"
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


class SearchString(db.Model, ModelController):
    __tablename__ = "sstring"
    __db_queue_primary_field_name__ = "strid"
    strid = Column(String, default=get_uuid, primary_key=True)
    inner_ = Column(Text, default="", nullable=False)
    ignorecase = Column(Boolean, default=True, nullable=False)
    lindex = Column(SmallInteger, default=0, nullable=False)
    rindex = Column(SmallInteger, default=-1, nullable=False)
    lignoreindex = Column(SmallInteger, default=0, nullable=True)
    rignoreindex = Column(SmallInteger, default=0, nullable=True)
    __table_args = (
        CheckConstraint("inner_!=''", name="required_inner"),
        CheckConstraint("lindex<0", name="invalid_l_sep_left_border"),
        CheckConstraint("rindex<=0", name="invalid_r_sep_left_border"),
        CheckConstraint("lindex>=LENGTH(inner_)-1", name="invalid_l_sep_right_border"),
        CheckConstraint("rindex>LENGTH(inner_)-1", name="invalid_r_sep_right_border"),
        CheckConstraint("lignoreindex<0", name="invalid_l_ignore_sep_left_border"),
        CheckConstraint("rignoreindex<=0", name="invalid_r_ignore_sep_left_border"),
        CheckConstraint("lignoreindex>=LENGTH(inner_)-1", name="invalid_l_ignore_sep_right_border"),
        CheckConstraint("rignoreindex>LENGTH(inner_)-1", name="invalid_r_ignore_sep_right_border"),
        CheckConstraint("lindex=rindex", name="empty_main_place"),
        CheckConstraint("lignoreindex=rignoreindex", name="empty_ignore_place"),
        CheckConstraint("lindex=lignoreindex AND rindex=rignoreindex", name="empty_matched"),
        CheckConstraint("lignoreindex IS NULL OR rignoreindex IS NULL", name="any_ignore_sep_isnt_set"),
        CheckConstraint("rindex!=-1 AND lindex>rindex", name="invalid_seq_ordering"),
        CheckConstraint("lignoreindex>rignoreindex", name="invalid_ignore_sep_ordering"),
    )


if __name__ == "__main__":
    def check_bad_attribute_name():
        TaskDelegation()
        Machine()
        OperationDelegation()
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
        SearchString()

    def test_unique_primary_key_column_name(field_name: str):
        """ Уникальность названия для столбца первичного ключа по всем таблицам """
        def primary_keys():
            for m in (TaskDelegation(), Machine(), OperationDelegation(), Condition(), Cnc(), HeadVarible(), Insert(), Comment(),
                      Uncomment(), Remove(), HeadVarDelegation(), Rename(), Numeration(), Replace(), SearchString(),):
                yield {m.__class__.__name__: getattr(m, field_name)}
        repeat_table_names = []
        primary_key_field_names = list(itertools.chain(*tuple(map(lambda x: tuple(x.values()), primary_keys()))))
        for elem in primary_keys():
            model_name, pk_key = tuple(elem.keys())[0], tuple(elem.values())[0]
            if primary_key_field_names.count(pk_key) > 1:
                repeat_table_names.append(model_name)
        if repeat_table_names:
            raise KeyError(f"Во всём проекте названия полей-первичных ключей должны быть уникальными! "
                           f" Повторы в таблицах: {', '.join(repeat_table_names)}")
    check_bad_attribute_name()
    #test_unique_primary_key_column_name("__primary_key__")  # test database PK
    #test_unique_primary_key_column_name("__db_queue_primary_field_name__")
    db.drop_all()
    db.create_all()
