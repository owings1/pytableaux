from ..utils import BaseCase
from pytableaux.lang import *
from pytableaux.proof import *

class Base(BaseCase):
    logic = 'P3'

class TestRules(Base, autorules=True):

    def test_Negation_nodes(self):
        sdn = self.sdnode
        tab = self.rule_test('DoubleNegationDesignated').tableau
        self.assertTrue(tab[0].all((
            sdn('a', False),
            sdn('Na', False),
        )))

class TestArguments(Base, autoargs=True): pass

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FNT',
        Negation = 'TFN',
        Conjunction = 'NNNNTFNFF',
        Disjunction = 'FNTNNTTTT',
        MaterialConditional = 'TTTFNTNNT',
        MaterialBiconditional = 'FNFNTFFFF',
        Conditional = 'TTTFNTNNT',
        Biconditional = 'FNFNTFFFF')


