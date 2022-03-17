import os
import re
import time
from typing import Optional
from abstractions import AbstractCNCFile
from temp import Temp


class CNCFile(AbstractCNCFile):
    REPLACEMENT_QUEUE = {}  # ЧТо: На_что
    INVALID_SYMBOLS = ""
    IS_FULLNAME = True  # Сохранить файл с расширением или без
    APPROACH = 3  # Допустимое кол-во попыток открыть файл снова при ошибке

    def __init__(self, path: str = "", name: str = "", frmt: Optional[str] = None):
        self.name: str = name
        self.format_: Optional[str] = frmt
        self.__full_path: str = f"{path}{name}"
        self._length: int = 0
        self.__last_modify_time: Optional[int] = None
        self._origin: Optional[os.open] = None
        self.__f_size: int = 0
        self.is_numerate = False
        self._status = False
        self._temp: Optional[Temp] = None
        self._head_index: tuple[int, int] = (0, 0)
        self.__open_errors_counter: int = 0
        if frmt is not None:
            self.__full_path = f"{self.__full_path}{frmt}"
        self._temp = Temp()
        self._origin = self.open(self.__full_path)
        self._length = len(self)
        self._head_index = self.parse_head()

    def parse_head(self):
        """
        :return: Кортеж с 2 позициями-индексами: начало и конец 'шапки'
        """
        end_index = self.find("G0") or False
        if not end_index:
            end_index = self.find("G1") or 0
        return 0, end_index

    def is_origin(self):
        """
         Перед записью временного файла в целевой придётся проверить:
          1) Существует ли исходный файл
          2) тот ли самый файл перед нами: (Если вес или время последнего редактирования изменились с
         момента первого откртия файла - это не оригинальный файл!)
        """
        if not os.path.exists(self.__full_path):  # Файла не существует в исходном каталоге
            raise FileNotFoundError
        if self.__last_modify_time is None:
            attrs_obj = os.stat(self.__full_path)
            self.__last_modify_time = attrs_obj.st_mtime
            self.__f_size = attrs_obj.st_size
        attrs_obj = os.stat(self.__full_path)
        if attrs_obj.st_mtime != self.__last_modify_time or attrs_obj.st_size != self.__f_size:
            raise FileNotFoundError(f"Исходный файл программы - {self.__full_path} изменился. Отмена")

    def open(self, path, mode="rt"):
        """
        Рекурсивное открытие файла
        :param path: строка, путь к файлу
        :param mode: строка, режим открытия файла
        :return:
        """
        try:
            origin = open(path, mode, encoding="utf-8")
        except FileExistsError:
            return
        except OSError:
            return self.re_connect(path, mode)
        return origin

    def re_connect(self, path, mode="rt"):
        self.__open_errors_counter += 1
        if self.__open_errors_counter == self.APPROACH:
            self._status = None
            raise FileNotFoundError
        time.sleep(1)
        origin = self.open(path, mode)
        return origin

    def is_valid_index(self, index):
        if not 0 <= index < self._length:
            raise IndexError

    def get_status(self):
        return self._status

    def __iter__(self):
        self.is_origin()
        if self._origin is None:
            return iter(tuple())
        return iter(self._origin)

    def __getitem__(self, line_number):
        self.is_valid_index(line_number)
        if self._status is not None:
            for index, line in enumerate(self):
                if index == line_number:
                    item = line
                    return item

    def find(self, string: str = ""):
        """
        Найти строку файле

        :param string: искомая строка
        :return: индекс найденной строки
        """
        counter = 0
        for str_ in self:
            if str_ == string:
                return counter
            counter += 1

    def get_lines(self, index: int, count_: int = 1) -> list:
        """
        :param index: индекс начала вхождения
        :param count_: количество возвращаемых строк
        :return:
        """
        store = []
        counter = 0
        counter_1 = 0
        for line in self:
            if counter < index:
                counter += 1
            else:
                if counter_1 <= count_:
                    counter_1 += 1
                    store.append(line)
                else:
                    return store

    def is_valid_last_modify_attr(self):
        pass

    def remove_invalid_symbols(self):
        pass

    def __len__(self) -> int:
        if self._length:
            return self._length
        self._length = sum(1 for _ in self)
        return self._length

    def close(self):
        self._origin.close()

    def is_valid_numerate(self):
        pass

    def re_numerate(self):
        pass

    @classmethod
    def get_filename(cls, name: str, format_: str):
        if cls.IS_FULLNAME and format_ is not None:
            return f"{name}{format_}"
        return name
