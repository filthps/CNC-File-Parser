import os
import time
import re
from typing import Optional, Union, Iterator, Tuple, Any
from abstractions import AbstractCNCFile
from temp import Temp
from config import TOOLS


class Tool:
    tools: dict[str, dict[tuple, tuple[int]]] = TOOLS

    @classmethod
    def start(cls, tool_name: str, header_data: dict, diameter: int):
        """
        Инициализация проверки
        :param tool_name:
        :param header_data:
        :param diameter:
        :return:
        """
        filename_data = cls.find_tool(cls.tools, tool_name, diameter)
        if not filename_data["tool"] or not filename_data["diam"] or filename_data["tool_family_name"] is None:
            return
        return filename_data

    @staticmethod
    def find_tool(tool_data, tool_name: str, tool_diameter: int) -> dict[str, bool, bool, Optional[str]]:
        """
        Запросить из константы TOOLS семейство, наименование инструмента и диаметр

        :param tool_data: архив доступного инструмента
        :param tool_name: искомый инструмент
        :param tool_diameter: искомый диаметр
        :return: результирующий словарь из 3 элементов
        """
        tool_name = str.lower(tool_name)
        status = {"tool": False, "diam": False, "tool_family_name": None}
        for tool_family, tools in tool_data:
            for tool, diam_tuple in tools:
                if tool_name == tool:
                    status["tool"] = True
                    status["tool_family_name"] = tool_family
                    if tool_diameter in diam_tuple:
                        status["diam"] = True
                        break
        return status

    @staticmethod
    def compare(filename_data, filehead_data):
        pass

class CNCFile(AbstractCNCFile, Tool):
    REPLACEMENT = {}  # ЧТо: На_что
    INVALID_SYMBOLS = ""
    IS_FULLNAME = True  # Сохранить файл с расширением или без
    APPROACH = 3  # Допустимое кол-во попыток открыть файл снова при ошибке
    MAX_NUM: Union[int, float] = float("inf")  # Максимально допустимый номер кадра
    LAST_SYMBOL = ""

    def __init__(self, path: str = "", name: str = "", frmt: Optional[str] = None):
        self._name: str = name
        self._format_: Optional[str] = frmt
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
        else:
            self.__full_path: str = f"{path}{name}"
        self._temp = Temp()
        self._origin = self.open(self.__full_path)
        self._length = len(self)
        if self._status:
            self._head_index = self.parse_head()


    def parse_name(self):
        full_name = re.match(r'(?P<name>[A-Z]?\d{2,5})_(?P<tool_name>\w+)_\w{1}(?P<diam>\d{1,3})', self._name)
        if bool(full_name):
            return full_name.groups()

    def parse_head(self):
        """
        :return: Кортеж с 2 позициями-индексами: начало и конец 'шапки'
        """
        end_index = self.find("G0") or False
        if not end_index:
            end_index = self.find("G1") or 0
        return 0, end_index

    def is_large(self):
        """
        Укладывается ли количество кадров в константу MAX_NUM - атрибут класса
        :return: bool()
        """
        return True if len(self) <= type(self).MAX_NUM else False

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
        else:
            self._status = True
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

    def is_valid_last_modify_attr(self):
        pass

    def is_valid_tail(self, symbol=""):
        if symbol:
            if not self.LAST_SYMBOL == symbol:
                self._status = False
                return False
        return True

    def get_status(self):
        return self._status

    def __iter__(self):
        self.is_origin()
        if self._origin is None:
            return iter(tuple())
        return iter(self._origin)

    def __getitem__(self, line_number):
        if line_number < 0:
            line_number = self._length - line_number
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

    def get_lines(self, index: int, count_: int = 1) -> Iterator[str]:
        """
        Извлечение среза содержимого файла
        :param index: индекс начала вхождения
        :param count_: количество возвращаемых строк
        :return: список строк
        """
        def gen():
            counter = 0
            counter_1 = 0
            for line in self:
                if counter < index:
                    counter += 1
                else:
                    if counter_1 <= count_:
                        yield line
                        counter_1 += 1
                    else:
                        break
        return gen()

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
