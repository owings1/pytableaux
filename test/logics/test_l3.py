from ..utils import BaseCase

class Base(BaseCase):
    logic = 'L3'

class TestRules(Base, autorules=True): pass

class TestArguments(Base, autoargs=True):

    def test_valid_bicond_from_mat_bicond(self):
        self.valid_tab('Bab:Eab')

    def test_invalid_mat_bicon_from_bicond(self):
        self.invalid_tab('Eab:Bab')

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FNT',
        Negation = 'TNF',
        Conjunction = 'FFFFNNFNT',
        Disjunction = 'FNTNNTTTT',
        MaterialConditional = 'TTTNNTFNT',
        MaterialBiconditional = 'TNFNNNFNT',
        Conditional = 'TTTNTTFNT',
        Biconditional = 'TNFNTNFNT')
