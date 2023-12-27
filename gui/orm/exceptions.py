""" Исключения для всех классов в данном пакете """


class ORMHelperException(Exception):
    def __init__(self):
        super().__init__()
        self.text = "Ошибка класса-адаптера ORMHelper"


class InvalidSetItem(ORMHelperException):
    def __init__(self):
        super().__init__()
        self.text = "Ошибка установки ноды в очередь"


class InvalidModel(InvalidSetItem):
    def __init__(self):
        super().__init__()
        self.text = "Нужен класс CustomModel, наследованный от flask-sqlalchemy.Model. Смотри models.py"


class InvalidPrimaryKey(InvalidSetItem):
    def __init__(self):
        self.text = "Неверно указан первичный ключ, который, как и его значение должен содержаться в словаре value"
