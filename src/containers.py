from __future__ import annotations

from decorators import operd, metad, wraps #deleg, 
from errors import DuplicateKeyError, DuplicateValueError
from utils import ABCMeta, IndexType, NOARG, cat, instcheck, notsubclscheck, \
    wrparens, wraprepr \
    # orepr, subclscheck

from collections import deque
from collections.abc import Callable, Collection, Hashable, Iterable, Iterator, \
    Mapping, MappingView, Sized, Reversible
import collections.abc as bases
import itertools
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

__all__ = (
    'Abc', 'Copyable',
    'SetApi', 'MutableSetApi',
    'setf', 'setm', # SetSeqPair,
    'SequenceApi', 'MutableSequenceApi',
    'SequenceSetApi', 'MutableSequenceSetApi',
    'qsetf', 'qsetm', # MutSetSeqPair,
    # LinkSequenceApi, LinkSequenceView, LinkOrderSet # LinkEntry
    # MapAttrView
    # DequeCache
)
class Abc(metaclass = ABCMeta):
    __slots__ = ()

class Copyable(Abc):

    @abstractmethod
    def __copy__(self): ...

    def copy(self):
        return self.__copy__()

# -------------- Sequence ---------------#

class SequenceApi(bases.Sequence[V], Copyable):
    "Fusion interface of collections.abc.Sequence and built-in tuple."

    __slots__ = ()

    @abstractmethod
    def __add__(self, other): ...

class MutableSequenceApi(bases.MutableSequence[V], SequenceApi[V]):
    'Fusion interface of collections.abc.MutableSequence and built-in list.'

    __slots__ = ()

    extend = operd.apply(opr.iadd, info = list.extend)

    @abstractmethod
    def sort(self, /, *, key = None, reverse = False): ...

    @abstractmethod
    def reverse(self): ...

# -------------- Set ---------------#

class SetApi(bases.Set[V], Copyable):
    'Fusion interface of collections.abc.Set and built-in frozenset.'

    __slots__ = ()

    _opts = dict(freturn = opr.methodcaller('_from_iterable'))

    issubset   = operd.apply(opr.le, info = set.issubset)
    issuperset = operd.apply(opr.ge, info = set.issuperset)

    union        = operd.reduce(opr.or_,  info = set.union,        **_opts)
    intersection = operd.reduce(opr.and_, info = set.intersection, **_opts)
    difference   = operd.reduce(opr.sub,  info = set.difference,   **_opts)

    symmetric_difference = operd.apply(opr.xor,
        info = set.symmetric_difference
    )

    del(_opts)

    def __copy__(self):
        return self._from_iterable(self)

class MutableSetApi(bases.MutableSet[V], SetApi[V]):
    'Fusion interface of collections.abc.MutableSet and built-in set.'

    __slots__ = ()

    update              = operd.iterself(opr.ior,  info = set.update)
    intersection_update = operd.iterself(opr.iand, info = set.intersection_update)
    difference_update   = operd.iterself(opr.isub, info = set.difference_update)

    symmetric_difference_update = operd.apply(opr.ixor,
        info = set.symmetric_difference_update
    )

class setf(SetApi[V]):
    'SetApi wrapper around built-in frozenset.'

    __slots__ = '_set_',

    def __init__(self, values: Iterable[V] = None, /):
        if values is None:
            values = ()
        self._set_ = frozenset(values)

    def __contains__(self, value: V):
        return value in self._set_

    def __iter__(self) -> Iterator[V]:
        return iter(self._set_)

    def __len__(self):
        return len(self._set_)

    def __repr__(self):
        return self._set_.__repr__()

class setm(MutableSetApi[V], setf[V]):
    'MutableSetApi wrapper around built-in set.'

    __slots__ = ()

    def __init__(self, values: Iterable[V] = None, /):
        self._set_ = set()
        if values is not None:
            self.update(values)

    def add(self, value: V):
        self._set_.add(value)

    def discard(self, value: V):
        self._set_.discard(value)

# ------------- SequenceSet ---------------#

class SequenceSetApi(SetApi[V], SequenceApi[V]):
    'Sequence set (ordered set) read interface.  Comparisons follow Set semantics.'

    __slots__ = ()

    def count(self, value: V) -> int:
        'Returns 1 if in the set, else 0.'
        return int(value in self)

    def index(self, value: V, start = 0, stop = None) -> int:
        'Get the index of the value in the set.'
        if value not in self:
            raise ValueError('%s is not in the set' % value)
        return super().index(value, start, stop)

    __add__ = operd.apply(opr.or_)

    @abstractmethod
    def __contains__(self, value):
        'Set-based `contains` implementation.'
        ...

    ImplNotes: Annotated[dict, dict(
        implement = {
            SequenceApi: {'__add__'},
        },
        override = {
            SequenceApi: {'__contains__', 'count', 'index'},
        },
        inherit = {
            SequenceApi: {'__iter__', '__reversed__'},
            SetApi : {
                '__eq__',
                '__le__', '__lt__', '__gt__', '__ge__',
                '__and__', '__or__', '__xor__', '__sub__',
                '__rand__', '__ror__', '__rxor__', '__rsub__',
                'isdisjoint', 'issubset', 'issuperset',
                'union', 'intersection', 'difference', 'symmetric_difference', 
                '_hash', '__copy__',
            },
        },
        abstract = {'__len__', '__contains__', '__getitem__'},
    )]

class MutableSequenceSetApi(MutableSequenceApi[V], MutableSetApi[V], SequenceSetApi[V]):
    """Mutable sequence set (ordered set) interface.
    Sequence methods such as ``append`` raise ``DuplicateValueError``."""

    __slots__ = ()

    def _new_value(self, value) -> V:
        'Hook to return the new value before it is added.'
        return value

    def _before_add(self, value: V):
        'Before add hook.'

    def _after_add(self, value: V):
        'After add hook.'

    def _before_remove(self, value: V):
        'Before remove hook.'

    def _after_remove(self, value: V):
        'After remove hook.'

    def add(self, value: V):
        'Calls ``append()`` and catches ``DuplicateValueError``.'
        try: self.append(value)
        except DuplicateValueError: pass

    def discard(self, value: V):
        'Calls ``remove()`` and catches ``ValueError``.'
        try: self.remove(value)
        except ValueError: pass

    ImplNotes: Annotated[dict, dict(
        implement = {
            MutableSetApi: {'add', 'discard'}
        },
        inherit = {
            SequenceSetApi: {
                '__iter__', '__reversed__',
                'count', 'index', '__add__',
                '__eq__',
                '__le__', '__lt__', '__gt__', '__ge__',
                '__and__', '__or__', '__xor__', '__sub__',
                '__rand__', '__ror__', '__rxor__', '__rsub__',
                'isdisjoint', 'issubset', 'issuperset',
                'union', 'intersection', 'difference', 'symmetric_difference', 
                '_hash', '__copy__',
            },
            MutableSetApi: {
                '__iand__', '__ior__', '__ixor__', '__isub__',
                'update', 'intersection_update', 'difference_update', 'symmetric_difference_update',
            },
            MutableSequenceApi: {
                'append', 'extend', '__iadd__',
                'pop', 'remove', 'clear',
                'reverse',
            },
        },
        resolve = {
            'pop'   : MutableSequenceApi,
            'remove': MutableSequenceApi,
        },
        abstract = {
            '__len__', '__contains__', '__getitem__',
            '__setitem__', '__delitem__', 'insert',
            'sort', 'reverse',
        }
    )]

class SetSeqPair(NamedTuple):
    set: SetApi
    seq: SequenceApi

class qsetf(SequenceSetApi[V]):
    'Immutable sequence set implementation with built-in set and list.'

    __slots__ = '_setseq_',
    _setseq_: SetSeqPair[V]

    def __init__(self, values: Iterable[V] = None, /):
        seq = () if values is None else tuple(dict.fromkeys(values))
        self._setseq_ = SetSeqPair(frozenset(seq), seq)

    def __len__(self):
        return len(self._setseq_.seq)

    def __contains__(self, value: V):
        return value in self._setseq_.set

    def __getitem__(self, index: IndexType) -> V:
        return self._setseq_.seq[index]

    def __copy__(self):
        inst = object.__new__(self.__class__)
        inst._setseq_ = self._setseq_.__class__(*self._setseq_)
        return inst

    def __repr__(self):
        return wraprepr(self, self._setseq_.seq)

    ImplNotes: Annotated[dict, dict(
        implement = {'__len__', '__contains__', '__getitem__'},
        override = {'__copy__', '__repr__'},
        inherit = {
            '__iter__', '__reversed__',
            'count', 'index', '__add__',
            '__eq__',
            '__le__', '__lt__', '__gt__', '__ge__',
            '__and__', '__or__', '__xor__', '__sub__',
            '__rand__', '__ror__', '__rxor__', '__rsub__',
            'isdisjoint', 'issubset', 'issuperset',
            'union', 'intersection', 'difference', 'symmetric_difference',
            '_hash',
        }
    )]

class MutSetSeqPair(SetSeqPair[V]):
    set: MutableSetApi[V]
    seq: MutableSequenceApi[V]

class qsetm(MutableSequenceSetApi[V], qsetf[V]):
    'MutableSequenceSetApi implementation backed by built-in set and list.'

    __slots__ = ()
    _setseq_: MutSetSeqPair[V]

    def __init__(self, values: Iterable[V] = None, /):
        self._setseq_ = MutSetSeqPair(set(), [])
        if values is not None:
            self.update(values)

    def __delitem__(self, index: IndexType):
        'Delete by index/slice.'
        values = self[index]
        if isinstance(index, int):
            values = values,
        else:
            instcheck(values, Collection)
        for value in values:
            self._before_remove(value)
        b = self._setseq_
        del b.seq[index]
        for value in values:
            b.set.remove(value)
        for value in values:
            self._after_remove(value)

    def __setitem__(self, index: int, value: V):
        """Set an the index to a value. Only ``int`` supported, not slice.
        Raises ``DuplicateValueError``."""
        instcheck(index, int)
        old = self[index]
        value = self._new_value(value)
        if value in self:
            if value == old:
                return
            raise DuplicateValueError(value)
        self._before_add(value)
        b = self._setseq_
        b.seq[index] = value
        b.set.add(value)
        self._after_add(value)

    def insert(self, index: int, value: V):
        'Insert a value before an index. Raises ``DuplicateValueError``.'
        value = self._new_value(value)
        if value in self:
            raise DuplicateValueError(value)
        self._before_add(value)
        b = self._setseq_
        b.seq.insert(index, value)
        b.set.add(value)
        self._after_add(value)

    def reverse(self):
        'Reverse in place.'
        self._setseq_.seq.reverse()

    def sort(self, /, *, key = None, reverse = False):
        'Sort the list in place.'
        self._setseq_.seq.sort(key = key, reverse = reverse)

    def clear(self):
        'Clear the list and set.'
        b = self._setseq_
        b.seq.clear()
        b.set.clear()

    ImplNotes: Annotated[dict, dict(
        implement = {
            '__setitem__', '__delitem__', 'insert', 'sort', 'reverse',
        },
        override = {'clear'},
        inherit = {
            qsetf: {
                '__len__', '__contains__', '__getitem__', '__copy__', '__repr__',
                '__iter__', '__reversed__',
                'count', 'index', '__add__',
                '__eq__',
                '__le__', '__lt__', '__gt__', '__ge__',
                '__and__', '__or__', '__xor__', '__sub__',
                '__rand__', '__ror__', '__rxor__', '__rsub__',
                'isdisjoint', 'issubset', 'issuperset',
                'union', 'intersection', 'difference', 'symmetric_difference',
                '_hash',
            },
            MutableSequenceSetApi: {
                'append', 'extend', '__iadd__',
                'pop', 'remove',
                'add',
                'discard', 
                '__ior__', '__iand__', '__ixor__', '__isub__',
                'update', 'intersection_update', 'difference_update',
                'symmetric_difference_update',
            },
        }
    )]

class LinkSequenceApi(SequenceApi[V], Abc):
    'Abstract class for a linked sequence view.'

    __slots__ = ()

    @abstractmethod
    def first(self) -> V: ...

    @abstractmethod
    def last(self) -> V: ...

    @abstractmethod
    def iterfrom(self, value: V, /, reverse = False) -> Iterator[V]: ...

class LinkSequenceView(LinkSequenceApi[T]):

    __slots__ = ()

    def __new__(cls, base: LinkSequenceApi):

        class ViewProxy(LinkSequenceView):
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
            def __add__(self, other):
                return LinkSequenceView(base + other)
            def __copy__(self):
                return self.__class__()
            def __repr__(self):
                return base.__class__.__repr__(self)
            __new__ = object.__new__
        ViewProxy.__qualname__ = '.'.join(
            (base.__class__.__qualname__, ViewProxy.__name__)
        )
        return ViewProxy()

class LinkEntry(Generic[V], Abc):
    'A value container with prev/next attributes.'

    value: V
    prev: LinkEntry[V]
    next: LinkEntry[V]

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
        return wraprepr(self, self.value)
        # return cat(self.__class__.__name__, wrparens(self.value.__repr__()))

class LinkOrderSet(LinkSequenceApi[T]):

    _link_map: dict[T, LinkEntry[T]]
    _link_first: LinkEntry[T]
    _link_last: LinkEntry[T]
    _link_viewcls: type[LinkSequenceView[T]]

    slots = '_link_first', '_link_last', '_link_map', '_link_viewcls'

    def __init__(self, values: Iterable[T] = None, /):
        self._link_first = self._link_last = None
        self._link_map = {}
        if values is not None:
            self.extend(values)

    def _new_value(self, value) -> T:
        """Overridable hook method to transform an value before add/remove methods.
        The method must take at least one positional argument. Iterating methods
        such as ``extend`` iterate over the first argument, and call _new_value
        with the remainder of the arguments for each value."""
        return value

    # @metad.temp
    # def itemhook(item_method: Callable[[T], R]) -> Callable[[T], R]:
    #     'Wrapper for add/remove methods that calls the _new_value hook.'
    #     @wraps(item_method)
    #     def wrap(self: LinkOrderSet, value, *args, **kw):
    #         value = self._new_value(value, *args, **kw)
    #         return item_method(self, value)
    #     return wrap

    # @metad.temp
    # def newlink(link_method: Callable[[LinkEntry[T]], R]) -> Callable[[T], R]:
    #     """Wrapper for add item methods. Ensures the value is not already in the
    #     collection, and creates a LinkEntry. If the collection is empty, sets
    #     first and last, and returns. Otherwise, calls the original method with
    #     the link as the argument."""
    #     @wraps(link_method)
    #     def prep(self: LinkOrderSet, value):
    #         if value in self:
    #             raise DuplicateValueError(value)
    #         link = self._link_map[value] = LinkEntry(value)
    #         if self._link_first is None:
    #             self._link_first = self._link_last = link
    #             return
    #         if self._link_first is self._link_last:
    #             self._link_first.next = link
    #         link_method(self, link)
    #     return prep

    # -----
    def __getitem__(self, index: int):
        instcheck(index, int)
        if index < 0:
            index = len(self) + index
        if index >= len(self):
            raise IndexError('sequence index out of range')
        if index > len(self) / 2:
            itsrc = reversed(self)
            index = len(self) - index - 1
        else:
            itsrc = self
        for i, value in enumerate(itsrc):
            if i == index:
                return value



    # @itemhook
    # @newlink
    # def append(self, link: LinkEntry[T]):
    #     if self._link_first is self._link_last:
    #         self._link_first.next = link
    #     link.prev = self._link_last
    #     link.prev.next = link
    #     self._link_last = link

    def append(self, value, *args, **kw):
        if len(self):
            self.insert_after(self.last(), value, *args, **kw)
            return
        value = self._new_value(value, *args, **kw)
        self._link_first = self._link_last = self._link_map[value] = LinkEntry(value)
        
    def insert_before(self, before_value: V, value, *args, **kw):
        try:
            before_link = self._link_map[before_value]
        except KeyError:
            raise ValueError(before_value) from None
        value = self._new_value(value, *args, **kw)
        if value in self:
            raise DuplicateValueError(value)
        link = self._link_map[value] = LinkEntry(value, before_link.prev, before_link)
        if before_link.prev is not None:
            before_link.prev.next = link
        before_link.prev = link
        if link.prev is None:
            self._link_first = link

    def insert_after(self, after_value: V, value, *args, **kw):
        try:
            after_link = self._link_map[after_value]
        except KeyError:
            raise ValueError(after_value) from None
        value = self._new_value(value, *args, **kw)
        if value in self:
            raise DuplicateValueError(value)
        link = self._link_map[value] = LinkEntry(value, after_link, after_link.next)
        if after_link.next is not None:
            after_link.next.prev = link
        after_link.next = link
        if link.next is None:
            self._link_last = link

    # @itemhook
    def remove(self, value: T):
        try:
            link = self._link_map.pop(value)
        except KeyError:
            raise ValueError(value) from None
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
        # del self[value]

    def clear(self):
        self._link_map.clear()
        self._link_first = self._link_last = None

    # def __delitem__(self, item: T | LinkEntry[T]):
    #     # TODO: convert to sequence index
    #     self.remove(item)



    # -----

    def __len__(self):
        return len(self._link_map)

    def __contains__(self, item: T | LinkEntry[T]):
        return item in self._link_map

    def __iter__(self) -> Iterator[T]:
        if len(self):
            yield from self.iterfrom(self.first())

    def __reversed__(self) -> Iterator[T]:
        if len(self):
            yield from self.iterfrom(self.last(), reverse = True)

    def iterfrom(self, value: T, /, reverse = False) -> Iterator[T]:
        cur = self._link_map[value]
        dir_ = -1 if reverse else 1
        while cur:
            value = cur.value
            yield value
            cur = cur.dir(dir_)

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

    def view(self) -> LinkSequenceApi[T]:
        try: return self._link_viewcls()
        except AttributeError: pass
        view = LinkSequenceView(self)
        self._link_viewcls = view.__class__
        return view

    # -------

    def extend(self, values: Iterable[T], *args, **kw):
        'Iterable version of ``append()``.'
        for value in values:
            self.append(value, *args, **kw)

    def add(self, value: T, *args, **kw):
        'Alias for ``append()``.'
        return self.append(value, *args, **kw)

    # TODO: temp until SequenceSetApi is added to bases
    def __add__(self, other):
        return self._from_iterable(itertools.chain(self, other))
    @classmethod
    def _from_iterable(cls, it):
        return cls(it)
    def __copy__(self) -> LinkOrderSet[T]:
        return self.__class__(self)

    # def __repr__(self):
    #     return orepr(self,
    #         len   = len(self),
    #         first = self.first(),
    #         last  = self.last(),
    #     )

    # def pop(self) -> T:
    #     'Remove and return the last value.'
    #     value = self.last()
    #     del self[value]
    #     return value

    # def shift(self) -> T:
    #     'Remove and return the first value.'
    #     value = self.first()
    #     del self[value]
    #     return value

    # def prependall(self, values: Iterable[T], *args, **kw):
    #     'Iterable version of ``prepend()``.'
    #     for value in values:
    #         self.prepend(value, *args, **kw)


    # def update(self, values: Iterable[T], *args, **kw):
    #     'Alias for ``extend()``.'
    #     return self.extend(values, *args, **kw)

    # def discard(self, value: T, *args, **kw):
    #     'KeyError safe version of ``remove()``.'
    #     try: self.remove(value, *args, **kw)
    #     except KeyError: pass


    # @itemhook
    # @newlink
    # def prepend(self, link: LinkEntry[T]):
    #     if self._link_first is self._link_last:
    #         self._link_last.prev = link
    #     link.next = self._link_first
    #     link.next.prev = link
    #     self._link_first = link

class MapAttrView(MappingView[str, V], Mapping[str, V], Copyable):
    'A Mapping view with attribute access.'

    # MappingView uses the '_mapping' slot.
    __slots__ = ()

    def __init__(self, base: Mapping[str, V]):
        self._mapping = instcheck(base, Mapping)

    def __getattr__(self, name: str):
        try:
            return self._mapping[name]
        except KeyError:
            raise AttributeError(name)

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
        try:
            return reversed(self._mapping)
        except TypeError:
            raise NotImplementedError

class DequeCache(Collection[V], Reversible, Sized, Abc):

    __slots__ = ()

    maxlen: int
    idx: int
    rev: Mapping[Any, V]

    @abstractmethod
    def clear(self): ...

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

        VT = TypeVar('VT')
        class Api(DequeCache[VT]):

            __slots__ = ()

            maxlen = property(lambda _: deck.maxlen)
            idx = property(lambda _: idxproxy)
            rev = property(lambda _: revproxy)

            def clear(self):
                for d in (idx, rev, deck): d.clear()

            def __len__(self):
                return len(deck)

            def __iter__(self) -> Iterator[VT]:
                return iter(deck)

            def __reversed__(self) -> Iterator[VT]:
                return reversed(deck)

            def __contains__(self, item: VT):
                return item in rev

            def __getitem__(self, key) -> VT:
                # if isinstance(key, IndexType): return deck[key]
                return idx[key]

            def __setitem__(self, key, item: VT):
                instcheck(item, V)
                if item in self:
                    item = self[item]
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