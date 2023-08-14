from .. import BaseCase
from pytableaux.lang import *
from pytableaux.proof import *

class Base(BaseCase):
    logic = 'P3'

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
        o = Operator.Negation
        self.assertEqual(self.logic.name, 'P3')
        rtd = self.rule_eg('DoubleNegationDesignated')
        rtu = self.rule_eg('DoubleNegationUndesignated')

        rule, tab = rtd
        self.assertTrue(tab[0].all((
            {'sentence': self.p('a'),  'designated': False},
            {'sentence': self.p('Na'), 'designated': False},
        )))

    def test_Conjunction(self):
        o = Operator.Conjunction
        self.rule_eg(f'{o.name}Designated')
        self.rule_eg(f'{o.name}Undesignated')
        self.rule_eg(f'{o.name}NegatedDesignated')
        self.rule_eg(f'{o.name}NegatedUndesignated')

    def test_MaterialConditional(self):
        o = Operator.MaterialConditional
        self.rule_eg(f'{o.name}Designated')
        self.rule_eg(f'{o.name}Undesignated')
        self.rule_eg(f'{o.name}NegatedDesignated')
        self.rule_eg(f'{o.name}NegatedUndesignated')

class TestQuantifierRules(Base):

    def test_Universal(self):
        q = Quantifier.Universal
        self.rule_eg(f'{q.name}Designated')
        self.rule_eg(f'{q.name}Undesignated')
        self.rule_eg(f'{q.name}NegatedDesignated')
        self.rule_eg(f'{q.name}NegatedUndesignated')
    def test_Existential(self):
        q = Quantifier.Existential
        self.rule_eg(f'{q.name}Designated')
        self.rule_eg(f'{q.name}Undesignated')
        self.rule_eg(f'{q.name}NegatedDesignated')
        self.rule_eg(f'{q.name}NegatedUndesignated')
