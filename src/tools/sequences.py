from __future__ import annotations

__all__ = (
    'SequenceApi',
    'MutableSequenceApi',
    'SequenceCover',
    'seqf',
    'seqm',
    'deqseq',
)

from errors import (
    Emsg,
    instcheck,
)
from tools.abcs import (
    Copyable, abcm, abcf,
    T, VT
)
from tools.decorators import abstract, final, overload, membr

from collections import deque
from itertools import chain, repeat
from typing import (
    Iterable,
    MutableSequence,
    Sequence,
    Sized,
    SupportsIndex,
    TypeVar,
)

EMPTY = ()
NOARG = object()

def absindex(seqlen: int, index: SupportsIndex, /, strict = True) -> int:
    'Normalize to positive/absolute index.'
    if not isinstance(index, int):
        index = int(instcheck(index, SupportsIndex))
    if index < 0:
        index = seqlen + index
    if strict and (index >= seqlen or index < 0):
        raise Emsg.IndexOutOfRange(index)
    return index

def slicerange(seqlen: int, slice_: slice, values: Sized, /, strict = True) -> range:
    'Get a range of indexes from a slice and new values, and perform checks.'
    range_ = range(*slice_.indices(seqlen))
    if len(range_) != len(values):
        if strict:
            raise Emsg.MismatchSliceSize(values, range_)
        if abs(slice_.step or 1) != 1:
            raise Emsg.MismatchExtSliceSize(values, range_)
    return range_

class SequenceApi(Sequence[VT], Copyable):
    "Extension of collections.abc.Sequence and built-in sequence (tuple)."

    __slots__ = EMPTY

    @overload
    def __getitem__(self: SeqApiT, s: slice) -> SeqApiT: ...

    @overload
    def __getitem__(self, i: SupportsIndex) -> VT: ...

    @abstract
    def __getitem__(self, index):
        raise IndexError

    def __add__(self: SeqApiT, other: Iterable) -> SeqApiT:
        if not isinstance(other, Iterable):
            return NotImplemented
        return self._from_iterable(chain(self, other))

    def __mul__(self: SeqApiT, other: SupportsIndex) -> SeqApiT:
        if not isinstance(other, SupportsIndex):
            return NotImplemented
        return self._from_iterable(chain.from_iterable(repeat(self, other)))

    __radd__ = __add__
    __rmul__ = __mul__

    def copy(self):
        return self._from_iterable(self)

    @classmethod
    def _from_iterable(cls, it: Iterable):
        return cls(it)

class MutableSequenceApi(SequenceApi[VT], MutableSequence[VT]):
    'Fusion interface of collections.abc.MutableSequence and built-in list.'

    __slots__ = EMPTY

    @abstract
    def sort(self, /, *, key = None, reverse = False):
        raise NotImplementedError

    def __imul__(self, other):
        if not isinstance(other, SupportsIndex):
            return NotImplemented
        self.extend(chain.from_iterable(repeat(self, int(other) - 1)))
        return self

    # def _setslice_range(self: MutSeqT, slice_: slice, values: Sized, /) -> range:
    #     range_ = range(*slice_.indices(len(self)))
    #     if abs(slice_.step or 1) != 1 and len(range_) != len(values):
    #         raise Emsg.MismatchExtSliceSize(values, range_)
    #     return range_

class SequenceCover(SequenceApi[VT]):

    __slots__ = '__seq',

    def __init__(self, sequence: Sequence[VT]):
        self.__seq = sequence

    def __len__(self):
        return len(self.__seq)

    def __getitem__(self, index):
        return self.__seq[index]

    def __contains__(self, value):
        return value in self.__seq

    def __iter__(self):
        return iter(self.__seq)

    def __reversed__(self):
        return reversed(self.__seq)

    def count(self, value):
        return self.__seq.count(value)

    def index(self, *args):
        return self.__seq.index(*args)

    def copy(self):
        'Immutable copy, returns self.'
        return self

    def __repr__(self):
        from tools.misc import wraprepr
        return wraprepr(self, list(self))  

    @classmethod
    def _from_iterable(cls, it):
        if isinstance(it, Sequence):
            return cls(it)
        return cls(tuple(it))

class SequenceProxy(SequenceApi[VT]):
    'Sequence view proxy.'

    # Creates a new type for each instance.

    __slots__ = EMPTY

    @abcf.temp
    @membr.defer
    def pxfn(member: membr[type[SequenceProxy]]):
        # Builds a class method that retrieves the source instance method
        # and overwrites our class method, in effect a lazy loading of methods.
        name, cls = member.name, member.owner
        cls._proxy_names_.add(name)
        method = getattr(SequenceApi, name, None)
        if callable(method) and not abcm.isabstract(method):
            default = method
        else: default = NOARG
        @classmethod
        def f(cls: type[SequenceProxy], *args):
            proxy_pass = cls._get_base_attr(name, default)
            setattr(cls, name, proxy_pass)
            return proxy_pass(*args)
        return f

    _proxy_names_ = set()

    __len__        = pxfn()
    __getitem__    = pxfn()
    __contains__   = pxfn()
    __iter__       = pxfn()
    __reversed__   = pxfn()
    count          = pxfn()
    index          = pxfn()
    _from_iterable = pxfn()

    @abcf.after
    def _(cls): cls._proxy_names_ = frozenset(cls._proxy_names_)

    def copy(self):
        'Immutable copy, returns self.'
        return self

    def __repr__(self):
        from tools.misc import wraprepr
        return wraprepr(self, list(self))

    @classmethod
    @abstract
    def _get_base_attr(cls, name): ...

    @final
    def __init__(self, *_): pass

    def __new__(cls, base: SequenceApi[VT]) -> SequenceProxy[VT]:

        instcheck(base, SequenceApi)
        names = frozenset(cls._proxy_names_)

        class SeqProxy(SequenceProxy):

            __slots__ = EMPTY
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

class seqf(tuple[VT, ...], SequenceApi[VT]):
    'Frozen sequence, fusion of tuple and SequenceApi.'

    # NB: tuple implements all equality and ordering methods,
    # as well as __hash__ method.

    __slots__ = EMPTY
    __add__ = SequenceApi.__add__

    @overload
    def __radd__(self, other: seqf[VT]) -> seqf[VT]: ...
    @overload
    def __radd__(self, other: tuple[VT, ...]) -> tuple[VT, ...]: ...
    @overload
    def __radd__(self, other: list[VT]) -> list[VT]: ...
    @overload
    def __radd__(self, other: deque[VT]) -> deque[VT]: ...

    def __radd__(self, other):
        if not isinstance(other, Iterable):
            return NotImplemented
        # Check for various concrete types that we can create before
        # falling back on our type with _from_iterable.
        otype = type(other)
        it = chain(other, self)
        # Since we inherit from tuple, Python will prefer our __radd__
        # to tuple's __add__, which we don't want to override when the
        # left operand is a plain tuple.
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

class seqm(list[VT], MutableSequenceApi[VT]):

    __slots__ = EMPTY

    __imul__ = MutableSequenceApi.__imul__
    __mul__  = MutableSequenceApi.__mul__
    __rmul__ = MutableSequenceApi.__rmul__
    __add__  = MutableSequenceApi.__add__
    __radd__ = MutableSequenceApi.__radd__
    copy     = MutableSequenceApi.copy
    __copy__ = MutableSequenceApi.__copy__

    @overload
    def __getitem__(self: SeqApiT, s: slice) -> SeqApiT: ...

    @overload
    def __getitem__(self, i: SupportsIndex) -> VT: ...

    def __getitem__(self, i):
        if isinstance(i, slice):
            # Ensure slice returns this type, not a list.
            return self._from_iterable(super().__getitem__(i))
        return super().__getitem__(i)

class deqseq(deque[VT], MutableSequenceApi[VT]):

    __slots__ = EMPTY

    __imul__ = MutableSequenceApi.__imul__
    __mul__  = MutableSequenceApi.__mul__
    __rmul__ = MutableSequenceApi.__rmul__
    __add__  = MutableSequenceApi.__add__
    __radd__ = MutableSequenceApi.__radd__
    copy     = MutableSequenceApi.copy
    __copy__ = MutableSequenceApi.__copy__

    def sort(self, /, *, key = None, reverse = False):
        values = sorted(self, key = key, reverse = reverse)
        self.clear()
        self.extend(values)

    @classmethod
    def _from_iterable(cls, it: Iterable[VT]):
        if isinstance(it, deque):
            return cls(it, maxlen = it.maxlen)
        return cls(it)

class SequenceHooks(MutableSequenceApi[VT]):

    __slots__ = EMPTY

# class HookedDeqSeq(deqseq[VT]):

#     __slots__ = EMPTY

#     def __init__(self, values: Iterable = None, /, maxlen: int|None = None):
#         if values is None:
#             super().__init__(maxlen = maxlen)
#         else:
#             super().__init__(map(self._new_value, values), maxlen)

#     def insert(self, index: int, value):
#         super().insert(index, self._new_value(value))

#     def append(self, value):
#         super().append(self._new_value(value))

#     def appendleft(self, value):
#         super().appendleft(self._new_value(value))

#     def extend(self, values):
#         super().extend(map(self._new_value, values))

#     def extendleft(self, values):
#         super().extendleft(map(self._new_value, values))

#     def __setitem__(self, index: SupportsIndex, value):
#         instcheck(index, SupportsIndex)
#         super().__setitem__(index, self._new_value(value))


EMPTY_SEQ = seqf()

SeqApiT  = TypeVar('SeqApiT',  bound = SequenceApi)
MutSeqT  = TypeVar('MutSeqT',  bound = MutableSequenceApi)

SequenceApi.register(tuple)
MutableSequenceApi.register(list)
# MutableSequenceApi.register(deque)


del(Copyable, abcf, abcm, abstract, final, overload, membr)