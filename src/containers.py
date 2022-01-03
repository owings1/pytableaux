from __future__ import annotations

from decorators import operd #, metad, wraps #deleg, 
from errors import DuplicateKeyError, DuplicateValueError, MissingValueError, SanityError
from utils import ABCMeta, IndexType, instcheck, notsubclscheck, \
    wraprepr \
    # cat, wrparens, orepr, subclscheck, NOARG

from collections import deque
from collections.abc import Callable, Collection, Hashable, Iterable, Iterator, \
    Mapping, MappingView, Sized, Reversible
import collections.abc as bases
import enum
import itertools
import operator as opr
from types import MappingProxyType as MapProxy
from typing import Any, Annotated, Generic, NamedTuple, TypeVar, abstractmethod #, final
# import abc
# from copy import copy
# from functools import reduce
# from itertools import chain, filterfalse
# import typing

from callables import preds, calls#, cchain, gets

K = TypeVar('K')
T = TypeVar('T')
R = TypeVar('R')
V = TypeVar('V')

__all__ = (
    'Abc', #'Copyable',
    'SetApi', #'MutableSetApi',
    'setf', 'setm', # SetSeqPair,
    #'SequenceApi', #'MutableSequenceApi',
    'SequenceSetApi', #'MutableSequenceSetApi',
    'qsetf', 'qsetm', # MutSetSeqPair,
    'linqset', # MutableLinkSequenceSetApi, LinkSequenceView, # LinkEntry
    # MapAttrView
    # DequeCache
)
class Abc(metaclass = ABCMeta):
    __slots__ = ()

class Copyable(Abc):

    @abstractmethod
    def __copy__(self):
        raise NotImplementedError

    def copy(self: T) -> T:
        return self.__copy__()

# -------------- Sequence ---------------#

class SequenceApi(bases.Sequence[V], Copyable):
    "Fusion interface of collections.abc.Sequence and built-in tuple."

    __slots__ = ()

    @abstractmethod
    def __add__(self, other):
        return NotImplemented

    def _absindex(self, index: int, verify = True) -> int:
        'Normalize to positive/absolute index.'
        instcheck(index, int)
        if index < 0:
            index = len(self) + index
        if verify and (index >= len(self) or index < 0):
            raise IndexError('sequence index out of range')
        return index

class MutableSequenceApi(bases.MutableSequence[V], SequenceApi[V]):
    'Fusion interface of collections.abc.MutableSequence and built-in list.'

    __slots__ = ()

    @abstractmethod
    def sort(self, /, *, key = None, reverse = False):
        raise NotImplementedError

    @abstractmethod
    def reverse(self):
        raise NotImplementedError

# -------------- Set ---------------#

class SetApi(bases.Set[V], Copyable):
    'Fusion interface of collections.abc.Set and built-in frozenset.'

    __slots__ = ()

    _opts = dict(freturn = calls.method('_from_iterable'))

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

EMPTY_SET = setf()

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

    def count(self, value: V, /) -> int:
        'Returns 1 if in the set, else 0.'
        return int(value in self)

    def index(self, value: V, start = 0, stop = None, /) -> int:
        'Get the index of the value in the set.'
        if value not in self:
            raise MissingValueError(value)
        return super().index(value, start, stop)

    __add__ = operd.apply(opr.or_)

    @abstractmethod
    def __contains__(self, value):
        'Set-based `contains` implementation.'
        return False

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
        'Append if value is not already a member.'
        if value not in self:
            self.append(value)

    def discard(self, value: V):
        'Remove if value is a member.'
        if value in self:
            self.remove(value)

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
        'Set value by index. Raises ``DuplicateValueError``. Slice not implemented.'
        try:
            instcheck(index, int)
        except TypeError:
            if isinstance(index, slice):
                # TODO: implement slice
                raise NotImplementedError
            raise
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

# ----------- Links ------------------ #

class LinkSub(enum.Enum):
    'Link directional/subscript enum.'

    prev = -1
    self = 0
    next = 1

    def __neg__(self) -> LinkSub:
        return __class__(-self.value)

    def __int__(self):
        return self.value

    def __add__(self, value) -> LinkSub:
        return __class__(self.value + int(value))

    def __radd__(self, value) -> int:
        return self.value + value

    def __sub__(self, value) -> LinkSub:
        return __class__(self.value - int(value))

    def __rsub__(self, value) -> int:
        return self.value - value

class LinkEntry(Generic[V], Copyable):
    'Link value container with prev/next attributes.'

    value: V
    prev: LinkEntry[V]
    next: LinkEntry[V]

    __slots__ = 'prev', 'next', 'value'

    @property
    def self(self: T) -> T:
        return self

    def __init__(self, value, prev: LinkEntry[V] = None, next: LinkEntry[V] = None):
        self.value = value
        self.prev = prev
        self.next = next

    def __eq__(self, other):
        return self is other or self.value == other or (
            isinstance(other, self.__class__) and
            self.value == other.value
        )

    def __getitem__(self, sub: LinkSub) -> LinkEntry[V] | None:
        'Get previous, self, or next with ``LinkSub`` enum.'
        return getattr(self, LinkSub(sub).name)

    def __setitem__(self, sub: LinkSub, link: LinkEntry[V]):
        'Set previous, self, or next with ``LinkSub`` enum.'
        setattr(self, LinkSub(sub).name, link)

    def __copy__(self):
        inst = object.__new__(self.__class__)
        inst.value = self.value
        inst.prev = self.prev
        inst.next = self.next
        return inst

    def invert(self):
        'Invert prev and next attributes in place.'
        self.prev, self.next = self.next, self.prev

    def __repr__(self):
        return wraprepr(self, self.value)

class LinkHashEntry(LinkEntry[V]):

    __slots__ = ()

    def __eq__(self, other):
        return super().__eq__(other)

    def __hash__(self):
        return hash(self.value)
 
class LinkIterApi(Iterator[T]):
    'Linked sequence iterator interface.'

    _link: LinkEntry
    _sub: LinkSub

    __slots__ = '_link', '_sub'

    def __init__(self, link: LinkEntry, sub: LinkSub):
        self._link = link
        self._sub = sub

    def __next__(self) -> T:
        link = self._link
        if link is None:
            raise StopIteration
        self._link = link[self._sub]
        return self._get(link)

    def __iter__(self):
        return self

    @abstractmethod
    def _get(self, link: LinkEntry) -> T:
        raise StopIteration

class LinkEntryIter(LinkIterApi[LinkEntry[V]]):
    'Linked sequence iterator over LinkEntry objects.'

    __slots__ = ()

    def _get(self, link: LinkEntry[V]) -> LinkEntry[V]:
        return link

class LinkValueIter(LinkIterApi[V]):
    'Linked sequence iterator over values.'

    __slots__ = ()

    def _get(self, link: LinkEntry[V]) -> V:
        return link.value

# ----------- LinkSequence ------------------ #

class LinkSequenceApi(SequenceApi[V]):
    'Linked sequence read interface.'

    __slots__ = ()

    @property
    @abstractmethod
    def _link_first_(self) -> LinkEntry[V]:
        return None

    @property
    @abstractmethod
    def _link_last_(self) -> LinkEntry[V]:
        return None

    def __iter__(self) -> Iterator[V]:
        return LinkValueIter(self._link_first_, LinkSub.next)

    def __reversed__(self) -> Iterator[V]:
        return LinkValueIter(self._link_last_, LinkSub.prev)

    def __getitem__(self, index: int) -> V:
        'Get element by index. Slice not implemented.'
        try:
            instcheck(index, int)
        except TypeError:
            if isinstance(index, slice):
                # TODO: Implement slice
                raise NotImplementedError
            raise

        return self._link_at(index).value

    def _link_at(self, index: int) -> LinkHashEntry[V]:
        'Get a link entry by index.'

        index = self._absindex(index)

        # Direct access for first/last.
        if index == 0:
            return self._link_first_
        if index == len(self) - 1:
            return self._link_last_

        # TODO: warn performance

        # Choose best iteration direction.
        len_ = len(self)
        if index > len_ / 2:
            it = LinkEntryIter(self._link_last_, LinkSub.prev)
            index = len_ - index - 1
        else:
            it = LinkEntryIter(self._link_first_, LinkSub.next)

        # Advance iterator.
        for i, link in enumerate(it):
            if i == index:
                return link

        raise SanityError

    def __repr__(self):
        return wraprepr(self, list(self))

class LinkSequenceView(LinkSequenceApi[V]):
    'Linked sequence view proxy.'

    __slots__ = ()

    def __new__(cls, base: LinkSequenceApi):

        def getfirst(_):
            return base._link_first_

        def getlast(_):
            return base._link_last_

        basecls = base.__class__

        class proxy(LinkSequenceView[V]):

            __slots__ = ()

            _link_first_ = property(getfirst)
            _link_last_  = property(getlast)

            __len__      = base.__len__
            __contains__ = base.__contains__
            __getitem__  = base.__getitem__

            __repr__ = basecls.__repr__
            __new__  = object.__new__

            def __add__(self, other):
                return cls(base + other)

            def __copy__(self):
                return self

            def __deepcopy__(self, memo):
                memo[id(self)] = self
                return self

        proxy.__qualname__ = '.'.join(
            (basecls.__qualname__, proxy.__name__)
        )
        proxy.__name__ = cls.__name__
        return proxy()

class MutableLinkSequenceApi(LinkSequenceApi[V], MutableSequenceApi[V]):
    'Linked sequence write interface.'

    __slots__ = '__viewcls',

    @abstractmethod
    def put_before(self, neighbor: V, value: V):
        'Insert a value before another value.'
        raise NotImplementedError

    @abstractmethod
    def put_after(self, neighbor: V, value: V):
        'Insert a value after another value.'
        raise NotImplementedError

    @abstractmethod
    def remove(self, value: V):
        'Remove element by value.'
        raise NotImplementedError

    def __delitem__(self, index: int):
        'Remove element by index. Slice not yet implemented.'
        try:
            instcheck(index, int)
        except TypeError:
            if isinstance(index, slice):
                # TODO: Implement slice
                raise NotImplementedError
            raise
        self.remove(self[index])

    def view(self) -> LinkSequenceApi[V]:
        'Return a read-only view proxy.'
        try: return self.__viewcls()
        except AttributeError: pass
        view = LinkSequenceView(self)
        self.__viewcls = view.__class__
        return view

# ----------- LinkSequenceSet ------------------ #

class MutableLinkSequenceSetApi(MutableLinkSequenceApi[V], LinkSequenceApi[V], MutableSequenceSetApi[V]):
    'Linked sequence set read/write interface.'

    __slots__ = ()

    @abstractmethod
    def _link_of(self, value: V) -> LinkEntry[V]:
        'Get a link entry by value.'
        raise NotImplementedError

    def iter_from_value(self, value: V, /, reverse = False) -> Iterator[V]:
        'Return an iterator starting from ``value``.'
        return LinkValueIter(self._link_of(value), LinkSub(-1 if reverse else 1))

class linqset(MutableLinkSequenceSetApi[V]):
    'MutableLinkSequenceSetApi implementation.'

    _link_first : LinkHashEntry[V]
    _link_last  : LinkHashEntry[V]
    _link_map   : dict[V, LinkHashEntry[V]]

    __slots__ = '_link_first', '_link_last', '_link_map'

    def __init__(self, values: Iterable[V] = None, /):
        self._link_map = {}
        self._link_first = None
        self._link_last = None
        if values is not None:
            self.update(values)

    @property
    def _link_first_(self) -> LinkEntry[V]:
        return self._link_first

    @property
    def _link_last_(self) -> LinkEntry[V]:
        return self._link_last

    def __len__(self):
        return len(self._link_map)

    def __contains__(self, value: V):
        return value in self._link_map

    def _link_of(self, value: V) -> LinkHashEntry[V]:
        'Get a link entry by value.'
        if value in self._link_map:
            return self._link_map[value]
        raise MissingValueError(value)

    def __setitem__(self, index: int, value: V):
        'Set value by index. Raises ``DuplicateValueError``. Slice not implemented.'
        try:
            instcheck(index, int)
        except TypeError:
            if isinstance(index, slice):
                # TODO: Implement slice
                raise NotImplementedError
            raise

        # Check for duplicate.
        link_old = self._link_at(index)
        value = self._new_value(value)
        if value in self:
            if value == link_old.value:
                return
            raise DuplicateValueError(value)

        # Create link.
        link = link_old.copy()
        link.value = value

        # Remove old element.
        self.remove(link_old.value)

        # Add new element.
        self._before_add(value)
        if link.prev is None:
            # New first element.
            self._link_first = link
        else:
            # Connect to previous element.
            link.prev.next = link
        if link.next is None:
            # New last element.
            self._link_last = link
        else:
            # Connect to next element.
            link.next.prev = link
        self._link_map[value] = link
        self._after_add(value)

    def insert(self, index: int, value: V):
        'Insert a value before an index. Raises ``DuplicateValueError``.'
        index = self._absindex(index, False)

        if len(self) == 0:
            # Singleton.
            value = self._new_value(value)
            # Create link.
            link = LinkHashEntry(value)
            # Add new element.
            self._before_add(value)
            self._link_first = link
            self._link_last = link
            self._link_map[value] = link
            self._after_add(value)
            return

        if index >= len(self):
            # Append.
            self._put_common(LinkSub.next, self._link_last_, value)
            return

        if index <= 0:
            # Prepend.
            self._put_common(LinkSub.prev, self._link_first_, value)
            return

        # TODO: warn performance

        # In-between.
        self._put_common(LinkSub.prev, self._link_at(index), value)

    def remove(self, value: V):
        'Remove element by value.'
        link = self._link_of(value)
        self._before_remove(value)
        if link.prev is None:
            if link.next is None:
                # No more elements.
                self._link_first = None
                self._link_last = None
            else:
                # Promote new first element.
                link.next.prev = None
                self._link_first = link.next
        else:
            if link.next is None:
                # Promote new last element.
                link.prev.next = None
                self._link_last = link.prev
            else:
                # Patch the gap.
                link.prev.next = link.next
                link.next.prev = link.prev
        del self._link_map[value]
        self._after_remove(value)

    def reverse(self):
        'Reverse in place.'
        link = self._link_last
        while link is not None:
            link.invert()
            link = link.next
        self._link_first, self._link_last = self._link_last, self._link_first

    def sort(self, /, *, key = None, reverse = False):
        'Sort in place.'
        if len(self) < 2:
            return
        values = sorted(self, key = key, reverse = reverse)
        it = iter(values)
        link = None
        try:
            while True:
                link_prev = link
                link = self._link_of(next(it))
                link.prev = link_prev
                if link_prev is not None:
                    link_prev.next = link

        except StopIteration:
            link.next = None
        self._link_first = self._link_of(values[0])
        self._link_last = self._link_of(values[-1])

    def put_before(self, neighbor: V, value: V):
        'Insert a value before another value. Raises ``DuplicateValueError``.'
        self._put_common(LinkSub.prev, self._link_of(neighbor), value)

    def put_after(self, neighbor: V, value: V):
        'Insert a value after another value. Raises ``DuplicateValueError``.'
        self._put_common(LinkSub.next, self._link_of(neighbor), value)

    def clear(self):
        self._link_map.clear()
        self._link_first = None
        self._link_last = None

    # -------

    def _put_common(self, sub: LinkSub, link_neigh: LinkHashEntry[V], value: V, /):
        'Generic put before/after value method. Raises ``DuplicateValueError``.'

        # Check for duplicate.
        value = self._new_value(value)
        if value in self:
            raise DuplicateValueError(value)

        # Arg checks.
        sub = LinkSub(sub)
        if sub is LinkSub.self:
            raise NotImplementedError
        instcheck(link_neigh, LinkHashEntry)

        # Create link.
        link = LinkHashEntry(value)
        link[sub] = link_neigh[sub]
        link[-sub] = link_neigh

        # Add new element.
        self._before_add(value)
        if link_neigh[sub] is not None:
            # Point neighbor's old neighbor to new link.
            link_neigh[sub][-sub] = link
        # Point neighbor to new link.
        link_neigh[sub] = link
        if link[sub] is None:
            # Promote new first/last element.
            if sub is LinkSub.prev:
                self._link_first = link
            else:
                self._link_last = link
        self._link_map[value] = link
        self._after_add(value)

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