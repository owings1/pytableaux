from __future__ import annotations

from callables import chain, preds
from utils import IndexType, IndexTypes, cat, instcheck, wrparens

import abc
from collections.abc import *
from copy import copy
import operator as opr
import typing
from typing import Any, Annotated, NamedTuple, TypeVar, Union, abstractmethod, cast

filter_identifier = chain.asfilter(preds.isidentifier)

T = TypeVar('T')


class ABCMeta(abc.ABCMeta):
    pass

class MapAttrView(MappingView, Mapping[str, T], metaclass = ABCMeta):
    """A Mapping view with attribute access."""

    # MappingView uses the '_mapping' slot.
    __slots__ = ('_mapping',)

    def __init__(self, base: Mapping[str, T]):
        self._mapping = instcheck(base, Mapping)

    def __getattr__(self, name: str):
        try: return self._mapping[name]
        except KeyError: raise AttributeError(name)

    def __dir__(self):
        return list(filter_identifier(self))

    def __copy__(self) -> MapAttrView[T]:
        inst = object.__new__(self.__class__)
        inst._mapping = self._mapping
        return inst

    def __getitem__(self, key: str) -> T:
        return self._mapping[key]

    def __iter__(self) -> Iterator[str]:
        yield from self._mapping

    def __reversed__(self) -> Iterator[str]:
        try: return reversed(self._mapping)
        except TypeError: return NotImplemented


class UniqueList(MutableSequence[T], MutableSet, metaclass = ABCMeta):

    __slots__ = ('__set', '__list')

    def __init__(self, items: Iterable[T] = None):
        self.__set = set()
        self.__list = []
        if items is not None: self.update(items)

    # ------------
    # List Methods
    # ------------
    def add(self, item: T):
        if item not in self:
            self.__set.add(item)
            self.__list.append(item)

    def update(self, items: Iterable[T]):
        for item in items: self.add(item)

    def discard(self, item: T):
        if item in self: self.remove(item)

    def union(self, other: Iterable) -> UniqueList[T]:
        inst = copy(self)
        if other is not self: inst.update(other)
        return inst

    def difference(self, other: Iterable):
        return self.__class__((x for x in self if x not in other))

    def difference_update(self, other: Iterable):
        for item in other: self.discard(item)
    
    def symmetric_difference(self, other: Iterable):
        inst = self.difference(other)
        inst.update((x for x in other if x not in self))
        return inst

    def symmetric_difference_update(self, other: Iterable):
        inst = self.symmetric_difference(other)
        self.clear()
        self.update(inst)

    def intersection(self, other: Iterable):
        return self.__class__((x for x in self if x in other))

    def intersection_update(self, other: Iterable):
        for item in self.__set.difference(other): self.remove(item)
    
    def issubset(self, other) -> bool:
        if isinstance(other, self.__class__):
            other = other.__set
        return self.__set.issubset(other)

    def issuperset(self, other) -> bool:
        if isinstance(other, self.__class__):
            other = other.__set
        return self.__set.issuperset(other)

    def __sub__(self, value: Iterable[T]):
        return self.difference(value)

    def __isub__(self, value: Iterable[T]):
        self.difference_update(value)
        return self

    def __getitem__(self, key: IndexType) -> T:
        return self.__list[key]

    def __delitem__(self, key: IndexType):
        instcheck(key, IndexTypes)
        if isinstance(key, int):
            self.pop(key)
        else:
            for item in self.__list[key]:
                self.__set.remove(item)
            del self.__list[key]

    def __setitem__(self, key, item: T):
        instcheck(key, int)
        se, li = self.__set, self.__list
        old = li[key]
        try:
            if old == item: return
        except TypeError: pass
        if item in se: raise ValueError('Duplicate: %s' % item)
        se.discard(item)
        se.add(item)
        li[key] = item

    def __add__(self, value: Iterable[T]) -> UniqueList[T]:
        inst = copy(self)
        if value is not self: inst.update(value)
        return inst

    def __iadd__(self, value: Iterable[T]) -> UniqueList[T]:
        if value is not self: self.update(value)
        return self

    def insert(self, index, item: T):
        se, li = self.__set, self.__list
        if item in se:
            if self.index(item) != index:
                raise ValueError('Duplicate: %s' % item)
        li.insert(index, item)
        se.add(item)

    def append(self, item: T):
        self.add(item)

    def extend(self, values):
        self.update(values)

    def count(self, item: T) -> int:
        return int(item in self)

    def index(self, item: T) -> int:
        return self.__list.index(item)

    def reverse(self):
        self.__list.reverse()

    def sort(self, **kw):
        self.__list.sort(**kw)

    # -------------------------
    # Dual Set and List methods
    # -------------------------

    def __len__(self):
        return len(self.__set)

    def __contains__(self, item: T):
        return item in self.__set

    def __iter__(self) -> Iterator[T]:
        yield from self.__list

    def __copy__(self) -> UniqueList[T]:
        return self.copy()

    def clear(self):
        self.__set.clear()
        self.__list.clear()

    def pop(self, *i: int) -> T:
        item = self.__list.pop(*i)
        self.__set.remove(item)
        return item

    def remove(self, item: T):
        # slow for list
        # list throws value error, set throws key error
        self.__set.remove(item)
        self.__list.remove(item)

    def copy(self) -> UniqueList[T]:
        return self.__class__(self)

    # ---------------
    # Comparisons
    # ---------------
    def cmpwrap(oper):
        fname = '__%s__' % oper.__name__
        def f(self: UniqueList, rhs):
            if isinstance(rhs, Set): lhs = self.__set
            elif isinstance(rhs, Sequence): lhs = self.__list
            else: return NotImplemented
            return oper(lhs, rhs)
        f.__qualname__ = fname
        return f

    __lt__ = cmpwrap(opr.lt)
    __le__ = cmpwrap(opr.le)
    __gt__ = cmpwrap(opr.gt)
    __ge__ = cmpwrap(opr.ge)

    __eq__ = cmpwrap(opr.eq)

    del(cmpwrap)

    def __repr__(self):
        return cat(self.__class__.__name__, wrparens(self.__list.__repr__()))
