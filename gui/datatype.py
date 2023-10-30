import weakref
import copy
from abc import ABC, abstractmethod
from weakref import ref
from typing import Optional, Iterable, Union, Any, Iterator


class LinkedListItem:

    def __init__(self, val=None):
        self.val = val
        self._index = 0
        self.__next = None
        self.__prev = None

    @property
    def next(self):
        return self.__next

    @next.setter
    def next(self, val: Optional["LinkedListItem"]):
        self._is_valid_item(val)
        self.__next = val
        if not val:
            return
        val.index = self._index + 1

    @property
    def prev(self):
        return self.__prev

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        if not isinstance(value, int):
            raise TypeError
        if value < 0:
            raise ValueError
        self._index = value

    @prev.setter
    def prev(self, item: Optional["LinkedListItem"]):
        self._is_valid_item(item)
        if not item:
            return
        self.__prev = ref(item)
        if not self._index:
            item.index = 0
            self._index = 1
        else:
            item.index = self._index - 1

    @classmethod
    def _is_valid_item(cls, item):
        if item is None:
            return
        if not type(item) is cls:
            raise TypeError

    def __eq__(self, other: "LinkedListItem"):
        self._is_valid_item(other)
        return self.val == other.val

    def __repr__(self):
        return f"{type(self)}({self.val})"

    def __str__(self):
        return str(self.val)


class LinkedList:
    LinkedListItem = LinkedListItem

    def __init__(self, items: Optional[Iterable[Any]] = None):
        self._head: Optional[LinkedListItem] = None
        self._tail: Optional[LinkedListItem] = None
        if items is not None:
            [self.append(val=item) for item in items]

    @property
    def head(self):
        return self._head

    @property
    def tail(self):
        return self._tail

    def append(self, **kwargs):
        """
        Добавить ноду в нонец
        """
        new_element = self.LinkedListItem(**kwargs)
        if self:
            last_elem = self._tail
            self.__set_next(last_elem, new_element)
            self._tail = new_element
        else:
            self._head = self._tail = new_element

    def add_to_head(self, **kwargs):
        """
        Добавить ноду в начало
        """
        node = self.LinkedListItem(**kwargs)
        if not self:
            self._head = self._tail = node
            return
        first_elem = self._head
        self._head = node
        node.next = first_elem

    def replace(self, old_node: LinkedListItem, new_node: LinkedListItem):
        if not isinstance(old_node, self.LinkedListItem) or not isinstance(new_node, self.LinkedListItem):
            raise TypeError
        if not len(self):
            return
        if len(self) == 1:
            self._head = self._tail = new_node
            return
        next_node = old_node.next
        previous_node = old_node.prev()
        if old_node.index == len(self) - 1:
            self._tail = new_node
        if old_node.index == 0:
            self._head = new_node
        previous_node.next = new_node
        next_node.prev = new_node
        return new_node

    def __getitem__(self, index):
        index = self.__support_negative_index(index)
        self._is_valid_index(index)
        return self.__forward_move(index)

    def __support_negative_index(self, index: int):
        if index < 0:
            index = len(self) + index
        return index

    def __setitem__(self, index, value):
        index = self.__support_negative_index(index)
        self._is_valid_index(index)
        new_element = self.LinkedListItem(value)
        if self:
            last_element = self.__forward_move(index)
            self.__set_next(last_element, new_element)
        else:
            self._head = self._tail = new_element

    def __delitem__(self, index):
        def decr_index_for_nex_items(cur_item: LinkedListItem):  # O(n)
            while cur_item:
                cur_item.index -= 1
                cur_item = cur_item.next
        index = self.__support_negative_index(index)
        self._is_valid_index(index)
        if not index:
            item = self.__forward_move(index)
            next_item = item.next
            item.next = None
            if next_item is not None:
                next_item.index = 0
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
        decr_index_for_nex_items(current_item)
        return current_item

    def __iter__(self):
        return self.__gen(self._head)

    def __repr__(self):
        return f"{self.__class__}({tuple(self)})"

    def __str__(self):
        return str([str(x) for x in self])

    def _replace_inner(self, new_head: LinkedListItem, new_tail: LinkedListItem):
        """
        Заменить значения инкапсулированных атрибутов head и tail на новые
        """
        if type(new_head) is not self.LinkedListItem or type(new_tail) is not self.LinkedListItem:
            raise TypeError
        self._head = new_head
        self._tail = new_tail

    def __len__(self):
        return sum(tuple(1 for _ in self))

    def __bool__(self):
        if len(self):
            return True
        return False

    def __contains__(self, item):
        if type(item) is not self.LinkedListItem:
            return False
        if not item:
            return False
        for node in self:
            if node == item:
                return True
        return False

    def _is_valid_index(self, index):
        if not isinstance(index, int):
            raise TypeError
        if index >= len(self):
            raise IndexError

    @staticmethod
    def __set_next(left_item: Union[LinkedListItem, weakref.ref], right_item: Union[LinkedListItem, weakref.ref]):
        left_item = left_item() if hasattr(left_item, "__call__") else left_item  # Check item is WeakRef
        right_item = right_item() if hasattr(right_item, "__call__") else right_item  # Check item is WeakRef
        right_item.index = left_item.index + 1
        left_item.next = right_item

    @staticmethod
    def __set_prev(right_item: Union[LinkedListItem, weakref.ref], left_item: Union[LinkedListItem, weakref.ref]):
        left_item = left_item() if hasattr(left_item, "__call__") else left_item  # Check item is WeakRef
        right_item = right_item() if hasattr(right_item, "__call__") else right_item  # Check item is WeakRef
        right_item.prev = left_item

    def __forward_move(self, index=-1):
        element = self._head
        for _ in range(len(self) - 1 if index == -1 else index):
            element = element.next
        return element

    @staticmethod
    def __gen(start_item: Optional[LinkedListItem] = None) -> Iterator:
        current_item = start_item
        while current_item is not None:
            yield current_item
            current_item = current_item.next


if __name__ == "__main__":
    list_ = LinkedList([6, 8, 10, 434])

    def test_delitem():
        print(list_)
        del list_[0]
        print(list_)
        del list_[-2]
        print(list_)
        del list_[0]
        print(list_)
    #test_delitem()

    def test_add_to_head():
        list_1_ = LinkedList()
        list_1_.add_to_head(val=1)
        list_1_.add_to_head(val=2)
        list_1_.add_to_head(val=0)
        print(list_1_)
    test_add_to_head()
