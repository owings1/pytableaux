from ..utils import BaseCase

class Base(BaseCase):
    logic = 'LP'

class TestRules(Base, autorules=True): pass

class TestArguments(Base, autoargs=True):

    def test_arguments(self):
        self.valid_tab('NUab', ('a', 'Na', 'Nb'))
        self.invalid_tab('NUab', ('a', 'UaNUbc'))
        self.invalid_tab('NUbc', ('a', 'UaNUbc'))
        self.invalid_tab('NBab', ('c', 'BcNUab'))

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FBT',
        Negation = 'TBF',
        Conjunction = 'FFFFBBFBT',
        Disjunction = 'FBTBBTTTT',
        MaterialConditional = 'TTTBBTFBT',
        MaterialBiconditional = 'TBFBBBFBT',
        Conditional = 'TTTBBTFBT',
        Biconditional = 'TBFBBBFBT')

class TestOperatorRules(Base):

    def test_regression_bad_rule_neg_bicond_undes(self):
        tab = self.tab('NBab', 'NBab', is_build = False)
        rule = tab.rules.get('BiconditionalNegatedUndesignated')
        self.assertTrue(rule.target(tab[0]))
        tab.build()
        self.assertTrue(tab.valid)

class TestModels(Base):

    def test_regression_model_not_a_countermodel(self):
        arg = self.parg('NBab', 'c', 'BcNUab')
        s1, s2, s3 = self.pp(*'abc')
        m = self.m()
        m.set_literal_value(s1, 'F')
        m.set_literal_value(s2, 'T')
        m.set_literal_value(s3, 'B')
        m.finish()
        self.assertEqual(m.value_of(arg.premises[1]), 'B')
