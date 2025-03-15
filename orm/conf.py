import datetime
from sqlalchemy import Column, DateTime
from abc import ABC, abstractmethod


RESERVED_WORDS = ("__insert", "__update", "__delete", "__ready", "__model", "column_names")


class AbstractModelController:
    @abstractmethod
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)


#  class CustomModel(ModelController, db.Model):
class CustomModel(AbstractModelController):
    __tablename__ = ...


class GlobalFields:
    _create_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
