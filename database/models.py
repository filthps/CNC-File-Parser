from uuid import uuid4
from sqlalchemy import MetaData, Integer, String, Column, ForeignKey, CheckConstraint, create_engine, Table, select, inspect, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base


Data = MetaData()
Base = declarative_base()


def get_uuid():
    return str(uuid4())


association_table = Table("association", Data,
                          Column('machine_id', ForeignKey('machine.machine_id')),
                          Column('operation_id', ForeignKey('operation.opid')),
                          )


Machine = Table("machine", Data,
                Column('machine_id', Integer(), primary_key=True, autoincrement=True),
                Column('machine_name', String(100), nullable=False, unique=True),
                Column('x_over', Integer(), nullable=True),
                Column('y_over', Integer(), nullable=True),
                Column('z_over', Integer(), nullable=True),
                Column('x_fspeed', Integer(), nullable=True),
                Column('y_fspeed', Integer(), nullable=True),
                Column('z_fspeed', Integer(), nullable=True),
                Column('spindele_speed', Integer(), nullable=True),
                Column('input_catalog', String(), nullable=False),
                Column('output_catalog', String(), nullable=False),
                Column("operation_id", ForeignKey('association.operation_id')),
                CheckConstraint('input_catalog!=""'),
                CheckConstraint('output_catalog!=""'),
                )


Operation = Table('operation', Data,
                  Column("machine_id", ForeignKey('association.machine_id')),
                  Column('opid', String(), primary_key=True, default=get_uuid),
                  Column('operation_type', String(), nullable=False),
                  Column('operation_name', String(), nullable=False),
                  Column('target', String(), nullable=False),
                  Column('after_or_before', String(), nullable=False),
                  Column('item', String(), nullable=False),
                  CheckConstraint('operation_type IN("a", "r", "d", "c")', name='type_choice'),
                  CheckConstraint('after_or_before IN("a", "b")', name='a_or_b'),
                  )


if __name__ == "__main__":
    engine = create_engine("sqlite:///../database.db")
    engine.connect()
    Data.create_all(engine)
    #Data.drop_all(engine)
    s = Machine.select()
    print(engine.execute(s).fetchone())
