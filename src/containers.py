from __future__ import annotations

from errors import DuplicateKeyError
from utils import Decorators, IndexType, IndexTypes, cat, instcheck, orepr, wrparens

import abc
from collections.abc import *
from copy import copy
import enum
from functools import reduce
import operator as opr
from types import MappingProxyType
import typing
from typing import Any, Annotated, Generic, NamedTuple, TypeVar, abstractmethod, final

# from callables import calls, cchain, gets, preds
# filter_identifier = cchain.asfilter(preds.isidentifier)

K = TypeVar('K')
T = TypeVar('T')
R = TypeVar('R')

def renamefn(fnew: T, forig) -> T:
    fnew.__qualname__ = forig.__qualname__
    fnew.__name__ = forig.__name__
    return fnew

class AttrFlag(enum.Flag):
    Blank      = 0
    ClassVar   = 1
    Merge      = 2
    SubClass   = 4
    MergeSubClassVar = ClassVar | Merge | SubClass

class AttrNote(NamedTuple):

    cls: type
    attr: str

    otype: type
    flag: AttrFlag
    merger: Any = None
    endtype: type = None
    extra: list = []

    @classmethod
    def forclass(cls, Class: type) -> dict[str, AttrNote]:
        annot = typing.get_type_hints(Class, include_extras = True)
        notes = (
            cls(Class, attr, *vals[0:4], vals[4:])
            for attr, vals in (
                (k, typing.get_args(v))
                for k, v in annot.items()
                if typing.get_origin(v) is Annotated
            )
        )
        return dict((n.attr,n) for n in notes)

class ABCMeta(abc.ABCMeta):

    # __attrnotes__: Mapping[str, AttrNote]

    def __new__(cls, clsname, bases, attrs, **kw):
        Class = super().__new__(cls, clsname, bases, attrs, **kw)
        # notes = AttrNote.forclass(Class)
        # Class.__attrnotes__ = MappingProxyType(notes)
        return Class

    @staticmethod
    def merge_mroattr(subcls: type, attr: str, supcls: type = None, oper: Callable = opr.or_) -> dict:
        return reduce(oper, (
            getattr(c, attr)
            for c in reversed(subcls.mro())
            if issubclass(c, supcls or subcls)
        ))
        # pred = preds.subclassof[supcls or subcls]
        # clsit = filter(pred, reversed(subcls.mro()))
        # valit = map(gets.attr(attr), clsit)
        # return reduce(oper, valit)

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
        return list(k for k in self if isinstance(k, str) and k.isidentifier())

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

class UniqueList(MutableSequence[T], MutableSet, metaclass = ABCMeta):
    'A list/set hybrid.'

    __slots__ = ('__set', '__list')

    def __init__(self, items: Iterable[T] = None):
        self.__set = set()
        self.__list = []
        if items is not None: self.update(items)

    # ----------
    # Set Methods
    # -----------
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

    # -----------------
    # List Methods
    # -----------------

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

    def extend(self, values: Iterable[T]):
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

class LinkedView(Collection[T], Reversible, metaclass = ABCMeta):
    'Abstract class for a linked collection view.'

    @abstractmethod
    def first(self) -> T: ...

    @abstractmethod
    def last(self) -> T: ...

class LinkEntry(Generic[T], Hashable, metaclass = ABCMeta):
    'An item container with prev/next attributes.'

    item: T
    prev: Any#LinkEntry[T]
    next: Any#LinkEntry[T]
    __slots__ = ('prev', 'next', 'item')

    def __init__(self, item, prev = None, next = None):
        self.item = item
        self.prev = prev
        self.next = next

    def __eq__(self, other):
        return self is other or self.item == other or (
            isinstance(other, self.__class__) and
            self.item == other.item
        )

    def __hash__(self):
        return hash(self.item)

    def __repr__(self):
        return cat(self.__class__.__name__, wrparens(self.item.__repr__()))


class LinkOrderSet(LinkedView[T], Collection):

    def _genitem_(self, item) -> T:
        """Overridable hook method to transform an item before add/remove methods.
        The method must take at least one positional argument. Iterating methods
        such as ``extend`` iterate over the first argument, and call _genitem_
        with the remainder of the arguments for each item.
        """
        return item

    # ----------
    # Decorators
    # ----------

    def itemhook(item_method: Callable[[T], R]) -> Callable[..., R]:
        'Wrapper for add/remove methods that calls the _genitem_ hook.'
        def wrap(self: LinkOrderSet, item, *args, **kw):
            item = self._genitem_(item, *args, **kw)
            return item_method(self, item)
        return renamefn(wrap, item_method)

    def newentry(entry_method: Callable[[LinkEntry], R]) -> Callable[[T], R]:
        """Wrapper for add item methods. Ensures the item is not already in the
        collection, and creates a LinkEntry. If the collection is empty, sets
        first and last, and returns. Otherwise, calls the original method with
        the entry as the argument.
        """
        def prep(self: LinkOrderSet, item):
            if item in self:
                if self.strict:
                    raise DuplicateKeyError(item)
                return
            entry = self.__idx[item] = LinkEntry(item)
            if self.__first is None:
                self.__first = self.__last = entry
                return
            if self.__first == self.__last:
                self.__first.next = entry
            entry_method(self, entry)
        return renamefn(prep, entry_method)

    slots = ('__first', '__last', '__idx', 'strict', '_utils__lazy_view')

    @itemhook
    @newentry
    def append(self, entry: LinkEntry):
        if self.__first == self.__last:
            self.__first.next = entry
        entry.prev = self.__last
        entry.prev.next = entry
        self.__last = entry

    @itemhook
    @newentry
    def prepend(self, entry: LinkEntry):
        if self.__first == self.__last:
            self.__last.prev = entry
        entry.next = self.__first
        entry.next.prev = entry
        self.__first = entry

    def extend(self, items, *args, **kw):
        for item in items:
            self.append(item, *args, **kw)

    def prependall(self, items, *args, **kw):
        for item in items:
            self.prepend(item, *args, **kw)

    @final
    def add(self, *args, **kw):
        return self.append(*args, **kw)

    @final
    def update(self, *args, **kw):
        return self.extend(*args, **kw)

    @itemhook
    def remove(self, item):
        entry = self.__idx.pop(item)
        if entry.prev == None:
            if entry.next == None:
                # Empty
                self.__first = self.__last = None
            else:
                # Remove first
                entry.next.prev = None
                self.__first = entry.next
        else:
            if entry.next == None:
                # Remove last
                entry.prev.next = None
                self.__last = entry.prev
            else:
                # Remove in-between
                entry.prev.next = entry.next
                entry.next.prev = entry.prev

    def pop(self):
        if not len(self):
            raise IndexError('pop from empty collection')
        item = self.last()
        self.remove(item)
        return item

    def shift(self):
        if not len(self):
            raise IndexError('shift from empty collection')
        item = self.first()
        self.remove(item)
        return item

    @itemhook
    def discard(self, item):
        try: self.remove(item)
        except KeyError: pass
    
    def clear(self):
        self.__idx.clear()
        self.__first = self.__last = None

    def first(self) -> T:
        return self.__first.item if self.__first else None

    def last(self) -> T:
        return self.__last.item if self.__last else None

    @property
    @Decorators.lazyget
    def view(self) -> LinkedView[T]:
        return LinkOrderSetView(self)

    def __init__(self, items: Iterable = None, strict = True):
        self.strict = strict
        self.__first = self.__last = None
        self.__idx: dict[Any, LinkEntry] = {}
        if items is not None:
            self.extend(items)

    def __len__(self):
        return len(self.__idx)

    def __contains__(self, item):
        return item in self.__idx

    def __getitem__(self, key):
        return self.__idx[key].item

    def __delitem__(self, key):
        self.remove(key)

    def __iter__(self):
        cur = self.__first
        while cur:
            item = cur.item
            yield item
            cur = cur.next
                
    def __reversed__(self):
        cur = self.__last
        while cur:
            item = cur.item
            yield item
            cur = cur.prev

    def __copy__(self):
        return self.__class__((x for x in self))

    def __repr__(self):
        return orepr(self,
            len = len(self),
            first = self.first(),
            last = self.last(),
        )

    del(itemhook, newentry)

class LinkOrderSetView(LinkedView[T]):
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
            def first(self) -> T:
                return base.first()
            def last(self) -> T:
                return base.last()
            def __repr__(self):
                return base.__class__.__repr__(self)
            def __copy__(self):
                return self.__class__()
        ViewProxy.__qualname__ = '.'.join(
            (base.__class__.__qualname__, ViewProxy.__name__)
        )
        return object.__new__(ViewProxy)


class KeyCacheFactory(dict[K, T]):

    def __getitem__(self, key: K) -> T:
        try: return super().__getitem__(key)
        except KeyError:
            val = self[key] = self.__fncreate__(key)
            return val

    def __call__(self, key: K) -> T:
        return self[key]

    __slots__ = ('__fncreate__',)
    __fncreate__: Callable[[K], T]

    def __init__(self, fncreate: Callable[[K], T]):
        super().__init__()
        self.__fncreate__ = fncreate

_ga = object.__getattribute__
class AttrCacheFactory(Generic[T]):

    def __getattribute__(self, name: str) -> T:
        if name.startswith('__'): return _ga(self, name)
        cache: dict = _ga(self, '__cache__')
        return cache[name]

    __slots__ = ('__cache__',)
    __cache__: KeyCacheFactory[str, T]

    def __init__(self, fncreate: Callable[[str], T]):
        self.__cache__ = KeyCacheFactory(fncreate)

    def __dir__(self):
        return list(self.__cache__.keys())