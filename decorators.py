import os
from typing import Callable

from config import MACHINES_INPUT_PATH


def re_numerate(func: Callable):
    """
    :param root_f: Декорируемая функция
    :return: Функция декоратор
    """
    def wrapper(path):
        pass


def file_locker(f: Callable):
    """
    :param root_f: Декорируемая функция
    :return: Функция декоратор

    Заблокировать файл
        """
    def wrap(path):
        file = open(path, "at")
        result = f(path)
        file.flush()
        return result
    return wrap

def init_path_tree(root_f: Callable):
    """
    :param root_f: Декорируемая функция
    :return: Функция декоратор

    Создать пустые каталоги, в которые можно закинуть
    файлы программ для форматирования.
    """
    def func():
        for machine_path in MACHINES_INPUT_PATH.values():
            if not os.path.exists(machine_path):
                os.makedirs(machine_path)
        return root_f()
    return func