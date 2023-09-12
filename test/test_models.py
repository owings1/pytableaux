
from pytableaux.models import BaseModel
from pytableaux.lang import *
from .utils import BaseCase

class Base(BaseCase):
    logic = 'CPL'


class TestModels(Base):

    def test_set_predicated_value1(self):
        s = Predicate.Identity(Constant.gen(2))
        with self.m() as m:
            m.set_value(s, 'T', world=0)
        res = m.value_of(s, world=0)
        self.assertEqual(res, 'T')

    def test_set_predicated_raises_free_variables(self):
        pred = Predicate(0, 0, 1)
        s1, s2 = pred(Constant.first()), pred(Variable.first())
        m = self.m()
        m.set_value(s1, 'F')
        with self.assertRaises(ValueError):
            m.set_predicated_value(s2, 'F')

    def test_model_value_of_atomic_unassigned(self):
        s = Atomic(0, 0)
        m = self.m().finish()
        self.assertEqual(m.value_of(s), m.Meta.unassigned_value)

class TestAccess(Base):

    def test_flat_unsorted(self):
        g = BaseModel.Access()
        g.addall([(1,0), (0, 1)])
        self.assertEqual(list(g.flat()), [(1, 0), (0, 1)])

    def test_flat_sorted(self):
        g = BaseModel.Access()
        g.addall([(1,0), (0, 1)])
        self.assertEqual(list(g.flat(sort=True)), [(0, 1), (1, 0)])