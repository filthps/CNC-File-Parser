import os
from typing import Callable
from uuid import uuid4
from config import MACHINES_INPUT_PATH, THREADS


def re_numerate(func: Callable):
    """
    :param root_f: Декорируемая функция
    :return: Функция декоратор
    """
    def wrapper(path):
        pass


def file_locker(f: Callable):
    """
    :param f: Декорируемая функция
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


def sort(t: Callable):
    """
    1) Сортировать словарь, содержащий информацию об объёме задачи:
    самые длинные задачи в начало
    2) В декорируемой функции условием выбирать самые длинные
    3) Выделять потоки исходя из средне-арифметического значения

    :param t: Декорируемая функция
    :return: Функция - декоратор
    """
    def get_threads(available_threads:int = THREADS, size: int = 1):
        """

        :param available_threads:
        :param size:
        :return:
        """

    sorted_stats = None
    all_tasks_length = None
    available_threads = THREADS
    sorted_data = {}

    def wrap(task):
        nonlocal sorted_stats, all_tasks_length, available_threads
        data, stats = t(task)
        if sorted_stats is None:
            all_tasks_length = sum(map(lambda val: len(val), stats.values()))
            # 1. Найти дробную долю задачи на конкретный станок, относительно длины всех задач
            # (разделить длину задач на конкретный станок / длина всех задач)
            sorted_stats = {key: stats[key] / all_tasks_length  for key in stats.keys()}
            # 2. Найти долю полученного коэффициента от длины всех потоков
            sorted_stats = {key: THREADS * sorted_stats[key] for key in stats.keys()}
            # 3. Определить разбивать ли конкретную задачу на несколько, и если да, то на сколько
        # На сколько частей разбивается конкретная задача
        return data, round(sorted_data[data[data.keys()[0]]])


def slice(c: Callable):
    """
    Вернуть список словарей, длина списка соответствует размеру доступных потоков
    :param c: декорируемая функция
    :return: функция-декоратор
    """
    main_store = []
    store = [] # Для маленьких задач

    def list_slice(l):
        pass

    def wrapper(task: list[dict], parts: int):
        nonlocal main_store, store
        machine_name = task.keys()[0]
        if parts < 1:
            store.append(task)
        else:
            main_store.append()
        main_store.append(store)
    return wrapper