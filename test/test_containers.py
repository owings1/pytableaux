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
from pytest import raises

from .tutils import BaseCase

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

class Test_abcm(BaseCase):
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

class TestSetList(BaseCase):

    def test_equalities(self):

        _ = qset
        def g(*items) -> qset: return _(items)

        self.assertEqual({1, 2, 3}, g(2, 1, 2, 3))
        self.assertEqual(_(range(5)) | _(range(6)), set(range(6)))

        s = s1 = g(1, 2, 3)
        s -= {3}
        self.assertEqual(s, {1,2})
        self.assertIs(s, s1)
        self.assertEqual(g(1) ^ g(2), {1, 2})
        self.assertEqual(sorted({2, 3, 1, 1, 2}), [1, 2, 3])

    def test_errors(self):

        _ = qset
        def g(*items): return _(items)

        with self.assertRaises(ValueError):
            g(1).append(1)

class TestListeners(BaseCase):

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

class TestLinkSet(BaseCase):

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
        def fnew(): return linqset(range(0,8,2))
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
        with raises(IndexError): del x[4]
        with raises(IndexError): del x[-5]

    def test_setitem(self):
        fnew = lambda: linqset([5,6])
        x = fnew()
        x[0] = 7
        self.assertEqual(list(x), [7,6])
        x = fnew()
        x[-1] = 7
        self.assertEqual(list(x), [5,7])
        with raises(IndexError): x[2] = 10
        with raises(IndexError): x[-3] = 10
        with raises(ValueError): x[1] = 5

    def test_reverse(self):
        x = linqset()
        x.reverse()
        self.assertEqual(list(x), [])
        self.assertEqual(len(x), 0)
        with raises(IndexError): x[0]
        with raises(IndexError): x[-1]

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

