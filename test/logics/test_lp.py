from ..utils import BaseCase

class Base(BaseCase):
    logic = 'LP'

class TestRules(Base, autorules=True): pass

class TestOperatorRules(Base):

    def test_regression_bad_rule_neg_bicond_undes(self):
        tab = self.tab('NBab', 'NBab', is_build = False)
        rule = tab.rules.get('BiconditionalNegatedUndesignated')
        self.assertTrue(rule.target(tab[0]))
        tab.build()
        self.assertTrue(tab.valid)

class TestArguments(Base):

    def test_arguments(self):
        self.valid_tab('Uab', 'b')
        self.valid_tab('NUab', ('a', 'Na', 'Nb'))
        self.invalid_tab('NUab', ('a', 'UaNUbc'))
        self.invalid_tab('NUbc', ('a', 'UaNUbc'))
        self.invalid_tab('NBab', ('c', 'BcNUab'))

    def test_invalid_lnc(self):
        self.invalid_tab('LNC')

    def test_invalid_mp(self):
        self.invalid_tab('MP')

    def test_valid_mat_ident(self):
        self.valid_tab('Material Identity')


class TestModels(Base):

    def test_regression_model_not_a_countermodel(self):
        arg = self.parg('NBab', 'c', 'BcNUab')
        model = self.m()
        model.set_literal_value(self.p('a'), 'F')
        model.set_literal_value(self.p('b'), 'T')
        model.set_literal_value(self.p('c'), 'B')
        self.assertEqual(model.value_of(arg.premises[1]), 'B')
