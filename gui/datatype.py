from abc import ABC, abstractmethod
from typing import Optional, Iterable, Union, Any, Iterator


class LinkedListItem:

    def __init__(self, val=None):
        self.value = val
        self.__next = None

    @property
    def next(self):
        return self.__next

    @next.setter
    def next(self, val):
        self.__is_valid_item(val)
        self.__next = val

    @classmethod
    def __is_valid_item(cls, item):
        if not type(item) is cls:
            raise TypeError

    def __repr__(self):
        return f"{type(self)}({self.value})"

    def __str__(self):
        return str(self.value)


class LinkedListAttributes(ABC):

    @abstractmethod
    def __init__(self):
        self._length: int = 0

    @classmethod
    def _set_next(cls, left_item: LinkedListItem, right_item: LinkedListItem):
        cls._is_valid_node(left_item)
        cls._is_valid_node(right_item)
        left_item.next = right_item

    @staticmethod
    def _forward_move(start_item: LinkedListItem, index):
        element = start_item
        for _ in range(index):
            element = element.next
        return element

    @classmethod
    def _is_valid_node(cls, obj):
        if not isinstance(obj, LinkedListItem):
            raise TypeError

    @staticmethod
    def _gen(start_item: Optional[LinkedListItem] = None) -> Iterator:
        current_item = start_item
        while current_item is not None:
            yield current_item.value
            current_item = current_item.next

    def __len__(self):
        if self._length:
            return self._length
        self._length = sum(tuple(1 for _ in self))
        return self._length

    @abstractmethod
    def __iter__(self):
        pass

    def __bool__(self):
        if len(self):
            return True
        return False

    def _is_valid_index(self, index):
        if not isinstance(index, int):
            raise TypeError
        if index >= len(self):
            raise IndexError


class LinkedList(LinkedListAttributes):

    def __init__(self, items: Optional[Iterable[Any]] = None):
        self.__head: Optional[LinkedListItem] = None
        self.__tail: Optional[LinkedListItem] = None
        super().__init__()
        if items is not None:
            [self.append(item) for item in items]

    def append(self, value):
        new_element = LinkedListItem(value)
        if self:
            last_elem = self.__tail
            self._set_next(last_elem, new_element)
            self.__tail = new_element
        else:
            self.__head = self.__tail = new_element

    def _forward_move(self, index: int):
        return super()._forward_move(self.__head, index)

    def __getitem__(self, index):
        self._is_valid_index(index)
        index = self._support_negative_index(index)
        return self._forward_move(index)

    def _support_negative_index(self, index: int):
        if index < 0:
            index = len(self) - index
        return index

    def __setitem__(self, index, value):
        self._is_valid_index(index)
        index = self._support_negative_index(index)
        new_element = LinkedListItem(value)
        if self:
            last_element = self._forward_move(index)
            self._set_next(last_element, new_element)
        else:
            self.__head = self.__tail = new_element

    def __delitem__(self, index):
        self._is_valid_index(index)
        index = self._support_negative_index(index)
        if not index:
            item = self._forward_move(index)
            next_item = item.next
            item.next = None
            self.__head = next_item
            return item
        item_prev = self._forward_move(index - 1)
        if index == len(self) - 1:
            item = item_prev.next
            item_prev.next = None
            self.__tail = item_prev
            return item
        current_item = item_prev.next
        next_item = current_item.next
        item_prev.next = next_item
        current_item.next = None
        return current_item

    def __iter__(self):
        return self._gen(self.__head)

    def __repr__(self):
        return f"{self.__class__}({tuple(self)})"

    def __str__(self):
        return str(tuple(self))


class LinkedDict(LinkedListAttributes):
    
    def __init__(self, items: Iterable[Union[tuple[Any, Any], list[Any, Any]]]):
        self.__keys = LinkedList()
        self.__values = LinkedList()
        super().__init__()
        for item in items:
            if len(item) != 2:
                raise ValueError
            self.update(*item)

    def update(self, key, value):
        self.__keys.append(key)
        self.__values.append(value)

    @classmethod
    def __set_next(cls, left_item: LinkedListItem, right_item: LinkedListItem):
        left_item.next = right_item

    def __iter__(self):
        return self._gen(self.__keys[0] if len(self.__keys) else None)

    def keys(self):
        return iter(self)

    def values(self):
        return self._gen(self.__values[0] if len(self.__values) else None)

    def items(self):
        return zip(self.keys(), self.values())

    def __getitem__(self, key: Any):
        value, index = self.__get_value(key)
        if value is None:
            raise KeyError
        return value

    def __get_value(self, key) -> Optional[tuple[Any, int]]:
        index = 0
        for k, value in self.items():
            if k == key:
                return value, index
            index += 1

    def __setitem__(self, key, value):
        value = self.__get_value(key)
        if value is not None:
            self.__keys.append(key)
            self.__values.append(value)

    def __delitem__(self, item):
        value, index = self.__get_value(item)
        if value is not None:
            del self.__keys[index]
            del self.__values[index]
            return value
        raise KeyError

    def __repr__(self):
        return list(self)

    def __str__(self):
        return str(tuple(self.items()))


if __name__ == "__main__":
    list_ = LinkedList([6, 8, 10, 434])
    print(list_)
    dict_ = LinkedDict([[1, 2], ["key", "value"], ("key", "value")])
    dict_.update("Ключ", 4)
    print(dict_)
