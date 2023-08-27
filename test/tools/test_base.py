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
# pytableaux.tools tests
from pytableaux.tools import *

from ..utils import BaseCase

class TestMinFloor(BaseCase):

    def test_simple(self):
        self.assertEqual(minfloor(2, [4,3,2,1]), 2)
        self.assertEqual(minfloor(0, [4,3,2,1]), 1)

class TestMaxCeil(BaseCase):

    def test_simple(self):
        self.assertEqual(maxceil(3, [1,2,3,4]), 3)
        self.assertEqual(maxceil(5, [1,2,3,4]), 4)
