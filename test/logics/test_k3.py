from unittest import skip
from .. import BaseCase
from pytableaux.lang import *
from pytableaux.proof import *
from pytableaux.errors import *

A = Atomic.first()

class Base(BaseCase):
    logic = 'K3'

class TestTabRules(Base, autorules=True): pass

class TestArguments(Base):

    def test_DeMorgan(self):
        self.valid_tab('DeMorgan 1')
        self.valid_tab('DeMorgan 2')
        self.valid_tab('DeMorgan 3')
        self.valid_tab('DeMorgan 4')

class TestOperators(Base):

    def test_Conjunction(self):
        self.valid_tab('LNC')

    def test_Disjunction(self):
        self.invalid_tab('LEM')

    def test_Biconditional(self):
        self.valid_tab('Biconditional Elimination 1')

