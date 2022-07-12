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
pytableaux.tools.sequences
^^^^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from abc import abstractmethod as abstract
from collections import deque
from itertools import chain, repeat
from typing import Iterable, MutableSequence, Sequence, SupportsIndex

from pytableaux.errors import Emsg, check
from pytableaux.tools import abcs, closure
from pytableaux.tools.sets import EMPTY_SET

__all__ = (
    'absindex',
    'deqseq',
    'EMPTY_SEQ',
    'MutableSequenceApi',
    'seqf',
    'seqm',
    'SequenceApi',
    'SeqCover',
    'slicerange',
)

NOARG = object()

def absindex(seqlen, index, /, strict = True):
    'Normalize to positive/absolute index.'
    if type(index) is not int:
        index = int(check.inst(index, SupportsIndex))
    if index < 0:
        index = seqlen + index
    if strict and (index >= seqlen or index < 0):
        raise Emsg.IndexOutOfRange(index)
    return index

def slicerange(seqlen, slice_: slice, values, /, strict = True):
    'Get a range of indexes from a slice and new values, and perform checks.'
    range_ = range(*slice_.indices(seqlen))
    if len(range_) != len(values):
        if strict:
            raise Emsg.MismatchSliceSize(values, range_)
        if abs(slice_.step or 1) != 1:
            raise Emsg.MismatchExtSliceSize(values, range_)
    return range_

class SequenceApi(Sequence, abcs.Copyable):
    "Extension of collections.abc.Sequence and built-in sequence (tuple)."

    __slots__ = EMPTY_SET

    @abstract
    def __getitem__(self, index, /):
        raise IndexError

    def __add__(self, other):
        if not isinstance(other, Iterable):
            return NotImplemented
        restype = self._concat_res_type(type(other))
        if not callable(restype):
            return NotImplemented
        return restype(chain(self, other))

    def __radd__(self, other):
        if not isinstance(other, Iterable):
            return NotImplemented
        restype = self._rconcat_res_type(type(other))
        if not callable(restype):
            return NotImplemented
        return restype(chain(other, self))

    def __mul__(self, other):
        if not isinstance(other, SupportsIndex):
            return NotImplemented
        return self._from_iterable(chain.from_iterable(repeat(self, other)))

    __rmul__ = __mul__

    def copy(self):
        return self._from_iterable(self)

    @classmethod
    def _from_iterable(cls, it, /):
        return cls(it)

    @classmethod
    def _concat_res_type(cls, othrtype, /):
        '''Return the type (or callable) to construct a new instance from __add__.'''
        return cls._from_iterable

    @classmethod
    def _rconcat_res_type(cls, othrtype, /):
        '''Return the type (or callable) to construct a new instance from __radd__.'''
        return cls._concat_res_type(othrtype)

class seqf(tuple, SequenceApi):
    'Frozen sequence, fusion of tuple and SequenceApi.'

    # NB: tuple implements all equality and ordering methods,
    # as well as __hash__ method.

    __slots__ = EMPTY_SET

    # Note that __getitem__ with slice returns a tuple, not a seqf,
    # because it does not call _from_iterable.

    @classmethod
    @closure
    def _rconcat_res_type():
        passtypes = {tuple, list, deque}
        def restype(cls: type[seqf], othrtype: type[Iterable], /):
            if othrtype is seqf or othrtype in passtypes:
                return othrtype
            return cls._concat_res_type(othrtype)
        return restype

    __add__ = SequenceApi.__add__
    __mul__  = SequenceApi.__mul__
    __rmul__ = SequenceApi.__rmul__

    def __repr__(self):
        return type(self).__name__ + super().__repr__()

class MutableSequenceApi(SequenceApi, MutableSequence):
    'Fusion interface of collections.abc.MutableSequence and built-in list.'

    __slots__ = EMPTY_SET

    @abstract
    def sort(self, /, *, key = None, reverse = False):
        raise NotImplementedError

    def __imul__(self, other):
        if not isinstance(other, SupportsIndex):
            return NotImplemented
        self.extend(chain.from_iterable(repeat(self, int(other) - 1)))
        return self


class CoverAttr(frozenset, abcs.Ebc):
    REQUIRED = {'__len__', '__getitem__', '__contains__', '__iter__',
        'count', 'index',}
    OPTIONAL = {'__reversed__'}
    ALL = REQUIRED | OPTIONAL

class SeqCover(SequenceApi, immutcopy = True):

    __slots__ = CoverAttr.ALL.copy()

    def __new__(cls, seq: Sequence, /):
        self = object.__new__(cls)
        sa = object.__setattr__
        for name in CoverAttr.REQUIRED:
            sa(self, name, getattr(seq, name))
        for name in CoverAttr.OPTIONAL:
            value = getattr(seq, name, NOARG)
            if value is not NOARG:
                sa(self, name, value)
        return self

    def __delattr__(self, name, /):
        if name in CoverAttr.ALL:
            raise Emsg.ReadOnly(self, name)
        super().__delattr__(name)

    def __setattr__(self, name, value, /):
        if name in CoverAttr.ALL:
            raise Emsg.ReadOnly(self, name)
        super().__setattr__(name, value)

    def __repr__(self):
        return f'{type(self).__name__}({list(self)})'

    @classmethod
    def _from_iterable(cls, it):
        if isinstance(it, cls):
            return it
        if isinstance(it, Sequence):
            return cls(it)
        return cls(tuple(it))

class seqm(list, MutableSequenceApi):

    __slots__ = EMPTY_SET

    __imul__ = MutableSequenceApi.__imul__
    __mul__  = MutableSequenceApi.__mul__
    __rmul__ = MutableSequenceApi.__rmul__
    __add__  = MutableSequenceApi.__add__
    __radd__ = MutableSequenceApi.__radd__
    copy     = MutableSequenceApi.copy

    def __getitem__(self, i, /):
        if isinstance(i, slice):
            # Ensure slice returns this type, not a list.
            return self._from_iterable(super().__getitem__(i))
        return super().__getitem__(i)

class deqseq(deque, MutableSequenceApi):

    __slots__ = EMPTY_SET

    __imul__ = MutableSequenceApi.__imul__
    __mul__  = MutableSequenceApi.__mul__
    __rmul__ = MutableSequenceApi.__rmul__
    __add__  = MutableSequenceApi.__add__
    __radd__ = MutableSequenceApi.__radd__
    copy     = MutableSequenceApi.copy

    def sort(self, /, *, key = None, reverse = False):
        values = sorted(self, key = key, reverse = reverse)
        self.clear()
        self.extend(values)

    @classmethod
    def _from_iterable(cls, it: Iterable):
        if isinstance(it, deque):
            return cls(it, maxlen = it.maxlen)
        return cls(it)

EMPTY_SEQ = seqf()

SequenceApi.register(tuple)
MutableSequenceApi.register(list)
MutableSequenceApi.register(deque)

