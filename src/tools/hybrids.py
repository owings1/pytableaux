from __future__ import annotations

__all__ = 'SequenceSetApi', 'MutableSequenceSetApi', 'qsetf', 'qset'

from errors import (
    instcheck as _instcheck,
    subclscheck,
    DuplicateValueError,
    MissingValueError,
)
from tools.abcs import T, VT
from tools.decorators import abstract, overload
from tools.sequences import SequenceApi, MutableSequenceApi, seqf
from tools.sets import SetApi, MutableSetApi, setf, setm

from typing import Iterable, MutableSequence, SupportsIndex

EMPTY = ()

class SequenceSetApi(SequenceApi[VT], SetApi[VT]):
    'Sequence set (ordered set) read interface.  Comparisons follow Set semantics.'

    __slots__ = EMPTY

    def count(self, value, /) -> int:
        'Returns 1 if in the set, else 0.'
        return int(value in self)

    def index(self, value, start = 0, stop = None, /) -> int:
        'Get the index of the value in the set.'
        if value not in self:
            raise MissingValueError(value)
        return super().index(value, start, stop)

    def __mul__(self, other):
        if isinstance(other, SupportsIndex):
            if int(other) > 1 and len(self) > 0:
                raise DuplicateValueError(self[0])
        return super().__mul__(other)

    __rmul__ = __mul__

    @abstract
    def __contains__(self, value):
        'Set-based `contains` implementation.'
        return False

class MutableSequenceSetApi(SequenceSetApi[VT], MutableSequenceApi[VT], MutableSetApi[VT]):
    """Mutable sequence set (ordered set) interface.
    Sequence methods such as ``append`` raise ``DuplicateValueError``."""

    __slots__ = EMPTY

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
        # Use contains check instead of try/except for set performance. 
        if value in self:
            self.remove(value)

    @abstract
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

class qsetf(SequenceSetApi[VT]):
    'Immutable sequence set implementation setf and seqf bases.'

    _set_type_ = setf
    _seq_type_ = seqf

    _set_: SetApi[VT]
    _seq_: SequenceApi[VT]

    __slots__ = '_set_', '_seq_'

    def __init__(self, values: Iterable = None, /):
        cls = type(self)
        if values is None:
            self._seq_ = cls._seq_type_()
            self._set_ = cls._set_type_()
        else:
            self._seq_ = cls._seq_type_(tuple(dict.fromkeys(values)))
            self._set_ = cls._set_type_(self._seq_)

    def __len__(self):
        return len(self._seq_)

    def __contains__(self, value):
        return value in self._set_

    @overload
    def __getitem__(self: T, index: slice) -> T: ...
    @overload
    def __getitem__(self, index: SupportsIndex) -> VT: ...

    def __getitem__(self, index):
        if isinstance(index, SupportsIndex):
            return self._seq_[index]
        _instcheck(index, slice)
        return self._from_iterable(self._seq_[index])

    def __iter__(self):
        return iter(self._seq_)

    def __reversed__(self):
        return reversed(self._seq_)

    def __repr__(self):
        return '%s({%s})' % (
            type(self).__name__,
            list(self._seq_).__repr__()[1:-1]
        )

class qset(MutableSequenceSetApi[VT]):
    'MutableSequenceSetApi implementation backed by built-in set and list.'

    _set_: MutableSetApi[VT]
    _seq_: MutableSequenceApi[VT]

    __slots__ = '_set_', '_seq_'

    def __init__(self, values: Iterable = None, /, qtype: type[MutableSequenceApi] = list):
        self._set_ = setm()
        self._seq_ = subclscheck(qtype, MutableSequenceApi)()#list()
        if values is not None:
            self |= values

    __len__      = qsetf.__len__
    __contains__ = qsetf.__contains__
    __getitem__  = qsetf[VT].__getitem__
    __iter__     = qsetf[VT].__iter__
    __reversed__ = qsetf[VT].__reversed__
    __repr__     = qsetf.__repr__

    def __delitem__(self, index: SupportsIndex|slice):
        'Delete by index/slice.'
        if isinstance(index, SupportsIndex):
            value = self[index]
            del self._seq_[index]
            self._set_.remove(value)
            self._after_remove(value)
            return

        _instcheck(index, slice)
        values = self[index]
        del self._seq_[index]
        bset = self._set_
        for value in values:
            bset.remove(value)
            self._after_remove(value)

    def __setitem__(self, index: SupportsIndex|slice, value):
        'Set value by index/slice. Raises ``DuplicateValueError``.'

        if isinstance(index, SupportsIndex):
            old = self._seq_[index]
            value = self._new_value(value)
            if value in self:
                if value == old:
                    return
                raise DuplicateValueError(value)
            self._set_.remove(old)
            self._seq_[index] = value
            try:
                self._after_remove(old)
                self._before_add(value)
            except:
                self._seq_[index] = old
                self._set_.add(old)
                raise
            self._set_.add(value)
            self._after_add(value)
            return

        _instcheck(index, slice)

        olds, values = self._setslice_prep(index, value)
        self._set_ -= olds
        try:
            self._seq_[index] = values
            try:
                for old in olds:
                    self._after_remove(old)
                for value in values:
                    self._before_add(value)
            except:
                self._seq_[index] = olds
                raise
        except:
            self._set_ |= olds
            raise
        self._set_ |= values
        for value in values:
            self._after_add(value)

    def insert(self, index: SupportsIndex, value):
        'Insert a value before an index. Raises ``DuplicateValueError``.'
        value = self._new_value(value)
        if value in self:
            raise DuplicateValueError(value)
        self._before_add(value)
        self._seq_.insert(index, value)
        self._set_.add(value)
        self._after_add(value)

    def reverse(self):
        'Reverse in place.'
        self._seq_.reverse()

    def sort(self, /, *, key = None, reverse = False):
        'Sort the list in place.'
        self._seq_.sort(key = key, reverse = reverse)

    def clear(self):
        'Clear the list and set.'
        self._seq_.clear()
        self._set_.clear()

    def copy(self):
        cls = type(self)
        inst = cls.__new__(cls)
        inst._set_ = self._set_.copy()
        inst._seq_ = self._seq_.copy()
        return inst

del(abstract, overload)