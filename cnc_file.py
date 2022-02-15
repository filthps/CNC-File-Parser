import os
import time
from abstractions import AbstractCNCFile
from temp import Temp
from data_type import LinkedListItem


class CNCFile(AbstractCNCFile, LinkedListItem):
    REPLACEMENT_QUEUE = {}  # ЧТо: На_что
    INVALID_SYMBOLS = ""
    IS_FULLNAME = True  # Сохранить файл с расширением или без
    APPROACH = 3

    def __init__(self, path: str = None, name: str = None, frmt: str = None):
        super(LinkedListItem, self).__init__()
        self.name = name
        self.format_ = frmt
        self.__full_path = f"{path}{name}.{frmt}"
        self._length = 0
        self.__last_modify_time = None
        self.__f_size = None
        self._head_attrs = {}
        self.is_numerate = False
        self._status = False
        self._origin = None
        self._temp = None
        self.__open_errors_counter = 0
        self._temp = Temp()
        self.__is_origin = None
        self._length = len(self)

    def parse_head(self):
        pass

    def find_head_template(self):
        pass

    def is_origin(self):
        """
         Каждый новый цикл итераций по экземпляру подразумевает open(file, 'r'),
         в связи с этим обстоятельством придётся проверить - тот ли самый файл перед нами:
         Если вес или время последнего редактирования изменились с
         момента первого откртия файла - это не оригинальный файл!
        """
        if self.__last_modify_time is None:
            attrs_obj = os.stat(self.__full_path)
            self.__last_modify_time = attrs_obj.st_mtime
            self.__f_size = attrs_obj.st_size
        attrs_obj = os.stat(self.__full_path)
        if attrs_obj.st_mtime != self.__last_modify_time or attrs_obj.st_size != self.__f_size:
            raise FileNotFoundError(f"Исходный файл программы - {self.__full_path} изменился. Отмена")

    def open(self, path, mode="r"):
        try:
            origin = open(path, mode, encoding="utf-8")
        except OSError:
            self.re_connect(path, mode=mode)
        else:
            if origin.closed:
                self.re_connect(path, mode=mode)
            return origin

    def re_connect(self, path, mode="r"):
        self.__open_errors_counter += 1
        if self.__open_errors_counter == self.APPROACH:
            self._status = None
            raise FileNotFoundError
        time.sleep(1)
        origin = self.open(path, mode=mode)
        return origin

    def is_valid_index(self, index):
        if not 0 <= index < self._length:
            raise IndexError
        return True

    def get_status(self):
        return self._status

    def __iter__(self):
        self.is_origin()
        self._origin = self.open(self.__full_path)
        if self._origin is None:
            return iter(tuple())
        return self._origin

    def __getitem__(self, line_number):
        if not self.is_valid_index(line_number):
            return
        if self._status is not None:
            for index, line in enumerate(self):
                if index == line_number:
                    item = line
                    return item

    def get_lines(self, index, count_=1) -> list:
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
        if cls.IS_FULLNAME:
            return f"{name}.{format_}"
        return name
