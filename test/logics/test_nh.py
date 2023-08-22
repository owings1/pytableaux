from ..utils import BaseCase

class Base(BaseCase):
    logic = 'NH'

class TestRules(Base, autorules=True): pass
class TestArguments(Base, autoargs=True): pass

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FBT',
        Negation = 'TBF',
        Conjunction = 'FFFFTBFBT',
        Disjunction = 'FBTBBTTTT',
        MaterialConditional = 'TTTBBTFBT',
        MaterialBiconditional = 'TBFBTBFBT',
        Conditional = 'TTTFTTFTT',
        Biconditional = 'TFFFTTFTT')
