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
# pytableaux.tools.hybrids tests
from pytableaux.tools.hybrids import *

from ..utils import BaseCase as Base


class TestSequenceSet(Base):

    def test_abstract_coverage(self):
        s = qsetf()
        self.assertIs(False, SequenceSet.__contains__(s, 3))


class TestQsetf(Base):

    def test_add_list(self):
        s1 = qsetf([1,2,3])
        s2 = s1 + [2,3,4]
        self.assertEqual(s2, qsetf([1,2,3,4]))
        self.assertIs(type(s2), qsetf)

    def test_add_set(self):
        s1 = qsetf([1,2,3])
        s2 = s1 + {2,3,4}
        self.assertEqual(s2, qsetf([1,2,3,4]))
        self.assertIs(type(s2), qsetf)

    def test_add_int_not_impl(self):
        s = qsetf()
        self.assertIs(NotImplemented, s.__add__(1))

    def test_radd_list(self):
        s1 = qsetf([1,2,3])
        s2 = [2,3,4] + s1
        self.assertEqual(s2, [2,3,4,1,2,3])
        self.assertIs(type(s2), list)

    def test_radd_set(self):
        s1 = qsetf([1,2,3])
        s2 = {2,3,4} + s1
        self.assertEqual(s2, {1,2,3,4})
        self.assertIs(type(s2), set)

    def test_radd_int_not_impl(self):
        s = qsetf()
        self.assertIs(NotImplemented, s.__radd__(1))

    def test_count(self):
        s = qsetf([1,1,1,2,2,2])
        self.assertEqual(s.count(1), 1)
        self.assertEqual(s.count(2), 1)
        self.assertEqual(s.count(3), 0)

    def test_index(self):
        s = qsetf([4,3,6])
        self.assertEqual(s.index(4), 0)
        self.assertEqual(s.index(3), 1)
        self.assertEqual(s.index(6), 2)

    def test_index_raises_value_error(self):
        s = qsetf()
        with self.assertRaises(ValueError):
            s.index(0)

    def test_reversed(self):
        s = qsetf([1,2,3])
        self.assertEqual(list(reversed(s)), [3,2,1])

    def test_repr_coverage(self):
        s = qsetf(range(3))
        r = repr(s)
        self.assertIs(type(r), str)

class TestQsetView(Base):

    def test_add_qsetf(self):
        s1 = qsetf([1,2,3])
        v1 = QsetView(s1)
        v2 = v1 + qsetf([4,5])
        self.assertEqual(v2, {1,2,3,4,5})
        self.assertIs(type(v2), QsetView)

    def test_or_qsetf(self):
        s1 = qsetf([1,2,3])
        v1 = QsetView(s1)
        v2 = v1 | qsetf([4,5])
        self.assertEqual(v2, {1,2,3,4,5})
        self.assertIs(type(v2), QsetView)

    def test_add_QsetView(self):
        s1 = qsetf([1,2,3])
        v1 = QsetView(s1)
        s2 = qsetf([4,5])
        v2 = QsetView(s2)
        v3 = v1 + v2
        self.assertEqual(v3, {1,2,3,4,5})
        self.assertIs(type(v3), QsetView)

    def test_or_QsetView(self):
        s1 = qsetf([1,2,3])
        v1 = QsetView(s1)
        s2 = qsetf([4,5])
        v2 = QsetView(s2)
        v3 = v1 | v2
        self.assertEqual(v3, {1,2,3,4,5})
        self.assertIs(type(v3), QsetView)

    def test_add_list(self):
        s1 = qsetf([1,2,3])
        v1 = QsetView(s1)
        v2 = v1 + [3,4]
        self.assertEqual(v2, {1,2,3,4})
        self.assertEqual(len(v2), 4)
        self.assertIs(type(v2), QsetView)

    def test_add_set(self):
        s1 = qsetf([1,2,3])
        v1 = QsetView(s1)
        v2 = v1 + {3,4}
        self.assertEqual(v2, {1,2,3,4})
        self.assertEqual(len(v2), 4)
        self.assertIs(type(v2), QsetView)

    def test_or_set(self):
        s1 = qsetf([1,2,3])
        v1 = QsetView(s1)
        v2 = v1 | {3,4}
        self.assertEqual(v2, {1,2,3,4})
        self.assertEqual(len(v2), 4)
        self.assertIs(type(v2), QsetView)

class TestMutableSequenceSet(Base):

    def test_cannot_construct_abstract(self):
        with self.assertRaises(TypeError):
            MutableSequenceSet()

    def test_reverse_not_impl_coverage(self):
        s = qsetf()
        with self.assertRaises(NotImplementedError):
            MutableSequenceSet.reverse(s)

class TestQset(Base):

    def test_reverse(self):
        s = qset([1,2,3,4,5])
        self.assertEqual(list(s), [1,2,3,4,5])
        s.reverse()
        self.assertEqual(list(s), [5,4,3,2,1])

    def test_delitem_slice(self):
        x = [1,2,3,4,5]
        s = qset(x)
        del x[2:4]
        del s[2:4]
        self.assertEqual(list(s), x)

    def test_setitem_slice_strict_size(self):
        m = [1,2,3,4,5]
        x = list(m)
        s = qset(m)
        x[2:4] = 'ab'
        s[2:4] = 'ab'
        self.assertEqual(list(s), list(x))

    def test_setitem_index_duplicate_value(self):
        s = qset([1,2])
        with self.assertRaises(ValueError):
            s[0] = 2

    def test_setitem_slice_duplicate_value(self):
        s = qset([1,2,3,4,5])
        with self.assertRaises(ValueError):
            s[2:4] = [2,4]

    def test_setitem_slice_duplicate_value_but_leaving(self):
        s = qset([1,2,3,4,5])
        s[2:4] = [4,3]
        self.assertEqual(list(s), [1,2,4,3,5])

    def test_equalities(self):

        def g(*items) -> qset:
            return qset(items)

        self.assertEqual({1, 2, 3}, g(2, 1, 2, 3))
        self.assertEqual(qset(range(5)) | qset(range(6)), set(range(6)))

        s = s1 = g(1, 2, 3)
        s -= {3}
        self.assertEqual(s, {1,2})
        self.assertIs(s, s1)
        self.assertEqual(g(1) ^ g(2), {1, 2})
        self.assertEqual(sorted({2, 3, 1, 1, 2}), [1, 2, 3])

    def test_errors(self):
        s = qset([1])
        with self.assertRaises(ValueError):
            s.append(1)
        with self.assertRaises(TypeError):
            del s['']
        with self.assertRaises(TypeError):
            s[''] = ''
