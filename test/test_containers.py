from .tutils import BaseSuite
from pytest import raises
from errors import *
from lexicals import *

from containers import *

class TestSetList(BaseSuite):

    def test_equalities(self):

        _ = ListSet
        def g(*items) -> ListSet: return _(items)
        
        assert {1, 2, 3} == g(2, 1, 2, 3)
        assert _(range(5)) | _(range(6)) == set(range(6))

        s = s1 = g(1, 2, 3)
        s -= {3}
        assert s == {1, 2}
        assert s is s1

        assert g(1) ^ g(2) == {1, 2}

        assert sorted({2, 3, 1, 1, 2}) == [1, 2, 3]
    def test_errors(self):

        _ = ListSet
        def g(*items): return _(items)

        with raises(ValueError):
            g(1).append(1)