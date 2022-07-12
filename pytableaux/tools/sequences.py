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

from collections.abc import Sequence
from pytableaux.tools import abcs

__all__ = ('SeqCover',)

NOARG = object()

class SeqCoverAttr(frozenset, abcs.Ebc):
    REQUIRED = {'__len__', '__getitem__', '__contains__', '__iter__',
                'count', 'index',}
    OPTIONAL = {'__reversed__'}
    ALL = REQUIRED | OPTIONAL

class SeqCover(Sequence, abcs.Copyable, immutcopy = True):

    __slots__ = SeqCoverAttr.ALL

    def __new__(cls, seq: Sequence, /):
        self = object.__new__(cls)
        sa = object.__setattr__
        for name in SeqCoverAttr.REQUIRED:
            sa(self, name, getattr(seq, name))
        for name in SeqCoverAttr.OPTIONAL:
            value = getattr(seq, name, NOARG)
            if value is not NOARG:
                sa(self, name, value)
        return self

    def __repr__(self):
        return f'{type(self).__name__}({list(self)})'


