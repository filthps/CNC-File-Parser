from typing import Optional


class Item:
    def __init__(self, key, val):
        self.key = key
        self.value = val
        self.__next = None

    @property
    def next(self):
        return self.__next

    @next.setter
    def next(self, val):
        self.__next = val


class LinkedList:
    ITEM_TYPE = Item

    def __init__(self, items: Optional[dict] = None):
        self.__head = None
        self.__tail = None
        self.__length = 0
        [self.update(key, value) for key, value in items.items()]

    def update(self, key, value):
        return self.__setitem__(key, value)

    @classmethod
    def __is_valid_node(cl, obj):
        if not isinstance(obj, cl):
            raise TypeError

    @classmethod
    def __set_next(cls, left_item: Item, right_item: Item):
        try:
            cls.__is_valid_node(left_item)
            cls.__is_valid_node(right_item)
        except TypeError:
            return
        left_item.next = right_item

    def __keys_gen(self):
        next_element = self.__head
        while next_element is not None:
            current_element = next_element.next
            yield next_element.key
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
        element = self.__head
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
            self.__head = self.__tail = new_element

    def __delitem__(self, index):
        self.__is_valid_index(index)
        if not index:
            item = self.__forward_move(index)
            next_item = item.next
            item.next = None
            self.__head = next_item
            return item
        item_prev = self.__forward_move(index - 1)
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

    def __repr__(self):
        return list(self)

    def __str__(self):
        return str(list(self))
