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
from pytableaux import tools

from ..utils import BaseCase

class Test_minfloor(BaseCase):

    def test_simple(self):
        self.assertEqual(minfloor(2, [4,3,2,1]), 2)
        self.assertEqual(minfloor(0, [4,3,2,1]), 1)
        self.assertEqual(minfloor(0, [], 1), 1)
        with self.assertRaises(ValueError):
            minfloor(0, [])

class Test_maxceil(BaseCase):

    def test_simple(self):
        self.assertEqual(maxceil(3, [1,2,3,4]), 3)
        self.assertEqual(maxceil(5, [1,2,3,4]), 4)
        with self.assertRaises(ValueError):
            maxceil(0, [])

class Test_sbool(BaseCase):

    def test(self):
        self.assertIs(sbool('yes'), True)
        self.assertIs(sbool('1'), True)
        self.assertIs(sbool('true'), True)
        self.assertIs(sbool('no'), False)
        self.assertIs(sbool('0'), False)
        self.assertIs(sbool('false'), False)

class Test_undund(BaseCase):

    def test(self):
        self.assertEqual(undund('__foo__'), 'foo')
        self.assertEqual(undund('foo'), 'foo')
        self.assertEqual(undund('_foo'), '_foo')
        self.assertEqual(undund('__foo'), '__foo')

class Test_getitem(BaseCase):

    def test(self):
        with self.assertRaises(KeyError):
            getitem({}, 0)
        self.assertIs(..., getitem({}, 0, ...))
        self.assertEqual(0, getitem({'x':0}, 'x'))
        self.assertEqual(1, getitem([1], 0))

class Test_slicerange(BaseCase):

    def test_slicerange_len_5_slice_1_3(self):
        r = slicerange(5, slice(1, 3), 'ab')
        self.assertEqual(r, range(1, 3))

    def test_slicerange_strict_raises_if_values_longer(self):
        with self.assertRaises(ValueError):
            slicerange(5, slice(1, 3), 'abc')

class Test_prevmodule(BaseCase):

    def test(self):
        tools._prevmodule()