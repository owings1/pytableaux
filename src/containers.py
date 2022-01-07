from __future__ import annotations


from decorators import abstract, operd, wraps, metad, namedf #deleg, 
from errors import instcheck, DuplicateValueError, MissingValueError #DuplicateKeyError, 
from utils import ABCMeta, IndexType, notsubclscheck, \
    wraprepr \
    # cat, wrparens, orepr, subclscheck, NOARG

from collections import deque
from collections.abc import Collection, Iterable, Iterator, \
    Mapping, MappingView, Sized, Reversible, Callable
import collections.abc as bases
import enum
import operator as opr
from types import MappingProxyType as MapProxy
from typing import Any, Annotated, Generic, NamedTuple, TypeVar, abstractmethod, final, overload
# import abc
# from copy import copy
# from functools import reduce
# from itertools import chain, filterfalse
import itertools
# import math
# import typing

from callables import preds, calls#, cchain, gets

__all__ = (
    'Abc', 'Copyable',
    'SetApi', #'MutableSetApi',
    'setf', 'setm', # SetSeqPair,
    'SequenceApi', #'MutableSequenceApi',
    'SequenceProxy',
    'seqf',
    'SequenceSetApi', #'MutableSequenceSetApi',
    'qsetf', 'qset', # MutSetSeqPair,
    'linqset', # MutableLinkSequenceSetApi, # Link
    'MapAttrView',
    # DequeCache
)

K = TypeVar('K')
T = TypeVar('T')
R = TypeVar('R')
V = TypeVar('V')
I = TypeVar('I')
NOARG = object()


class ErrMsg(enum.Enum):
    SliceSize = 'attempt to assign sequence of size %d to slice of size %d'
    ExtendedSliceSize = 'attempt to assign sequence of size %d to extended slice of size %d'
    StepZero = 'step cannot be zero'
    IndexRange = 'sequence index out of range'

class Abc(metaclass = ABCMeta):
    __slots__ = ()

class Copyable(Abc):
    __slots__ = ()

    @abstractmethod
    def copy(self: T) -> T:
        raise NotImplementedError

    def __copy__(self):
        return self.copy()

    def __deepcopy__(self, memo):
        inst = self.copy()
        memo[id(self)] = inst
        return inst

    __subcls_methods = '__copy__', 'copy', '__deepcopy__'

    @classmethod
    def __subclasshook__(cls, subcls: type):
        if cls is not __class__:
            return NotImplemented
        return cls.check_mrodict(subcls.mro(), cls.__subcls_methods)

# -------------- Sequence ---------------#

class SequenceApi(bases.Sequence[V], Copyable):
    "Extension of collections.abc.Sequence and built-in sequence (tuple)."

    __slots__ = ()

    @overload
    def __getitem__(self: T, s: slice) -> T: ...

    @overload
    def __getitem__(self, i: int) -> V: ...

    @abstractmethod
    def __getitem__(self, index):
        raise IndexError

    @overload
    def __add__(self:T, other: Iterable) -> T: ...
    def __add__(self, other):
        if not isinstance(other, Iterable):
            return NotImplemented
        return self._from_iterable(itertools.chain(self, other))

    __radd__ = __add__

    @overload
    def __mul__(self:T, other: int) -> T: ...
    def __mul__(self, other):
        if not isinstance(other, int):
            return NotImplemented
        return self._from_iterable(
            itertools.chain.from_iterable(
                itertools.repeat(self, other)
            )
        )

    __rmul__ = __mul__

    def _absindex(self, index: int, strict = True, /) -> int:
        'Normalize to positive/absolute index.'
        instcheck(index, int)
        if index < 0:
            index = len(self) + index
        if strict and (index >= len(self) or index < 0):
            raise IndexError(ErrMsg.IndexRange.value)
        return index

    def copy(self):
        return self._from_iterable(self)

    @classmethod
    def _from_iterable(cls: type[T], it: Iterable) -> T:
        return cls(it)

SequenceApi.register(tuple)

class MutableSequenceApi(SequenceApi[V], bases.MutableSequence[V]):
    'Fusion interface of collections.abc.MutableSequence and built-in list.'

    __slots__ = ()

    @abstractmethod
    def sort(self, /, *, key = None, reverse = False):
        raise NotImplementedError

    def _new_value(self, value):
        '''Hook to return the new value before it is attempted to be added.
        Must be idempotent. Does not affect deletions.'''
        return value

    @overload
    def _setslice_prep(self:T, slc: slice, values: Iterable, /) -> tuple[T, T]: ...
    def _setslice_prep(self, slc: slice, values: Iterable, /):
        olds = self[slc]
        values = self._from_iterable(map(self._new_value, values))
        if abs(slc.step or 1) != 1 and len(olds) != len(values):
            raise ValueError(
                ErrMsg.ExtendedSliceSize.value % (len(values), len(olds))
            )
        return olds, values

    @overload
    def __imul__(self:T, other: int) -> T: ...
    def __imul__(self, other):
        if not isinstance(other, int):
            return NotImplemented
        self.extend(itertools.chain.from_iterable(
            itertools.repeat(self, other - 1)
        ))
        return self

MutableSequenceApi.register(list)
MutableSequenceApi.register(deque)

class SequenceProxy(SequenceApi[V]):
    'Sequence view proxy.'

    __slots__ = ()

    _proxy_names_ = set()

    @metad.after
    def _after(cls):
        cls._proxy_names_ = frozenset(cls._proxy_names_)

    @metad.temp
    def proxyfn(default = NOARG, *args):
        def defer(member: namedf[type[SequenceProxy]], default = NOARG):
            owner, name = member._owner_name
            owner._proxy_names_.add(name)
            if default is NOARG:
                method = getattr(SequenceApi, name, None)
                if callable(method) and not abstract.isabstract(method):
                    default = method
            def f(cls: type[SequenceProxy], *args):
                proxy_method = cls._get_base_attr(name, default)
                setattr(cls, name, proxy_method)
                return proxy_method(*args)
            return classmethod(wraps(member)(f))
        return namedf(defer, *args)

    __len__      = proxyfn()
    __getitem__  = proxyfn()
    __contains__ = proxyfn()
    __iter__     = proxyfn()
    __reversed__ = proxyfn()
    count        = proxyfn()
    index        = proxyfn()
    _from_iterable = proxyfn()

    def copy(self):
        return self

    def __repr__(self):
        return wraprepr(self, list(self))

    @classmethod
    @abstractmethod
    def _get_base_attr(cls, name): ...

    def __new__(cls, base: SequenceApi):

        instcheck(base, SequenceApi)
        names = cls._proxy_names_

        class SeqProxy(SequenceProxy):

            __slots__ = EMPTY_SET
            __new__ = object.__new__

            @classmethod
            def _get_base_attr(cls, name, default = NOARG,/):
                if name in names:
                    value = getattr(base, name, default)
                    if value is not NOARG: return value
                raise AttributeError(name)

        SeqProxy.__qualname__ = '%s.%s' % (
            type(base).__qualname__, SeqProxy.__name__
        )
        return SeqProxy()

class seqf(tuple[V], SequenceApi[V]):
    'Frozen sequence, fusion of tuple and SequenceApi.'
    # __eq__  = tuple.__eq__
    # __ne__  = tuple.__ne__

    # __gt__  = tuple.__gt__
    # __ge__  = tuple.__ge__
    # __lt__  = tuple.__lt__
    # __le__  = tuple.__le__

    # __hash__ = tuple.__hash__

    __add__  = SequenceApi.__add__

    @overload
    def __radd__(self, other: seqf[V]) -> seqf[V]: ...
    @overload
    def __radd__(self, other: tuple[V, ...]) -> tuple[V, ...]: ...
    @overload
    def __radd__(self, other: list[V]) -> list[V]: ...
    @overload
    def __radd__(self, other: deque[V]) -> deque[V]: ...

    def __radd__(self, other):
        if not isinstance(other, Iterable):
            return NotImplemented
        # Check concrete type, not subclass.
        otype = type(other)
        it = itertools.chain(other, self)
        # Since we inherit from tuple, Python will prefer our __radd__
        # to tuple's __add__, which we don't want to override.
        if otype is tuple or otype is list:
            return otype(it)
        if otype is deque:
            maxlen = other.maxlen
            if maxlen is not None and len(other) + len(self) > maxlen:
                # Making a new deque that exceeds maxlen of lhs is not supported.
                raise TypeError(
                    "deque maxlen (%d) would be exceeded by "
                    "new instance (%s)" % (maxlen, len(other) + len(self))
                )
            return otype(it, maxlen)
        return self._from_iterable(it)

    __mul__  = SequenceApi.__mul__
    __rmul__ = SequenceApi.__rmul__

    def __repr__(self):
        return type(self).__name__ + super().__repr__()


EMPTY_SEQ = seqf()

# -------------- Set ---------------#

class SetApi(bases.Set[V], Copyable):
    'Fusion interface of collections.abc.Set and built-in frozenset.'

    __slots__ = EMPTY_SEQ

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

    def __or__(self :T|SetApi, other) -> T: ...
    def __and__(self :T|SetApi, other) -> T: ...
    def __sub__(self :T|SetApi, other) -> T: ...
    def __xor__(self :T|SetApi, other) -> T: ...
    __or__  = bases.Set.__or__
    __and__ = bases.Set.__and__
    __sub__ = bases.Set.__sub__
    __xor__ = bases.Set.__xor__

    def copy(self):
        return self._from_iterable(self)

    @classmethod
    def _from_iterable(cls: type[T], it: Iterable) -> T:
        return cls(it)

class setf(SetApi[V], frozenset[V]):
    'SetApi wrapper around built-in frozenset.'
    __slots__ = ()
    __len__      = frozenset.__len__
    __contains__ = frozenset.__contains__
    __iter__     = frozenset[V].__iter__

EMPTY_SET = setf()

class MutableSetApi(bases.MutableSet[V], SetApi[V]):
    'Fusion interface of collections.abc.MutableSet and built-in set.'

    __slots__ = EMPTY_SET

    update              = operd.iterself(opr.ior,  info = set.update)
    intersection_update = operd.iterself(opr.iand, info = set.intersection_update)
    difference_update   = operd.iterself(opr.isub, info = set.difference_update)

    symmetric_difference_update = operd.apply(opr.ixor,
        info = set.symmetric_difference_update
    )

class setm(MutableSetApi[V], set[V]):
    'MutableSetApi wrapper around built-in set.'
    __slots__ = EMPTY_SET
    __len__      = set.__len__
    __contains__ = set.__contains__
    __iter__     = set[V].__iter__
    clear   = set.clear
    add     = set.add
    discard = set.discard

# ------------- SequenceSet ---------------#

class SequenceSetApi(SequenceApi[V], SetApi[V]):
    'Sequence set (ordered set) read interface.  Comparisons follow Set semantics.'

    __slots__ = EMPTY_SET

    def count(self, value, /) -> int:
        'Returns 1 if in the set, else 0.'
        return int(value in self)

    def index(self, value, start = 0, stop = None, /) -> int:
        'Get the index of the value in the set.'
        if value not in self:
            raise MissingValueError(value)
        return super().index(value, start, stop)

    def __mul__(self, other):
        if isinstance(other, int):
            if other > 1 and len(self) > 0:
                raise DuplicateValueError(self[0])
        return super().__mul__(other)

    __rmul__ = __mul__

    # __add__ = operd.apply(opr.or_)

    @abstractmethod
    def __contains__(self, value):
        'Set-based `contains` implementation.'
        return False

    ImplNotes: Annotated[dict, dict(
        # implement = {
        #     SequenceApi: {'__add__'},
        # },
        override = {
            SequenceApi: {
                'count', 'index', '__mul__', '__rmul__',
            },
        },
        inherit = {
            SequenceApi: {
                '__iter__', '__reversed__', '__add__', '__radd__',
            },
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
        abstract = {'__len__', '__contains__', '__getitem__', 'copy'},
    )]

class MutableSequenceSetApi(SequenceSetApi[V], MutableSequenceApi[V], MutableSetApi[V]):
    """Mutable sequence set (ordered set) interface.
    Sequence methods such as ``append`` raise ``DuplicateValueError``."""

    __slots__ = EMPTY_SET

    def _before_add(self, value):
        '''Before add hook. Not guaranteed that the value will be added, and
        it may already be in the sequence, but not the set.'''
        pass

    def _after_add(self, value):
        'After add hook.'
        pass

    def _after_remove(self, value):
        'After remove hook.'
        pass

    def add(self, value):
        'Append, catching ``DuplicateValueError``.'
        # Unlike discard() we try/except instead of pre-checking membership,
        # to make sure the _new_value hook is called.
        try:
            self.append(value)
        except DuplicateValueError:
            pass

    def discard(self, value):
        'Remove if value is a member.'
        if value in self:
            self.remove(value)

    @abstractmethod
    def reverse(self):
        'Reverse in place.'
        # Must re-implement MutableSequence method.
        raise NotImplementedError

    def _setslice_prep(self: T, slc: slice, values: Iterable) -> tuple[T, T]:
        olds, values = super()._setslice_prep(slc, values)
        for v in values:
            if v in self and v not in olds:
                raise DuplicateValueError(v)
        return olds, values

    ImplNotes: Annotated[dict, dict(
        implement = {
            MutableSetApi: {'add', 'discard'}
        },
        inherit = {
            SequenceApi: {
                '__iter__', '__reversed__', '__add__', '__radd__',
            },
            SequenceSetApi: {
                'count', 'index', '__mul__', '__rmul__',
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
                'update', 'intersection_update', 'difference_update',
                'symmetric_difference_update',
            },
            MutableSequenceApi: {
                'append', 'extend', '__iadd__', '__imul__',
                'pop', 'remove', 'clear',
            },
        },
        resolve = {
            'pop'   : MutableSequenceApi.pop,
            'remove': MutableSequenceApi.remove,
        },
        abstract = {
            '__len__', '__contains__', '__getitem__',
            '__setitem__', '__delitem__', 'insert',
            'sort', 'reverse',
        }
    )]

class qsetf(SequenceSetApi[V]):
    'Immutable sequence set implementation with built-in frozenset and tuple.'

    class _SetSeq_(NamedTuple):
        set: frozenset
        seq: tuple

    _setseq_: _SetSeq_[V]
    __slots__ = '_setseq_',

    def __init__(self, values: Iterable = None, /):
        seq = EMPTY_SEQ if values is None else tuple(dict.fromkeys(values))
        self._setseq_ = self._SetSeq_(frozenset(seq), seq)

    def __len__(self):
        return len(self._setseq_.seq)

    def __contains__(self, value):
        return value in self._setseq_.set

    @overload
    def __getitem__(self: T, index: slice) -> T: ...
    @overload
    def __getitem__(self, index: int) -> V: ...

    def __getitem__(self, index):
        if isinstance(index, int):
            return self._setseq_.seq[index]
        instcheck(index, slice)
        return self._from_iterable(self._setseq_.seq[index])

    def __iter__(self):
        return iter(self._setseq_.seq)

    def __reversed__(self):
        return reversed(self._setseq_.seq)

    def __repr__(self):
        return wraprepr(self, self._setseq_.seq)

    ImplNotes: Annotated[dict, dict(
        implement = {'__len__', '__contains__', '__getitem__'},
        override = {'__repr__', 'copy'},
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


class qset(MutableSequenceSetApi[V]):
    'MutableSequenceSetApi implementation backed by built-in set and list.'

    class _SetSeq_(NamedTuple):
        set: setm
        seq: list

    _setseq_: _SetSeq_
    __slots__ = '_setseq_',

    def __init__(self, values: Iterable = None, /):
        self._setseq_ = self._SetSeq_(setm(), list())
        if values is not None:
            self.update(values)

    __len__      = qsetf.__len__
    __contains__ = qsetf.__contains__
    __getitem__  = qsetf[V].__getitem__
    __iter__     = qsetf[V].__iter__
    __reversed__ = qsetf[V].__reversed__
    __repr__     = qsetf.__repr__

    def __delitem__(self, index: IndexType):
        'Delete by index/slice.'
        value = self[index]
        bset, bseq = self._setseq_
        if isinstance(index, int):
            del bseq[index]
            bset.remove(value)
            self._after_remove(value)
            return
        instcheck(index, slice)
        del bseq[index]
        for v in value:
            bset.remove(v)
            self._after_remove(v)

    def __setitem__(self, index: IndexType, value):
        'Set value by index/slice. Raises ``DuplicateValueError``.'
        bset, bseq = self._setseq_
        if isinstance(index, slice):
            olds, values = self._setslice_prep(index, value)
            bset.difference_update(olds)
            try:
                bseq[index] = values
                try:
                    for old in olds:
                        self._after_remove(old)
                    for v in values:
                        self._before_add(v)
                except:
                    bseq[index] = olds
                    raise
            except:
                bset.update(olds)
                raise
            bset.update(values)
            for v in values:
                self._after_add(v)
            return

        instcheck(index, int)
        old = bseq[index]
        value = self._new_value(value)
        if value in self:
            if value == old:
                return
            raise DuplicateValueError(value)
        bset.remove(old)
        bseq[index] = value
        try:
            self._after_remove(old)
            self._before_add(value)
        except:
            bseq[index] = old
            bset.add(old)
            raise
        bset.add(value)
        self._after_add(value)

    def insert(self, index: int, value):
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
        self._setseq_.seq.clear()
        self._setseq_.set.clear()

    def copy(self):
        inst = object.__new__(type(self))
        inst._setseq_ = self._SetSeq_(
            self._setseq_.set, self._setseq_.seq
            # self._setseq_.set.copy(), self._setseq_.seq.copy()
        )
        return inst

    ImplNotes: Annotated[dict, dict(
        implement = {
            '__setitem__', '__delitem__', 'insert', 'sort', 'reverse',
        },
        override = {'clear', 'copy'},
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

class LinkRel(enum.Enum):
    'Link directional/subscript enum.'

    prev = -1
    self = 0
    next = 1

    def __neg__(self) -> LinkRel:
        return __class__(-self.value)

    def __int__(self):
        return self.value

class Link(Generic[V], Copyable):
    'Link value container.'

    value: V
    prev: Link[V]
    next: Link[V]

    __slots__ = 'prev', 'next', 'value'

    @property
    def self(self: T) -> T:
        return self

    def __init__(self, value, prev: Link = None, nxt: Link = None, /):
        self.value = value
        self.prev = prev
        self.next = nxt

    def __getitem__(self, rel: int|LinkRel) -> Link[V] | None:
        'Get previous, self, or next with -1, 0, 1, or ``LinkRel`` enum.'
        return getattr(self, LinkRel(rel).name)

    def __setitem__(self, rel: int|LinkRel, link: Link):
        'Set previous or next with -1, 1, or ``LinkRel`` enum.'
        setattr(self, LinkRel(rel).name, link)

    def invert(self):
        'Invert prev and next attributes in place.'
        self.prev, self.next = self.next, self.prev

    def copy(self, value = NOARG):
        inst: Link = object.__new__(self.__class__)
        inst.value = self.value if value is NOARG else value
        inst.prev = self.prev
        inst.next = self.next
        return inst

    def __repr__(self):
        return wraprepr(self, self.value)

class HashLink(Link[V]):

    __slots__ = EMPTY_SET

    def __eq__(self, other):
        if self is other:
            return True
        if isinstance(other, self.__class__):
            return self.value == other.value
        return self.value == other

    def __hash__(self):
        return hash(self.value)

class LinkIter(Iterator[Link[V]], Abc):
    'Linked sequence iterator.'

    _start: Link
    _step: int
    _rel: LinkRel
    _count: int
    _cur: Link

    __slots__ = '_start', '_step', '_count', '_cur', '_rel'

    def __init__(self, start: Link, step: int = 1, count: int = -1, /):
        step = int(step)
        self._start = start if count else None
        self._step = abs(step)
        self._count = count
        try:
            self._rel = LinkRel(step / self._step)
        except ZeroDivisionError:
            raise ValueError(ErrMsg.StepZero.value) from None
        self._cur = None

    @classmethod
    def from_slice(
        cls: type[LinkIter[V]],
        seq: LinkSequenceApi[V],
        slc: slice,
    /) -> LinkIter[V]:
        istart, stop, step = slc.indices(len(seq))
        count = (stop - istart) / step
        if count % 1: count += 1 # ceil
        start = None if count < 1 else seq._link_at(istart)
        return cls(start, step, int(count))

    def __iter__(self):
        return self

    @final
    def advance(self):
        if not self._count:
            self._cur = None
        elif self._cur is None:
            self._cur = self._start
        else:
            i = 0
            while i < self._step and self._cur is not None:
                i += 1
                self._cur = self._cur[self._rel]
        if self._cur is None:
            del self._start
            self._count = None
            raise StopIteration
        self._count -= 1

    def __next__(self) -> Link[V]:
        self.advance()
        return self._cur

class LinkValueIter(LinkIter[V]):
    'Linked sequence iterator over values.'

    __slots__ = EMPTY_SET

    @classmethod
    def from_slice(
        cls: type[LinkValueIter[V]],
        seq: LinkSequenceApi[V],
        slc: slice,
    /) -> LinkValueIter[V]: ...
    from_slice = LinkIter.from_slice

    def __next__(self) -> V:
        self.advance()
        return self._cur.value

# ----------- LinkSequence ------------------ #

class LinkSequenceApi(SequenceApi[V]):
    'Linked sequence read interface.'

    __slots__ = EMPTY_SET

    @property
    @abstractmethod
    def _link_first_(self) -> Link[V]:
        return None

    @property
    @abstractmethod
    def _link_last_(self) -> Link[V]:
        return None

    def __iter__(self):
        return LinkValueIter(self._link_first_, 1)

    def __reversed__(self):
        return LinkValueIter(self._link_last_, -1)

    @overload
    def __getitem__(self, index: int) -> V:...
    @overload
    def __getitem__(self:T, index: slice) -> T: ...

    def __getitem__(self, index):
        '''Get element(s) by index/slice.

        Retrieves links using _link_at(index) method. Subclasses should
        avoid overriding this method, and instead override _link_at() for
        any performance enhancements.'''
        if isinstance(index, slice):
            return self._from_iterable(
                LinkValueIter.from_slice(self, index)
            )
        return self._link_at(index).value

    def _link_at(self, index: int) -> Link:
        'Get a Link entry by index. Supports negative value. Raises ``IndexError``.'

        index = self._absindex(index)

        # Direct access for first/last.
        if index == 0:
            return self._link_first_
        if index == len(self) - 1:
            return self._link_last_

        # TODO: warn performance

        # Choose best iteration direction.
        if index > len(self) / 2:
            # Scan reversed from end.
            it = LinkIter(self._link_last_, index - len(self) + 1, 2)
        else:
            # Scan forward from beginning.
            it = LinkIter(self._link_first_, index, 2)

        # Advance iterator.
        it.advance()
        return next(it)

    def __repr__(self):
        return wraprepr(self, list(self))

class MutableLinkSequenceApi(LinkSequenceApi[V], MutableSequenceApi[V]):
    'Linked sequence write interface.'
    __slots__  = EMPTY_SET

    _new_link = Link
    # @abstractmethod
    # def __setitem__(self, index: IndexType, value):
    #     ...

class linkseq(MutableLinkSequenceApi[V]):
    # __first : Link
    # __last  : Link

    # def __init__(self, values: Iterable = None, /):
    #     self.__first = None
    #     self.__last = None
    #     if values is not None:
    #         self.extend(values)
    # @property
    # def _link_first_(self) -> Link:
    #     return self.__first

    # @property
    # def _link_last_(self) -> Link:
    #     return self.__last

    ...

# ----------- LinkSequenceSet ------------------ #

class MutableLinkSequenceSetApi(MutableLinkSequenceApi[V], MutableSequenceSetApi[V]):
    'Linked sequence set read/write interface.'

    __slots__ = EMPTY_SET

    _new_link = HashLink

    @abstractmethod
    def _link_of(self, value) -> Link:
        'Get a link entry by value. Implementations must raise ``MissingValueError``.'
        raise NotImplementedError

    @abstractmethod
    def _seed(self, link: Link, /):
        'Add the link as the intial (only) member.'
        raise NotImplementedError

    @abstractmethod
    def _wedge(self, rel: LinkRel, neighbor: Link, link: Link, /):
        'Add the new link and wedge it next to neighbor.'
        raise NotImplementedError

    @abstractmethod
    def _unlink(self, link: Link):
        'Remove a link entry. Implementations must not alter the link attributes.'
        raise NotImplementedError

    def insert(self, index: int, value):
        '''Insert a value before an index. Raises ``DuplicateValueError`` and
        ``MissingValueError``.'''
        index = self._absindex(index, False)
        if len(self) == 0:
            # Seed.
            self.seed(value)
        elif index >= len(self):
            # Append.
            self.wedge(1, self._link_last_.value, value)
        elif index <= 0:
            # Prepend.
            self.wedge(-1, self._link_first_.value, value)
        else:
            # In-between.
            self.wedge(-1, self._link_at(index).value, value)

    def __setitem__(self, index: IndexType, value):
        '''Set value by index/slice. Raises ``DuplicateValueError``.

        Retrieves the existing link at index using _link_at(), then calls
        remove() with the value. If the set is empty, seed() is called.
        Otherwise, wedge() is used to place the value after the old link's
        previous link, or, if setting the first value, before the old link's
        next link.
        
        Note that the old value is removed before the attempt to set the new value.
        This is to avoid double-calling the _new_value hook to check for membership.
        If a DuplicateValueError is raised, an attempt is made to re-add the old
        value using the old link attributes, skipping _new_value, _before_add, and
        _after_add hooks, by calling the _wedge method.'''
        if isinstance(index, slice):
            olds, values = self._setslice_prep(index, value)
            if len(olds) != len(values):
                raise ValueError(ErrMsg.SliceSize.value % (len(values), len(olds)))
            it = LinkIter.from_slice(self, index)
            for link, v in zip(it, values):
                if v in self:
                    # Skip hooks since we are just re-ordering the value.
                    link.value = v
                    continue
                self.remove(link.value)
                if len(self) == 0:
                    self.seed(v)
                elif link.prev is not None:
                    self.wedge(1, link.prev.value, v)
                else:
                    self.wedge(-1, link.next.value, v)
            return
        instcheck(index, int)
        link = self._link_at(index)
        self.remove(link.value)
        if len(self) == 0:
            self.seed(value)
            return
        try:
            if link.prev is not None:
                self.wedge(1, link.prev.value, value)
            else:
                self.wedge(-1, link.next.value, value)
        except DuplicateValueError:
            if link.prev is not None:
                self._wedge(LinkRel(1), link.prev, link)
            else:
                self._wedge(LinkRel(-1), link.next, link)
            raise

    def __delitem__(self, index: IndexType):
        '''Remove element(s) by index/slice.
        
        Retrieves the link with _link_at() and calls remove() with the value.
        
        For slices, an iterator is created from LinkIter.from_slice(), which
        uses _link_at() to retrieve the first link. Each value is deleted by
        calling remove() as it is yielded from the iterator. This avoids loading
        all values into memory, but assumes neither remove() nor _unlink() will
        modify the prev/next attributes of the Link object.'''
        if isinstance(index, slice):
            for value in LinkValueIter.from_slice(self, index):
                self.remove(value)
            return
        self.remove(self._link_at(index).value)

    def remove(self, value):
        '''Remove element by value. Raises ``MissingValueError``.
        
        Retrieves the link using _link_of and delegates to the subclass _unlink
        implementation. This handles the _after_remove hook.'''
        self._unlink(self._link_of(value))
        self._after_remove(value)

    def seed(self, value):
        '''Add the initial element. Raises ``IndexError`` if non-empty.

        This is called by __setitem__ and insert when the set is empty.
        This calls the _new_value hook and handles the _before_add and
        _after_add hooks, then delegates to the subclass _seed implementation.'''
        if len(self) > 0: raise IndexError
        value = self._new_value(value)
        self._before_add(value)
        self._seed(self._new_link(value))
        self._after_add(value)

    def wedge(self, rel: int|LinkRel, neighbor, value, /):
        '''Place a new value next to another value. Raises ``DuplicateValueError``
        and ``MissingValueError``.
        
        This is called by __setitem__ and insert when the set is non-empty.
        This calls the _new_value hook and handles the _before_add and
        _after_add hooks. The neighbor link is retrieved using _link_of.
        This handles missing/duplicate errors, and delegates to the subclass
        _wedge implementation.'''
        rel = LinkRel(rel)
        if rel is LinkRel.self:
            raise NotImplementedError
        neighbor = self._link_of(neighbor)
        value = self._new_value(value)
        if value in self:
            raise DuplicateValueError(value)
        self._before_add(value)
        self._wedge(rel, neighbor, self._new_link(value))
        self._after_add(value)

    def iter_from_value(self, value, /, reverse = False) -> Iterator[V]:
        'Return an iterator starting from ``value``.'
        return LinkValueIter(self._link_of(value), -1 if reverse else 1)

class linqset(MutableLinkSequenceSetApi[V]):
    'MutableLinkSequenceSetApi implementation.'

    __first : HashLink[V]
    __last  : HashLink[V]
    __links : dict[V, HashLink[V]]

    __slots__ = '__first', '__last', '__links'

    def __init__(self, values: Iterable = None, /):
        self.__links = {}
        self.__first = None
        self.__last = None
        if values is not None:
            self.update(values)

    @property
    def _link_first_(self) -> HashLink[V]:
        return self.__first

    @property
    def _link_last_(self) -> HashLink[V]:
        return self.__last

    def __len__(self):
        return len(self.__links)

    def __contains__(self, value: V):
        return value in self.__links

    def _link_of(self, value: V) -> HashLink[V]:
        if value in self.__links:
            return self.__links[value]
        raise MissingValueError(value)

    def _seed(self, link: Link, /):
        self.__first = \
        self.__last = \
        self.__links[link.value] = link

    def _wedge(self, sub: LinkRel, neighbor: Link, link: Link, /):
        link[sub] = neighbor[sub]
        link[-sub] = neighbor
        if neighbor[sub] is not None:
            # Point neighbor's old neighbor to new link.
            neighbor[sub][-sub] = link
        # Point neighbor to new link.
        neighbor[sub] = link
        if link[sub] is None:
            # Promote new first/last element.
            if sub is sub.prev:
                self.__first = link
            else:
                self.__last = link
        self.__links[link.value] = link

    def _unlink(self, link: Link):
        if link.prev is None:
            if link.next is None:
                # No more elements.
                self.__first = None
                self.__last = None
            else:
                # Promote new first element.
                link.next.prev = None
                self.__first = link.next
        else:
            if link.next is None:
                # Promote new last element.
                link.prev.next = None
                self.__last = link.prev
            else:
                # Patch the gap.
                link.prev.next = link.next
                link.next.prev = link.prev
        del self.__links[link.value]

    def reverse(self):
        'Reverse in place.'
        link = self.__last
        while link is not None:
            link.invert()
            link = link.next
        self.__first, self.__last = self.__last, self.__first

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
        self.__first = self._link_of(values[0])
        self.__last = self._link_of(values[-1])

    def clear(self):
        'Clear the collection.'
        self.__links.clear()
        self.__first = None
        self.__last = None

    def copy(self):
        inst = object.__new__(self.__class__)
        inst.__links = links = self.__links.__class__()
        it = LinkIter(self.__first)
        try:
            link = next(it)
        except StopIteration:
            inst.__first = inst.__last = None
        else:
            inst.__first = links[link.value] = link.copy()
            for link in it:
                links[link.value] = link.copy()
            inst.__last = link
        return inst

class MapAttrView(Mapping[str, V], Copyable):
    'A Mapping with attribute access.'

    __slots__ = '_mapping',

    def __init__(self, base: Mapping[str, V]):
        self._mapping = base

    def __getattr__(self, name: str) -> V:
        try:
            return self._mapping[name]
        except KeyError:
            raise AttributeError(name)

    def __dir__(self):
        return list(filter(preds.isidentifier, self))

    def copy(self):
        inst = object.__new__(self.__class__)
        inst._mapping = self._mapping
        return inst

    def __len__(self):
        return len(self._mapping)

    def __getitem__(self, key: str) -> V:
        return self._mapping[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._mapping)

    def __reversed__(self) -> Iterator[str]:
        return reversed(self._mapping)

class DequeCache(Collection[V], Reversible, Sized, Abc):

    __slots__ = EMPTY_SET

    maxlen: int
    idx: int
    rev: Mapping[Any, V]

    @abstractmethod
    def clear(self): ...

    @abstractmethod
    def __getitem__(self, key) -> V: ...

    @abstractmethod
    def __setitem__(self, key, item: V): ...

    def __new__(cls, Vtype: type, maxlen = 10):

        notsubclscheck(Vtype, IndexType)
        instcheck(Vtype, type)

        idx      : dict[Any, V] = {}
        idxproxy : Mapping[Any, V] = MapProxy(idx)

        rev      : dict[V, set] = {}
        revproxy : Mapping[V, set] = MapProxy(rev)

        deck     : deque[V] = deque(maxlen = maxlen)

        class Api(DequeCache[V]):

            __slots__ = EMPTY_SET

            maxlen = property(lambda _: deck.maxlen)
            idx = property(lambda _: idxproxy)
            rev = property(lambda _: revproxy)

            def clear(self):
                for d in (idx, rev, deck): d.clear()

            def __len__(self):
                return len(deck)

            def __iter__(self) -> Iterator[V]:
                return iter(deck)

            def __reversed__(self) -> Iterator[V]:
                return reversed(deck)

            def __contains__(self, item: V):
                return item in rev

            def __getitem__(self, key) -> V:
                # if isinstance(key, IndexType): return deck[key]
                return idx[key]

            def __setitem__(self, key, item: V):
                instcheck(item, Vtype)
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

            __new__  = object.__new__

        Api.__qualname__ = 'DequeCache.Api'
        return Api()

del(operd, metad, abstract, namedf, )