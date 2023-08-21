from ..utils import BaseCase
from pytableaux.lang import *
from pytableaux.proof import *

class Base(BaseCase):
    logic = 'GO'

class TestRules(Base, autorules=True): pass

class TestArguments(Base, autoargs=True):

    def test_valid_prior_b3e_rule_defect2(self):
        self.valid_tab('AANaTbNa', 'Na')

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FFT',
        Negation = 'TNF',
        Disjunction = 'FFTFFTTTT',
        Conjunction = 'FFFFFFFFT',
        MaterialConditional = 'TTTFFTFFT',
        MaterialBiconditional = 'TFFFFFFFT',
        Conditional = 'TTTFTTFFT',
        Biconditional = 'TFFFTFFFT',
    )

class TestGO(Base):


    def test_MaterialConditionalNegatedDesignated_step(self):
        sdn = self.sdnode
        tab, b = self.tabb(sdn('NCab', True))
        tab.step()
        self.assertTrue(b.has(sdn('Na',  False)))
        self.assertTrue(b.has(sdn('b',  False)))

    def test_MaterialBionditionalNegatedDesignated_step(self):
        sdn = self.sdnode
        tab = self.tab(nn=sdn('NEab', True))
        tab.step()
        b1, b2 = tab
        self.assertTrue(b1.has(sdn('Na', False)))
        self.assertTrue(b1.has(sdn('b', False)))
        self.assertTrue(b2.has(sdn('a', False)))
        self.assertTrue(b2.has(sdn('Nb', False)))

    def test_ConditionalDesignated_step(self):
        sdn = self.sdnode
        tab = self.tab(nn=sdn('Uab', True))
        tab.step()
        b1, b2 = tab
        self.assertTrue(b1.has(sdn('ANab', True)))
        self.assertTrue(b2.has(sdn('a', False)))
        self.assertTrue(b2.has(sdn('b', False)))
        self.assertTrue(b2.has(sdn('Na', False)))
        self.assertTrue(b2.has(sdn('Nb', False)))

    def test_ConditionalNegatedDesignated_step(self):
        sdn = self.sdnode
        tab = self.tab(nn=sdn('NUab', True))
        tab.step()
        b1, b2 = tab
        self.assertTrue(b1.has(sdn('a', True)))
        self.assertTrue(b1.has(sdn('b', False)))
        self.assertTrue(b2.has(sdn('Na', False)))
        self.assertTrue(b2.has(sdn('Nb', True)))

    def test_BiconditionalDesignated_step(self):
        sdn = self.sdnode
        tab, b = self.tabb(sdn('Bab', True))
        tab.step()
        self.assertTrue(b.has(sdn('Uab', True)))
        self.assertTrue(b.has(sdn('Uba', True)))

    def test_BiconditionalNegatedDesignated_step(self):
        sdn = self.sdnode
        tab = self.tab(nn=sdn('NBab', True))
        tab.step()
        b1, b2 = tab
        self.assertTrue(b1.has(sdn('NUab', True)))
        self.assertTrue(b2.has(sdn('NUba', True)))

    def test_AssertionUndesignated_step(self):
        sdn = self.sdnode
        tab, b = self.tabb(sdn('Ta', False))
        tab.step()
        self.assertTrue(b.has(sdn('a', False)))

    def test_AssertionNegatedDesignated_step(self):
        sdn = self.sdnode
        tab, b = self.tabb(sdn('NTa', True))
        tab.step()
        self.assertTrue(b.has(sdn('a', False)))

    def test_AssertionNegatedUndesignated_step(self):
        sdn = self.sdnode
        tab, b = self.tabb(sdn('NTa', False))
        tab.step()
        self.assertTrue(b.has(sdn('a', True)))

    def test_branching_complexity_inherits_branchables(self):
        sdn = self.sdnode
        tab, b = self.tabb(sdn('Kab', False))
        node = b[0]
        self.assertEqual(self.logic.System.branching_complexity(node, tab.rules), 0)