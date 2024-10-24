""" Исключения для всех классов в данном пакете """


class ModelsConfigurationError(Exception):
    def __init__(self, text=""):
        super().__init__(text or "Ошибка в models.py. Конфигурация чисто кастомная!! Стандартное")


class ORMException(Exception):
    def __init__(self, text="Ошибка уровня модуля orm"):
        super().__init__(text)


class ORMInitializationError(ORMException):
    def __init__(self, text="Неправильная настройка модуля"):
        super().__init__(text)


class ORMExternalDataError(ORMException):
    def __init__(self, text="Данные в кеше непригоды для использования в рамках текещей конфигурации. "
                            "Требуется сброс"):
        super.__init__(text)


class NodeError(ORMException):
    def __init__(self, text="Ошибка ноды в очереди"):
        super().__init__(text)


class NodePrimaryKeyError(NodeError):
    def __init__(self,
                 text="Неверно указан первичный ключ, который, как и его значение должен содержаться в словаре value"):
        super().__init__(text)


class NodeDMLTypeError(NodeError):
    def __init__(self, text="Любая нода, будь то insert, update или delete,"
                            "должна иметь в значении поле первичного ключа (для базы данных) со значением!"):
        super().__init__(text)


class NodeEmptyData(NodeError):
    def __init__(self, text="Нода не содержит полей с данными"):
        super().__init__(text)


class NodeAttributeError(NodeError):
    def __init__(self, text="Ошибка значиния атрибута в ноде"):
        super().__init__(text)


class NodeColumnError(NodeError):
    def __init__(self, text="", field_name="", model_name=""):
        if text:
            super().__init__(text)
            return
        super().__init__(f"Столбец {field_name} не найден в таблице {model_name if model_name else ''}"
                         if field_name else text)


class NodeColumnValueError(NodeColumnError):
    def __init__(self, value=None, text="Ошибка значения столбца в ноде"):
        super().__init__(f"Значение {value} не является корректным" if value else text)


class InvalidModel(NodeError):
    def __init__(self, text="Нужен класс CustomModel, наследованный от flask-sqlalchemy.Model. Смотри models.py"):
        super().__init__(text)


class QueueError(ORMException):
    def __init__(self, text="Ощибка в контейнере(очереди) нод"):
        super().__init__(text)


class DoesNotExists(QueueError):
    def __init__(self, text="Нода не найдена"):
        super().__init__(text)


class JoinedResultError(ORMException):
    def __init__(self, message="Исключение на уровне экземпляра класса JoinedORMItem"):
        super().__init__(message)


class JoinedItemPointerError(JoinedResultError):
    def __init__(self, message="Ошибка указателя Pointer"):
        super().__init__(message)


class WrapperError(JoinedItemPointerError):
    def __init__(self, msg="В качестве элементов-указателей на содержимое принимается список строк"):
        super().__init__(msg)
