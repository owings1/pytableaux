from unittest import skip
from .. import BaseCase
from pytableaux.lang import *
from pytableaux.proof import *
from pytableaux.errors import *

A = Atomic.first()

class Base(BaseCase):
    logic = 'K3'

class TestArguments(Base):

    def test_DeMorgan(self):
        self.valid_tab('DeMorgan 1')
        self.valid_tab('DeMorgan 2')
        self.valid_tab('DeMorgan 3')
        self.valid_tab('DeMorgan 4')

class TestClosure(Base):

    def test_GlutClosure(self):
        self.rule_eg('GlutClosure')

class TestOperators(Base):

    def test_Negation(self):
        self.rule_eg('DoubleNegationDesignated')
        self.rule_eg('DoubleNegationUndesignated')

    def test_Assertion(self):
        o = Operator.Assertion
        self.rule_eg(f'{o.name}Designated')
        self.rule_eg(f'{o.name}Undesignated')
        self.rule_eg(f'{o.name}NegatedDesignated')
        self.rule_eg(f'{o.name}NegatedUndesignated')

    def test_Conjunction(self):
        o = Operator.Conjunction
        rtd = self.rule_eg(f'{o.name}Designated')
        rtu = self.rule_eg(f'{o.name}Undesignated')
        rtnd = self.rule_eg(f'{o.name}NegatedDesignated')
        rtnu = self.rule_eg(f'{o.name}NegatedUndesignated')
        self.valid_tab('LNC')

    def test_Disjunction(self):
        o = Operator.Disjunction
        self.rule_eg(f'{o.name}Designated')
        self.rule_eg(f'{o.name}Undesignated')
        self.rule_eg(f'{o.name}NegatedDesignated')
        self.rule_eg(f'{o.name}NegatedUndesignated')
        self.invalid_tab('LEM')

    def test_MaterialConditional(self):
        o = Operator.MaterialConditional
        self.rule_eg(f'{o.name}Designated')
        self.rule_eg(f'{o.name}Undesignated')
        self.rule_eg(f'{o.name}NegatedDesignated')
        self.rule_eg(f'{o.name}NegatedUndesignated')

    def test_MaterialBiconditional(self):
        o = Operator.MaterialBiconditional
        self.rule_eg(f'{o.name}Designated')
        self.rule_eg(f'{o.name}Undesignated')
        self.rule_eg(f'{o.name}NegatedDesignated')
        self.rule_eg(f'{o.name}NegatedUndesignated')

    def test_Conditional(self):
        o = Operator.Conditional
        self.rule_eg(f'{o.name}Designated')
        self.rule_eg(f'{o.name}Undesignated')
        self.rule_eg(f'{o.name}NegatedDesignated')
        self.rule_eg(f'{o.name}NegatedUndesignated')

    def test_Biconditional(self):
        o = Operator.Biconditional
        self.rule_eg(f'{o.name}Designated')
        self.rule_eg(f'{o.name}Undesignated')
        self.rule_eg(f'{o.name}NegatedDesignated')
        self.rule_eg(f'{o.name}NegatedUndesignated')
        self.valid_tab('Biconditional Elimination 1')

