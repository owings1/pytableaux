from pytableaux.tools import *

from .tutils import BaseSuite, skip

class TestFuncs(BaseSuite):
    class TestMinFloor(BaseSuite):
        def test_simple(self):
            assert minfloor(2, [4,3,2,1]) == 2
            assert minfloor(0, [4,3,2,1]) == 1
    class TestMaxCeil(BaseSuite):
        def test_simple(self):
            assert maxceil(3, [1,2,3,4]) == 3
            assert maxceil(5, [1,2,3,4]) == 4
            