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
#
# ------------------
#
# pytableaux.tools.abcs tests
import operator as opr
from itertools import filterfalse
from typing import TypeVar

from pytableaux.tools import abcs, qset

from ..utils import BaseCase as Base

_T = TypeVar('_T')

def subclasses(supcls: type[_T]) -> qset[type[_T]]:
    classes = qset()
    todo = [supcls]
    while len(todo):
        for child in filterfalse(classes.__contains__, todo.pop().__subclasses__()):
            todo.append(child)
            if not abcs.isabstract(child):
                classes.append(child)
    return classes

class Test_abcm(Base):

    def test_merged_mroattr(self):
        class A:
            x = 'A',
        class B1(A):
            x = 'B1',
        class B2(A):
            x = 'B2',
        class C(B2, B1):
            pass
        res = abcs.merged_attr('x', cls = C, default = qset(), oper=opr.or_, supcls=A)
        self.assertEqual(tuple(res), ('A', 'B1', 'B2'))