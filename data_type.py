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

    def __init__(self, items_: Iterable[Any] = tuple(), node=None):
        if node is not None:
            self.NODE_TYPE = node
        self._head = None
        self._tail = None
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
            self._head = self._tail = self._wrap_element(elem)

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
        next_element = self._head
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
        element = self._head
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
            self._head = next_item
            return item
        item_prev = self.forward_move(index - 1)
        if index == len(self) - 1:
            item = item_prev.next
            item_prev.next = None
            self._tail = item_prev
            return item
        current_item = item_prev.next
        next_item = current_item.next
        item_prev.next = next_item
        current_item.next = None
        return current_item

    def __repr__(self):
        return list(self)

    def __str__(self):
        return str(list(self))


class LinkedListDictionary(LinkedList):
    _append = LinkedList.append

    def __init__(self, items: dict):
        super().__init__(items.values(), node=self.NODE_TYPE)
        self.__keys = LinkedList(items.keys())

    def update(self, key, elem):
        self.__keys.append(key)
        if len(self):
            last_element = self.forward_move(len(self))
            self.__set_next(last_element, self._wrap_element(elem))
        else:
            self._head = self._tail = self._wrap_element(elem)

    def items(self):
        return self.gen()

    def keys(self):
        return self.__keys.__iter__()

    def values(self):
        return super().__iter__()

    def gen(self):
        key_next_item = self.__keys._head
        value_next_item = self._head
        print()
        while True:
            if key_next_item is None or value_next_item is None:
                return
            yield key_next_item, value_next_item
            key_next_item = key_next_item.next
            value_next_item = value_next_item.next

    def __iter__(self):
        return self.keys()

    def __getitem__(self, item: str):
        if not item == self.__key:
            raise KeyError
        return self.value

    def __setitem__(self, key, value):
        if not isinstance(key, (str, bool, tuple, int)):
            raise KeyError
        self.__keys.append(key)
        self._append(value)

    def __str__(self):
        d = {}
        for k, v in self.items():
            d.update({str(k): str(v)})
        return str(d)


if __name__ == "__main__":
    d = LinkedListDictionary({"q": "sdfsdfsdf", 123: "sdfsdfsdf"})
    print(d)
