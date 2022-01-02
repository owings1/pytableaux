from .tutils import BaseSuite
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