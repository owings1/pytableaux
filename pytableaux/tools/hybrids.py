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

from abc import abstractmethod as abstract
from collections.abc import MutableSequence, MutableSet, Sequence, Set
from itertools import chain, filterfalse
from typing import Iterable, SupportsIndex, TypeVar

from ..errors import DuplicateValueError, Emsg, check
from . import EMPTY_SEQ, EMPTY_SET, abcs, slicerange

__all__ = (
    'EMPTY_QSET',
    'MutableSequenceSet',
    'qset',
    'qsetf',
    'QsetView',
    'SequenceSet')

_T = TypeVar('_T')

class SequenceSet(Sequence[_T], Set[_T], metaclass = abcs.AbcMeta):
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

    @abstract
    def __contains__(self, value):
        'Set-based `contains` implementation.'
        return False

    def __repr__(self):
        return f'{type(self).__name__}(''{'f'{repr(list(self))[1:-1]}''})'

    @classmethod
    def _from_iterable(cls, it, /):
        return cls(it)

    def __add__(self, other):
        if isinstance(other, (Sequence, Set)):
            return self._from_iterable(chain(self, other))
        return NotImplemented

    def __radd__(self, other):
        if type(other) in (list, set):
            return type(other)(chain(other, self))
        return NotImplemented

class qsetf(SequenceSet[_T], abcs.Copyable, immutcopy = True):
    'Immutable sequence set implementation with frozenset and tuple bases.'

    _set_: frozenset
    _seq_: tuple

    __slots__ = ('_set_', '_seq_')

    def __new__(cls, values: Iterable = None, /):
        self = object.__new__(cls)
        if values is None:
            self._seq_ = EMPTY_SEQ
            self._set_ = EMPTY_SET
        else:
            self._seq_ = tuple(dict.fromkeys(values))
            self._set_ = frozenset(self._seq_)
        return self

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

class QsetView(SequenceSet, abcs.Copyable, immutcopy = True):
    """SequenceSet view.
    """

    __slots__ = ('__len__', '__contains__', '__getitem__', '__iter__', '__reversed__')

    def __new__(cls, base: SequenceSet, /,):
        check.inst(base, SequenceSet)
        self = object.__new__(cls)
        self.__len__ = base.__len__
        self.__iter__ = base.__iter__
        self.__getitem__ = base.__getitem__
        self.__contains__ = base.__contains__
        self.__reversed__ = base.__reversed__
        return self

    @classmethod
    def _from_iterable(cls, it):
        if isinstance(it, cls):
            return it
        if isinstance(it, SequenceSet):
            return cls(it)
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

    @abstract
    def reverse(self):
        'Reverse in place.'
        # Must re-implement MutableSequence method.
        raise NotImplementedError

class qset(MutableSequenceSet[_T], abcs.Copyable):
    'Mutable sequence set implementation backed by built-in set and list.'

    _set_type_ = set
    _seq_type_ = list

    _set_: set
    _seq_: list

    __slots__ = qsetf.__slots__

    def __new__(cls, *args, **kw):
        self = object.__new__(cls)
        self._set_ = cls._set_type_()
        self._seq_ = cls._seq_type_()
        return self

    def __init__(self, values = None, /,):
        if values is not None:
            self |= values

    def copy(self):
        inst = object.__new__(type(self))
        inst._set_ = self._set_.copy()
        inst._seq_ = self._seq_.copy()
        return inst

    __len__      = qsetf.__len__
    __contains__ = qsetf.__contains__
    __getitem__  = qsetf.__getitem__
    __iter__     = qsetf.__iter__
    __reversed__ = qsetf.__reversed__
    __repr__     = qsetf.__repr__

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

    @abcs.hookable('cast', 'check', 'done')
    def insert(self, index, value, /, *, cast = None, check = None, done = None):
        'Insert a value before an index. Raises ``DuplicateValueError``.'
        if cast is not None:
            value = cast(value)
        if value in self:
            raise DuplicateValueError(value)
        if check is not None:
            check(self, (value,), EMPTY_SET)
        self._seq_.insert(index, value)
        self._set_.add(value)
        if done is not None:
            done(self, (value,), EMPTY_SET)

    @abcs.hookable('check', 'done')
    def __delitem__(self, key, /, *, check = None, done = None):
        'Delete by index/slice.'
        if isinstance(key, SupportsIndex):
            setdelete = self._set_.remove
        elif isinstance(key, slice):
            setdelete = self._set_.difference_update
        else:
            raise Emsg.InstCheck(key, (slice, SupportsIndex))
        leaving = self[key]
        if check is not None:
            check(self, EMPTY_SET, (leaving,))
        del self._seq_[key]
        setdelete(leaving)
        if done is not None:
            done(self, EMPTY_SET, (leaving,))

    @abcs.hookable('cast')
    def __setitem__(self, key, value, /, *, cast = None):
        'Set value by index/slice. Raises ``DuplicateValueError``.'
        if isinstance(key, SupportsIndex):
            if cast is not None:
                value = cast(value)
            self.__setitem_index__(key, value)
            return
        if isinstance(key, slice):
            if cast is not None:
                value = tuple(map(cast, value))
            self.__setitem_slice__(key, value)
            return
        raise Emsg.InstCheck(key, (slice, SupportsIndex))

    @abcs.hookable('check', 'done')
    def __setitem_index__(self, index, arriving, /, *, check = None, done = None):
        'Index setitem Implementation'
        leaving = self._seq_[index]
        if arriving in self and arriving != leaving:
            raise Emsg.DuplicateValue(arriving)
        if check is not None:
            check(self, (arriving,), (leaving,))
        self._set_.remove(leaving)
        try:
            self._seq_[index] = arriving
        except:
            self._set_.add(leaving)
            raise
        else:
            self._set_.add(arriving)
        if done is not None:
            done(self, (arriving,), (leaving,))

    @abcs.hookable('check', 'done')
    def __setitem_slice__(self, slice_, arriving, /, *, check = None, done = None):
        'Slice setitem Implementation'
        # Check length and compute range. This will fail for some bad input,
        # and it is fast to compute.
        _ = slicerange(len(self), slice_, arriving)
        leaving = self[slice_]
        # Check for duplicates.
        # Any value that we already contain, and is not leaving with the others
        # is a duplicate.
        for v in filterfalse(leaving.__contains__, filter(self.__contains__, arriving)):
            raise Emsg.DuplicateValue(v)
        if check is not None:
            check(self, arriving, leaving)
        self._set_ -= leaving
        try:
            self._seq_[slice_] = arriving
        except:
            self._set_ |= leaving
            raise
        else:
            self._set_ |= arriving
        if done is not None:
            done(self, arriving, leaving)
