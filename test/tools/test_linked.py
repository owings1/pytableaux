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
# pytableaux.tools.linked tests
from pytableaux.tools.linked import *

from ..utils import BaseCase as Base

class TestLinkSet(Base):

    def test_iter(self):
        x = linqset(range(10))
        self.assertEqual(list(reversed(x)), list(reversed(range(10))))
        self.assertEqual(list(x.iter_from_value(6)), [6,7,8,9])
        self.assertEqual(list(x.iter_from_value(6, reverse=True)), [6,5,4,3,2,1,0])
        with self.assertRaises(ValueError):
            next(x.iter_from_value(11))

    def test_getitem(self):
        x = linqset(range(0,8,2))
        self.assertEqual(x[0], 0)
        self.assertEqual(x[1], 2)
        self.assertEqual(x[2], 4)
        self.assertEqual(x[3], 6)
        self.assertEqual(x[-1], 6)
        self.assertEqual(x[-2], 4)
        self.assertEqual(x[-3], 2)
        self.assertEqual(x[-4], 0)
        with self.assertRaises(IndexError): x[-5]
        with self.assertRaises(IndexError): x[4]
        x.clear()
        with self.assertRaises(IndexError): x[0]
        with self.assertRaises(IndexError): x[-1]

    def test_getitem_slice(self):
        x = linqset(range(10))
        y = list(range(10))
        self.assertEqual(list(x[:]), y[:])
        self.assertEqual(list(x[-1:]), y[-1:])
        self.assertEqual(list(x[-1:4]), y[-1:4])
        self.assertEqual(list(x[-1:4:-1]), y[-1:4:-1])
        self.assertEqual(list(x[::2]), y[::2])
        self.assertEqual(list(x[::4]), y[::4])
        self.assertEqual(list(x[::9]), y[::9])
        self.assertEqual(list(x[3::2]), y[3::2])

    def test_delitem(self):
        def fnew():
            return linqset(range(0,8,2))
        x = fnew()
        del x[0]
        self.assertEqual(list(x), [2,4,6])
        x = fnew()
        del x[-1]
        self.assertEqual(list(x), [0,2,4])
        x = fnew()
        del x[2]
        self.assertEqual(list(x), [0,2,6])
        x = fnew()
        del x[-3]
        self.assertEqual(list(x), [0,4,6])
        x = fnew()
        with self.assertRaises(IndexError): del x[4]
        with self.assertRaises(IndexError): del x[-5]

    def test_setitem(self):
        def fnew():
            return linqset([5,6])
        x = fnew()
        x[0] = 7
        self.assertEqual(list(x), [7,6])
        x = fnew()
        x[-1] = 7
        self.assertEqual(list(x), [5,7])
        with self.assertRaises(IndexError): x[2] = 10
        with self.assertRaises(IndexError): x[-3] = 10
        with self.assertRaises(ValueError): x[1] = 5

    def test_reverse(self):
        x = linqset()
        x.reverse()
        self.assertEqual(list(x), [])
        self.assertEqual(len(x), 0)
        with self.assertRaises(IndexError): x[0]
        with self.assertRaises(IndexError): x[-1]

        x = linqset('a')
        x.reverse()
        self.assertEqual(list(x), list('a'))
        self.assertEqual(len(x), 1)
        self.assertEqual(x[0], 'a')
        self.assertEqual(x[-1], 'a')

        x = linqset('ab')
        x.reverse()
        self.assertEqual(list(x), list('ba'))
        self.assertEqual(len(x), 2)
        self.assertEqual(x[0], 'b')
        self.assertEqual(x[-1], 'a')
        self.assertEqual(x[1], 'a')

        x = linqset('abc')
        x.reverse()
        self.assertEqual(list(x), list('cba'))
        x.reverse()
        self.assertEqual(list(x), list('abc'))

    def test_wedge(self):
        x = linqset('abcdeg')
        x.wedge('f', 'g', -1)
        self.assertEqual(list(x), list('abcdefg'))

        x = linqset('abcdeg')
        x.wedge('f', 'e', 1)
        self.assertEqual(list(x), list('abcdefg'))

