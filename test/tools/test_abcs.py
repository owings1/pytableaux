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
import enum
from copy import copy, deepcopy
from pytableaux.tools import abcs, qset
from collections.abc import Mapping
from ..utils import BaseCase as Base


class Test_merge_attr(Base):

    def test_non_class_raises_type_error_coverage(self):
        with self.assertRaises(TypeError):
            abcs.merge_attr(object(), 'foo')

class Test_check_mrodict(Base):

    def test_empty_mro_coverage(self):
        self.assertIs(NotImplemented, abcs.check_mrodict([], 'foo'))

class Test_isabstract(Base):

    def test_class(self):
        self.assertTrue(abcs.isabstract(Mapping))
        self.assertFalse(abcs.isabstract(qset))

    def test_method(self):
        self.assertTrue(abcs.isabstract(Mapping.__len__))
        self.assertFalse(abcs.isabstract(Mapping.get))

class Test_merged_attr(Base):

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


class TestEnumLookup(Base):

    class X(abcs.Ebc):
        a = 1
        b = 2
        c = 3

    def test_iter(self):
        X = self.X
        v = list(iter(X._lookup))
        self.assertIn(X.a, v)
        self.assertIn('a', v)
        self.assertIn(1, v)

    def test_reversed(self):
        X = self.X
        v = list(reversed(X._lookup))
        self.assertIn(X.a, v)
        self.assertIn('a', v)
        self.assertIn(1, v)

    def test_asdict(self):
        X = self.X
        v = X._lookup._asdict()
        self.assertIn(X.a, v)
        self.assertIn('a', v)
        self.assertIn(1, v)

    def test_len(self):
        self.assertGreater(len(self.X._lookup), 3)

    def test_setattr(self):
        with self.assertRaises(AttributeError):
            self.X._lookup._mapping = {}

    def test_delattr(self):
        with self.assertRaises(AttributeError):
            del(self.X._lookup._mapping)

    def test_repr_coverage(self):
        r = repr(self.X._lookup)
        self.assertIs(type(r), str)

    def test_psuedo_keys(self):
        class X(enum.Flag, abcs.Ebc):
            a = 1
            b = 2
            p = 4
            q = 8
        c = X.a | X.b
        self.assertEqual(self.X._lookup._pseudo_keys(c), {c, 3})

    def test_init_raises_type_error(self):
        with self.assertRaises(TypeError):
            self.X._lookup.__init__(self.X)

class TestEbc(Base):

    class X(abcs.Ebc):
        a = 1
        b = 2
        c = 3

    def test_enum_reserved_names_raises_type_error(self):

        with self.assertRaises(TypeError):
            class _(abcs.Ebc):
                a = 1
                _lookup = 2

    def test_get_method(self):
        X = self.X
        self.assertIs(X.get('a'), X.a)
        self.assertIs(X.get(1), X.a)
        self.assertIs(X.get('b'), X.b)
        self.assertIs(X.get(2), X.b)
        self.assertIs(X.get('b'), X.b)
        self.assertIs(X.get(3), X.c)
        self.assertIs(X.get('d', None), None)
        with self.assertRaises(KeyError):
            X.get('d')
    
    def test_getitem_slice(self):
        X = self.X
        self.assertEqual(X[0:], (X.a, X.b, X.c))
        self.assertEqual(X[0:2], (X.a, X.b))

    def test_call_slice(self):
        X = self.X
        self.assertEqual(X(slice(0, None)), (X.a, X.b, X.c))
        self.assertEqual(X(slice(0, 2)), (X.a, X.b))

    def test_call_list_raises_type_error(self):
        X = self.X
        with self.assertRaises(TypeError):
            X([])

    def test_getitem_list_raises_type_error(self):
        X = self.X
        with self.assertRaises(TypeError):
            X[[]]

    def test_reversed(self):
        X = self.X
        self.assertEqual(list(reversed(X)), [X.c, X.b, X.a])

    def test_dir(self):
        self.assertEqual(dir(self.X), ['a', 'b', 'c'])

    def test_copy_returns_self(self):
        X = self.X
        self.assertIs(copy(X.a), X.a)
        self.assertIs(deepcopy(X.a), X.a)

    def test_repr_coverage(self):
        r = repr(self.X.a)
        self.assertIs(type(r), str)
        class Y(str, abcs.Ebc):
            a = 'a'
        self.assertIn(repr('a'), repr(Y.a))
    
    def test_functional_construct(self):
        e = abcs.Ebc('Spam', ['a', 'b', 'c'])
        self.assertTrue(issubclass(e, abcs.Ebc))
        self.assertEqual(e.a.name, 'a')

class TestCopyable(Base):

    def test_is_copyable_with_copy_methods(self):
        class X:
            def copy(self): return self
            __copy__ = copy
        self.assertIsInstance(X(), abcs.Copyable)

    def test_is_not_copyable_with_method_none(self):
        class X:
            def copy(self): return self
            __copy__ = None
        self.assertNotIsInstance(X(), abcs.Copyable)

    def test_object_is_not_copyable(self):
        self.assertNotIsInstance(object(), abcs.Copyable)

    def test_copy_abstract_coverage(self):
        o = {}
        self.assertEqual(abcs.Copyable.copy(o), o)