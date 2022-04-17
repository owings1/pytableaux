from __future__ import annotations

__all__ = (
    'SequenceApi',
    'MutableSequenceApi',
    'SequenceCover',
    'seqf',
    'seqm',
    'deqseq',
)

from pytableaux.errors import Emsg, instcheck
from pytableaux.tools import abstract
from pytableaux.tools.abcs import Copyable, abcm, abcf
from pytableaux.tools.typing import VT

from collections import deque
from itertools import chain, repeat
from typing import (
    final, overload,
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
    def __getitem__(self: SeqApiT, s: slice, /) -> SeqApiT: ...

    @overload
    def __getitem__(self, i: SupportsIndex, /) -> VT: ...

    @abstract
    def __getitem__(self, index, /):
        raise IndexError

    def __add__(self: SeqApiT, other: Iterable) -> SeqApiT:
        if not isinstance(other, Iterable):
            return NotImplemented
        restype = self._concat_res_type(type(other))
        if not callable(restype):
            return NotImplemented
        return restype(chain(self, other))

    def __radd__(self: SeqApiT, other: Iterable) -> SeqApiT:
        if not isinstance(other, Iterable):
            return NotImplemented
        restype = self._rconcat_res_type(type(other))
        if not callable(restype):
            return NotImplemented
        return restype(chain(other, self))

    def __mul__(self: SeqApiT, other: SupportsIndex) -> SeqApiT:
        if not isinstance(other, SupportsIndex):
            return NotImplemented
        return self._from_iterable(chain.from_iterable(repeat(self, other)))

    __rmul__ = __mul__

    def copy(self):
        return self._from_iterable(self)

    @classmethod
    def _from_iterable(cls, it: Iterable, /):
        return cls(it)

    @classmethod
    def _concat_res_type(cls, othrtype: type[Iterable], /):
        '''Return the type (or callable) to construct a new instance from __add__.'''
        return cls._from_iterable

    @classmethod
    def _rconcat_res_type(cls, othrtype: type[Iterable], /):
        '''Return the type (or callable) to construct a new instance from __radd__.'''
        return cls._concat_res_type(othrtype)

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
        from pytableaux.tools.misc import wraprepr
        return wraprepr(self, list(self))  

    @classmethod
    def _from_iterable(cls, it):
        if isinstance(it, Sequence):
            return cls(it)
        return cls(tuple(it))

class seqf(tuple[VT, ...], SequenceApi[VT]):
    'Frozen sequence, fusion of tuple and SequenceApi.'

    # NB: tuple implements all equality and ordering methods,
    # as well as __hash__ method.

    __slots__ = EMPTY
    __add__ = SequenceApi.__add__

    # Note that __getitem__ with slice returns a tuple, not a seqf,
    # because it does not call _from_iterable.

    @overload
    def __radd__(self, other: tuple[VT, ...]) -> tuple[VT, ...]: ...
    @overload
    def __radd__(self, other: list[VT]) -> list[VT]: ...
    @overload
    def __radd__(self, other: deque[VT]) -> deque[VT]: ...
    @abcf.temp
    @overload
    def __radd__(self, other: seqf[VT]) -> seqf[VT]: ...

    @classmethod
    def _rconcat_res_type(cls, othrtype: type[Iterable], /):
        if othrtype in {tuple, list, deque, seqf}:
            return othrtype
        return cls._concat_res_type(othrtype)

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
    def __getitem__(self: MutSeqT, s: slice, /) -> MutSeqT: ...

    @overload
    def __getitem__(self, i: SupportsIndex, /) -> VT: ...

    def __getitem__(self, i, /):
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


EMPTY_SEQ = seqf()

SeqApiT  = TypeVar('SeqApiT',  bound = SequenceApi)
MutSeqT  = TypeVar('MutSeqT',  bound = MutableSequenceApi)

SequenceApi.register(tuple)
MutableSequenceApi.register(list)
# MutableSequenceApi.register(deque)

del(Copyable, abcf, abcm, abstract, final, overload)