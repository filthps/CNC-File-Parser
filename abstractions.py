from abc import ABC, abstractmethod, abstractproperty


class AbsOptionsNavigation(ABC):
    """
    Навигация по вкладке 'настройки'
    """


class Navigation(ABC):
    """
    Каждый метод описывает сигнал-навигация
    """

class Actions(ABC):
    """
    Каждый метод описывает сигнал-действие
    """


class AbsOptions(ABC, Navigation, Actions):
    """
    Каждый метод описывает сигнал-навигация
    """
