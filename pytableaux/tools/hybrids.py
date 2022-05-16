# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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

from collections.abc import Collection
from itertools import filterfalse
from typing import Iterable, SupportsIndex

from pytableaux.errors import (DuplicateValueError, Emsg,
                               check)
from pytableaux.tools import abstract, abcs
from pytableaux.tools.sequences import (EMPTY_SEQ, MutableSequenceApi,
                                        SequenceApi, seqf, seqm, slicerange)
from pytableaux.tools.sets import EMPTY_SET, MutableSetApi, SetApi, setf, setm


__all__ = (
    'EMPTY_QSET',
    'MutableSequenceSet',
    'qset',
    'qsetf',
    'QsetView',
    'SequenceSet',
)

class SequenceSet(SequenceApi, SetApi):
    'Sequence set (ordered set) read interface.  Comparisons follow Set semantics.'

    __slots__ = EMPTY_SET

    def count(self, value, /) -> int:
        'Returns 1 if in the set, else 0.'
        return int(value in self)

    def index(self, value, start: int = 0, stop: int = None, /) -> int:
        'Get the index of the value in the sequence.'
        if value not in self:
            raise Emsg.MissingValue(value)
        return super().index(value, start, stop)

    def __mul__(self, other):
        if isinstance(other, SupportsIndex):
            if int(other) > 1 and len(self) > 0:
                raise Emsg.DuplicateValue(self[0])
        return super().__mul__(other)

    __rmul__ = __mul__

    @abstract
    def __contains__(self, value):
        'Set-based `contains` implementation.'
        return False

    def __repr__(self):
        return f'{type(self).__name__}(''{'f'{repr(list(self))[1:-1]}''})'

class qsetf(SequenceSet):
    'Immutable sequence set implementation setf and seqf bases.'

    _set_: SetApi
    _seq_: SequenceApi

    __slots__ = '_set_', '_seq_'

    def __new__(cls, values: Iterable = None, /):
        self = object.__new__(cls)
        if values is None:
            self._seq_ = EMPTY_SEQ
            self._set_ = EMPTY_SET
        else:
            self._seq_ = seqf(dict.fromkeys(values))
            self._set_ = setf(self._seq_)
        return self

    def copy(self):
        inst = object.__new__(type(self))
        # copy reference only
        inst._seq_ = self._seq_
        inst._set_ = self._set_
        return inst

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
        yield from self._seq_

    def __reversed__(self):
        return reversed(self._seq_)


EMPTY_QSET = qsetf()

class QsetView(SequenceSet):
    """SequenceSet view.
    """

    __slots__ = ('__len__', '__contains__', '__getitem__', '__iter__', '__reversed__')

    def __new__(cls, base: SequenceSet, /,):

        check.inst(base, SequenceSet)

        inst = object.__new__(cls)
        inst.__len__ = base.__len__
        inst.__iter__ = base.__iter__
        inst.__getitem__ = base.__getitem__
        inst.__contains__ = base.__contains__
        inst.__reversed__ = base.__reversed__

        return inst

    def copy(self):
        'Immutable copy, returns self.'
        return self


    @classmethod
    def _from_iterable(cls, it):
        if isinstance(it, cls):
            return it
        if isinstance(it, SequenceSet):
            return cls(it)
        return cls(qsetf(it))

class MutableSequenceSet(SequenceSet, MutableSequenceApi, MutableSetApi):
    """Mutable sequence set (ordered set) interface.

    Sequence methods such as ``append`` raise ``DuplicateValueError``.
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

    @abstract
    def reverse(self):
        'Reverse in place.'
        # Must re-implement MutableSequence method.
        raise NotImplementedError


class qset(MutableSequenceSet):
    'Mutable sequence set implementation backed by built-in set and list.'

    _set_type_: type = setm
    _seq_type_: type = seqm

    _set_: setm
    _seq_: seqm

    __slots__ = qsetf.__slots__

    def __new__(cls, *args, **kw):
        inst = object.__new__(cls)
        inst._set_ = cls._set_type_()
        inst._seq_ = cls._seq_type_()
        return inst

    def __init__(self, values: Iterable = None, /,):
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
    def insert(self, index: SupportsIndex, value, /, *,
        cast = None, check = None, done = None
    ):
        'Insert a value before an index. Raises ``DuplicateValueError``.'

        # hook.cast
        if cast is not None:
            value = cast(value)

        if value in self:
            raise DuplicateValueError(value)

        # hook.check
        if check is not None:
            check(self, (value,), EMPTY_SET)

        # --- begin changes -----
        self._seq_.insert(index, value)
        self._set_.add(value)
        # --- end changes -----

        # hook.done
        if done is not None:
            done(self, (value,), EMPTY_SET)

    @abcs.hookable('check', 'done')
    def __delitem__(self, key: SupportsIndex|slice, /, *,
        check = None, done = None
    ):
        'Delete by index/slice.'

        if isinstance(key, SupportsIndex):
            setdelete = self._set_.remove

        elif isinstance(key, slice):
            setdelete = self._set_.difference_update

        else:
            raise Emsg.InstCheck(key, (slice, SupportsIndex))

        # Retrieve the departing
        leaving = self[key]

        # hook.check
        if check is not None:
            check(self, EMPTY_SET, (leaving,))

        # --- begin changes -----
        del self._seq_[key]
        setdelete(leaving)
        # --- end changes -----

        # hook.done
        if done is not None:
            done(self, EMPTY_SET, (leaving,))


    @abcs.hookable('cast')
    def __setitem__(self, key, value, /, *,
        cast = None
    ):
        'Set value by index/slice. Raises ``DuplicateValueError``.'

        if isinstance(key, SupportsIndex):
            # hook.cast
            if cast is not None:
                value = cast(value)
            self.__setitem_index__(key, value)
            return

        if isinstance(key, slice):
            # hook.cast
            if cast is not None:
                value = tuple(map(cast, value))
            else:
                check.inst(value, Collection)
            self.__setitem_slice__(key, value)
            return

        raise Emsg.InstCheck(key, (slice, SupportsIndex))

    @abcs.hookable('check', 'done')
    def __setitem_index__(self, index: SupportsIndex, arriving, /, *,
        check = None, done = None,
    ):
        'Index setitem Implementation'

        #  Retrieve the departing
        leaving = self._seq_[index]
    
        #  Check for duplicates
        if arriving in self and arriving != leaving:
            raise Emsg.DuplicateValue(arriving)

        # hook.check
        if check is not None:
            check(self, (arriving,), (leaving,))

        # --- begin changes -----

        # Remove from set
        self._set_.remove(leaving)
        try:
            # Assign by index to list.
            self._seq_[index] = arriving
        except:
            # On error, restore the set.
            self._set_.add(leaving)
            raise
        else:
            #  Add new value to the set
            self._set_.add(arriving)

        # --- end changes -----

        # hook.done
        if done is not None:
            done(self, (arriving,), (leaving,))

    @abcs.hookable('check', 'done')
    def __setitem_slice__(self, slice_: slice, arriving: Collection, /, *,
        check = None, done = None,
    ):
        'Slice setitem Implementation'

        # Check length and compute range. This will fail for some bad input,
        # and it is fast to compute.
        range_ = slicerange(len(self), slice_, arriving)

        # Retrieve the departing.
        leaving = self[slice_]

        # Check for duplicates.
        # Any value that we already contain, and is not leaving with the others
        # is a duplicate.
        for v in filterfalse(leaving.__contains__, filter(self.__contains__, arriving)):
            raise Emsg.DuplicateValue(v)

        # hook.check
        if check is not None:
            check(self, arriving, leaving)

        # --- begin changes -----
        # Remove from set.
        self._set_ -= leaving
        try:
            # Assign by slice to list.
            self._seq_[slice_] = arriving
        except:
            # On error, restore the set.
            self._set_ |= leaving
            raise
        else:
            # Add new values to set.
            self._set_ |= arriving
        # --- end changes -----

        # hook.done
        if done is not None:
            done(self, arriving, leaving)


