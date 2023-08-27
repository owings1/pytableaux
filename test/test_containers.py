import operator as opr
from itertools import filterfalse
from typing import TypeVar

from pytableaux.errors import *
from pytableaux.lang.lex import *
from pytableaux.tools import abcs
from pytableaux.tools.abcs import *
from pytableaux.tools.events import *
from pytableaux.tools.hybrids import *
from pytableaux.tools.linked import *

from unittest import TestCase as Base

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

    def test_add_QsetView(self):
        s1 = qsetf([1,2,3])
        v1 = QsetView(s1)
        s2 = qsetf([4,5])
        v2 = QsetView(s2)
        v3 = v1 + v2
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

class TestListeners(Base):

    def test_once_listener(self):
        e = EventsListeners()
        e.create('test')
        def cb(): pass
        e.once('test', cb)
        self.assertEqual(len(e['test']), 1)
        self.assertIn(cb, e['test'])
        e.emit('test')
        self.assertEqual(len(e['test']), 0)

    def test_off(self):
        def cb(): pass
        e = EventsListeners()
        e.create('test')
        e.on('test', cb)
        self.assertIn(cb, e['test'])
        e.off('test', cb)
        self.assertEqual(len(e['test']), 0)

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

