from typing import ClassVar
from factory import CNCFileFactory


class LinkedListItem:
    def __init__(self):
        self.__next = None

    @property
    def next(self):
        return self.__next

    @next.setter
    def next(self, val):
        self.__next = val


class LinkedList:
    def __init__(self, items=None, type_=None):
        self._head = None
        self._tail = None
        self._length = 0

        CNCFileFactory.FILE_TYPE = type_
        for item in items:
            inst = CNCFileFactory.create(item)
            self.append(inst)

    def append(self, elem):
        if len(self):
            last_element = self.forward_move(self._length)
            self.set_next(last_element, elem)
        else:
            self._head = self._tail = elem

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
        return next_element

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

