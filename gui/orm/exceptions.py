""" Исключения для всех классов в данном пакете """


class ORMException(Exception):
    def __init__(self):
        super().__init__()
        self.text = "Ошибка класса-адаптера ORMHelper"


class InvalidNodeItem(ORMException):
    def __init__(self):
        super().__init__()
        self.text = "Ошибка установки ноды в очередь"


class InvalidModel(InvalidNodeItem):
    def __init__(self):
        super().__init__()
        self.text = "Нужен класс CustomModel, наследованный от flask-sqlalchemy.Model. Смотри models.py"


class InvalidPrimaryKey(InvalidNodeItem):
    def __init__(self):
        super().__init__()
        self.text = "Неверно указан первичный ключ, который, как и его значение должен содержаться в словаре value"


class InvalidIsValidValue(InvalidNodeItem):
    def __init__(self):
        super().__init__()
        self.text = "Неверно указано значение параметра _is_valid, ожидается bool"
