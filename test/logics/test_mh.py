from ..utils import BaseCase

class Base(BaseCase):
    logic = 'MH'

class TestRules(Base, autorules=True): pass
class TestArguments(Base, autoargs=True): pass

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FNT',
        Negation = 'TNF',
        Conjunction = 'FFFFNNFNT',
        Disjunction = 'FNTNFTTTT',
        MaterialConditional = 'TTTNFTFNT',
        MaterialBiconditional = 'TNFNFNFNT',
        Conditional = 'TTTTTTFFT',
        Biconditional = 'TTFTTFFFT')

