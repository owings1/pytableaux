from ..utils import BaseCase

class Base(BaseCase):
    logic = 'B3E'

class TestRules(Base, autorules=True): pass
class TestAutoArgs(Base, autoargs=True): pass


class TestArguments(Base):

    def test_valid_cond_contraction(self):
        self.valid_tab('Conditional Contraction')

    def test_valid_bicond_elim_1(self):
        self.valid_tab('Biconditional Elimination 1')

    def test_valid_bicond_elim_3(self):
        self.valid_tab('Biconditional Elimination 3')

    def test_valid_bicond_intro_1(self):
        self.valid_tab('Biconditional Introduction 1')

    def test_invalid_lem(self):
        self.invalid_tab('Law of Excluded Middle')

    def test_invalid_prior_rule_defect(self):
        self.invalid_tab('ANAabNa', 'Na')

    def test_valid_prior_rule_defect2(self):
        self.valid_tab('AANaTbNa', 'Na')

    def test_valid_asserted_addition(self):
        self.valid_tab('AaTb', 'a')

    def test_valid_cond_lem(self):
        self.valid_tab('AUabNUab')

class TestTruthTables(Base):

    def test_truth_table_assertion(self):
        tbl = self.m().truth_table('Assertion')
        self.assertEqual(tbl.outputs, ('F', 'F', 'T'))

    def test_truth_table_conditional(self):
        tbl = self.m().truth_table('Conditional')
        self.assertEqual(tbl.outputs[3], 'T')
        self.assertEqual(tbl.outputs[4], 'T')
        self.assertEqual(tbl.outputs[7], 'F')

    def test_truth_table_biconditional(self):
        tbl = self.m().truth_table('Biconditional')
        self.assertEqual(tbl.outputs[2], 'F')
        self.assertEqual(tbl.outputs[4], 'T')
        self.assertEqual(tbl.outputs[7], 'F')