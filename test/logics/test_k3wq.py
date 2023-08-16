from ..utils import BaseCase

class Base(BaseCase):
    logic = 'K3WQ'

class TestRules(Base, autorules=True): pass

class TestArguments(Base):

    def test_valid_quantifier_interdefinability_1(self):
        self.valid_tab('Quantifier Interdefinability 1')

    def test_valid_quantifier_interdefinability_2(self):
        self.valid_tab('Quantifier Interdefinability 2')
        
    def test_valid_quantifier_interdefinability_3(self):
        self.valid_tab('Quantifier Interdefinability 3')

    def test_valid_quantifier_interdefinability_4(self):
        self.valid_tab('Quantifier Interdefinability 4')

    def test_valid_existential_to_if_a_then_a(self):
        self.valid_tab('CFmFm', 'SxFx')

class TestModels(Base):

    def test_model_existential_from_predicate_sentence_countermodel(self):
        s1, s2, s3 = self.pp('SxFx', 'Fm', 'Fn')
        arg = self.parg(s1, s2)
        m, = self.tab(arg, is_build_models = True).models
        self.assertIn(str(m.value_of(s1)), {'F', 'N'})
        self.assertEqual(m.value_of(s2), 'T')
        self.assertEqual(m.value_of(s3), 'N')
        self.assertTrue(m.is_countermodel_to(arg))

    def test_model_universal_from_predicate_sentence_countermodel(self):
        s1, s2 = self.pp('VxFx', 'Fm')
        arg = self.parg(s1, s2)
        m, = self.tab(arg, is_build_models = True).models
        self.assertIn(m.value_of(s1), ('F', 'N'))
        self.assertEqual(m.value_of(s2), 'T')
        self.assertTrue(m.is_countermodel_to(arg))
