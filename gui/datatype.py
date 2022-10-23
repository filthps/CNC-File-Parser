from typing import Optional, Iterable, Union, Any


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


class LinkedList:
    def __init__(self, items=None):
        self._head = None
        self._tail = None
        self.__length = 0
        if items is not None:
            [self.append(item) for item in items]

    def append(self, value):
        new_element = LinkedListItem(value)
        if len(self):
            last_elem = self._tail
            self.__set_next(last_elem, new_element)
            self._tail = new_element
        else:
            self._head = self._tail = new_element

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

    def __iter__(self):
        def gen():
            current_item = self._head
            while current_item is not None:
                yield current_item
                current_item = current_item.next
        return gen()

    def __len__(self):
        if self.__length:
            return self.__length
        self.__length = sum((1 for _ in self))
        return self.__length

    def __bool__(self):
        if len(self):
            return True
        return False

    def __forward_move(self, index):
        element = self._head
        for _ in range(index):
            element = element.next
        return element

    def __is_valid_index(self, index):
        if not isinstance(index, int):
            raise TypeError
        if index >= len(self):
            raise IndexError

    def __getitem__(self, index):
        self.__is_valid_index(index)
        return self.__forward_move(index)

    def __setitem__(self, index, value):
        if index < 0:
            index = len(self) - index
        new_element = LinkedListItem(value)
        self.__is_valid_index(index)
        if len(self):
            last_element = self.__forward_move(index)
            self.__set_next(last_element, new_element)
        else:
            self._head = self._tail = new_element

    def __delitem__(self, index):
        self.__is_valid_index(index)
        if not index:
            item = self.__forward_move(index)
            next_item = item.next
            item.next = None
            self._head = next_item
            return item
        item_prev = self.__forward_move(index - 1)
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
        return f"{self.__class__}({tuple(self)})"

    def __str__(self):
        return tuple(self)


class LinkedDict(LinkedList):
    
    def __init__(self, items: Iterable[Iterable[Union[tuple[Any, Any], list[Any, Any], frozenset[Any, Any]]]]):
        self.__keys = LinkedList()
        self.__values = LinkedList()
        self.__length = 0
        for item in items:
            for element in item:
                if len(element) != 2:
                    raise ValueError
                self.update(*element)

    def update(self, key, value):
        return self.__setitem__(key, value)

    @classmethod
    def __set_next(cls, left_item: LinkedListItem, right_item: LinkedListItem):
        left_item.next = right_item

    def __keys_gen(self):
        next_element = self.__keys
        while next_element is not None:
            current_element = next_element.next
            yield next_element
            if current_element is None:
                break
            next_element = current_element



    def __iter__(self):
        return self.__items_gen()

    def __len__(self):
        if self.__length:
            return self.__length
        self.__length = sum((1 for _ in self))
        return self.__length

    def __bool__(self):
        if len(self):
            return True
        return False

    def __forward_move(self, index):
        element = self._head
        for _ in range(index):
            element = element.next
        return element

    def __getitem__(self, index):
        self.__is_valid_index(index)
        return self.__forward_move(index)

    def __setitem__(self, key, value):
        new_element = self.ITEM_TYPE(key, value)
        if len(self):
            last_element = self.__forward_move(self.keys()[len(self) - 1])
            self.__set_next(last_element, new_element)
        else:
            self._head = self._tail = new_element

    def __delitem__(self, index):
        self.__is_valid_index(index)
        if not index:
            item = self.__forward_move(index)
            next_item = item.next
            item.next = None
            self._head = next_item
            return item
        item_prev = self.__forward_move(index - 1)
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
