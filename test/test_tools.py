from pytableaux.tools import *
from pytableaux.tools import inflect

from .utils import BaseCase

class TestMinFloor(BaseCase):

    def test_simple(self):
        self.assertEqual(minfloor(2, [4,3,2,1]), 2)
        self.assertEqual(minfloor(0, [4,3,2,1]), 1)

class TestMaxCeil(BaseCase):

    def test_simple(self):
        self.assertEqual(maxceil(3, [1,2,3,4]), 3)
        self.assertEqual(maxceil(5, [1,2,3,4]), 4)

class TestInflect(BaseCase):
    def test_dashcase(self):
        self.assertEqual(inflect.dashcase('SentenceNode'), 'sentence-node')
        self.assertEqual(inflect.dashcase('margin_left'), 'margin-left')