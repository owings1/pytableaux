from .tutils import BaseSuite, get_subclasses, skip
from itertools import filterfalse
import operator as opr
from pytest import raises

from pytableaux.errors import *
from pytableaux.lang.lex import *

from pytableaux.tools.abcs import *
from pytableaux.tools.events import EventsListeners, Listeners
from pytableaux.tools.hybrids import *
from pytableaux.tools.linked import *
from pytableaux.tools.mappings import *
from pytableaux.tools.sequences import *
from pytableaux.tools.sets import *
from pytableaux.tools.typing import T


from collections import deque



def subclasses(supcls: type[T]) -> qset[type[T]]:
    classes = qset()
    todo = [supcls]
    while len(todo):
        for child in filterfalse(classes.__contains__, todo.pop().__subclasses__()):
            todo.append(child)
            if not abcm.isabstract(child):
                classes.append(child)
    return classes

class Test_abcm(BaseSuite):
    def test_merged_mroattr(self):
        class A:
            x = 'A',
        class B1(A):
            x = 'B1',
        class B2(A):
            x = 'B2',
        class C(B2, B1):
            pass
        res = abcm.merged_mroattr(C, 'x', default = qset(), oper=opr.or_, supcls=A)
        assert tuple(res) == ('A', 'B1', 'B2')

class Test_seqf(BaseSuite):
    def test_add_radd(self):
        lh = seqf('abc')
        rh = 'd',
        r = lh + rh
        assert list(r) == list('abcd')
        assert type(r) is seqf
        r = rh + lh
        assert list(r) == list('dabc')
        assert type(r) is tuple
        rh = ['d']
        r = lh + rh
        assert list(r) == list('abcd')
        assert type(r) is seqf
        r = rh + lh
        assert list(r) == list('dabc')
        assert type(r) is list
        rh = deque('d')
        r = lh + rh
        assert list(r) == list('abcd')
        assert type(r) is seqf
        r = rh + lh
        assert list(r) == list('dabc')
        assert type(r) is deque

class TestSetList(BaseSuite):

    def test_equalities(self):

        _ = qset
        def g(*items) -> qset: return _(items)
        
        assert {1, 2, 3} == g(2, 1, 2, 3)
        assert _(range(5)) | _(range(6)) == set(range(6))

        s = s1 = g(1, 2, 3)
        s -= {3}
        assert s == {1, 2}
        assert s is s1

        assert g(1) ^ g(2) == {1, 2}

        assert sorted({2, 3, 1, 1, 2}) == [1, 2, 3]

    def test_errors(self):

        _ = qset
        def g(*items): return _(items)

        with raises(ValueError):
            g(1).append(1)

class TestListeners(BaseSuite):

    def test_once_listener(self):
        e = EventsListeners()
        e.create('test')
        def cb(): pass
        e.once('test', cb)
        assert len(e['test']) == 1
        assert cb in e['test']
        e.emit('test')
        assert len(e['test']) == 0

    def test_off(self):
        def cb(): pass
        e = EventsListeners()
        e.create('test')
        e.on('test', cb)
        assert cb in e['test']
        e.off('test', cb)
        assert len(e['test']) == 0

class TestLinkSet(BaseSuite):

    def test_iter(self):
        x = linqset(range(10))
        assert list(reversed(x)) == list(reversed(range(10)))
        assert list(x.iter_from_value(6)) == [6,7,8,9]
        assert list(x.iter_from_value(6, reverse=True)) == [6,5,4,3,2,1,0]
        with raises(ValueError):
            next(x.iter_from_value(11))

    def test_getitem(self):
        x = linqset(range(0,8,2))
        assert x[0] == 0
        assert x[1] == 2
        assert x[2] == 4
        assert x[3] == 6
        assert x[-1] == 6
        assert x[-2] == 4
        assert x[-3] == 2
        assert x[-4] == 0
        with raises(IndexError): x[-5]
        with raises(IndexError): x[4]
        x.clear()
        with raises(IndexError): x[0]
        with raises(IndexError): x[-1]

    def test_getitem_slice(self):
        x = linqset(range(10))
        y = list(range(10))
        assert list(x[:]) == y[:]
        assert list(x[-1:]) == y[-1:]
        assert list(x[-1:4]) == y[-1:4]
        assert list(x[-1:4:-1]) == y[-1:4:-1]
        assert list(x[::2]) == y[::2]
        assert list(x[::4]) == y[::4]
        assert list(x[::9]) == y[::9]
        assert list(x[3::2]) == y[3::2]

    def test_delitem(self):
        fnew = lambda: linqset(range(0,8,2))
        x = fnew()
        del x[0]
        assert list(x) == [2,4,6]
        x = fnew()
        del x[-1]
        assert list(x) == [0,2,4]
        x = fnew()
        del x[2]
        assert list(x) == [0,2,6]
        x = fnew()
        del x[-3]
        assert list(x) == [0,4,6]
        x = fnew()
        with raises(IndexError): del x[4]
        with raises(IndexError): del x[-5]

    def test_setitem(self):
        fnew = lambda: linqset([5,6])
        x = fnew()
        x[0] = 7
        assert list(x) == [7,6]
        x = fnew()
        x[-1] = 7
        assert list(x) == [5,7]
        with raises(IndexError): x[2] = 10
        with raises(IndexError): x[-3] = 10
        with raises(ValueError): x[1] = 5

    def test_reverse(self):
        x = linqset()
        x.reverse()
        assert list(x) == []
        assert len(x) == 0
        with raises(IndexError): x[0]
        with raises(IndexError): x[-1]

        x = linqset('a')
        x.reverse()
        assert list(x) == list('a')
        assert len(x) == 1
        assert x[0] == 'a'
        assert x[-1] == 'a'

        x = linqset('ab')
        x.reverse()
        assert list(x) == list('ba')
        assert len(x) == 2
        assert x[0] == 'b'
        assert x[-1] == 'a'
        assert x[1] == 'a'

        x = linqset('abc')
        x.reverse()
        assert list(x) == list('cba')
        x.reverse()
        assert list(x) == list('abc')

    def test_wedge(self):
        x = linqset('abcdeg')
        x.wedge('f', 'g', -1)
        # x.wedge(-1, 'g', 'f')
        assert list(x) == list('abcdefg')

        x = linqset('abcdeg')
        x.wedge('f', 'e', 1)
        # x.wedge(1, 'e', 'f')
        assert list(x) == list('abcdefg')

    def test_sort(self):
        x = linqset('fedcba')
        x.sort()
        assert list(x) == list('abcdef')

class TestMappingApi(BaseSuite):

    def test_subclasses(self):
        # Ensure modules are loaded
        from pytableaux.lang.parsing import ParseTable
        from pytableaux.proof.common import Target
        from pytableaux.proof.helpers import BranchCache
        from pytableaux.proof.tableaux import TreeStruct
        from pytableaux.web.util import AppMetrics

        rule = self.rule_tab('Conjunction').rule

        def clean(*dd):
            dd = tuple(map(dict, dd))
            for d in dd:
                # TreeStruct
                d.pop('id', None)
            return dd

        classes = get_subclasses(MappingApi) | (
            # Make sure these are tested, for good measure.
            BranchCache,
            ParseTable,
            EventsListeners,
            Target,
            TreeStruct,
            AppMetrics,
        )

        for cls in classes:

            if cls is AppMetrics:
                # AppMetrics copies the metrics, which makes equality fail.
                exp = dict(AppMetrics._from_mapping({}))
            elif cls is EventsListeners:
                # EventsListeners expects Listeners value type.
                exp = dict(test = Listeners())
            elif issubclass(cls, BranchCache):
                # BranchCache classes want BranchCache instances.
                exp = BranchCache(rule)
            elif cls is TreeStruct:
                # TreeStruct has defaults.
                exp = dict(TreeStruct())
            elif cls is dmapattr:
                exp = dict()
            else:
                # ParseTable needs [str, item] structure.
                # Target requires branch key.
                exp = dict(branch = (..., ...),)

            inst = cls._from_iterable(exp.items())
            if inst is not NotImplemented:
                a, b = clean(inst, exp)
                assert a == b

            inst = cls._from_mapping(exp)
            assert inst is not NotImplemented
            a, b = clean(inst, exp)
            assert a == b

            inst = inst.copy()
            a, b = clean(inst, exp)
            assert a == b

