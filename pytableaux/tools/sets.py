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

from collections.abc import Set

from pytableaux.errors import check
from pytableaux.tools import abcs

__all__ = (
    'SetView',
)

EMPTY_SET = frozenset()


class SetView(Set, abcs.Copyable, immutcopy = True):
    'Set cover.'

    __slots__ = ('__contains__', '__iter__', '__len__')

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
