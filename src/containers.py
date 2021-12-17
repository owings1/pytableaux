from __future__ import annotations

from decorators import operd, metad, wraps #deleg, 
from errors import DuplicateKeyError, DuplicateValueError
from utils import ABCMeta, IndexType, NOARG, cat, instcheck, notsubclscheck, \
    orepr, wrparens, wraprepr \
    # subclscheck

from collections import deque
from collections.abc import Callable, Collection, Hashable, Iterable, Iterator, \
    Mapping, MappingView, Reversible
import collections.abc as bases
import operator as opr
from types import MappingProxyType as MapProxy
from typing import Any, Annotated, Generic, NamedTuple, TypeVar, abstractmethod #, final
# import abc
# from copy import copy
# from functools import reduce
# from itertools import chain, filterfalse
# import typing

from callables import preds #, calls, cchain, gets

K = TypeVar('K')
T = TypeVar('T')
R = TypeVar('R')
V = TypeVar('V')

class Abc(metaclass = ABCMeta):
    __slots__ = ()

class Copyable(Abc):

    @abstractmethod
    def __copy__(self): ...

    def copy(self):
        return self.__copy__()

class SetApi(bases.Set[V], Copyable):

    __slots__ = ()

    rdckw = dict(freturn = opr.methodcaller('_from_iterable'))

    # ------- Builtin set API ------------
    issubset   = operd.apply(opr.le, info = set.issubset)
    issuperset = operd.apply(opr.ge, info = set.issuperset)

    union        = operd.reduce(opr.or_,  info = set.union,        **rdckw)
    intersection = operd.reduce(opr.and_, info = set.intersection, **rdckw)
    difference   = operd.reduce(opr.sub,  info = set.difference,   **rdckw)

    symmetric_difference = operd.apply(opr.xor,
        info = set.symmetric_difference
    )
    # -------------------------------

    del(rdckw)

class MutableSetApi(bases.MutableSet, SetApi):

    __slots__ = ()

    # ------- Builtin set API ------------
    update              = operd.iterself(opr.ior,  info = set.update)
    intersection_update = operd.iterself(opr.iand, info = set.intersection_update)
    difference_update   = operd.iterself(opr.isub, info = set.difference_update)

    symmetric_difference_update = operd.apply(opr.ixor,
        info = set.symmetric_difference_update
    )
    # -------------------------------

class SequenceApi(bases.Sequence[V], Copyable):

    __slots__ = ()

    @abstractmethod
    def __add__(self, other): ...

class MutableSequenceApi(bases.MutableSequence, SequenceApi):

    __slots__ = ()

    # ---------- Builtin list API -----------
    extend = operd.apply(opr.iadd, info = list.extend)

    @abstractmethod
    def sort(self, /, *, key = None, reverse = False): ...

    @abstractmethod
    def reverse(self): ...
    # -------------------------------

class SetSeqPair(NamedTuple):
    set: SetApi
    seq: SequenceApi

class MutSetSeqPair(SetSeqPair):
    set: MutableSetApi
    seq: MutableSequenceApi

class SequenceSetView(SetApi[V], SequenceApi):
    'Sequence set (ordered set) read interface.'

    __slots__ = '_setseq_',

    @abstractmethod
    def __init__(self, setseq: SetSeqPair):
        self._setseq_ = instcheck(setseq, SetSeqPair)

    # -------------   Collection ---------------

    def __contains__(self, value: V):
        return value in self._setseq_.set

    def __len__(self):
        return len(self._setseq_.seq)

    # --------------  Sequence  -------------------

    def __getitem__(self, index: IndexType) -> V:
        return self._setseq_.seq[index]

    def count(self, value: V) -> int:
        'Returns 1 if in the set, else 0.'
        return int(value in self)

    def index(self, value: V, start = 0, stop = None) -> int:
        'Get the index of the value in the set.'
        if value not in self:
            raise ValueError('%s is not in the set' % value)
        return super().index(value, start, stop)

    __add__ = operd.apply(opr.or_)

    # -----------  Copyable -----------

    def __copy__(self) -> SequenceSetView[V]:
        inst = object.__new__(self.__class__)
        inst._setseq_ = self._setseq_.__class__(*self._setseq_)
        return inst

    # -----------  Other -----------

    def __repr__(self):
        return wraprepr(self, self._setseq_.seq)

    ImplNotes: Annotated[dict, {
        Collection: dict(
            implement = {'__contains__', '__len__'},
        ),
        SequenceApi: dict(
            implement = {'__getitem__', '__add__'},
            override  = {'count', 'index'},
            inherit   = {'__iter__', '__reversed__'},
        ),
        SetApi: dict(
            inherit = {
                '__and__', '__rand__', '__or__', '__ror__',
                '__sub__', '__rsub__', '__xor__', '__rxor__',
                '__le__', '__lt__', '__gt__', '__ge__', '__eq__',
                '_hash', 'isdisjoint',
                'union', 'intersection', 'difference',
                'symmetric_difference', 
                'issubset', 'issuperset',
            },
        ),
    }]

class FrozenSequenceSet(SequenceSetView[V]):
    'Immutable sequence set.'

    __slots__ = ()

    def __init__(self, values: Iterable[V] = None):
        d = dict.fromkeys(() if values is None else values)
        setseq = SetSeqPair(frozenset(d), tuple(d.keys()))
        super().__init__(setseq)
        del(d)

class MutableSequenceSet(MutableSequenceApi[V], MutableSetApi, SequenceSetView):
    """Mutable sequence set. Set-like properties are primary, such as comparisons.
    Sequence methods such as ``append`` raises ``ValueError`` on duplicate values."""

    __slots__ = ()

    _setseq_: MutSetSeqPair

    @abstractmethod
    def __init__(self, setseq: MutSetSeqPair):
        self._setseq_ = instcheck(setseq, MutSetSeqPair)

    def _new_value(self, value) -> V:
        'Hook to return the new value before it is added.'
        print(value)
        return value

    def _after_add(self, value: V):
        'After add hook.'
        pass

    def _after_remove(self, value: V):
        'After remove hook.'
        pass

    # ---------------   MutableSequence ---------------

    def __delitem__(self, index: IndexType):
        'Delete by index/slice.'
        values = self[index]
        if isinstance(index, int): values = values,
        else: instcheck(values, Collection)
        b = self._setseq_
        del b.seq[index]
        for value in values:
            b.set.remove(value)
        for value in values:
            self._after_remove(value)

        # if isinstance(index, int):
        #     b.set.remove(value)
        #     self._after_remove(value)
        # else:
        #     for value in self[index]:
        #         b.set.remove(value)
        # del b.seq[index]

    def __setitem__(self, index: int, value: V):
        'Set an the index to a value. Raises ``DuplicateValueError``.'
        instcheck(index, int)
        old = self[index]
        value = self._new_value(value)
        if value in self:
            if value == old: return
            raise DuplicateValueError('Duplicate: %s' % value)
        b = self._setseq_
        b.seq[index] = value
        b.set.add(value)
        self._after_add(value)

    def insert(self, index: int, value: V):
        'Insert a value before an index. Raises ``DuplicateValueError``.'
        value = self._new_value(value)
        if value in self:
            raise DuplicateValueError('Duplicate: %s' % value)
        b = self._setseq_
        b.seq.insert(index, value)
        b.set.add(value)
        self._after_add(value)

    # def append(self, value: V):
    #     'Append an value. Raises ValueError for duplicate.'
    #     if value in self:
    #         raise ValueError('Duplicate: %s' % value)
    #     return super().append(value)

    def reverse(self):
        'Reverse in place.'
        self._setseq_.seq.reverse()

    def clear(self):
        'Clear the list and set.'
        b = self._setseq_
        b.seq.clear()
        b.set.clear()
        
        # if not len(self):
        #     return
        # st, sq = self._setseq_
        # setseq = self._setseq_.__class__(st.__class__(), sq.__class__())
        # # from sys import getrefcount
        # # if getrefcount(st) + getrefcount(ls) > 4:
        # #     MutableSequence.clear(self)
        # del(st, sq, self._setseq_)
        # self._setseq_ = setseq

    def sort(self, /, *, key = None, reverse = False):
        'Sort the list in place.'
        self._setseq_.seq.sort(key = key, reverse = reverse)

    # ---------------  MutableSet  --------------------

    def add(self, value: V):
        'Calls ``append()`` and catches ``DuplicateValueError``.'
        try: self.append(value)
        except DuplicateValueError: pass

    def discard(self, value: V):
        'Calls ``remove()`` and catches ``DuplicateValueError``.'
        try: self.remove(value)
        except DuplicateValueError: pass

    ImplNotes: Annotated[dict, dict(
        implement = {
            MutableSequenceApi: {'__setitem__', '__delitem__', 'insert', 'sort'},
            MutableSetApi:      {'add', 'discard'}
        },
        override = {
            MutableSequenceApi: {'clear', 'reverse',},
            MutableSetApi:      {'clear',},
        },
        inherit = {
            MutableSequenceApi: {
                'append', 'extend', 'pop', 'remove', '__iadd__',
            },
            MutableSetApi: {
                '__ior__', '__iand__', '__ixor__', '__isub__',
                'update', 'intersection_update', 'difference_update',
                'symmetric_difference_update',
            },
            SequenceSetView: {
                '__contains__', '__len__', '__iter__', '__reversed__',
                '__getitem__', 'count', 'index', '__add__',

                '__and__', '__rand__', '__or__', '__ror__',
                '__sub__', '__rsub__', '__xor__', '__rxor__',
                '__le__', '__lt__', '__gt__', '__ge__', '__eq__',
                'union', 'intersection', 'difference', 'symmetric_difference', 
                'issubset', 'issuperset', 'isdisjoint', '_hash',

                '__copy__', '__repr__',
            },
        },
        resolve = {
            'pop'   : MutableSequenceApi,
            'remove': MutableSequenceApi,
        }
    )]

class ListSet(MutableSequenceSet[V]):
    'MutableSequenceSet implementation with built-in set and list.'

    __slots__ = ()

    def __init__(self, values: Iterable[V] = None):
        super().__init__(MutSetSeqPair(set(), []))
        if values is not None:
            self.update(values)

class MapAttrView(MappingView[str, V], Mapping, Copyable):
    'A Mapping view with attribute access.'

    # MappingView uses the '_mapping' slot.
    __slots__ = ()

    def __init__(self, base: Mapping[str, V]):
        self._mapping = instcheck(base, Mapping)

    def __getattr__(self, name: str):
        try: return self._mapping[name]
        except KeyError: raise AttributeError(name)

    def __dir__(self):
        return list(filter(preds.isidentifier, self))

    def __copy__(self) -> MapAttrView[V]:
        inst = object.__new__(self.__class__)
        inst._mapping = self._mapping
        return inst

    def __getitem__(self, key: str) -> V:
        return self._mapping[key]

    def __iter__(self) -> Iterator[str]:
        yield from self._mapping

    def __reversed__(self) -> Iterator[str]:
        try: return reversed(self._mapping)
        except TypeError: raise NotImplementedError()

class LinkedView(Collection[T], Reversible, Abc):
    'Abstract class for a linked collection view.'

    __slots__ = ()

    @abstractmethod
    def first(self) -> T: ...

    @abstractmethod
    def last(self) -> T: ...

    @abstractmethod
    def iterfrom(self, item: T | LinkEntry[T], reverse = False) -> Iterator[T]: ...

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

class LinkEntry(Generic[T], Hashable, Abc):
    'An item container with prev/next attributes.'

    value: T
    prev: LinkEntry[T]
    next: LinkEntry[T]

    __slots__ = 'prev', 'next', 'value'

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

class LinkOrderSet(LinkedView[T], Collection, Copyable):

    def __init__(self, values: Iterable[T] = None, strict: bool = True):
        self.strict = strict
        self._link_first = self._link_last = None
        self._link_map: dict[Any, LinkEntry] = {}
        if values is not None:
            self.extend(values)

    slots = '_link_first', '_link_last', '_link_map', 'strict', '_link_viewcls'

    def _genitem_(self, value) -> T:
        """Overridable hook method to transform an value before add/remove methods.
        The method must take at least one positional argument. Iterating methods
        such as ``extend`` iterate over the first argument, and call _genitem_
        with the remainder of the arguments for each value."""
        return value

    @metad.temp
    def itemhook(item_method: Callable[[T], R]) -> Callable[[T], R]:
        'Wrapper for add/remove methods that calls the _genitem_ hook.'
        @wraps(item_method)
        def wrap(self: LinkOrderSet, value, *args, **kw):
            value = self._genitem_(value, *args, **kw)
            return item_method(self, value)
        return wrap

    @metad.temp
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
        return prep

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

    def __copy__(self) -> LinkOrderSet[T]:
        return self.__class__(self, self.strict)

    def __repr__(self):
        return orepr(self,
            len   = len(self),
            first = self.first(),
            last  = self.last(),
        )

class DequeCache(Collection[V], Abc):

    __slots__ = ()

    maxlen: int
    idx: int
    rev: Mapping[Any, V]

    @abstractmethod
    def clear(self): ...

    @abstractmethod
    def add(self, item: V, keys = None): ...

    @abstractmethod
    def update(self, d: dict): ...

    @abstractmethod
    def get(self, key, default = None): ...

    @abstractmethod
    def __len__(self): ...

    @abstractmethod
    def __iter__(self) -> Iterator[V]: ...

    @abstractmethod
    def __reversed__(self) -> Iterator[V]: ...

    @abstractmethod
    def __contains__(self, item: V): ...

    @abstractmethod
    def __getitem__(self, key) -> V: ...

    @abstractmethod
    def __setitem__(self, key, item: V): ...

    def __new__(cls, V: type, maxlen = 10):

        notsubclscheck(V, IndexType)
        instcheck(V, type)

        idx      : dict[Any, V] = {}
        idxproxy : Mapping[Any, V] = MapProxy(idx)

        rev      : dict[V, set] = {}
        revproxy : Mapping[V, set] = MapProxy(rev)

        deck     : deque[V] = deque(maxlen = maxlen)

        class Api(DequeCache, Collection[V]):

            __slots__ = ()

            maxlen: int = property(lambda _: deck.maxlen)
            idx: int = property(lambda _: idxproxy)
            rev: Mapping[Any, V] = property(lambda _: revproxy)

            def clear(self):
                for d in (idx, rev, deck): d.clear()

            def add(self, item: V, keys = None):
                self[item] = item
                if keys is not None:
                    for k in keys: self[k] = item

            def update(self, d: dict):
                for k, v in d.items(): self[k] = v

            def get(self, key, default = None):
                try: return self[key]
                except KeyError: return default

            def __len__(self):
                return len(deck)

            def __iter__(self) -> Iterator[V]:
                return iter(deck)

            def __reversed__(self) -> Iterator[V]:
                return reversed(deck)

            def __contains__(self, item: V):
                return item in rev

            def __getitem__(self, key) -> V:
                if isinstance(key, IndexType): return deck[key]
                return idx[key]

            def __setitem__(self, key, item: V):
                instcheck(item, V)
                if item in self: item = self[item]
                else:
                    if len(deck) == deck.maxlen:
                        old = deck.popleft()
                        for k in rev.pop(old): del(idx[k])
                    idx[item] = item
                    rev[item] = {item}
                    deck.append(item)
                idx[key] = item
                rev[item].add(key)

        Api.__qualname__ = 'DequeCache.Api'
        return object.__new__(Api)