from __future__ import annotations

from decorators import delegate, meta
from errors import DuplicateKeyError
from utils import ABCMeta, IndexType, IndexTypes, cat, instcheck, orepr, wrparens

# import abc
from collections.abc import *
from copy import copy
import enum
from functools import reduce, wraps
from itertools import chain, filterfalse
import operator as opr
from types import MappingProxyType, MethodType
import typing
from typing import Any, Annotated, Generic, NamedTuple, TypeVar, abstractmethod, final

from callables import calls, cchain, gets, preds

K = TypeVar('K')
T = TypeVar('T')
R = TypeVar('R')
V = TypeVar('V')

NOARG = enum.auto()

class SetlistPair(NamedTuple):
    set: set
    list: list

class MapAttrView(MappingView, Mapping[str, T], metaclass = ABCMeta):
    'A Mapping view with attribute access.'

    # MappingView uses the '_mapping' slot.
    __slots__ = ('_mapping',)

    def __init__(self, base: Mapping[str, T]):
        self._mapping = instcheck(base, Mapping)

    def __getattr__(self, name: str):
        try: return self._mapping[name]
        except KeyError: raise AttributeError(name)

    def __dir__(self):
        return list(filter(preds.isidentifier, self))

    def __copy__(self) -> MapAttrView[T]:
        inst = object.__new__(self.__class__)
        inst._mapping = self._mapping
        return inst

    def __getitem__(self, key: str) -> T:
        return self._mapping[key]

    def __iter__(self) -> Iterator[T]:
        yield from self._mapping

    def __reversed__(self) -> Iterator[str]:
        try: return reversed(self._mapping)
        except TypeError: raise NotImplementedError()


class UniqueList(MutableSequence[V], MutableSet, metaclass = ABCMeta):
    'A list/set hybrid.'

    __slots__ = '__base',

    def __init__(self, items: Iterable[V] = None):
        self.__base = SetlistPair(set(), [])
        if items is not None:
            self.update(items)

    # -------------   Collection ---------------

    def __contains__(self, value: V):
        return value in self.__base.set

    def __len__(self):
        return len(self.__base.list)

    # -------------------  Sequence  -------------------

    def __getitem__(self, index: IndexType) -> V:
        'Get value by index or slice.'
        return self.__base.list[index]

    def count(self, value: V) -> int:
        'Returns 1 if in the set, else 0.'
        return int(value in self)

    def index(self, value: V, start = 0, stop = None) -> int:
        'Get the index of the value in the list.'
        if value not in self:
            raise ValueError('%s is not in the list' % value)
        return Sequence.index(self, value, start, stop)

    # ---------------   MutableSequence ---------------

    def __delitem__(self, key: IndexType):
        'Delete by index or slice.'
        value = self[key]
        b = self.__base
        if isinstance(key, int):
            b.set.remove(value)
        else:
            for value in self[key]:
                b.set.remove(value)            
        del b.list[key]

    def __setitem__(self, index: int, value: V):
        'Set an the index to a value. Raises ValueError for duplicate..'
        instcheck(index, int)
        old = self[index]
        if value in self:
            if value == old:
                return
            raise ValueError('Duplicate: %s' % value)
        b = self.__base
        b.set.add(value)
        b.list[index] = value

    def insert(self, index: int, value: V):
        'Insert a value before an index. Raises ValueError for duplicate.'
        if value in self:
            raise ValueError('Duplicate: %s' % value)
        b = self.__base
        b.list.insert(index, value)
        b.set.add(value)

    def append(self, value: V):
        'Append an value. Raises ValueError for duplicate.'
        if value in self:
            raise ValueError('Duplicate: %s' % value)
        return MutableSequence.append(self, value)

    def reverse(self):
        'Reverse in place.'
        self.__base.list.reverse()

    def clear(self):
        'Clear the list and set.'
        if not len(self):
            return
        st, ls = self.__base
        # from sys import getrefcount
        # if getrefcount(st) + getrefcount(ls) > 4:
        #     MutableSequence.clear(self)
        del(st, ls, self.__base)
        self.__base = SetlistPair(set(), [])

    # ----------- builtin list --------------

    def __add__(self, rhs: Iterable[V]) -> UniqueList[V]:
        'Copy and extend, ignoring duplicates.'
        inst = self.copy()
        if rhs is not self:
            inst.update(rhs)
        return inst

    def sort(self, **kw):
        'Sort the list in place.'
        self.__base.list.sort(**kw)

    # ------- builtin set (non-mutating methods) ------------

    @meta.temp
    class iterator:
        '''Takes a method that returns an iterator, makes variations
        for the math operators, and replaces it with a method that
        returns a new collection.'''
        iterator: Callable
        left: Callable
        right: Callable

        def __new__(cls, iter_method) -> UniqueList.iterator:

            @wraps(iter_method)
            def method(self, other):
                return self._from_iterable(iter_method(self, other))

            def math_left(self, other):
                if not isinstance(other, Iterable):
                    return NotImplemented
                return self._from_iterable(iter_method(self, other))

            def math_right(self, other):
                if not isinstance(other, Iterable):
                    return NotImplemented
                if isinstance(other, Sequence):
                    fnew = self._from_iterable
                else:
                    fnew = set
                return fnew(iter_method(self, other))

            method: UniqueList.iterator = method
            method.iterator = iter_method
            method.left = math_left
            method.right = math_right
            return method

    @iterator
    def union(self, other: Iterable) -> UniqueList[V]:
        'Return the union as a new instance, appending new values.'
        if self is other: return iter(self)
        return chain(self, other)

    @iterator
    def intersection(self, other: Iterable) -> UniqueList[V]:
        'Return the intersection as a new instance.'
        if self is other: return iter(())
        if not isinstance(other, Container):
            other = set(other)
        return filter(other.__contains__, self)

    @iterator
    def difference(self, other: Iterable) -> UniqueList[V]:
        'Return the difference as a new instance, maintaining original order.'
        if self is other: return iter(())
        if not isinstance(other, Container):
            other = set(other)
        return filterfalse(other.__contains__, self)

    @iterator
    def symmetric_difference(self, other: Iterable) -> UniqueList[V]:
        'Return the symmetric difference as a new instance, appending new values.'
        if self is other: return iter(())
        if not isinstance(other, Container):
            other = set(other)
        return iter(()) if self is other else chain(
            filterfalse(other.__contains__, self),
            filterfalse(self.__contains__, other),
        )

    def issubset(self, other) -> bool:
        'Delegate to set.'
        return self is other or self.__base.set.issubset(other)

    def issuperset(self, other) -> bool:
        'Delegate to set.'
        return self is other or self.__base.set.issuperset(other)

    # --------------------- Set ------------------------

    @meta.temp
    def math(source):
        def f(method):
            wraps(method)(source)
            return source
        return f

    @math(intersection.left)
    def __and__(): ...
    @math(intersection.right)
    def __rand__(): ...

    @math(union.left)
    def __or__(): ...
    @math(union.right)
    def __ror__(): ...

    @math(difference.left)
    def __sub__(): ...
    @math(difference.right)
    def __rsub__(): ...

    @math(symmetric_difference.left)
    def __xor__(): ...
    @math(symmetric_difference.right)
    def __rxor__(): ...

    @meta.temp
    def order(method):
        # The Set implementation of < is subset.
        # Builtin list implements for list type only, so we add support here,
        #   since we can just compare the bases.
        # Disadvantage here is that our [1, 2] != list([2, 1]), but does equal {2, 1}
        oname = method.__name__
        oper = getattr(opr, oname)
        setfunc = getattr(Set, oname)
        @wraps(method)
        def f(self, other):
            setcmp = setfunc(self, other)
            if setcmp is NotImplemented:
                if isinstance(other, list):
                    return oper(self.__base.list, other)
            return setcmp
        return f

    @order
    def __le__(): ...
    @order
    def __lt__(): ...
    @order
    def __gt__(): ...
    @order
    def __ge__(): ...
    @order
    def __eq__(): ...


    # ------- builtin set (mutating methods) ------------

    def update(self, values: Iterable):
        'Append all values not in the set.'
        for value in values:
            self.add(value)

    def intersection_update(self, other: Iterable):
        'Remove any value that is not in the other.'
        if self is other:
            return
        for value in filterfalse(other.__contains__, self):
            self.remove(value)

    def difference_update(self, other: Iterable):
        'Discard any items contained in the other collection.'
        if other is self:
            return
        for value in filter(self.__contains__, other):
            self.remove(value)

    def symmetric_difference_update(self, other: Iterable):
        'Update the instance to contain the symmetric difference.'
        # It is cheaper to reconstruct the list than perform
        # individual removals.
        inst = self.symmetric_difference(other)
        self.clear()
        self.update(inst)

    # ---------------  MutableSet  --------------------

    def add(self, value: V):
        'Appends to the list if not in the set.'
        if value not in self:
            self.append(value)

    def discard(self, value: V):
        'Calls ``remove()`` and catches ValueError.'
        try:
            self.remove(value)
        except ValueError:
            pass

    @meta.temp
    def imath(source):
        def wrapper(method):
            @wraps(method)
            def f(self, it):
                if not isinstance(it, Iterable):
                    return NotImplemented
                source(self, it)
                return self
            return f
        return wrapper

    @imath(update)
    def __ior__(): ...
    @imath(intersection_update)
    def __iand__(): ...
    @imath(symmetric_difference_update)
    def __ixor__(): ...
    @imath(difference_update)
    def __isub__(): ...

    # -----------  Other -----------

    def __copy__(self):
        return self.copy()

    def copy(self) -> UniqueList[V]:
        return self.__class__(self)

    def __repr__(self):
        return cat(
            self.__class__.__name__,
            wrparens(self.__base.list.__repr__())
        )

    ImplNotes: Annotated[dict, {
        Collection: dict(
            implement = {'__contains__', '__len__'},
            inherit   = {'__iter__'},
        ),
        Sequence: dict(
            implement = {'__getitem__'},
            override  = {'count'},
            extend    = {'index'},
            inherit   = {'__reversed__'},
        ),
        MutableSequence: dict(
            implement = {'__setitem__', '__delitem__', 'insert'},
            override  = {'reverse', 'clear'},
            extend    = {'append'},
            inherit   = {'extend', 'pop', 'remove', '__iadd__'},
        ),
        list: dict(
            override = {'__add__'},
            delegate = {'sort'}
        ),
        set: dict(
            implement = {
                'union', 'intersection', 'difference', 'symmetric_difference', 
                'issubset','issuperset',
                'update', 'intersection_update', 'difference_update',
                'symmetric_difference_update',
            }
        ),
        Set: dict(
            override = {
                '__and__', '__rand__', '__or__', '__ror__',
                '__sub__', '__rsub__', '__xor__', '__rxor__',
            },
            extend   = {'__le__', '__lt__', '__gt__', '__ge__', '__eq__'},
            inherit = {'_hash', 'isdisjoint'},
        ),
        MutableSet: dict(
            implement = {'add', 'discard', },
            override  = {'remove', 'pop', 'clear',},
            inherit   = {'__ior__', '__iand__', '__ixor__', '__isub__'},
        )
    }]

class LinkedView(Collection[T], Reversible, metaclass = ABCMeta):
    'Abstract class for a linked collection view.'

    @abstractmethod
    def first(self) -> T: ...

    @abstractmethod
    def last(self) -> T: ...

class LinkEntry(Generic[T], Hashable, metaclass = ABCMeta):
    'An item container with prev/next attributes.'

    value: T
    prev: LinkEntry[T]
    next: LinkEntry[T]
    __slots__ = ('prev', 'next', 'value')

    def __init__(self, value, prev = None, next = None):
        self.value = value
        self.prev = prev
        self.next = next

    def __eq__(self, other):
        return self is other or self.value == other or (
            isinstance(other, self.__class__) and
            self.value == other.value
        )

    def dir(self, n):
        if n == 1: return self.next
        if n == -1: return self.prev
        if isinstance(n, int): raise ValueError(n)
        raise TypeError(n)

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return cat(self.__class__.__name__, wrparens(self.value.__repr__()))

class LinkOrderSet(LinkedView[T], Collection):

    def __init__(self, values: Iterable[T] = None, strict: bool = True):
        self.strict = strict
        self._link_first = self._link_last = None
        self._link_map: dict[Any, LinkEntry] = {}
        if values is not None:
            self.extend(values)

    slots = ('_link_first', '_link_last', '_link_map', 'strict', '_link_viewcls')

    def _genitem_(self, value) -> T:
        """Overridable hook method to transform an value before add/remove methods.
        The method must take at least one positional argument. Iterating methods
        such as ``extend`` iterate over the first argument, and call _genitem_
        with the remainder of the arguments for each value."""
        return value

    #: Decorators

    def itemhook(item_method: Callable[[T], R]) -> Callable[[T], R]:
        'Wrapper for add/remove methods that calls the _genitem_ hook.'
        @wraps(item_method)
        def wrap(self: LinkOrderSet, value, *args, **kw):
            value = self._genitem_(value, *args, **kw)
            return item_method(self, value)
        return item_method
        # return renamef(wrap, item_method)

    def newlink(link_method: Callable[[LinkEntry[T]], R]) -> Callable[[T], R]:
        """Wrapper for add item methods. Ensures the value is not already in the
        collection, and creates a LinkEntry. If the collection is empty, sets
        first and last, and returns. Otherwise, calls the original method with
        the link as the argument."""
        @wraps(link_method)
        def prep(self: LinkOrderSet, value):
            if value in self:
                if self.strict:
                    raise DuplicateKeyError(value)
                return
            link = self._link_map[value] = LinkEntry(value)
            if self._link_first is None:
                self._link_first = self._link_last = link
                return
            if self._link_first is self._link_last:
                self._link_first.next = link
            link_method(self, link)
        return link_method
        # return renamef(prep, link_method)

    @itemhook
    @newlink
    def append(self, link: LinkEntry[T]):
        if self._link_first is self._link_last:
            self._link_first.next = link
        link.prev = self._link_last
        link.prev.next = link
        self._link_last = link

    @itemhook
    @newlink
    def prepend(self, link: LinkEntry[T]):
        if self._link_first is self._link_last:
            self._link_last.prev = link
        link.next = self._link_first
        link.next.prev = link
        self._link_first = link

    @itemhook
    def remove(self, value: T):
        del self[value]

    def clear(self):
        self._link_map.clear()
        self._link_first = self._link_last = None

    def first(self, default = NOARG) -> T:
        if len(self):
            return self._link_first.value
        if default is not NOARG:
            return default
        raise IndexError('Empty collection')

    def last(self, default = NOARG) -> T:
        if len(self):
            return self._link_last.value
        if default is not NOARG:
            return default
        raise IndexError('Empty collection')

    def __getitem__(self, item: T | LinkEntry[T]) -> T:
        return self._link_map[item].value

    def __delitem__(self, item: T | LinkEntry[T]):
        link = self._link_map.pop(item)
        if link.prev is None:
            if link.next is None:
                # Empty
                self._link_first = self._link_last = None
            else:
                # Remove first
                link.next.prev = None
                self._link_first = link.next
        else:
            if link.next is None:
                # Remove last
                link.prev.next = None
                self._link_last = link.prev
            else:
                # Remove in-between
                link.prev.next = link.next
                link.next.prev = link.prev

    def __len__(self):
        return len(self._link_map)

    def __contains__(self, item: T | LinkEntry[T]):
        return item in self._link_map

    # def __eq__(self, other):
    #     return self is other or self._link_map == other

    def __iter__(self) -> Iterator[T]:
        if len(self):
            yield from self.iterfrom(self.first())

    def __reversed__(self) -> Iterator[T]:
        if len(self):
            yield from self.iterfrom(self.last(), reverse = True)

    def iterfrom(self, item: T | LinkEntry[T], reverse = False) -> Iterator[T]:
        cur = self._link_map[item]
        dir_ = -1 if reverse else 1
        while cur:
            value = cur.value
            yield value
            cur = cur.dir(dir_)

    def pop(self) -> T:
        'Remove and return the last value.'
        value = self.last()
        del self[value]
        return value

    def shift(self) -> T:
        'Remove and return the first value.'
        value = self.first()
        del self[value]
        return value

    def extend(self, values: Iterable[T], *args, **kw):
        'Iterable version of ``append()``.'
        for value in values:
            self.append(value, *args, **kw)

    def prependall(self, values: Iterable[T], *args, **kw):
        'Iterable version of ``prepend()``.'
        for value in values:
            self.prepend(value, *args, **kw)

    def add(self, value: T, *args, **kw):
        'Alias for ``append()``.'
        return self.append(value, *args, **kw)

    def update(self, values: Iterable[T], *args, **kw):
        'Alias for ``extend()``.'
        return self.extend(values, *args, **kw)

    def discard(self, value: T, *args, **kw):
        'KeyError safe version of ``remove()``.'
        try: self.remove(value, *args, **kw)
        except KeyError: pass

    def view(self) -> LinkedView[T]:
        try: return self._link_viewcls()
        except AttributeError: pass
        view = LinkOrderSetView(self)
        self._link_viewcls = view.__class__
        return view

    def copy(self) -> LinkOrderSet[T]:
        return self.__class__(self, self.strict)

    def __copy__(self) -> LinkOrderSet[T]:
        return self.copy()

    def __repr__(self):
        return orepr(self,
            len   = len(self),
            first = self.first(),
            last  = self.last(),
        )

    del(itemhook, newlink)

class LinkOrderSetView(LinkedView[T]):

    __slots__ = ()

    def __new__(cls, base: LinkedView):

        class ViewProxy(LinkOrderSetView):
            __slots__ = ()
            def __len__(self):
                return len(base)
            def __iter__(self) -> Iterator[T]:
                return iter(base)
            def __reversed__(self) -> Iterator[T]:
                return reversed(base)
            def __contains__(self, item):
                return item in base
            def __getitem__(self, key) -> T:
                return base[key]
            def first(self, *a) -> T:
                return base.first(*a)
            def last(self, *a) -> T:
                return base.last((a))
            def iterfrom(self, *a, **k):
                return base.iterfrom(*a, **k)
            def __repr__(self):
                return base.__class__.__repr__(self)
            __new__ = object.__new__
        ViewProxy.__qualname__ = '.'.join(
            (base.__class__.__qualname__, ViewProxy.__name__)
        )
        return ViewProxy()

