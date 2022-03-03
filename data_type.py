from typing import ClassVar, Any
from factory import CNCFileFactory


class LinkedListItem:
    def __init__(self, val: Any = None):
        self.__next = None
        self.value = val

    @property
    def next(self):
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
        self._head = None
        self._tail = None
        self._length = 0

        CNCFileFactory.FILE_TYPE = type_
        for item in items:
            inst = CNCFileFactory.create(item)
            self.append(LinkedListItem(inst))

    def append(self, elem):
        if self._length:
            last_element = self.forward_move(self._length)
            self.set_next(last_element, elem)
        else:
            self._head = self._tail = elem

    def is_valid_index(self, value: int):
        if

    @staticmethod
    def set_next(left_item: LinkedListItem, right_item: LinkedListItem):
        left_item.next = right_item

    def items_gen(self):
        next_element = self._head
        while next_element is not None:
            current_element = next_element.next
            yield next_element
            if current_element is not None:
                next_element = current_element
            else:
                break

    def __iter__(self):
        return self.items_gen()

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
            next_element = element.next
            if next_element is None:
                raise IndexError
            element = next_element
        return element

    def __getitem__(self, item):
        return self.forward_move(item)

    def __repr__(self):
        return list(self.__iter__())

    def __str__(self):
        return str(list(self.__iter__()))
