from unittest import skip
from ..utils import BaseCase
from pytableaux.lang import *
from pytableaux.proof import *
from pytableaux.errors import *

A = Atomic.first()

class Base(BaseCase):
    logic = 'K3'

class TestRules(Base, autorules=True): pass

class TestArguments(Base, autoargs=True): pass

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FNT',
        Negation = 'TNF',
        Conjunction = 'FFFFNNFNT',
        Disjunction = 'FNTNNTTTT',
        MaterialConditional = 'TTTNNTFNT',
        MaterialBiconditional = 'TNFNNNFNT',
        Conditional = 'TTTNNTFNT',
        Biconditional = 'TNFNNNFNT',
    )

class TestOperators(Base):

    def test_Conjunction(self):
        self.valid_tab('LNC')

    def test_Disjunction(self):
        self.invalid_tab('LEM')

    def test_Biconditional(self):
        self.valid_tab('Biconditional Elimination 1')

