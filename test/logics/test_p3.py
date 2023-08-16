from ..utils import BaseCase
from pytableaux.lang import *
from pytableaux.proof import *

class Base(BaseCase):
    logic = 'P3'

class TestRules(Base, autorules=True): pass

class TestArguments(Base):

    def test_invalid_lem(self):
        self.invalid_tab('LEM')

    def test_invalid_demorgan_1(self):
        self.invalid_tab('DeMorgan 1')

    def test_invalid_demorgan_2(self):
        self.invalid_tab('DeMorgan 2')

    def test_invalid_demorgan_3(self):
        self.invalid_tab('DeMorgan 3')

    def test_invalid_demorgan_4(self):
        self.invalid_tab('DeMorgan 4')

    def test_invalid_demorgan_5(self):
        self.invalid_tab('DeMorgan 5')

    def test_valid_demorgan_6(self):
        self.valid_tab('DeMorgan 6')

class TestOperatorRules(Base):

    def test_Negation(self):
        self.assertEqual(self.logic.Meta.name, 'P3')
        rtd = self.rule_eg('DoubleNegationDesignated')

        rule, tab = rtd
        self.assertTrue(tab[0].all((
            {'sentence': self.p('a'),  'designated': False},
            {'sentence': self.p('Na'), 'designated': False},
        )))

