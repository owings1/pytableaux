from ..utils import BaseCase
from pytableaux.lang import Argument

class Base(BaseCase):
    logic = 'K3WQ'

class TestRules(Base, autorules=True): pass

class TestArguments(Base, autoargs=True):

    def test_valid_existential_to_if_a_then_a(self):
        self.valid_tab('CFmFm:SxFx')

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FNT',
        Negation = 'TNF',
        Conjunction = 'FNFNNNFNT',
        Disjunction = 'FNTNNNTNT',
        MaterialConditional = 'TNTNNNFNT',
        MaterialBiconditional = 'TNFNNNFNT',
        Conditional = 'TNTNNNFNT',
        Biconditional = 'TNFNNNFNT')

class TestModels(Base):

    def test_model_existential_from_predicate_sentence_countermodel(self):
        s1, s2 = arg = Argument('SxFx:Fm')
        s3 = self.p('Fn')
        m, = self.tab(arg, is_build_models = True).models
        self.assertIn(str(m.value_of(s1)), {'F', 'N'})
        self.assertEqual(m.value_of(s2), 'T')
        self.assertEqual(m.value_of(s3), 'N')
        self.assertTrue(m.is_countermodel_to(arg))

    def test_model_universal_from_predicate_sentence_countermodel(self):
        s1, s2 = arg = Argument('VxFx:Fm')
        m, = self.tab(arg, is_build_models = True).models
        self.assertIn(m.value_of(s1), ('F', 'N'))
        self.assertEqual(m.value_of(s2), 'T')
        self.assertTrue(m.is_countermodel_to(arg))
