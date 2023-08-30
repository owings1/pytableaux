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
import operator as opr
from ..utils import BaseCase

class Test_dmerged(BaseCase):

    def test_overwrites_non_mapping_from_b(self):
        a = {1: None}
        b = {1: {2: 3}}
        c = dmerged(a, b)
        self.assertEqual(c, b)

class Test_getitem(BaseCase):

    def test(self):
        with self.assertRaises(KeyError):
            getitem({}, 0)
        self.assertIs(..., getitem({}, 0, ...))
        self.assertEqual(0, getitem({'x':0}, 'x'))
        self.assertEqual(1, getitem([1], 0))

class Test_limit_best(BaseCase):

    def test_as_minfloor(self):
        res = tools.limit_best(opr.lt, 2, [4,3,2,1])
        self.assertEqual(res, 2)

class Test_minfloor(BaseCase):

    def test_simple(self):
        self.assertEqual(minfloor(2, [4,3,2,1]), 2)
        self.assertEqual(minfloor(0, [4,3,2,1]), 1)
        self.assertEqual(minfloor(0, [], 1), 1)
        with self.assertRaises(ValueError):
            minfloor(0, [])

    def test_default_ignored_in_non_empty_collection(self):
        it = [1, 2, 3]
        floor = 2
        default = 0
        self.assertEqual(minfloor(floor, it, default), floor)

class Test_maxceil(BaseCase):

    def test_simple(self):
        self.assertEqual(maxceil(3, [1,2,3,4]), 3)
        self.assertEqual(maxceil(5, [1,2,3,4]), 4)
        with self.assertRaises(ValueError):
            maxceil(0, [])

    def test_default_ignored_in_non_empty_collection(self):
        it = [1]
        ceil = 2
        default = 3
        self.assertEqual(maxceil(ceil, it, default), 1)

class Test_sbool(BaseCase):

    def test(self):
        self.assertIs(sbool('yes'), True)
        self.assertIs(sbool('1'), True)
        self.assertIs(sbool('true'), True)
        self.assertIs(sbool('no'), False)
        self.assertIs(sbool('0'), False)
        self.assertIs(sbool('false'), False)

class Test_slicerange(BaseCase):

    def test_slicerange_len_5_slice_1_3(self):
        r = slicerange(5, slice(1, 3), 'ab')
        self.assertEqual(r, range(1, 3))

    def test_slicerange_strict_raises_if_values_longer(self):
        with self.assertRaises(ValueError):
            slicerange(5, slice(1, 3), 'abc')

class Test_undund(BaseCase):

    def test(self):
        self.assertEqual(undund('__foo__'), 'foo')
        self.assertEqual(undund('foo'), 'foo')
        self.assertEqual(undund('_foo'), '_foo')
        self.assertEqual(undund('__foo'), '__foo')

class Test_prevmodule(BaseCase):

    def test(self):
        tools._prevmodule()

class Test_membr(BaseCase):

    def test_name_membr_coverage(self):
        m = membr(lambda: None)
        self.assertEqual('membr', m.name)

    def test_repr_coverage(self):
        r = repr(membr(lambda: None))
        self.assertIs(type(r), str)
        m = membr(lambda: None)
        m.__qualname__ = 'x.m'
        r = repr(m)
        self.assertIs(type(r), str)

class TestMapCover(BaseCase):

    def test_reversed(self):
        m = MapCover({'a':1, 'b': 2})
        self.assertEqual(list(reversed(m)), list('ba'))

    def test_asdict(self):
        d = {'a':1, 'b': 2}
        m = MapCover(d)
        self.assertEqual(m._asdict(), d)

    def test_repr_coverage(self):
        r = repr(MapCover({}))
        self.assertIs(type(r), str)

class TestKeySetAttr(BaseCase):

    def test_default_coverage(self):
        self.assertTrue(KeySetAttr._keyattr_ok('abc'))
        self.assertFalse(KeySetAttr._keyattr_ok('__class__'))

class TestSeqCover(BaseCase):

    def test_raises_bad_sequence(self):
        with self.assertRaises(AttributeError):
            SeqCover(3)

    def test_repr_coverage(self):
        r = repr(SeqCover([]))
        self.assertIs(type(r), str)

class TestPathedDict(BaseCase):

    def test_delitem_path(self):
        d = PathedDict()
        d['a:b:c'] = 1
        del(d['a:b'])
        self.assertEqual(d, {'a': {}})

    def test_delitem_raises(self):
        d = PathedDict()
        d['a:b'] = 1
        with self.assertRaises(KeyError):
            del(d['b'])

class Test_dictns(BaseCase):

    def test_init(self):
        d = dictns(a=1)
        self.assertEqual(d['a'], 1)
        self.assertEqual(d.a, 1)

    def test_setitem(self):
        d = dictns()
        d['a'] = 1
        self.assertEqual(d['a'], 1)
        self.assertEqual(d.a, 1)

    def test_delitem(self):
        d = dictns(a=1)
        del d['a']
        with self.assertRaises(KeyError):
            d['a']
        with self.assertRaises(AttributeError):
            d.a

    def test_setattr(self):
        d = dictns()
        d.a = 1
        self.assertEqual(d['a'], 1)
        self.assertEqual(d.a, 1)

    def test_delattr(self):
        d = dictns(a=1)
        del d.a
        with self.assertRaises(KeyError):
            d['a']
        with self.assertRaises(AttributeError):
            d.a

    def test_update(self):
        d = dictns()
        d.update({'a':1}, b=2)
        self.assertEqual(d['a'], 1)
        self.assertEqual(d.a, 1)
        self.assertEqual(d['b'], 2)
        self.assertEqual(d.b, 2)

    def test_setdefault(self):
        d = dictns()
        d.setdefault('a', 1)
        self.assertEqual(d['a'], 1)
        self.assertEqual(d.a, 1)

    def test_get(self):
        d = dictns()
        d['a'] = 1
        d.b = 2
        self.assertEqual(d.get('a'), 1)
        self.assertEqual(d.get('b'), 2)

    def test_pop(self):
        d = dictns()
        d['a'] = 1
        d.b = 2
        self.assertEqual(d.pop('a'), 1)
        self.assertEqual(d.pop('b'), 2)
        with self.assertRaises(KeyError):
            d['a']
        with self.assertRaises(AttributeError):
            d.a
        with self.assertRaises(KeyError):
            d['b']
        with self.assertRaises(AttributeError):
            d.b

    def test_popitem(self):
        d = dictns()
        d['a'] = 1
        self.assertEqual(d.popitem(), ('a', 1))
        with self.assertRaises(KeyError):
            d['a']
        with self.assertRaises(AttributeError):
            d.a

class Test_wraps(BaseCase):

    def test_wraps_classmethod(self):
        def wrapped(): pass
        class X:
            @wraps(wrapped)
            @classmethod
            def wrapper(cls): pass
        self.assertEqual(X.wrapper.__name__, 'wrapped')

    def test_overwrite_raises_keyerror(self):
        w = wraps()
        w['__name__'] = 'foo'
        with self.assertRaises(KeyError):
            w['__name__'] = 'bar'

    def test_repr_coverage(self):
        r = repr(wraps())
        self.assertIs(type(r), str)
    
    def test_wraps_object(self):
        class A: pass
        wraps(A())

    def test_reads_name(self):
        class A:
            name = 'foo'
        w = wraps()
        w.update(A())
        self.assertEqual(w['__name__'], 'foo')