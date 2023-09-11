# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
pytableaux.tools.hybrids
^^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from abc import abstractmethod
from collections.abc import MutableSequence, MutableSet, Sequence, Set
from itertools import chain, filterfalse
from typing import (TYPE_CHECKING, Any, Callable, Iterable, Iterator, Self,
                    SupportsIndex, TypeVar)

from ..errors import DuplicateValueError, Emsg, check
from . import EMPTY_SEQ, EMPTY_SET, abcs, slicerange

if TYPE_CHECKING:
    from typing import overload

__all__ = (
    'EMPTY_QSET',
    'MutableSequenceSet',
    'qset',
    'qsetf',
    'QsetView',
    'SequenceSet')

_T = TypeVar('_T')
_T1 = TypeVar('_T1')

class SequenceSet(Sequence[_T], Set[_T], metaclass=abcs.AbcMeta):
    'Sequence set (ordered set) read interface.  Comparisons follow Set semantics.'

    __slots__ = EMPTY_SET

    def count(self, value, /) -> int:
        'Returns 1 if in the set, else 0.'
        return int(value in self)

    def index(self, value, start = 0, stop = None, /) -> int:
        'Get the index of the value in the sequence.'
        if value not in self:
            raise Emsg.MissingValue(value)
        return super().index(value, start, stop)

    @abstractmethod
    def __contains__(self, value):
        'Set-based `contains` implementation.'
        return False

    def __repr__(self):
        return f'{type(self).__name__}(''{'f'{repr(list(self))[1:-1]}''})'

    @classmethod
    def _from_iterable(cls, it, /):
        return cls(it)

    if TYPE_CHECKING:
        @overload
        def __ior__(self, other: Any) -> Self: ...
        @overload
        def __or__(self, other: Any) -> Self: ...
        @overload
        def __iand__(self, other: Any) -> Self: ...
        @overload
        def __and__(self, other: Any) -> Self: ...
        @overload
        def __iadd__(self, other: Any) -> Self: ...
        @overload
        def __radd__(self, other: list[_T1]) -> list[_T1]: ...
        @overload
        def __radd__(self, other: set[_T1]) -> set[_T1]: ...
        @overload
        def __sub__(self, other: Any) -> Self: ...
        @overload
        def __isub__(self, other: Any) -> Self: ...

    def __add__(self, other) -> Self:
        if isinstance(other, (Sequence, Set)):
            return self._from_iterable(chain(self, other))
        return NotImplemented

    def __radd__(self, other):
        if type(other) in (list, set):
            return type(other)(chain(other, self))
        return NotImplemented

class qsetf(SequenceSet[_T], abcs.Copyable, immutcopy=True):
    'Immutable sequence set implementation with frozenset and tuple bases.'

    _set_: Set[_T]
    _seq_: Sequence[_T]

    __slots__ = ('_set_', '_seq_')

    def __init__(self, values: Iterable = None, /):
        if values is None:
            self._seq_ = EMPTY_SEQ
            self._set_ = EMPTY_SET
        else:
            self._seq_ = tuple(dict.fromkeys(values))
            self._set_ = frozenset(self._seq_)

    def __len__(self):
        return len(self._seq_)

    def __contains__(self, value):
        return value in self._set_

    def __getitem__(self, index):
        if isinstance(index, SupportsIndex):
            return self._seq_[index]
        if isinstance(index, slice):
            return self._from_iterable(self._seq_[index])
        raise Emsg.InstCheck(index, (slice, SupportsIndex))

    def __iter__(self):
        return iter(self._seq_)

    def __reversed__(self):
        return reversed(self._seq_)


EMPTY_QSET = qsetf()

class QsetView(SequenceSet[_T], abcs.Copyable, immutcopy=True):
    """SequenceSet view.
    """

    if TYPE_CHECKING:
        __iter__: Callable[[Self], Iterator[_T]]
        __reversed__: Callable[[Self], Iterator[_T]]

    __slots__ = ('__len__', '__contains__', '__getitem__', '__iter__', '__reversed__')

    def __new__(cls, base, /):
        check.inst(base, SequenceSet)
        self = object.__new__(cls)
        for name in __class__.__slots__:
            setattr(self, name, getattr(base, name))
        return self

    @classmethod
    def _from_iterable(cls, it):
        return cls(qsetf(it))

class MutableSequenceSet(SequenceSet[_T], MutableSequence[_T], MutableSet[_T]):
    """Mutable sequence set (ordered set) interface.

    Sequence methods such as :attr:`append` raise :class:`DuplicateValueError`.
    """
    __slots__ = EMPTY_SET

    def add(self, value):
        'Append, catching ``DuplicateValueError``.'
        # Unlike discard() we try/except instead of pre-checking membership,
        # to allow for hooks to be called.
        try:
            self.append(value)
        except DuplicateValueError:
            pass

    def discard(self, value):
        'Remove if value is a member.'
        # Use contains check instead of try/except for set performance. 
        if value in self:
            self.remove(value)

    def update(self, it):
        for _ in map(self.add, it): pass

    @abstractmethod
    def reverse(self):
        'Reverse in place.'
        # Must re-implement MutableSequence method.
        raise NotImplementedError

class qset(MutableSequenceSet[_T], abcs.Copyable):
    'Mutable sequence set implementation backed by built-in set and list.'

    _set_type_ = set
    _seq_type_ = list

    _set_: set[_T]
    _seq_: list[_T]

    __slots__ = qsetf.__slots__

    def __new__(cls, *args, **kw):
        self = object.__new__(cls)
        self._set_ = cls._set_type_()
        self._seq_ = cls._seq_type_()
        return self

    def __init__(self, values = None, /,):
        if values is not None:
            self.update(values)

    def copy(self):
        inst = object.__new__(type(self))
        inst._set_ = self._set_.copy()
        inst._seq_ = self._seq_.copy()
        return inst

    if TYPE_CHECKING:
        @overload
        def __getitem__(self, index: SupportsIndex) -> _T: ...
        @overload
        def __getitem__(self, index: slice) -> Self: ...
        @overload
        def __iter__(self) -> Iterator[_T]: ...
        @overload
        def __reversed__(self) -> Iterator[_T]: ...

    __len__      = qsetf.__len__
    __contains__ = qsetf.__contains__
    __getitem__  = qsetf.__getitem__
    __iter__     = qsetf.__iter__
    __reversed__ = qsetf.__reversed__
    __repr__     = qsetf.__repr__

    def discard(self, value):
        return super().discard(self._hook_cast(value))

    def reverse(self):
        'Reverse in place.'
        self._seq_.reverse()

    def sort(self, /, *, key: Callable[[_T], Any]|None=None, reverse:bool=False):
        'Sort the list in place.'
        if key is None:
            key = self._default_sort_key
        self._seq_.sort(key=key, reverse=reverse)

    def clear(self):
        'Clear the list and set.'
        self._seq_.clear()
        self._set_.clear()

    def insert(self, index: SupportsIndex, value: _T, /):
        'Insert a value before an index. Raises ``DuplicateValueError``.'
        value = self._hook_cast(value)
        if value in self:
            raise DuplicateValueError(value)
        arriving = (value,)
        self._hook_check(arriving, EMPTY_SEQ)
        self._seq_.insert(index, value)
        self._set_.add(value)
        self._hook_done(arriving, EMPTY_SEQ)

    def __delitem__(self, key):
        'Delete by index/slice.'
        if isinstance(key, SupportsIndex):
            values = (self[key],)
        else:
            values = self[key]
        self._hook_check(EMPTY_SEQ, values)
        del self._seq_[key]
        self._set_.difference_update(values)
        self._hook_done(EMPTY_SEQ, values)

    def __setitem__(self, key, value):
        'Set value by index/slice. Raises ``DuplicateValueError``.'
        if isinstance(key, SupportsIndex):
            value = self._hook_cast(value)
            self.__setitem_index__(key, value)
            return
        if isinstance(key, slice):
            values = tuple(map(self._hook_cast, value))
            self.__setitem_slice__(key, values)
            return
        raise Emsg.InstCheck(key, (slice, SupportsIndex))

    def __setitem_index__(self, index: SupportsIndex, value, /):
        'Index setitem Implementation'
        old = self._seq_[index]
        if value in self and value != old:
            raise Emsg.DuplicateValue(value)
        arriving = (value,)
        leaving = (old,)
        self._hook_check(arriving, leaving)
        self._set_.remove(old)
        try:
            self._seq_[index] = value
        except:
            self._set_.add(old)
            raise
        else:
            self._set_.add(value)
        self._hook_done(arriving, leaving)

    def __setitem_slice__(self, slice_: slice, values, /):
        'Slice setitem Implementation'
        # Check length and compute range. This will fail for some bad input,
        # and it is fast to compute.
        _ = slicerange(len(self), slice_, values)
        leaving = self[slice_]
        # Check for duplicates.
        # Any value that we already contain, and is not leaving with the others
        # is a duplicate.
        for v in filterfalse(leaving.__contains__, filter(self.__contains__, values)):
            raise Emsg.DuplicateValue(v)
        self._hook_check(values, leaving)
        self._set_.difference_update(leaving)
        try:
            self._seq_[slice_] = values
        except:
            self._set_.update(leaving)
            raise
        else:
            self._set_.update(values)
        self._hook_done(values, leaving)

    def _hook_check(self, arriving: Sequence[_T], leaving: Sequence[_T]) -> None:
        pass
    
    def _hook_done(self, arriving: Sequence[_T], leaving: Sequence[_T]) -> None:
        pass

    def _hook_cast(self, value: Any) -> _T:
        return value

    def _default_sort_key(self, value: _T) -> Any:
        return value