from ..utils import BaseCase

class Base(BaseCase):
    logic = 'B3E'

class TestRules(Base, autorules=True): pass

class TestArguments(Base, autoargs=True):

    def test_invalid_prior_rule_defect(self):
        self.invalid_tab('ANAabNa:Na')

    def test_valid_prior_rule_defect2(self):
        self.valid_tab('AANaTbNa:Na')


class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FFT',
        Negation = 'TNF',
        Conjunction = 'FNFNNNFNT',
        Disjunction = 'FNTNNNTNT',
        MaterialConditional = 'TNTNNNFNT',
        MaterialBiconditional = 'TNFNNNFNT',
        Conditional = 'TTTTTTFFT',
        Biconditional = 'TTFTTFFFT')

