from typing import ClassVar, Any, Optional
from converter.cnc_file import CNCFile
from converter.factory import CNCFileFactory


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
    def __init__(self, items=None, type_: ClassVar = None):
        self._head: Optional[LinkedListItem] = None
        self._tail: Optional[LinkedListItem] = None
        self._length: int = 0

        CNCFileFactory.FILE_TYPE = type_
        for item in items:
            inst = CNCFileFactory.create(item)
            self.append(LinkedListItem(inst))

    def append(self, elem):
        if len(self):
            last_element = self.forward_move(len(self))
            self.__set_next(last_element, elem)
        else:
            self._head = self._tail = elem

    def __is_valid_index(self, value: int):
        if not isinstance(value, int):
            raise TypeError
        if value >= self._length:
            raise IndexError

    @classmethod
    def __is_valid_node(cl, obj):
        if not isinstance(obj, cl):
            raise TypeError

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
        if self._length:
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
