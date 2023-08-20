from ..utils import BaseCase

class Base(BaseCase):
    logic = 'L3'

class TestRules(Base, autorules=True): pass

class TestArguments(Base, autoargs=True):

    def test_valid_bicond_from_mat_bicond(self):
        self.valid_tab('Bab', 'Eab')

    def test_invalid_mat_bicon_from_bicond(self):
        self.invalid_tab('Eab', 'Bab')

class TestTruthTables(Base):

    def test_truth_table_conditional(self):
        tbl = self.m().truth_table('Conditional')
        self.assertEqual(tbl.outputs[3], 'N')
        self.assertEqual(tbl.outputs[4], 'T')
        self.assertEqual(tbl.outputs[6], 'F')