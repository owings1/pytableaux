from ..utils import BaseCase

class Base(BaseCase):
    logic = 'L3'

class TestRules(Base, autorules=True): pass

class TestArguments(Base):

    def test_valid_cond_identity(self):
        self.valid_tab('Conditional Identity')

    def test_valid_cond_mp(self):
        self.valid_tab('Conditional Modus Ponens')

    def test_valid_bicond_elim_1(self):
        self.valid_tab('Biconditional Elimination 1')

    def test_valid_bicond_elim_3(self):
        self.valid_tab('Biconditional Elimination 3')

    def test_valid_bicond_intro_3(self):
        self.valid_tab('Biconditional Introduction 3')

    def test_valid_bicond_ident(self):
        self.valid_tab('Biconditional Identity')

    def test_valid_bicond_from_mat_bicond(self):
        self.valid_tab('Bab', 'Eab')

    def test_invalid_material_identify(self):
        self.invalid_tab('Material Identity')

    def test_invalid_cond_contraction(self):
        self.invalid_tab('Conditional Contraction')

    def test_invalid_cond_pseudo_contraction(self):
        self.invalid_tab('Conditional Pseudo Contraction')

    def test_invalid_mat_bicon_from_bicond(self):
        self.invalid_tab('Eab', 'Bab')

    def test_invalid_cond_lem(self):
        self.invalid_tab('AUabNUab')

class TestTruthTables(Base):

    def test_truth_table_conditional(self):
        tbl = self.m().truth_table('Conditional')
        self.assertEqual(tbl.outputs[3], 'N')
        self.assertEqual(tbl.outputs[4], 'T')
        self.assertEqual(tbl.outputs[6], 'F')