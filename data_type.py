from typing import Any, Optional, Iterable
from converter.cnc_file import CNCFile


class LinkedListItem:
    def __init__(self, val: Any = None):
        self.__next = None
        self.value = val

    @property
    def next(self) -> Optional[CNCFile]:
        return self.__next

    @next.setter
    def next(self, val):
        self.__next = val

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"{self.__class__}({self.value})"


class LinkedList:
    NODE_TYPE = LinkedListItem

    def __init__(self, *items_, node=None):
        if node is not None:
            self.NODE_TYPE = node
        self.head = None
        self.tail = None
        self._length: int = 0
        self._initial(items_)

    def _initial(self, items):
        for item in items:
            self.append(item)

    def append(self, elem):
        if len(self):
            last_element = self.forward_move(len(self))
            self.__set_next(last_element, self._wrap_element(elem))
        else:
            self.head = self.tail = self._wrap_element(elem)

    def __is_valid_index(self, value: int):
        if not isinstance(value, int):
            raise TypeError
        if value >= self._length:
            raise IndexError

    @classmethod
    def __is_valid_node(cl, obj):
        if not isinstance(obj, cl.NODE_TYPE):
            raise TypeError

    @classmethod
    def _wrap_element(cls, element):
        return cls.NODE_TYPE(element)

    @classmethod
    def __set_next(cls, left_item: LinkedListItem, right_item: LinkedListItem):
        try:
            cls.__is_valid_node(left_item)
            cls.__is_valid_node(right_item)
        except TypeError:
            return
        left_item.next = right_item

    def __items_gen(self) -> Optional[CNCFile]:
        next_element = self.head
        while next_element is not None:
            current_element = next_element.next
            yield next_element.value
            if current_element is None:
                break
            next_element = current_element

    def __iter__(self) -> CNCFile:
        return self.__items_gen()

    def __len__(self):
        if not self._length:
            return self._length
        self._length = sum((1 for _ in self))
        return self._length

    def __bool__(self):
        if self._length:
            return True
        return False

    def forward_move(self, index):
        element = self.head
        for _ in range(index):
            element = element.next
        return element

    def __getitem__(self, index):
        self.__is_valid_index(index)
        return self.forward_move(index)

    def __delitem__(self, index):
        self.__is_valid_index(index)
        if index == 0:
            item = self.forward_move(index)
            next_item = item.next
            item.next = None
            self.head = next_item
            return item
        item_prev = self.forward_move(index - 1)
        if index == len(self) - 1:
            item = item_prev.next
            item_prev.next = None
            self.tail = item_prev
            return item
        current_item = item_prev.next
        next_item = current_item.next
        item_prev.next = next_item
        current_item.next = None
        return current_item

    def __contains__(self, item):
        for i in self:
            if i == item:
                return True
        return False

    def __repr__(self):
        return list(self)

    def __str__(self):
        return str(list(self))


class LinkedListDictionary:

    def __init__(self, *values: tuple):
        self.__keys = LinkedList(*self.__get_items(values, 0))
        self.__values = LinkedList(*self.__get_items(values, 1))

    @staticmethod
    def is_valid(v):
        if not isinstance(v, tuple):
            raise TypeError

    @staticmethod
    def __get_items(items, index):
        return (item[index] for item in items)

    def get(self, item, alt_val=None):
        v = None
        for key, value in self.items():
            if str(key) == str(item):
                v = value
        return v or alt_val

    def update(self, item: tuple):
        self.__setitem__(item)

    def pop(self, item):
        item = self.get(item)
        if item is not None:
            del self[item]
        return item

    @staticmethod
    def __find_index(container, elem):
        counter = 0
        for i in container:
            if i == elem:
                break
            counter += 1
        if counter:
            return counter
        return

    def items(self):
        return self.gen()

    def keys(self):
        return self.__keys.__iter__()

    def values(self):
        return self.__values.__iter__()

    def gen(self):
        key_next_item = self.__keys.head
        value_next_item = self.__values.head
        while True:
            if key_next_item is None or value_next_item is None:
                return
            yield key_next_item, value_next_item
            key_next_item = key_next_item.next
            value_next_item = value_next_item.next

    def __iter__(self):
        return self.keys()

    def __getitem__(self, item: str):
        if item not in self.__keys:
            raise KeyError
        for key, value in self.items():
            if str(key) == str(item):
                return value

    def __setitem__(self, val: tuple):
        self.is_valid(val)
        if not isinstance(val, tuple):
            raise TypeError
        if not len(val) == 2:
            raise ValueError
        self.__keys.append(val[0])
        self.__values.append(val[1])

    def __delitem__(self, key):
        key_index = self.__find_index(self.keys(), key)
        del self.__keys[key_index]
        del self.__values[key_index]

    def __contains__(self, item):
        for i in self:
            if item == i:
                return True
        return False

    def __str__(self):
        s = ""
        for k, v in self.items():
            s += str((str(k), str(v),))
        return s

    def __repr__(self):
        return f"{self.__class__.__name__}({str(self)})"


if __name__ == "__main__":
    d = LinkedListDictionary(("q", "sdfsdfsdf"), (123, "sdfsdfsdf"), ("test", "strt"))
    print(d.items())
    d.update(("232", "sdfsdfsdf"))
    print(d.items())
    print("232" in d)
