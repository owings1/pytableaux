from .tutils import BaseSuite, skip
from pytest import raises
from errors import *
from events import EventsListeners, Listener, Listeners, EventEmitter
from lexicals import *

from containers import *

class TestSetList(BaseSuite):

    def test_equalities(self):

        _ = qsetm
        def g(*items) -> qsetm: return _(items)
        
        assert {1, 2, 3} == g(2, 1, 2, 3)
        assert _(range(5)) | _(range(6)) == set(range(6))

        s = s1 = g(1, 2, 3)
        s -= {3}
        assert s == {1, 2}
        assert s is s1

        assert g(1) ^ g(2) == {1, 2}

        assert sorted({2, 3, 1, 1, 2}) == [1, 2, 3]
    def test_errors(self):

        _ = qsetm
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
    @skip
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
        with raises(ValueError): next(x.iter_from_value(11))

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

    def test_put_before_after(self):
        x = linqset('abcdeg')
        x.put_before('g', 'f')
        assert list(x) == list('abcdefg')

        x = linqset('abcdeg')
        x.put_after('e', 'f')
        assert list(x) == list('abcdefg')

    def test_view(self):
        x = linqset('abcdef')
        v = x.view()
        assert len(v) == 6
        assert list(v) == list('abcdef')
        x.append('g')
        assert len(v) == 7
        assert v[-1] == 'g'
        assert list(reversed(v)) == list(reversed('abcdefg'))

    def test_sort(self):
        x = linqset('fedcba')
        x.sort()
        assert list(x) == list('abcdef')