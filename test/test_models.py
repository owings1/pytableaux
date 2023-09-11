
from pytableaux.errors import *
from pytableaux.lang import Operator
from pytableaux.logics import registry
from pytableaux.models import AccessGraph, BaseModel

from .utils import BaseCase as Base


class TestModel(Base):

    logic = 'CPL'


class TestAccessGraph(Base):

    def test_flat_unsorted(self):
        g = AccessGraph()
        g.addall([(1,0), (0, 1)])
        self.assertEqual(list(g.flat()), [(1, 0), (0, 1)])

    def test_flat_sorted(self):
        g = AccessGraph()
        g.addall([(1,0), (0, 1)])
        self.assertEqual(list(g.flat(sort=True)), [(0, 1), (1, 0)])