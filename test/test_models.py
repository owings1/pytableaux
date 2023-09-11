
from pytableaux.models import AccessGraph

from .utils import BaseCase as Base


class TestAccessGraph(Base):

    def test_flat_unsorted(self):
        g = AccessGraph()
        g.addall([(1,0), (0, 1)])
        self.assertEqual(list(g.flat()), [(1, 0), (0, 1)])

    def test_flat_sorted(self):
        g = AccessGraph()
        g.addall([(1,0), (0, 1)])
        self.assertEqual(list(g.flat(sort=True)), [(0, 1), (1, 0)])