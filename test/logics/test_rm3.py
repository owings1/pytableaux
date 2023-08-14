from .. import BaseCase

class Base(BaseCase):
    logic = 'RM3'

class TestTabRules(Base, autorules=True): pass

class TestArguments(Base):
    def test_valid_cond_mp(self):
        self.valid_tab('Conditional Modus Ponens')

    def test_valid_demorgan_1(self):
        self.valid_tab('DeMorgan 1')

    def test_valid_demorgan_2(self):
        self.valid_tab('DeMorgan 2')

    def test_valid_demorgan_3(self):
        self.valid_tab('DeMorgan 3')

    def test_valid_demorgan_4(self):
        self.valid_tab('DeMorgan 4')

    def test_invalid_b_then_a_arrow_b(self):
        self.invalid_tab('Uab', 'b')

    def test_valid_cond_modus_ponens(self):
        self.valid_tab('Conditional Modus Ponens')

    def test_invalid_a_a_arrow_not_b_arrow_c_thus_not_a_arrow_b(self):
        self.invalid_tab('NUab', 'a', 'UaNUbc')

    def test_valid_a_a_arrow_not_b_arrow_c_thus_not_b_arrow_c(self):
        # this is an instance of modus ponens
        self.valid_tab('NUbc', 'a', 'UaNUbc')

    def test_valid_bicond_thus_matbicond(self):
        self.valid_tab('Eab', 'Bab')

    def test_invalid_matbicon_thus_bicond(self):
        self.invalid_tab('Bab', 'Eab')

    def test_valid_mp_with_neg_bicon(self):
        self.valid_tab('NBab', 'c', 'BcNUab')


class TestModels(Base):

    def test_truth_table_conditional(self):
        tbl = self.m().truth_table('Conditional')
        self.assertEqual(tbl.outputs[0], 'T')
        self.assertEqual(tbl.outputs[1], 'T')
        self.assertEqual(tbl.outputs[2], 'T')
        self.assertEqual(tbl.outputs[3], 'F')
        self.assertEqual(tbl.outputs[4], 'B')
        self.assertEqual(tbl.outputs[5], 'T')
        self.assertEqual(tbl.outputs[6], 'F')
        self.assertEqual(tbl.outputs[7], 'F')
        self.assertEqual(tbl.outputs[8], 'T')

    def test_model_value_of_biconditional(self):
        model = self.m()
        model.set_literal_value(self.p('a'), 'B')
        model.set_literal_value(self.p('b'), 'F')
        self.assertEqual(model.value_of(self.p('Bab')), 'F')