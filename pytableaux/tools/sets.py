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

from pytableaux.errors import check
from pytableaux.tools import abcs, operd

__all__ = (
    'EMPTY_SET',
    'MutableSetApi',
    'SetApi',
    'SetView',
)

EMPTY_SET = frozenset()

class SetApi(Set, abcs.Copyable):
    'Fusion interface of collections.abc.Set and built-in frozenset.'

    __slots__ = EMPTY_SET

    __or__  = Set.__or__
    __and__ = Set.__and__
    __sub__ = Set.__sub__
    __xor__ = Set.__xor__

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
    def _from_iterable(cls, it):
        return cls(it)

class MutableSetApi(MutableSet, SetApi):
    'Fusion interface of collections.abc.MutableSet and built-in set.'
    __slots__ = EMPTY_SET
    rep = operd.repeat
    update = rep(opr.ior, set.update)
    intersection_update = rep(opr.iand, set.intersection_update)
    difference_update   = rep(opr.isub, set.difference_update)
    symmetric_difference_update = operd.apply(opr.ixor,
        set.symmetric_difference_update)
    del(rep)

class SetView(SetApi):
    'SetApi cover.'

    __slots__ = frozenset(SetApi.__abstractmethods__)

    def __new__(cls, set_, /,):
        check.inst(set_, Set)
        self = object.__new__(cls)
        self.__len__      = set_.__len__
        self.__iter__     = set_.__iter__
        self.__contains__ = set_.__contains__
        return self

    def __repr__(self):
        prefix = type(self).__name__
        if len(self):
            return f'{prefix}{set(self)}'
        return f'{prefix}''{}'

    @classmethod
    def _from_iterable(cls, it):
        return cls(frozenset(it))

del(
    abcs,
    functools,
    operd,
    opr,
)