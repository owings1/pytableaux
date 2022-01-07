from __future__ import annotations
from errors import (
    MissingValueError, DuplicateValueError,
    instcheck as _instcheck
)
from .sets import setm
import utils

import enum
# import itertools
import typing

from .sequences import EMPTY_SEQ
from .sets import EMPTY_SET

T = typing.TypeVar('T')
V = typing.TypeVar('V')

class ErrMsg(enum.Enum):
    # SliceSize = 'attempt to assign sequence of size %d to slice of size %d'
    # ExtendedSliceSize = 'attempt to assign sequence of size %d to extended slice of size %d'
    StepZero = 'step cannot be zero'
    IndexRange = 'sequence index out of range'

class bases:
    from collections.abc import Iterable
    from .sets import SetApi, MutableSetApi
    from .sequences import SequenceApi, MutableSequenceApi

class d:
    from decorators import (
        abstract, overload#, metad, namedf, wraps
    )

class SequenceSetApi(bases.SequenceApi[V], bases.SetApi[V]):
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

    @d.abstract.impl
    def __contains__(self, value):
        'Set-based `contains` implementation.'
        return False


class MutableSequenceSetApi(SequenceSetApi[V], bases.MutableSequenceApi[V], bases.MutableSetApi[V]):
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

    @d.abstract
    def reverse(self):
        'Reverse in place.'
        # Must re-implement MutableSequence method.
        raise NotImplementedError

    def _setslice_prep(self: T, slc: slice, values: bases.Iterable) -> tuple[T, T]:
        olds, values = super()._setslice_prep(slc, values)
        for v in values:
            if v in self and v not in olds:
                raise DuplicateValueError(v)
        return olds, values

class qsetf(SequenceSetApi[V]):
    'Immutable sequence set implementation with built-in frozenset and tuple.'

    class _SetSeq_(typing.NamedTuple):
        set: frozenset
        seq: tuple

    _setseq_: _SetSeq_[V]
    __slots__ = '_setseq_',

    def __init__(self, values: bases.Iterable = None, /):
        seq = EMPTY_SEQ if values is None else tuple(dict.fromkeys(values))
        self._setseq_ = self._SetSeq_(frozenset(seq), seq)

    def __len__(self):
        return len(self._setseq_.seq)

    def __contains__(self, value):
        return value in self._setseq_.set

    @d.overload
    def __getitem__(self: T, index: slice) -> T: ...
    @d.overload
    def __getitem__(self, index: int) -> V: ...

    def __getitem__(self, index):
        if isinstance(index, int):
            return self._setseq_.seq[index]
        _instcheck(index, slice)
        return self._from_iterable(self._setseq_.seq[index])

    def __iter__(self):
        return iter(self._setseq_.seq)

    def __reversed__(self):
        return reversed(self._setseq_.seq)

    def __repr__(self):
        return utils.wraprepr(self, self._setseq_.seq)


class qset(MutableSequenceSetApi[V]):
    'MutableSequenceSetApi implementation backed by built-in set and list.'

    class _SetSeq_(typing.NamedTuple):
        set: setm
        seq: list

    _setseq_: _SetSeq_
    __slots__ = '_setseq_',

    def __init__(self, values: bases.Iterable = None, /):
        self._setseq_ = self._SetSeq_(setm(), list())
        if values is not None:
            self.update(values)

    __len__      = qsetf.__len__
    __contains__ = qsetf.__contains__
    __getitem__  = qsetf[V].__getitem__
    __iter__     = qsetf[V].__iter__
    __reversed__ = qsetf[V].__reversed__
    __repr__     = qsetf.__repr__

    def __delitem__(self, index: int | slice):
        'Delete by index/slice.'
        value = self[index]
        bset, bseq = self._setseq_
        if isinstance(index, int):
            del bseq[index]
            bset.remove(value)
            self._after_remove(value)
            return
        _instcheck(index, slice)
        del bseq[index]
        for v in value:
            bset.remove(v)
            self._after_remove(v)

    def __setitem__(self, index: int | slice, value):
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

        _instcheck(index, int)
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