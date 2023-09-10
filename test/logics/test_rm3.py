from ..utils import BaseCase

class Base(BaseCase):
    logic = 'RM3'

class TestRules(Base, autorules=True): pass

class TestArguments(Base, autoargs=True):

    def test_invalid_b_then_a_arrow_b(self):
        self.invalid_tab('Uab:b')

    def test_invalid_a_a_arrow_not_b_arrow_c_thus_not_a_arrow_b(self):
        self.invalid_tab('NUab:a:UaNUbc')

    def test_valid_a_a_arrow_not_b_arrow_c_thus_not_b_arrow_c(self):
        # this is an instance of modus ponens
        self.valid_tab('NUbc:a:UaNUbc')

    def test_valid_bicond_thus_matbicond(self):
        self.valid_tab('Eab:Bab')

    def test_invalid_matbicon_thus_bicond(self):
        self.invalid_tab('Bab:Eab')

    def test_valid_mp_with_neg_bicon(self):
        self.valid_tab('NBab:c:BcNUab')

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FBT',
        Negation = 'TBF',
        Conjunction = 'FFFFBBFBT',
        Disjunction = 'FBTBBTTTT',
        MaterialConditional = 'TTTBBTFBT',
        MaterialBiconditional = 'TBFBBBFBT',
        Conditional = 'TTTFBTFFT',
        Biconditional = 'TFFFBFFFT')

class TestModels(Base):

    def test_model_value_of_biconditional(self):
        s1, s2, s3 = self.pp('a', 'b', 'Bab')
        m = self.m()
        m.set_literal_value(s1, 'B')
        m.set_literal_value(s2, 'F')
        m.finish()
        self.assertEqual(m.value_of(s3), 'F')