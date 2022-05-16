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
pytableaux.tools.sets
^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

import functools
import operator as opr
from collections.abc import MutableSet, Set
from typing import TYPE_CHECKING

from pytableaux.errors import check
from pytableaux.tools import abcs
from pytableaux.tools.decorators import operd
from pytableaux.tools.typing import VT

if TYPE_CHECKING:
    from typing import Iterable, overload

    from pytableaux.tools.typing import SetApiT

__all__ = (
    'EMPTY_SET',
    'MutableSetApi',
    'SetApi',
    'setf',
    'setm',
    'SetView',
)

EMPTY_SET: setf = frozenset()

class SetApi(Set[VT], abcs.Copyable):
    'Fusion interface of collections.abc.Set and built-in frozenset.'

    __slots__ = EMPTY_SET

    # if TYPE_CHECKING:
    #     @overload
    #     def __or__(self:SetApiT, other) -> SetApiT: ...
    #     @overload
    #     def __and__(self:SetApiT, other) -> SetApiT: ...
    #     @overload
    #     def __sub__(self:SetApiT, other) -> SetApiT: ...
    #     @overload
    #     def __xor__(self:SetApiT, other) -> SetApiT: ...
    #     @overload
    #     def issubset(self, other: Iterable) -> bool: ...
    #     @overload
    #     def issuperset(self, other: Iterable) -> bool: ...
    #     @overload
    #     def union(self:SetApiT, *others: Iterable) -> SetApiT: ...
    #     @overload
    #     def intersection(self:SetApiT, *others: Iterable) -> SetApiT: ...
    #     @overload
    #     def difference(self:SetApiT, *others: Iterable) -> SetApiT: ...
    #     @overload
    #     def symmetric_difference(self:SetApiT, other: Iterable) -> SetApiT: ...

    __or__  = Set[VT].__or__
    __and__ = Set[VT].__and__
    __sub__ = Set[VT].__sub__
    __xor__ = Set[VT].__xor__

    red = functools.partial(operd.reduce, freturn = '_from_iterable')
    app = operd.apply

    issubset     = app(opr.le,   set.issubset)
    issuperset   = app(opr.ge,   set.issuperset)
    union        = red(opr.or_,  set.union)
    intersection = red(opr.and_, set.intersection)
    difference   = red(opr.sub,  set.difference)
    symmetric_difference = app(opr.xor, set.symmetric_difference)

    del(red, app)

    def copy(self):
        return self._from_iterable(self)

    @classmethod
    def _from_iterable(cls: type[SetApiT], it: Iterable) -> SetApiT:
        return cls(it)

class MutableSetApi(MutableSet[VT], SetApi[VT]):
    'Fusion interface of collections.abc.MutableSet and built-in set.'

    __slots__ = EMPTY_SET

    # if TYPE_CHECKING:
    #     @overload
    #     def update(self, *others: Iterable): ...
    #     @overload
    #     def intersection_update(self, *others: Iterable): ...
    #     @overload
    #     def difference_update(self, *others: Iterable): ...
    #     @overload
    #     def symmetric_difference_update(self, other: Iterable): ...

    rep = operd.repeat

    update = rep(opr.ior, set.update)

    intersection_update = rep(opr.iand, set.intersection_update)
    difference_update   = rep(opr.isub, set.difference_update)

    symmetric_difference_update = operd.apply(
        opr.ixor,
        set.symmetric_difference_update
    )

    del(rep)

class setf(SetApi[VT], frozenset[VT]):
    'SetApi wrapper around built-in frozenset.'
    __slots__ = EMPTY_SET

    __len__      = frozenset.__len__
    __iter__     = frozenset[VT].__iter__
    __contains__ = frozenset.__contains__

EMPTY_SET = setf()

class setm(MutableSetApi[VT], set[VT]):
    'MutableSetApi wrapper around built-in set.'
    __slots__ = EMPTY_SET

    __len__      = set.__len__
    __iter__     = set[VT].__iter__
    __contains__ = set.__contains__

    if TYPE_CHECKING:
        @overload
        def clear(self): ...
        @overload
        def add(self, value: VT): ...
        @overload
        def discard(self, value: VT): ...

    clear   = set.clear
    add     = set.add
    discard = set.discard

class SetView(SetApi[VT]):
    'SetApi cover.'

    __slots__ = setf(SetApi.__abstractmethods__)

    def __new__(cls, set_: Set[VT], /,):
        check.inst(set_, Set)

        inst = object.__new__(cls)
        inst.__len__      = set_.__len__
        inst.__iter__     = set_.__iter__
        inst.__contains__ = set_.__contains__

        return inst

    def __repr__(self):
        prefix = type(self).__name__
        if len(self):
            return f'{prefix}{set(self)}'
        return f'{prefix}''{}'

    @classmethod
    def _from_iterable(cls: type[SetApiT], it: Iterable[VT]) -> SetApiT:
        return cls(setf(it))

del(
    abcs,
    functools,
    operd,
    opr,
)